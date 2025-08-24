#!/usr/bin/env python3
"""
Recursive Descent C++ Parser for tree-sitter AST
Based on comprehensive grammar analysis of 50 Orkid classes
Handles all node types properly including pure virtual methods
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import tree_sitter_cpp as ts_cpp
from tree_sitter import Language, Parser, Node

from .cpp_entities_v2 import (
    Entity, Member, Parameter, Location,
    EntityType, MemberType, AccessLevel, LocationType
)
from .cpp_type_system import TypeInfo, TypeRegistry, compose_type

class RecursiveDescentCppParser:
    """
    Clean recursive descent parser following tree-sitter-cpp grammar v0.22.3
    Properly handles all field_declaration_list child node types
    """
    
    def __init__(self, verbose: bool = False, db_path: Optional[str] = None):
        self.verbose = verbose
        self.parser = Parser()
        self.parser.set_language(Language(ts_cpp.language(), "cpp"))
        self.current_namespace = []
        self.current_file = None
        # Initialize type registry for unified type system
        self.type_registry = TypeRegistry(db_path) if db_path else None
        self.entities = []
        
    def parse_file(self, filepath: Path, source_code: Optional[str] = None) -> List[Entity]:
        """Parse a C++ file and return all entities"""
        self.current_file = filepath
        self.entities = []
        self.current_namespace = []
        
        # Read source if not provided
        if source_code is None:
            source_code = filepath.read_text(encoding='utf-8', errors='ignore')
        
        # Parse with tree-sitter
        tree = self.parser.parse(source_code.encode('utf-8'))
        source_bytes = source_code.encode('utf-8')
        
        # Start recursive descent
        self._parse_translation_unit(tree.root_node, source_bytes)
        
        return self.entities
    
    def parse_preprocessed(self, source_code: str, filepath: Path) -> List[Entity]:
        """Parse preprocessed source code"""
        return self.parse_file(filepath, source_code)
    
    # ============================================================
    # MAIN RECURSIVE DESCENT PARSER
    # ============================================================
    
    def _parse_translation_unit(self, node: Node, source: bytes):
        """Parse top-level translation unit"""
        for child in node.children:
            self._parse_top_level_item(child, source)
    
    def _parse_top_level_item(self, node: Node, source: bytes):
        """Parse any top-level declaration or definition"""
        if node.type == 'namespace_definition':
            self._parse_namespace_definition(node, source)
        elif node.type == 'class_specifier':
            entity = self._parse_class_specifier(node, source, is_struct=False)
            if entity:
                self.entities.append(entity)
        elif node.type == 'struct_specifier':
            entity = self._parse_class_specifier(node, source, is_struct=True)
            if entity:
                self.entities.append(entity)
        elif node.type == 'function_definition':
            entity = self._parse_function_definition_top_level(node, source)
            if entity:
                self.entities.append(entity)
        elif node.type == 'template_declaration':
            self._parse_template_declaration_top_level(node, source)
        elif node.type == 'enum_specifier':
            entity = self._parse_enum_specifier(node, source)
            if entity:
                self.entities.append(entity)
        elif node.type == 'type_definition':
            entity = self._parse_type_definition(node, source)
            if entity:
                self.entities.append(entity)
        elif node.type == 'alias_declaration':
            entity = self._parse_alias_declaration_top_level(node, source)
            if entity:
                self.entities.append(entity)
        elif node.type == 'declaration':
            # Could be variable, function declaration, etc.
            self._parse_declaration_top_level(node, source)
    
    # ============================================================
    # NAMESPACE HANDLING
    # ============================================================
    
    def _parse_namespace_definition(self, node: Node, source: bytes):
        """Parse namespace definition - handles both simple and nested namespaces"""
        namespace_parts = []
        
        for child in node.children:
            if child.type == 'namespace_identifier':
                # Simple namespace like 'namespace ork'
                namespace_parts.append(self._extract_text(child, source))
            elif child.type == 'nested_namespace_specifier':
                # Nested namespace like 'namespace ork::lev2'
                namespace_parts = self._extract_nested_namespace(child, source)
                break
        
        # Push all namespace parts
        for part in namespace_parts:
            self.current_namespace.append(part)
        
        # Parse namespace body
        for child in node.children:
            if child.type == 'declaration_list':
                for item in child.children:
                    if item.type not in ['{', '}']:
                        self._parse_top_level_item(item, source)
        
        # Pop all namespace parts
        for _ in namespace_parts:
            self.current_namespace.pop()
    
    def _extract_nested_namespace(self, node: Node, source: bytes) -> List[str]:
        """Extract all parts from a nested namespace specifier like ork::lev2::detail"""
        parts = []
        
        def extract_recursive(n: Node):
            """Recursively extract namespace parts from nested structure"""
            for child in n.children:
                if child.type == 'namespace_identifier':
                    parts.append(self._extract_text(child, source))
                elif child.type == 'nested_namespace_specifier':
                    # Recursively process nested namespace specifiers
                    extract_recursive(child)
        
        extract_recursive(node)
        
        if self.verbose and parts:
            print(f"DEBUG: Extracted nested namespace parts: {parts}")
        return parts
    
    # ============================================================
    # CLASS/STRUCT PARSING
    # ============================================================
    
    def _parse_class_specifier(self, node: Node, source: bytes, is_struct: bool) -> Optional[Entity]:
        """Parse class or struct definition"""
        entity_type = EntityType.STRUCT if is_struct else EntityType.CLASS
        namespace = '::'.join(self.current_namespace) if self.current_namespace else None
        
        has_body = False
        base_clause_node = None
        short_name = None
        
        # First pass: extract name, base classes, and check for body
        for child in node.children:
            if child.type == 'type_identifier':
                short_name = self._extract_text(child, source)
            elif child.type == 'base_class_clause':
                base_clause_node = child
            elif child.type == 'field_declaration_list':
                has_body = True
        
        if not short_name:
            return None
        
        # Now create entity with required fields
        full_name = self._build_full_name(short_name)
        entity = Entity(
            canonical_name=full_name,
            short_name=short_name,
            entity_type=entity_type
        )
        entity.namespace = namespace
        
        # Add location
        entity.locations.append(Location(
            file_path=str(self.current_file),
            line_number=source[:node.start_byte].count(b'\n') + 1,
            column_number=node.start_point[1] + 1,
            location_type=LocationType.DEFINITION if has_body else LocationType.DECLARATION
        ))
        
        # Parse base classes
        if base_clause_node:
            self._parse_base_class_clause(base_clause_node, source, entity)
        
        # Parse members if has body
        if has_body:
            for child in node.children:
                if child.type == 'field_declaration_list':
                    self._parse_field_declaration_list(
                        child, source, entity,
                        default_access=AccessLevel.PUBLIC if is_struct else AccessLevel.PRIVATE
                    )
        
        return entity
    
    def _parse_field_declaration_list(self, node: Node, source: bytes, entity: Entity,
                                     default_access: AccessLevel):
        """
        Parse class/struct body - THE CRITICAL METHOD
        Handles ALL member node types according to grammar
        """
        current_access = default_access
        
        for child in node.children:
            if child.type in ['{', '}', ';']:
                continue
                
            elif child.type == 'access_specifier':
                # Update access level
                current_access = self._parse_access_specifier(child, source)
                
            elif child.type == 'field_declaration':
                # Regular fields and method declarations
                member = self._parse_field_declaration(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == 'function_definition':
                # Methods with bodies, pure virtual methods, etc.
                member = self._parse_function_definition_member(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == 'template_declaration':
                # Template methods or nested template classes
                member = self._parse_template_declaration_member(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == 'declaration':
                # Forward declarations, nested types, etc.
                member = self._parse_declaration_member(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == 'alias_declaration':
                # Type aliases (using declarations)
                member = self._parse_alias_declaration_member(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == 'using_declaration':
                # Using declarations
                member = self._parse_using_declaration(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == 'friend_declaration':
                # Friend declarations
                pass  # Skip for now
                
            elif child.type == 'static_assert_declaration':
                # Static assertions
                pass  # Skip for now
                
            elif child.type == 'type_definition':
                # Typedef inside class
                member = self._parse_type_definition_member(child, source, current_access)
                if member:
                    entity.add_member(member)
                    
            elif child.type == ':':
                # Colon after access specifier
                continue
            else:
                if self.verbose:
                    print(f"Unknown member node type: {child.type}")
    
    # ============================================================
    # MEMBER PARSING
    # ============================================================
    
    def _parse_field_declaration(self, node: Node, source: bytes, 
                                access_level: AccessLevel) -> Optional[Member]:
        """Parse field_declaration - could be field or method declaration"""
        
        if self.verbose:
            print(f"DEBUG: _parse_field_declaration with {len(node.children)} children")
            for child in node.children:
                print(f"  Child: {child.type}")
        
        # Check if it's a function declaration
        has_function_declarator = False
        for child in node.children:
            if child.type == 'function_declarator':
                has_function_declarator = True
                break
            elif child.type == 'pointer_declarator':
                # Check if pointer_declarator contains function_declarator
                for ptr_child in child.children:
                    if ptr_child.type == 'function_declarator':
                        has_function_declarator = True
                        break
        
        if has_function_declarator:
            return self._parse_method_declaration(node, source, access_level)
        else:
            return self._parse_field_member(node, source, access_level)
    
    def _parse_function_definition_member(self, node: Node, source: bytes,
                                         access_level: AccessLevel) -> Optional[Member]:
        """
        Parse function_definition - CRITICAL FOR INLINE METHODS
        Uses unified type system for return type composition.
        """
        member = Member(name="", member_type=MemberType.METHOD)
        member.member_type = MemberType.METHOD
        member.access_level = access_level
        
        function_declarator = None
        return_type_info = None
        
        # Parse all children to extract complete information
        for child in node.children:
            if child.type == 'storage_class_specifier':
                # Check for static, inline, etc.
                for sc_child in child.children:
                    if sc_child.type == 'static':
                        member.is_static = True
                    elif sc_child.type == 'inline':
                        member.is_inline = True
                        
            elif child.type == 'virtual':
                member.is_virtual = True
                
            elif child.type == 'function_declarator':
                function_declarator = child
                
            elif child.type == 'pointer_declarator':
                # Function declarator might be inside pointer_declarator for pointer return types
                for ptr_child in child.children:
                    if ptr_child.type == 'function_declarator':
                        function_declarator = ptr_child
                        # Collect return type info using unified system
                        if not return_type_info:
                            return_type_info = self._collect_type_info(node, source)
                        
            elif child.type == 'reference_declarator':
                # Function declarator might be inside reference_declarator for reference return types
                for ref_child in child.children:
                    if ref_child.type == 'function_declarator':
                        function_declarator = ref_child
                        # Collect return type info using unified system
                        if not return_type_info:
                            return_type_info = self._collect_type_info(node, source)
                
            elif child.type == 'pure_virtual_clause':
                # THIS IS THE KEY FIX - detect pure virtual!
                member.is_pure_virtual = True
                
            elif child.type == 'default_method_clause':
                member.is_default = True
                
            elif child.type == 'delete_method_clause':
                member.is_deleted = True
                    
            elif child.type == 'compound_statement':
                # Has implementation body
                pass
        
        # Collect return type if not already done
        if not return_type_info:
            return_type_info = self._collect_return_type_info(node, source)
        
        # Compose and store the return type using unified system
        if return_type_info and return_type_info.base_type:
            member.data_type = compose_type(return_type_info)
            # Store in flyweight registry if available
            if self.type_registry:
                member.base_type_id = self.type_registry.get_or_create_type(return_type_info)
                # Store type modifiers separately
                member.is_reference = return_type_info.is_reference
                member.is_rvalue_reference = return_type_info.is_rvalue_reference
                member.is_volatile = return_type_info.is_volatile
                member.return_const = return_type_info.is_const
        
        # Extract name and parameters from function_declarator
        if function_declarator:
            self._parse_function_declarator(function_declarator, source, member)
        
        # Determine if it's constructor/destructor
        if member.name:
            if member.name.startswith('~'):
                member.member_type = MemberType.DESTRUCTOR
            elif member.name == self._get_current_class_name():
                member.member_type = MemberType.CONSTRUCTOR
        
        # Set line number
        member.line_number = source[:node.start_byte].count(b'\n') + 1
        
        return member if member.name else None
    
    def _parse_method_declaration(self, node: Node, source: bytes,
                                 access_level: AccessLevel) -> Optional[Member]:
        """Parse method declaration from field_declaration with function_declarator
        Uses unified type system for return type composition.
        """
        member = Member(name="", member_type=MemberType.METHOD)
        member.member_type = MemberType.METHOD
        member.access_level = access_level
        
        function_declarator = None
        return_type_info = None
        
        if self.verbose:
            print(f"DEBUG: Parsing method declaration, node has {len(node.children)} children")
        
        for child in node.children:
            if self.verbose:
                print(f"  Child: {child.type}")
            
            if child.type == 'storage_class_specifier':
                for sc_child in child.children:
                    if sc_child.type == 'static':
                        member.is_static = True
                        if self.verbose:
                            print(f"    Found static keyword")
                    elif sc_child.type == 'inline':
                        member.is_inline = True
                        
            elif child.type == 'static':
                # Static can also appear directly
                member.is_static = True
                if self.verbose:
                    print(f"    Found static keyword (direct)")
                        
            elif child.type == 'virtual':
                member.is_virtual = True
                if self.verbose:
                    print(f"    Found virtual keyword")
                
            elif child.type == 'function_declarator':
                function_declarator = child
                
            elif child.type == 'pointer_declarator':
                # Function declarator might be inside pointer_declarator for pointer return types
                for ptr_child in child.children:
                    if ptr_child.type == 'function_declarator':
                        function_declarator = ptr_child
                        # Collect return type using unified system
                        if not return_type_info:
                            return_type_info = self._collect_type_info(node, source)
                
            elif child.type == 'pure_virtual_clause':
                member.is_pure_virtual = True
                if self.verbose:
                    print(f"    Found pure virtual clause (= 0)")
        
        # Collect return type if not already done
        if not return_type_info:
            return_type_info = self._collect_return_type_info(node, source)
        
        # Compose and store the return type using unified system
        if return_type_info and return_type_info.base_type:
            member.data_type = compose_type(return_type_info)
            # Store in flyweight registry if available
            if self.type_registry:
                member.base_type_id = self.type_registry.get_or_create_type(return_type_info)
                # Store type modifiers separately
                member.is_reference = return_type_info.is_reference
                member.is_rvalue_reference = return_type_info.is_rvalue_reference
                member.is_volatile = return_type_info.is_volatile
                member.return_const = return_type_info.is_const
        
        if function_declarator:
            self._parse_function_declarator(function_declarator, source, member)
            if self.verbose:
                print(f"  After parsing function_declarator: name='{member.name}', is_static={member.is_static}")
        
        # Check for constructor/destructor
        if member.name:
            if member.name.startswith('~'):
                member.member_type = MemberType.DESTRUCTOR
            elif member.name == self._get_current_class_name():
                member.member_type = MemberType.CONSTRUCTOR
        
        member.line_number = source[:node.start_byte].count(b'\n') + 1
        
        return member if member.name else None
    
    def _parse_field_member(self, node: Node, source: bytes,
                          access_level: AccessLevel) -> Optional[Member]:
        """Parse a field member using unified type system"""
        member = Member(name="", member_type=MemberType.FIELD)
        member.access_level = access_level
        
        # Check for nested class/struct definition first
        for child in node.children:
            if child.type in ['class_specifier', 'struct_specifier']:
                # This is a nested type definition
                type_name = self._extract_nested_type_name(child, source)
                if type_name:
                    member.name = type_name
                    member.member_type = MemberType.NESTED_TYPE
                    member.data_type = child.type.replace('_specifier', '')
                    member.line_number = source[:node.start_byte].count(b'\n') + 1
                    return member
        
        # Use unified type collection for ALL type information
        type_info = self._collect_type_info(node, source)
        
        # Extract field name and handle special declarators
        field_name = None
        field_value = None
        
        for child in node.children:
            if child.type == 'field_identifier':
                field_name = self._extract_text(child, source)
                
            elif child.type == 'init_declarator':
                # Has an initializer, extract name and value
                for init_child in child.children:
                    if init_child.type == 'field_identifier':
                        field_name = self._extract_text(init_child, source)
                    elif init_child.type == 'pointer_declarator':
                        # Field name is nested in pointer declarator
                        for ptr_child in init_child.children:
                            if ptr_child.type == 'field_identifier':
                                field_name = self._extract_text(ptr_child, source)
                    elif init_child.type == 'array_declarator':
                        # Field name is nested in array declarator
                        for arr_child in init_child.children:
                            if arr_child.type == 'field_identifier':
                                field_name = self._extract_text(arr_child, source)
                    elif init_child.type == 'reference_declarator':
                        # Field name is nested in reference declarator
                        for ref_child in init_child.children:
                            if ref_child.type == 'field_identifier':
                                field_name = self._extract_text(ref_child, source)
                    elif init_child.type == '=':
                        # Next sibling is the value
                        idx = list(child.children).index(init_child)
                        if idx + 1 < len(child.children):
                            field_value = self._extract_text(child.children[idx + 1], source)
                            
            elif child.type == 'pointer_declarator':
                # Extract name from pointer declarator
                for ptr_child in child.children:
                    if ptr_child.type == 'field_identifier':
                        field_name = self._extract_text(ptr_child, source)
                        
            elif child.type == 'array_declarator':
                # Extract name from array declarator
                for arr_child in child.children:
                    if arr_child.type == 'field_identifier':
                        field_name = self._extract_text(arr_child, source)
                        
            elif child.type == 'reference_declarator':
                # Extract name from reference declarator
                for ref_child in child.children:
                    if ref_child.type == 'field_identifier':
                        field_name = self._extract_text(ref_child, source)
                        
            elif child.type == '=' and not field_value:
                # Direct initializer at field level
                idx = list(node.children).index(child)
                if idx + 1 < len(node.children):
                    field_value = self._extract_text(node.children[idx + 1], source)
        
        # Store collected type information in member
        member.name = field_name
        member.value = field_value
        
        # Apply type modifiers from TypeInfo
        member.is_static = type_info.is_constexpr or member.is_static  # constexpr implies static
        member.is_const = type_info.is_const
        member.is_volatile = type_info.is_volatile
        member.is_constexpr = type_info.is_constexpr
        member.is_mutable = type_info.is_mutable
        member.is_reference = type_info.is_reference
        member.is_rvalue_reference = type_info.is_rvalue_reference
        member.pointer_depth = type_info.pointer_depth
        member.array_dimensions = ''.join(f'[{d}]' for d in type_info.array_dimensions) if type_info.array_dimensions else None
        
        # Compose and store the complete type string
        member.data_type = compose_type(type_info)
        
        # Store type in flyweight registry if available
        if self.type_registry and type_info.base_type:
            member.base_type_id = self.type_registry.get_or_create_type(type_info)
        
        member.line_number = source[:node.start_byte].count(b'\n') + 1
        
        return member if member.name else None
    
    def _parse_function_declarator(self, node: Node, source: bytes, member: Member):
        """Parse function_declarator to extract name, parameters, qualifiers"""
        if self.verbose:
            print(f"DEBUG: Parsing function_declarator with {len(node.children)} children")
            for child in node.children:
                print(f"  Child type: {child.type}")
        
        params = []
        
        # First pass: collect all information before building signature
        for child in node.children:
            if child.type in ['field_identifier', 'identifier', 'destructor_name', 'operator_name']:
                member.name = self._extract_text(child, source)
                if self.verbose:
                    print(f"  Found function name: {member.name}")
                
            elif child.type == 'parameter_list':
                params = self._parse_parameter_list(child, source)
                    
            elif child.type == 'type_qualifier':
                qual = self._extract_text(child, source)
                if qual == 'const':
                    member.is_const = True
                elif qual == 'noexcept':
                    member.is_noexcept = True
                    
            elif child.type == 'virtual_specifier':
                spec = self._extract_text(child, source)
                if spec == 'override':
                    member.is_override = True
                elif spec == 'final':
                    member.is_final = True
                    
            elif child.type == 'ref_qualifier':
                # Handle && and & qualifiers
                pass
        
        # Build signature with all qualifiers for proper overload detection
        if member.name and params is not None:
            param_strs = []
            for param in params:
                param_str = param.param_type
                if param.name:
                    param_str += f" {param.name}"
                if param.default_value:
                    param_str += f" = {param.default_value}"
                param_strs.append(param_str)

            # Build qualifiers string
            qualifiers = []
            if member.is_const:
                qualifiers.append("const")
            if member.is_noexcept:
                qualifiers.append("noexcept")
            if member.is_override:
                qualifiers.append("override")
            if member.is_final:
                qualifiers.append("final")
                
            qualifier_str = " ".join(qualifiers)
            if qualifier_str:
                qualifier_str = " " + qualifier_str

            if member.data_type:
                member.signature = f"{member.data_type} {member.name}({', '.join(param_strs)}){qualifier_str}"
            else:
                member.signature = f"{member.name}({', '.join(param_strs)}){qualifier_str}"
    
    def _parse_parameter_list(self, node: Node, source: bytes) -> List[Parameter]:
        """Parse parameter list"""
        params = []
        
        for child in node.children:
            if child.type == 'parameter_declaration':
                param = self._parse_parameter_declaration(child, source)
                if param:
                    params.append(param)
            elif child.type == 'optional_parameter_declaration':
                param = self._parse_optional_parameter_declaration(child, source)
                if param:
                    params.append(param)
            elif child.type == 'variadic_parameter_declaration':
                param = self._parse_variadic_parameter_declaration(child, source)
                if param:
                    params.append(param)
        
        return params
    
    def _parse_parameter_declaration(self, node: Node, source: bytes) -> Optional[Parameter]:
        """Parse a parameter declaration"""
        param_type = ""
        param_name = None
        is_reference = False
        is_pointer = False
        
        for child in node.children:
            if child.type in ['primitive_type', 'type_identifier', 'qualified_identifier']:
                param_type = self._extract_text(child, source)
            elif child.type == 'identifier':
                param_name = self._extract_text(child, source)
            elif child.type == 'reference_declarator':
                # Handle reference parameters
                is_reference = True
                for ref_child in child.children:
                    if ref_child.type == 'identifier':
                        param_name = self._extract_text(ref_child, source)
            elif child.type == 'pointer_declarator':
                # Handle pointer parameters
                is_pointer = True
                for ptr_child in child.children:
                    if ptr_child.type == 'identifier':
                        param_name = self._extract_text(ptr_child, source)
        
        if param_type:
            param = Parameter(name=param_name, param_type=param_type)
            param.is_reference = is_reference
            param.is_pointer = is_pointer
            return param
        return None
    
    def _parse_optional_parameter_declaration(self, node: Node, source: bytes) -> Optional[Parameter]:
        """Parse optional parameter (with default value)"""
        param = self._parse_parameter_declaration(node, source)
        if param:
            # Find default value
            for child in node.children:
                if child.type == '=':
                    # Next sibling should be the default value
                    idx = node.children.index(child)
                    if idx + 1 < len(node.children):
                        param.default_value = self._extract_text(node.children[idx + 1], source)
                    break
        return param
    
    def _parse_variadic_parameter_declaration(self, node: Node, source: bytes) -> Optional[Parameter]:
        """Parse variadic parameter (...)"""
        param = Parameter(name=None, param_type="...")
        return param
    
    def _parse_template_declaration_member(self, node: Node, source: bytes,
                                          access_level: AccessLevel) -> Optional[Member]:
        """Parse template declaration inside class"""
        # Find the actual declaration inside template
        for child in node.children:
            if child.type == 'function_definition':
                member = self._parse_function_definition_member(child, source, access_level)
                if member:
                    member.is_template = True
                return member
            elif child.type == 'declaration':
                member = self._parse_declaration_member(child, source, access_level)
                if member:
                    member.is_template = True
                return member
            elif child.type in ['class_specifier', 'struct_specifier']:
                # Nested template class
                type_name = self._extract_nested_type_name(child, source)
                if type_name:
                    member = Member(name="", member_type=MemberType.METHOD)
                    member.name = type_name
                    member.member_type = MemberType.NESTED_TYPE
                    member.data_type = f"template {child.type.replace('_specifier', '')}"
                    member.access_level = access_level
                    member.is_template = True
                    member.line_number = source[:node.start_byte].count(b'\n') + 1
                    return member
        return None
    
    def _parse_declaration_member(self, node: Node, source: bytes,
                                 access_level: AccessLevel) -> Optional[Member]:
        """Parse declaration inside class"""
        # Could be function declaration, variable declaration, etc.
        has_function = any(child.type == 'function_declarator' for child in node.children)
        
        if has_function:
            return self._parse_method_declaration(node, source, access_level)
        else:
            return self._parse_field_member(node, source, access_level)
    
    def _parse_alias_declaration_member(self, node: Node, source: bytes,
                                       access_level: AccessLevel) -> Optional[Member]:
        """Parse type alias (using declaration) inside class"""
        member = Member(name="", member_type=MemberType.METHOD)
        member.member_type = MemberType.NESTED_TYPE
        member.access_level = access_level
        
        alias_name = None
        alias_type = None
        
        for child in node.children:
            if child.type == 'type_identifier' and not alias_name:
                alias_name = self._extract_text(child, source)
            elif child.type in ['type_identifier', 'qualified_identifier', 'template_type']:
                if alias_name:  # This is the aliased type
                    alias_type = self._extract_text(child, source)
        
        if alias_name:
            member.name = alias_name
            member.data_type = f"using {alias_name} = {alias_type or 'unknown'}"
            member.line_number = source[:node.start_byte].count(b'\n') + 1
            return member
        
        return None
    
    def _parse_type_definition_member(self, node: Node, source: bytes,
                                     access_level: AccessLevel) -> Optional[Member]:
        """Parse typedef inside class"""
        member = Member(name="", member_type=MemberType.METHOD)
        member.member_type = MemberType.NESTED_TYPE
        member.access_level = access_level
        
        typedef_name = None
        typedef_type = None
        
        for child in node.children:
            if child.type == 'type_identifier':
                if not typedef_type:
                    typedef_type = self._extract_text(child, source)
                else:
                    typedef_name = self._extract_text(child, source)
        
        if typedef_name:
            member.name = typedef_name
            member.data_type = f"typedef {typedef_type or 'unknown'} {typedef_name}"
            member.line_number = source[:node.start_byte].count(b'\n') + 1
            return member
        
        return None
    
    def _parse_using_declaration(self, node: Node, source: bytes,
                                access_level: AccessLevel) -> Optional[Member]:
        """Parse using declaration inside class"""
        # Skip for now - rarely used for members
        return None
    
    # ============================================================
    # ACCESS SPECIFIER PARSING
    # ============================================================
    
    def _parse_access_specifier(self, node: Node, source: bytes) -> AccessLevel:
        """Parse access specifier and return access level"""
        for child in node.children:
            if child.type in ['public', 'private', 'protected']:
                text = self._extract_text(child, source)
                if text == 'public':
                    return AccessLevel.PUBLIC
                elif text == 'private':
                    return AccessLevel.PRIVATE
                elif text == 'protected':
                    return AccessLevel.PROTECTED
        return AccessLevel.PRIVATE  # Default
    
    # ============================================================
    # TOP-LEVEL ENTITY PARSING
    # ============================================================
    
    def _parse_function_definition_top_level(self, node: Node, source: bytes) -> Optional[Entity]:
        """Parse top-level function definition"""
        namespace = '::'.join(self.current_namespace) if self.current_namespace else None
        
        function_declarator = None
        return_type = None
        short_name = None
        
        for child in node.children:
            if child.type == 'function_declarator':
                function_declarator = child
            elif child.type in ['primitive_type', 'type_identifier', 'qualified_identifier', 'auto']:
                if not return_type:
                    return_type = self._extract_text(child, source)
        
        if function_declarator:
            # Extract function name
            for child in function_declarator.children:
                if child.type in ['identifier', 'qualified_identifier', 'operator_name']:
                    short_name = self._extract_text(child, source)
                    break
        
        if short_name:
            # Now create entity with required fields
            full_name = self._build_full_name(short_name)
            entity = Entity(
                canonical_name=full_name,
                short_name=short_name,
                entity_type=EntityType.FUNCTION
            )
            entity.namespace = namespace
            
            entity.locations.append(Location(
                file_path=str(self.current_file),
                line_number=source[:node.start_byte].count(b'\n') + 1,
                column_number=node.start_point[1] + 1,
                location_type=LocationType.DEFINITION
            ))
            return entity
        
        return None
    
    def _parse_template_declaration_top_level(self, node: Node, source: bytes):
        """Parse top-level template declaration"""
        # Find what's being templated
        for child in node.children:
            if child.type in ['class_specifier', 'struct_specifier']:
                entity = self._parse_class_specifier(
                    child, source, 
                    is_struct=(child.type == 'struct_specifier')
                )
                if entity:
                    entity.is_template = True
                    self.entities.append(entity)
            elif child.type == 'function_definition':
                entity = self._parse_function_definition_top_level(child, source)
                if entity:
                    entity.is_template = True
                    self.entities.append(entity)
    
    def _parse_enum_specifier(self, node: Node, source: bytes) -> Optional[Entity]:
        """Parse enum definition"""
        namespace = '::'.join(self.current_namespace) if self.current_namespace else None
        short_name = None
        
        for child in node.children:
            if child.type == 'type_identifier':
                short_name = self._extract_text(child, source)
                break
        
        if short_name:
            # Now create entity with required fields
            full_name = self._build_full_name(short_name)
            entity = Entity(
                canonical_name=full_name,
                short_name=short_name,
                entity_type=EntityType.ENUM
            )
            entity.namespace = namespace
            
            entity.locations.append(Location(
                file_path=str(self.current_file),
                line_number=source[:node.start_byte].count(b'\n') + 1,
                column_number=node.start_point[1] + 1,
                location_type=LocationType.DEFINITION
            ))
            return entity
        
        return None
    
    def _parse_type_definition(self, node: Node, source: bytes) -> Optional[Entity]:
        """Parse typedef"""
        namespace = '::'.join(self.current_namespace) if self.current_namespace else None
        
        # Find typedef name (usually the last type_identifier)
        type_identifiers = []
        for child in node.children:
            if child.type == 'type_identifier':
                type_identifiers.append(self._extract_text(child, source))
        
        if type_identifiers:
            short_name = type_identifiers[-1]
            full_name = self._build_full_name(short_name)
            
            # Now create entity with required fields
            entity = Entity(
                canonical_name=full_name,
                short_name=short_name,
                entity_type=EntityType.TYPEDEF
            )
            entity.namespace = namespace
            
            entity.locations.append(Location(
                file_path=str(self.current_file),
                line_number=source[:node.start_byte].count(b'\n') + 1,
                column_number=node.start_point[1] + 1,
                location_type=LocationType.DEFINITION
            ))
            return entity
        
        return None
    
    def _parse_alias_declaration_top_level(self, node: Node, source: bytes) -> Optional[Entity]:
        """Parse top-level type alias"""
        namespace = '::'.join(self.current_namespace) if self.current_namespace else None
        short_name = None
        
        for child in node.children:
            if child.type == 'type_identifier':
                short_name = self._extract_text(child, source)
                break
        
        if short_name:
            # Now create entity with required fields
            full_name = self._build_full_name(short_name)
            entity = Entity(
                canonical_name=full_name,
                short_name=short_name,
                entity_type=EntityType.TYPEDEF  # Treat as typedef
            )
            entity.namespace = namespace
            
            entity.locations.append(Location(
                file_path=str(self.current_file),
                line_number=source[:node.start_byte].count(b'\n') + 1,
                column_number=node.start_point[1] + 1,
                location_type=LocationType.DEFINITION
            ))
            return entity
        
        return None
    
    def _parse_declaration_top_level(self, node: Node, source: bytes):
        """Parse top-level declaration"""
        # Could be function declaration, variable, etc.
        has_function = any(child.type == 'function_declarator' for child in node.children)
        
        if has_function:
            # Function declaration
            namespace = '::'.join(self.current_namespace) if self.current_namespace else None
            short_name = None
            
            for child in node.children:
                if child.type == 'function_declarator':
                    for fc in child.children:
                        if fc.type in ['identifier', 'qualified_identifier']:
                            short_name = self._extract_text(fc, source)
                            break
            
            if short_name:
                # Now create entity with required fields
                full_name = self._build_full_name(short_name)
                entity = Entity(
                    canonical_name=full_name,
                    short_name=short_name,
                    entity_type=EntityType.FUNCTION
                )
                entity.namespace = namespace
                
                entity.locations.append(Location(
                    file_path=str(self.current_file),
                    line_number=source[:node.start_byte].count(b'\n') + 1,
                    column_number=node.start_point[1] + 1,
                    location_type=LocationType.DECLARATION
                ))
                self.entities.append(entity)
    
    def _parse_base_class_clause(self, node: Node, source: bytes, entity: Entity):
        """Parse base class clause for inheritance"""
        for child in node.children:
            if child.type == 'type_identifier':
                base_name = self._extract_text(child, source)
                entity.base_classes.append(base_name)
            elif child.type == 'qualified_identifier':
                base_name = self._extract_text(child, source)
                entity.base_classes.append(base_name)
    
    def _parse_reference_declarator(self, node: Node, source: bytes, member: Member):
        """Parse reference declarator - NEW METHOD"""
        for child in node.children:
            if child.type == 'field_identifier':
                member.name = self._extract_text(child, source)
            elif child.type == 'identifier':
                member.name = self._extract_text(child, source)
        
        # Add reference indication to data type
        if member.data_type:
            member.data_type += '&'
        else:
            member.data_type = '&'  # In case type wasn't set yet
    
    def _parse_pointer_declarator(self, node: Node, source: bytes, member: Member):
        """Parse pointer declarator"""
        for child in node.children:
            if child.type == 'field_identifier':
                member.name = self._extract_text(child, source)
            elif child.type == 'identifier':
                member.name = self._extract_text(child, source)
        
        # Add * to type
        if member.data_type:
            member.data_type += '*'
    
    def _parse_array_declarator(self, node: Node, source: bytes, member: Member):
        """Parse array declarator - FIXED for multi-dimensional arrays"""
        dimensions = []
        
        def extract_dimensions_recursive(n: Node):
            """Recursively extract dimensions from nested array_declarator nodes"""
            for child in n.children:
                if child.type == 'field_identifier':
                    member.name = self._extract_text(child, source)
                elif child.type == 'identifier':
                    # Could be field name OR array dimension - check context
                    text = self._extract_text(child, source)
                    if not member.name:
                        member.name = text
                    else:
                        # This is an array dimension identifier (e.g., [kAABUFTILES])
                        dimensions.append(text)
                elif child.type == 'number_literal':
                    dimensions.append(self._extract_text(child, source))
                elif child.type == 'array_declarator':
                    # Recursively handle nested array declarators
                    extract_dimensions_recursive(child)
        
        extract_dimensions_recursive(node)
        
        if dimensions:
            member.array_dimensions = ''.join(f'[{d}]' for d in dimensions)
    
    def _parse_init_declarator(self, node: Node, source: bytes, member: Member):
        """Parse init_declarator to extract field name and initializer value"""
        for child in node.children:
            if child.type == 'field_identifier':
                member.name = self._extract_text(child, source)
            elif child.type == 'pointer_declarator':
                self._parse_pointer_declarator(child, source, member)
            elif child.type == 'array_declarator':
                self._parse_array_declarator(child, source, member)  
            elif child.type == 'reference_declarator':
                self._parse_reference_declarator(child, source, member)
            elif child.type == '=':
                # Found initializer - extract the value
                # Find the next sibling that contains the initializer value
                found_equals = False
                for sibling in node.children:
                    if found_equals and sibling.type not in [';', ' ', '\n', '\t']:
                        member.value = self._extract_text(sibling, source)
                        break
                    if sibling == child:
                        found_equals = True
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _extract_text(self, node: Node, source: bytes) -> str:
        """Extract text from a node"""
        return source[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
    
    # ============================================================
    # UNIFIED TYPE SYSTEM METHODS
    # ============================================================
    
    def _collect_type_info(self, node: Node, source: bytes) -> TypeInfo:
        """
        Collect complete type information from AST nodes.
        Central method for ALL type extraction - replaces scattered type composition.
        """
        type_info = TypeInfo()
        
        # Process the node and its children to collect all type metadata
        self._collect_type_info_recursive(node, source, type_info)
        
        return type_info
    
    def _collect_return_type_info(self, node: Node, source: bytes) -> TypeInfo:
        """
        Collect return type information specifically for methods.
        This is more targeted than _collect_type_info to avoid mixing
        return type qualifiers with method qualifiers.
        """
        type_info = TypeInfo()
        
        # Look for return type nodes specifically
        for child in node.children:
            if child.type in ['primitive_type', 'type_identifier', 'qualified_identifier', 
                            'auto', 'template_type', 'sized_type_specifier']:
                # This is the base return type
                type_info.base_type = self._extract_text(child, source)
                if child.type == 'template_type':
                    type_info.is_template = True
                    
                # Check for const qualifier BEFORE the type
                idx = list(node.children).index(child)
                if idx > 0:
                    prev = node.children[idx - 1]
                    if prev.type == 'type_qualifier':
                        qual = self._extract_text(prev, source)
                        if qual == 'const':
                            type_info.is_const = True
                        elif qual == 'volatile':
                            type_info.is_volatile = True
                            
            elif child.type == 'pointer_declarator':
                # Check if function is inside pointer declarator (pointer return type)
                has_function = False
                for ptr_child in child.children:
                    if ptr_child.type == 'function_declarator':
                        has_function = True
                        break
                        
                if has_function:
                    # This is a pointer return type
                    type_info.pointer_depth = 1
                    # Get base type from before pointer_declarator
                    idx = list(node.children).index(child)
                    if idx > 0:
                        prev = node.children[idx - 1]
                        if prev.type in ['primitive_type', 'type_identifier', 'qualified_identifier', 'template_type']:
                            type_info.base_type = self._extract_text(prev, source)
                            if prev.type == 'template_type':
                                type_info.is_template = True
                                
                        # Check for const before type
                        if idx > 1:
                            prev2 = node.children[idx - 2]
                            if prev2.type == 'type_qualifier' and self._extract_text(prev2, source) == 'const':
                                type_info.is_const = True
                                
            elif child.type == 'reference_declarator':
                # Check if function is inside reference_declarator (reference return type)
                has_function = False
                for ref_child in child.children:
                    if ref_child.type == 'function_declarator':
                        has_function = True
                        break
                    elif ref_child.type == '&&':
                        type_info.is_rvalue_reference = True
                        
                if has_function:
                    # This is a reference return type
                    if not type_info.is_rvalue_reference:
                        type_info.is_reference = True
                        
                    # Get base type from before reference_declarator
                    idx = list(node.children).index(child)
                    if idx > 0:
                        prev = node.children[idx - 1]
                        if prev.type in ['primitive_type', 'type_identifier', 'qualified_identifier', 'template_type']:
                            type_info.base_type = self._extract_text(prev, source)
                            if prev.type == 'template_type':
                                type_info.is_template = True
                                
                        # Check for const before type
                        if idx > 1:
                            prev2 = node.children[idx - 2]
                            if prev2.type == 'type_qualifier' and self._extract_text(prev2, source) == 'const':
                                type_info.is_const = True
        
        return type_info
    
    def _collect_type_info_recursive(self, node: Node, source: bytes, type_info: TypeInfo):
        """Recursively collect type information from AST nodes"""
        
        # Handle type qualifiers
        if node.type == 'type_qualifier':
            qual = self._extract_text(node, source)
            if qual == 'const':
                type_info.is_const = True
            elif qual == 'volatile':
                type_info.is_volatile = True
            elif qual == 'mutable':
                type_info.is_mutable = True
                
        # Handle storage class specifiers
        elif node.type == 'storage_class_specifier':
            for child in node.children:
                spec = self._extract_text(child, source)
                if spec == 'constexpr':
                    type_info.is_constexpr = True
                elif spec == 'mutable':
                    type_info.is_mutable = True
                    
        # Handle base types
        elif node.type in ['primitive_type', 'type_identifier', 'qualified_identifier', 'auto']:
            if not type_info.base_type:
                type_info.base_type = self._extract_text(node, source)
                
        # Handle template types
        elif node.type == 'template_type':
            if not type_info.base_type:
                type_info.base_type = self._extract_text(node, source)
                type_info.is_template = True
                
        # Handle sized type specifiers (e.g., "unsigned int")
        elif node.type == 'sized_type_specifier':
            if not type_info.base_type:
                type_info.base_type = self._extract_text(node, source)
                
        # Handle pointer declarators
        elif node.type == 'pointer_declarator':
            type_info.pointer_depth += 1
            # Continue collecting from children
            for child in node.children:
                if child.type != '*':
                    self._collect_type_info_recursive(child, source, type_info)
                    
        # Handle reference declarators
        elif node.type == 'reference_declarator':
            type_info.is_reference = True
            # Continue collecting from children
            for child in node.children:
                if child.type not in ['&', '&&']:
                    self._collect_type_info_recursive(child, source, type_info)
                elif child.type == '&&':
                    type_info.is_rvalue_reference = True
                    type_info.is_reference = False  # rvalue ref is distinct from lvalue ref
                    
        # Handle array declarators
        elif node.type == 'array_declarator':
            # Extract array dimensions
            for child in node.children:
                if child.type == 'number_literal':
                    type_info.array_dimensions.append(self._extract_text(child, source))
                elif child.type == 'identifier':
                    # Could be array dimension constant
                    text = self._extract_text(child, source)
                    if text and text[0].isupper():  # Likely a constant
                        type_info.array_dimensions.append(text)
                elif child.type not in ['[', ']', 'field_identifier']:
                    self._collect_type_info_recursive(child, source, type_info)
                    
        # Recurse for other node types
        else:
            for child in node.children:
                self._collect_type_info_recursive(child, source, type_info)
    
    def _build_full_name(self, short_name: str) -> str:
        """Build full qualified name"""
        if self.current_namespace:
            return '::'.join(self.current_namespace) + '::' + short_name
        return short_name
    
    def _get_current_class_name(self) -> Optional[str]:
        """Get the name of the class currently being parsed"""
        # This would need to be tracked during parsing
        # For now, return None
        return None
    
    def _extract_nested_type_name(self, node: Node, source: bytes) -> Optional[str]:
        """Extract name from nested class/struct"""
        for child in node.children:
            if child.type == 'type_identifier':
                return self._extract_text(child, source)
        return None
    
    def parse_source(self, source_code: bytes, filepath: str) -> List[Entity]:
        """Parse source code bytes and return entities - compatible with database usage"""
        self.current_file = Path(filepath)
        self.entities = []
        self.current_namespace = []
        
        # Parse with tree-sitter
        tree = self.parser.parse(source_code)
        
        # Start recursive descent
        self._parse_translation_unit(tree.root_node, source_code)
        
        return self.entities

# Export alias for compatibility
CppParser = RecursiveDescentCppParser