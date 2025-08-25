"""
Stack-based C++ Access Analyzer
Implements context-aware AST traversal to track entity accesses

TODO: Type-Aware Method Call Tracking
--------------------------------------
Current limitation: When tracking method calls like `ctx->SetDisplayMode(mode)`, 
we record the access to the method name but cannot determine:
1. The actual type of `ctx` (could be Context* or ContextGL*)
2. Which overload of SetDisplayMode is being called (depends on type of `mode`)
3. The correct method entity in the inheritance hierarchy

Future enhancement: Integrate libclang for type-aware access tracking
- Use libclang to get exact types of variables and expressions
- Resolve method calls to specific overloads based on argument types  
- Track both the object being called AND the specific method entity
- Handle virtual dispatch correctly

Implementation approach:
1. Keep tree-sitter for fast structural parsing
2. Add optional libclang pass for type resolution when compile_commands.json available
3. For each method call, record TWO accesses:
   - READ access to the object variable (if it's a member)
   - CALL access to the specific method entity (with correct overload)

See test_class_parsing_validation_clang.py for existing libclang integration example.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Tuple
from pathlib import Path
import json
import tree_sitter as ts
import tree_sitter_cpp as ts_cpp
from tree_sitter import Language, Parser, Node
from obt.cpp_database_v2 import CppDatabaseV2

class StackTreeNode:
    """Wrapper for tree-sitter nodes that tracks parent relationships"""
    def __init__(self, ts_node: Node, parent: Optional['StackTreeNode'] = None):
        self.node = ts_node  # The actual tree-sitter node
        self.parent = parent  # Our parent StackTreeNode
        self._children = None  # Cache children
    
    @property
    def type(self):
        return self.node.type
    
    @property
    def text(self):
        return self.node.text
    
    @property
    def start_point(self):
        return self.node.start_point
    
    @property
    def end_point(self):
        return self.node.end_point
    
    @property
    def children(self):
        """Wrap children on demand with self as parent"""
        if self._children is None:
            self._children = [StackTreeNode(child, parent=self) for child in self.node.children]
        return self._children
    
    def get_ancestor(self, levels_up: int = 1) -> Optional['StackTreeNode']:
        """Walk up the tree by specified levels"""
        current = self
        for _ in range(levels_up):
            if current.parent:
                current = current.parent
            else:
                return None
        return current

class AccessType(Enum):
    """Types of entity access"""
    READ = "read"
    WRITE = "write"
    CALL = "call"
    ADDRESS_OF = "address_of"
    READ_WRITE = "read_write"  # For ++ and +=
    DEF = "def"  # Definition/declaration
    IMPL = "impl"  # Implementation/instantiation (static members, templates, etc.)


@dataclass
class Access:
    """Represents a detected access"""
    raw_identifier: str
    access_type: AccessType
    file_path: Path
    trimmed_line: int
    original_line: int
    column: int
    context_function: Optional[str] = None
    context_class: Optional[str] = None
    context_namespace: Optional[str] = None
    context_snippet: Optional[str] = None
    entity_id: Optional[int] = None
    member_id: Optional[int] = None

class StackBasedAccessAnalyzer:
    """Stack-based analyzer for C++ entity accesses"""
    
    def __init__(self, db_path: str, track_operators: bool = False):
        self.db = CppDatabaseV2(db_path)
        self.track_operators = track_operators
        self.accesses: List[Access] = []
        self.current_file: Optional[Path] = None
        self.line_mapping: Optional[Dict[int, int]] = None
        self.source_bytes: Optional[bytes] = None
        
        # Context tracking
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
        self.current_namespace: Optional[str] = None
        
        # Initialize parser
        self.parser = Parser()
        self.parser.set_language(Language(ts_cpp.language(), "cpp"))
        
    def analyze_file(self, file_path: Path, trimmed_source: str, 
                     line_mapping: Dict[int, int]) -> List[Access]:
        """
        Main entry point for analyzing a file
        
        Args:
            file_path: Path to the source file
            trimmed_source: The trimmed source code
            line_mapping: Maps trimmed line numbers to original line numbers
            
        Returns:
            List of detected accesses
        """
        self.current_file = file_path
        self.line_mapping = line_mapping
        self.accesses = []
        self.source_bytes = trimmed_source.encode()
        
        # Parse the source
        tree = self.parser.parse(self.source_bytes)
        
        # Wrap root node and analyze
        wrapped_root = StackTreeNode(tree.root_node, parent=None)
        self._analyze_node(wrapped_root)
        
        return self.accesses
    
    def _analyze_node(self, node: StackTreeNode):
        """
        Single traversal - node already has parent tracking
        """
        # Update namespace/class/function context
        self._update_context(node)
            
        
        # Process terminal nodes (actual accesses and declarations)
        if node.type in ['identifier', 'field_identifier']:
            # Check if this is being declared
            if self._is_being_declared(node):
                # Track as definition
                self._record_access(node, AccessType.DEF)
            else:
                access_type = self._determine_access_type(node)
                if access_type:  # None means don't track (just navigation)
                    self._record_access(node, access_type)
        # Note: qualified_identifier is NOT a terminal - its children will be processed by recursion
        
        # ALWAYS recurse to children - this is orthogonal to pattern matching
        for child in node.children:
            self._analyze_node(child)
    
    def _determine_access_type(self, node: StackTreeNode) -> Optional[AccessType]:
        """
        Determine if and how to track this access.
        Returns None if this is just navigation (not an endpoint).
        """
        # Check if we're an endpoint or just part of the path
        if not self._is_endpoint(node):
            return None
        
        parent = node.parent
        if not parent:
            return AccessType.READ  # Default for top-level identifiers
        
        grandparent = node.get_ancestor(2)
        
        # Check immediate parent type
        if parent.type == 'pointer_expression':
            # Check if it's address-of
            for child in parent.children:
                if child.type == '&' and child.text == b'&':
                    return AccessType.ADDRESS_OF
        
        # Update expressions (++, --, +=, etc)
        if parent.type == 'update_expression':
            return AccessType.READ_WRITE
        
        # Field expression - could be member access or method call
        if parent.type == 'field_expression':
            # Determine if we're the object or the field
            # In obj.field, obj is children[0], field is children[2] (after the dot)
            if parent.children[0] == node:
                # We're the object part - always READ (reading the object to access its member)
                return AccessType.READ
            else:
                # We're the field part - check what's happening to the field
                if grandparent and grandparent.type == 'call_expression':
                    # Check if the field_expression is being called
                    if grandparent.children[0] == parent:
                        # TODO: This records CALL access to just the method NAME, not the actual method entity
                        # For proper tracking, we need to:
                        # 1. Determine the type of the object (children[0])
                        # 2. Find the method entity in that class with matching signature
                        # 3. Record CALL access to that specific method entity
                        # This requires type resolution - see file header TODO for libclang integration
                        return AccessType.CALL  # The field is a method being called
                # Check if grandparent is assignment
                if grandparent and grandparent.type == 'assignment_expression':
                    # Check if we're on left side of assignment
                    if grandparent.children[0] == parent:
                        return AccessType.WRITE  # The field is being written to
                return AccessType.READ  # The field is being read
        
        # Direct call (function name)
        if parent.type == 'call_expression':
            # Check if we're the function being called
            if parent.children[0] == node:
                return AccessType.CALL
            return AccessType.READ  # We're an argument
        
        # Assignment expression
        if parent.type == 'assignment_expression':
            # Check which side we're on
            left_side = parent.children[0]
            if left_side == node:
                return AccessType.WRITE
            # Skip the operator, check if we're on right side
            for i, child in enumerate(parent.children):
                if child == node and i > 0:
                    return AccessType.READ
        
        # Argument list - parameters are being read
        if parent.type == 'argument_list':
            return AccessType.READ
        
        # Binary expressions - operands are read
        if parent.type == 'binary_expression':
            return AccessType.READ
        
        # Subscript expression - array/container access
        if parent.type == 'subscript_expression':
            # The array/container is being read
            if parent.children[0] == node:
                return AccessType.READ
            # The index is also being read
            return AccessType.READ
        
        # Qualified identifier - like Class::member
        if parent.type == 'qualified_identifier':
            # Check what the qualified identifier is used for
            grandparent = node.get_ancestor(2)
            if grandparent:
                if grandparent.type == 'declaration':
                    # If it's a qualified name in a declaration (e.g., Context::mDisplayModes),
                    # it's implementing/instantiating something already declared
                    if '::' in parent.text.decode():
                        return AccessType.IMPL
                    return AccessType.DEF
                elif grandparent.type == 'assignment_expression':
                    if grandparent.children[0] == parent:
                        return AccessType.WRITE
                    return AccessType.READ
            return AccessType.READ
        
        # Return statement - value is being read
        if parent.type == 'return_statement':
            return AccessType.READ
        
        # Default
        return AccessType.READ
    
    def _is_endpoint(self, node: StackTreeNode) -> bool:
        """
        Check if this node is an endpoint (should be tracked) 
        or just part of navigation path.
        
        For now, let's track everything and refine later.
        """
        # TODO: Implement proper endpoint detection once parent tracking is verified
        return True
    
    def _is_call_target(self, node: StackTreeNode) -> bool:
        """Check if this node is the target of a call expression"""
        if parent and parent.type == 'call_expression':
            # The first child is the function being called
            return parent.children and node == parent.children[0]
        return False
    
    def _is_terminal_field(self, node: StackTreeNode) -> bool:
        """Check if this field_identifier is the terminal field in a chain"""
        # TODO: Implement proper terminal field detection
        return True
    
    def _record_access(self, node: StackTreeNode, access_type: AccessType):
        """Record a detected access"""
        # Get identifier text
        identifier = node.text.decode() if node.text else ""
        
        # Get line and column
        trimmed_line = node.start_point[0] + 1  # tree-sitter uses 0-based
        column = node.start_point[1]
        
        # Map to original line
        original_line = self.line_mapping.get(trimmed_line, trimmed_line)
        
        # Get context snippet
        snippet = self._get_context_snippet(node)
        
        # Create access record
        access = Access(
            raw_identifier=identifier,
            access_type=access_type,
            file_path=self.current_file,
            trimmed_line=trimmed_line,
            original_line=original_line,
            column=column,
            context_function=self.current_function,
            context_class=self.current_class,
            context_namespace=self.current_namespace,
            context_snippet=snippet
        )
        
        self.accesses.append(access)
    
    def _is_declaration_context(self, node: StackTreeNode) -> bool:
        """
        Check if this node is part of a declaration context where
        identifiers should not be tracked as accesses.
        """
        # These node types are declarations, not accesses
        # Note: We only want the declaration part, not the body/initializer
        declaration_types = {
            'declaration',
            'field_declaration',
            'field_declaration_list',  # Class/struct member declarations
            'parameter_declaration',
            # Don't include function_declaration - we want to track accesses in function bodies
            # Don't include class_specifier - we want to track accesses in class bodies
            # Only pure type declarations:
            'type_descriptor',
            'abstract_declarator',
            'abstract_pointer_declarator',
            'abstract_array_declarator',
            'abstract_function_declarator',
            'abstract_reference_declarator'
        }
        
        # Check if this node itself is a declaration
        return node.type in declaration_types
    
    def _is_being_declared(self, node: StackTreeNode) -> bool:
        """
        Check if this specific identifier is the thing being declared,
        not just something used in a declaration's initializer.
        """
        parent = node.parent
        if not parent:
            return False
            
        # In an init_declarator, the first child is the identifier being declared
        if parent.type == 'init_declarator':
            return parent.children and node == parent.children[0]
            
        # If we are a field_identifier in a field_declaration
        if node.type == 'field_identifier':
            # Check if parent is field_declaration
            if parent and parent.type == 'field_declaration':
                return True
                
        # In a parameter_declaration, the identifier is being declared
        if parent.type == 'parameter_declaration':
            return True
            
        # In a function_declarator, the identifier is the function name being declared
        if parent.type == 'function_declarator':
            # Check if we're the function name (usually first identifier child)
            for child in parent.children:
                if child.type in ['identifier', 'field_identifier', 'qualified_identifier']:
                    return node == child
                    
        return False
    
    def _update_context(self, node: StackTreeNode):
        """Update namespace/class/function context based on node type"""
        if node.type == 'namespace_definition':
            # Extract namespace name
            for child in node.children:
                if child.type == 'namespace_identifier':
                    self.current_namespace = child.text.decode()
                    break
                    
        elif node.type in ['class_specifier', 'struct_specifier']:
            # Extract class/struct name
            for child in node.children:
                if child.type == 'type_identifier':
                    self.current_class = child.text.decode()
                    break
                    
        elif node.type == 'function_definition':
            # Extract function name from declarator
            for child in node.children:
                if child.type == 'function_declarator':
                    # Get the identifier from the declarator
                    for subchild in child.children:
                        if subchild.type in ['identifier', 'field_identifier', 'qualified_identifier']:
                            full_name = subchild.text.decode()
                            self.current_function = full_name
                            
                            # If it's a qualified identifier (Class::method), extract class context
                            if subchild.type == 'qualified_identifier' and '::' in full_name:
                                parts = full_name.rsplit('::', 1)
                                if len(parts) == 2:
                                    self.current_class = parts[0]
                                    self.current_function = parts[1]
                            break
                    break
                elif child.type == 'reference_declarator':
                    # Sometimes the function_declarator is inside a reference_declarator
                    for subchild in child.children:
                        if subchild.type == 'function_declarator':
                            for subsubchild in subchild.children:
                                if subsubchild.type in ['identifier', 'field_identifier', 'qualified_identifier']:
                                    full_name = subsubchild.text.decode()
                                    self.current_function = full_name
                                    
                                    # If it's a qualified identifier (Class::method), extract class context
                                    if subsubchild.type == 'qualified_identifier' and '::' in full_name:
                                        parts = full_name.rsplit('::', 1)
                                        if len(parts) == 2:
                                            self.current_class = parts[0]
                                            self.current_function = parts[1]
                                    break
                            break
    
    
    def _get_operator_text(self, node: StackTreeNode) -> str:
        """Extract operator text from a node"""
        # Find the operator child
        for child in node.children:
            if child.type in ['&', '*', '++', '--', '+', '-', '/', '%', '<<', '>>', 
                              '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!']:
                return child.type
        
        # Fallback to extracting from text
        if node.text:
            text = node.text.decode()
            # Extract operator from text...
            # This is simplified - real implementation would be more robust
            return text
        
        return ""
    
    def _is_assignment_operator(self, node: StackTreeNode) -> bool:
        """Check if node is an assignment operator"""
        return node.type in ['=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=']
    
    def _get_context_snippet(self, node: StackTreeNode, context_lines: int = 1) -> str:
        """Get a code snippet around the access for context"""
        if not self.source_bytes:
            return ""
        
        # Get the line containing the access
        lines = self.source_bytes.decode().split('\n')
        line_idx = node.start_point[0]
        
        # Get surrounding lines
        start_idx = max(0, line_idx - context_lines)
        end_idx = min(len(lines), line_idx + context_lines + 1)
        
        snippet_lines = lines[start_idx:end_idx]
        return '\n'.join(snippet_lines)
    
    def resolve_accesses(self, accesses: List[Access]) -> List[Access]:
        """
        Resolve raw identifiers to database entities.
        This runs after all files have been analyzed.
        """
        with self.db.connect() as conn:
            cursor = conn.cursor()
            
            for access in accesses:
                entity_id, member_id = self._resolve_identifier(
                    cursor,
                    access.raw_identifier,
                    access.context_class,
                    access.context_namespace
                )
                
                access.entity_id = entity_id
                access.member_id = member_id
        
        return accesses
    
    def _resolve_identifier(self, cursor, identifier: str, 
                           context_class: Optional[str], 
                           context_namespace: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """
        Resolve identifier to entity/member IDs.
        
        Resolution order:
        1. If contains ::, treat as qualified name
        2. Check as member of context class (if in class context)
        3. Check local namespace
        4. Check global namespace
        """
        # This is a simplified version - full implementation would be more sophisticated
        
        # Try to find as a member of the context class (NO PREFIX ASSUMPTIONS)
        if context_class:
            # Look for member in context class
            result = cursor.execute("""
                SELECT em.id, em.entity_id
                FROM entity_members em
                JOIN entities e ON em.entity_id = e.id
                WHERE e.short_name = ? AND em.name = ?
            """, (context_class, identifier)).fetchone()
            
            if result:
                return result['entity_id'], result['id']
        
        # Try to find as a function or type
        if '::' in identifier:
            # Qualified name
            result = cursor.execute("""
                SELECT id FROM entities WHERE canonical_name = ?
            """, (identifier,)).fetchone()
        else:
            # Unqualified - try with namespace context
            if context_namespace:
                full_name = f"{context_namespace}::{identifier}"
                result = cursor.execute("""
                    SELECT id FROM entities WHERE canonical_name = ?
                """, (full_name,)).fetchone()
            else:
                result = cursor.execute("""
                    SELECT id FROM entities WHERE short_name = ?
                """, (identifier,)).fetchone()
        
        if result:
            return result['id'], None
        
        return None, None

# Module exports
__all__ = ['StackBasedAccessAnalyzer', 'AccessType', 'Access', 'ContextFrame']