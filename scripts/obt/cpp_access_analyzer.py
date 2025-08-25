#!/usr/bin/env python3
"""
C++ Access Analyzer - Second-pass analysis for tracking entity accesses
Analyzes C++ source code to track reads, writes, and calls to entities
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import tree_sitter_cpp as ts_cpp
from tree_sitter import Language, Parser, Node

@dataclass
class AccessRecord:
    """Record of an entity access"""
    accessed_entity: str  # Canonical name or partial name
    access_type: str  # 'read', 'write', 'call'  
    file_path: str
    line_number: int
    column_number: int
    accessing_function: Optional[str] = None  # Function performing the access
    context_snippet: Optional[str] = None  # Code snippet for context
    
class CppAccessAnalyzer:
    """
    Second-pass analyzer for tracking entity accesses in C++ code
    Runs after initial parsing to track reads, writes, and calls
    """
    
    def __init__(self, db=None, verbose: bool = False, debug: bool = False):
        """
        Initialize the access analyzer
        
        Args:
            db: CppDatabaseV2 instance with populated entities
            verbose: Enable verbose output
            debug: Enable debug output
        """
        self.db = db
        self.verbose = verbose
        self.debug = debug
        self.parser = Parser()
        self.parser.set_language(Language(ts_cpp.language(), "cpp"))
        
        # Access tracking state
        self.accesses = []
        self.current_file = None
        self.current_function_context = None
        self.current_class_context = None  # Track current class for member resolution
        self.namespace_stack = []
        self.class_stack = []  # Stack for nested classes
        
    def analyze_file(self, filepath: Path, source_code: Optional[str] = None) -> List[AccessRecord]:
        """
        Analyze a file for entity accesses
        
        Args:
            filepath: Path to the C++ file
            source_code: Optional source code (if not provided, will read from file)
            
        Returns:
            List of AccessRecord objects
        """
        self.current_file = filepath
        self.accesses = []
        self.namespace_stack = []
        self.current_function_context = None
        
        # Read source if not provided
        if source_code is None:
            source_code = filepath.read_text(encoding='utf-8', errors='ignore')
        
        # Parse with tree-sitter
        tree = self.parser.parse(source_code.encode('utf-8'))
        source_bytes = source_code.encode('utf-8')
        
        # Analyze the AST
        self._analyze_node(tree.root_node, source_bytes)
        
        return self.accesses
    
    def _analyze_node(self, node: Node, source: bytes):
        """Recursively analyze AST nodes"""
        
        if self.debug and node.type in ['function_definition', 'call_expression', 'field_expression']:
            print(f"DEBUG: Found {node.type} at line {source[:node.start_byte].count(b'\\n') + 1}")
        
        # Track namespace context
        if node.type == 'namespace_definition':
            self._enter_namespace(node, source)
            for child in node.children:
                self._analyze_node(child, source)
            self._exit_namespace()
            return
        
        # Track class/struct context
        elif node.type in ['class_specifier', 'struct_specifier']:
            self._analyze_class_definition(node, source)
            return
        
        # Track function context
        elif node.type == 'function_definition':
            self._analyze_function_definition(node, source)
            return
        
        # Look for expressions that access entities
        elif node.type == 'expression_statement':
            self._analyze_expression_statement(node, source)
        
        elif node.type == 'return_statement':
            self._analyze_return_statement(node, source)
        
        elif node.type == 'if_statement':
            self._analyze_if_statement(node, source)
        
        elif node.type == 'for_statement' or node.type == 'while_statement':
            self._analyze_loop_statement(node, source)
        
        elif node.type == 'declaration':
            self._analyze_declaration(node, source)
        
        # Recurse for other node types
        else:
            for child in node.children:
                self._analyze_node(child, source)
    
    def _enter_namespace(self, node: Node, source: bytes):
        """Enter a namespace scope"""
        for child in node.children:
            if child.type == 'identifier' or child.type == 'namespace_identifier':
                namespace_name = self._extract_text(child, source)
                self.namespace_stack.append(namespace_name)
                break
    
    def _exit_namespace(self):
        """Exit a namespace scope"""
        if self.namespace_stack:
            self.namespace_stack.pop()
    
    def _analyze_class_definition(self, node: Node, source: bytes):
        """Analyze a class/struct definition"""
        class_name = None
        
        # Extract class name
        for child in node.children:
            if child.type == 'type_identifier':
                class_name = self._extract_text(child, source)
                break
        
        if class_name:
            # Build full qualified name
            full_name = '::'.join(self.namespace_stack + [class_name]) if self.namespace_stack else class_name
            
            # Enter class context
            self.class_stack.append(full_name)
            old_class = self.current_class_context
            self.current_class_context = full_name
            
            # Analyze class body
            for child in node.children:
                if child.type == 'field_declaration_list':
                    # This contains the class members
                    for member_child in child.children:
                        self._analyze_node(member_child, source)
            
            # Exit class context
            self.class_stack.pop()
            self.current_class_context = old_class
    
    def _analyze_function_definition(self, node: Node, source: bytes):
        """Analyze a function definition and its body"""
        print(f"ENTERING FUNCTION at line {source[:node.start_byte].count(b'\n') + 1}")
        
        # Extract function name for context
        function_name = None
        compound_statement = None
        
        for child in node.children:
            if child.type == 'function_declarator':
                function_name = self._extract_function_name(child, source)
                print(f"  Function name: {function_name}")
            elif child.type == 'compound_statement':
                compound_statement = child
                print(f"  Found compound_statement")
        
        if function_name:
            # Build full qualified name with namespace
            if self.namespace_stack:
                full_name = '::'.join(self.namespace_stack) + '::' + function_name
            else:
                full_name = function_name
            
            print(f"  Full function name: {full_name}")
            
            # Analyze function body with this context
            if compound_statement:
                print(f"  ANALYZING BODY with class context: {self.current_class_context}")
                old_func_context = self.current_function_context
                old_class_context = self.current_class_context
                self.current_function_context = full_name
                # Note: current_class_context may have been set by qualified_identifier extraction
                self._analyze_compound_statement(compound_statement, source)
                self.current_function_context = old_func_context
                self.current_class_context = old_class_context
                print(f"  DONE WITH BODY")
    
    def _extract_function_name(self, declarator_node: Node, source: bytes) -> Optional[str]:
        """Extract function name from function_declarator node"""
        for child in declarator_node.children:
            if child.type == 'qualified_identifier':
                # This is like ClassName::methodName
                text = self._extract_text(child, source)
                # Also extract the class name for context
                parts = text.split('::')
                if len(parts) >= 2:
                    # Set class context from the qualified name
                    self.current_class_context = '::'.join(parts[:-1])
                return text
            elif child.type in ['identifier', 'field_identifier', 'destructor_name']:
                return self._extract_text(child, source)
            elif child.type == 'operator_name':
                return self._extract_operator_name(child, source)
        return None
    
    def _extract_operator_name(self, node: Node, source: bytes) -> str:
        """Extract operator name like operator+"""
        text = self._extract_text(node, source)
        # Normalize operator names
        return text.replace(' ', '')
    
    def _analyze_compound_statement(self, node: Node, source: bytes):
        """Analyze a compound statement (block)"""
        for child in node.children:
            if child.type not in ['{', '}']:
                self._analyze_node(child, source)
    
    def _analyze_expression_statement(self, node: Node, source: bytes):
        """Analyze an expression statement"""
        for child in node.children:
            if child.type != ';':
                self._analyze_expression(child, source)
    
    def _analyze_return_statement(self, node: Node, source: bytes):
        """Analyze a return statement"""
        for child in node.children:
            if child.type not in ['return', ';']:
                self._analyze_expression(child, source)
    
    def _analyze_if_statement(self, node: Node, source: bytes):
        """Analyze an if statement"""
        for child in node.children:
            if child.type == 'parenthesized_expression':
                self._analyze_expression(child, source)
            elif child.type == 'compound_statement':
                self._analyze_compound_statement(child, source)
            elif child.type not in ['if', 'else']:
                self._analyze_node(child, source)
    
    def _analyze_loop_statement(self, node: Node, source: bytes):
        """Analyze a for or while loop"""
        for child in node.children:
            if child.type == 'parenthesized_expression':
                self._analyze_expression(child, source)
            elif child.type == 'compound_statement':
                self._analyze_compound_statement(child, source)
            elif child.type not in ['for', 'while', 'do']:
                self._analyze_node(child, source)
    
    def _analyze_declaration(self, node: Node, source: bytes):
        """Analyze a declaration which may have initializers"""
        for child in node.children:
            if child.type == 'init_declarator':
                self._analyze_init_declarator(child, source)
    
    def _analyze_init_declarator(self, node: Node, source: bytes):
        """Analyze variable initialization"""
        for child in node.children:
            if child.type not in ['identifier', '=', 'pointer_declarator']:
                self._analyze_expression(child, source)
    
    def _analyze_expression(self, node: Node, source: bytes, is_write: bool = False):
        """
        Analyze an expression for entity accesses
        
        Args:
            node: The expression node
            source: Source code bytes
            is_write: Whether this expression is being written to
        """
        if node.type == 'field_expression':
            self._analyze_field_expression(node, source, is_write)
        
        elif node.type == 'call_expression':
            self._analyze_call_expression(node, source)
        
        elif node.type == 'assignment_expression':
            self._analyze_assignment_expression(node, source)
        
        elif node.type == 'parenthesized_expression':
            # Unwrap parentheses
            for child in node.children:
                if child.type not in ['(', ')']:
                    self._analyze_expression(child, source, is_write)
        
        elif node.type == 'binary_expression':
            # Analyze both sides of binary expression
            for child in node.children:
                if child.type not in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '&', '|', '^', '<<', '>>']:
                    self._analyze_expression(child, source)
        
        elif node.type == 'unary_expression':
            # Analyze the operand
            for child in node.children:
                if child.type not in ['!', '~', '-', '+', '++', '--', '*', '&']:
                    # Dereference (*) is a read, address-of (&) doesn't access the value
                    if node.children[0].type == '*':
                        self._analyze_expression(child, source)
                    elif node.children[0].type != '&':
                        self._analyze_expression(child, source, is_write)
        
        elif node.type == 'update_expression':
            # ++ or -- operators
            for child in node.children:
                if child.type not in ['++', '--']:
                    self._analyze_expression(child, source, is_write=True)
        
        elif node.type == 'subscript_expression':
            # Array access like arr[i]
            for child in node.children:
                if child.type not in ['[', ']']:
                    self._analyze_expression(child, source, is_write)
        
        elif node.type == 'conditional_expression':
            # Ternary operator
            for child in node.children:
                if child.type not in ['?', ':']:
                    self._analyze_expression(child, source)
        
        elif node.type == 'cast_expression':
            # Type cast
            for child in node.children:
                if child.type not in ['(', ')'] and not child.type.endswith('_type'):
                    self._analyze_expression(child, source, is_write)
        
        elif node.type == 'sizeof_expression':
            # sizeof doesn't actually access the value
            pass
        
        elif node.type == 'identifier':
            # Bare identifier - could be member, local, or global
            var_name = self._extract_text(node, source)
            
            # If we're in a class context, this might be a member variable
            # Record it with the class context for later resolution
            if self.current_class_context:
                # Store as "ClassName::memberName" for resolution
                entity_name = f"{self.current_class_context}::{var_name}"
            else:
                entity_name = var_name
            
            access_type = 'write' if is_write else 'read'
            self._record_access(entity_name, access_type, node, source)
        
        elif node.type == 'qualified_identifier':
            # Fully qualified name like Class::member or std::cout
            qual_name = self._extract_text(node, source)
            access_type = 'write' if is_write else 'read'
            self._record_access(qual_name, access_type, node, source)
        
        else:
            # Recurse for other expression types
            for child in node.children:
                if child.type not in ['(', ')', '{', '}', ';', ',']:
                    self._analyze_expression(child, source, is_write)
    
    def _analyze_field_expression(self, node: Node, source: bytes, is_write: bool = False):
        """Analyze field access like obj.member or obj->member"""
        field_name = None
        object_expr = None
        
        for child in node.children:
            if child.type == 'field_identifier':
                field_name = self._extract_text(child, source)
            elif child.type not in ['.', '->']:
                object_expr = child
        
        if field_name:
            # Record the field access
            access_type = 'write' if is_write else 'read'
            self._record_access(field_name, access_type, node, source)
        
        # Analyze the object expression (it's being read to access the field)
        if object_expr:
            self._analyze_expression(object_expr, source, is_write=False)
    
    def _analyze_call_expression(self, node: Node, source: bytes):
        """Analyze function/method calls"""
        function_name = None
        argument_list = None
        
        for child in node.children:
            if child.type == 'identifier':
                function_name = self._extract_text(child, source)
            elif child.type == 'qualified_identifier':
                function_name = self._extract_text(child, source)
            elif child.type == 'field_expression':
                # Method call like obj.method()
                self._analyze_field_expression_for_call(child, source)
            elif child.type == 'argument_list':
                argument_list = child
        
        if function_name:
            self._record_access(function_name, 'call', node, source)
        
        # Analyze arguments
        if argument_list:
            for child in argument_list.children:
                if child.type not in ['(', ')', ',']:
                    self._analyze_expression(child, source)
    
    def _analyze_field_expression_for_call(self, node: Node, source: bytes):
        """Analyze field expression that's being called as a method"""
        method_name = None
        object_expr = None
        
        for child in node.children:
            if child.type == 'field_identifier':
                method_name = self._extract_text(child, source)
            elif child.type not in ['.', '->']:
                object_expr = child
        
        if method_name:
            self._record_access(method_name, 'call', node, source)
        
        # The object is being read to call the method
        # This includes nested field expressions like rval._frustum.set()
        # where we need to record both the access to _frustum and the call to set
        if object_expr:
            self._analyze_expression(object_expr, source, is_write=False)
    
    def _analyze_assignment_expression(self, node: Node, source: bytes):
        """Analyze assignment to properly classify reads and writes"""
        left_side = True
        
        for child in node.children:
            if child.type in ['=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=']:
                left_side = False
            else:
                # Left side is written to, right side is read from
                self._analyze_expression(child, source, is_write=left_side)
    
    def _record_access(self, entity_name: str, access_type: str, node: Node, source: bytes):
        """Record an entity access"""
        line_num = source[:node.start_byte].count(b'\n') + 1
        col_num = node.start_point[1] + 1
        
        # Extract a small context snippet
        start = max(0, node.start_byte - 20)
        end = min(len(source), node.end_byte + 20)
        context = source[start:end].decode('utf-8', errors='ignore').strip()
        
        access = AccessRecord(
            accessed_entity=entity_name,
            access_type=access_type,
            file_path=str(self.current_file),
            line_number=line_num,
            column_number=col_num,
            accessing_function=self.current_function_context,
            context_snippet=context
        )
        
        self.accesses.append(access)
        
        # ALWAYS LOG DETECTIONS
        print(f"DETECTED: {access_type:5} '{entity_name}' at {self.current_file}:{line_num}:{col_num}")
        
        if self.verbose:
            print(f"  Context: {context[:50]}")
    
    def _extract_text(self, node: Node, source: bytes) -> str:
        """Extract text from a node"""
        return source[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
    
    def store_accesses_to_db(self, accesses: List[AccessRecord]):
        """
        Store access records to the database
        
        Args:
            accesses: List of AccessRecord objects to store
        """
        if not self.db:
            raise ValueError("No database connection available")
        
        for access in accesses:
            # Try to resolve the entity in the database
            # This is where we'd look up the canonical name from partial names
            # For now, we'll store with the name we found
            
            # TODO: Implement entity resolution logic
            # - Look up entity by name
            # - Handle qualified vs unqualified names
            # - Resolve member access to full canonical path
            
            # For now, just store the raw access
            # The database will need methods to resolve these later
            pass