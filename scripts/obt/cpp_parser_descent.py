#!/usr/bin/env python3
"""
Recursive Descent C++ Parser for tree-sitter AST
Based on comprehensive grammar analysis of 50 Orkid classes
Handles all node types properly including pure virtual methods
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
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
                result = self._parse_field_declaration(child, source, current_access)
                if result:
                    # Could be a single member or list of members
                    if isinstance(result, list):
                        for member in result:
                            entity.add_member(member)
                    else:
                        entity.add_member(result)
                    
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
                                access_level: AccessLevel) -> Optional[Union[Member, List[Member]]]:
        """Parse field_declaration - could be field or method declaration
        Returns single Member for methods, or Member/List[Member] for fields"""
        
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
            elif child.type == 'reference_declarator':
                # Check if reference_declarator contains function_declarator
                for ref_child in child.children:
                    if ref_child.type == 'function_declarator':
                        has_function_declarator = True
                        break
        
        if has_function_declarator:
            return self._parse_method_declaration(node, source, access_level)
        else:
            # Could return multiple members for comma-separated declarations
            return self._parse_field_members(node, source, access_level)
    
    def _parse_function_definition_member(self, node: Node, source: bytes,
                                         access_level: AccessLevel) -> Optional[Member]:
        """
        Parse function_definition - CRITICAL FOR INLINE METHODS
        WORKAROUND: Also detects fields with = 0 initializers that are misclassified as function_definition
        Uses unified type system for return type composition.
        """
        # WORKAROUND FOR TREE-SITTER-CPP GRAMMAR BUG
        # GitHub Issue: https://github.com/tree-sitter/tree-sitter-cpp/issues/273
        # Related Fix (not yet in our version): https://github.com/tree-sitter/tree-sitter-cpp/pull/286
        # 
        # Problem: tree-sitter-cpp incorrectly parses field declarations with '= 0' initializers
        # as function_definition nodes with pure_virtual_clause instead of field_declaration nodes.
        # This affects fields like: size_t _width = 0; int _count = 0; bool _flag = 0;
        #
        # This workaround detects these misclassified nodes and properly handles them as fields.
        if self._is_field_with_zero_initializer(node, source):
            return self._parse_misclassified_field(node, source, access_level)
        
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
                            return_type_info = self._collect_return_type_info(node, source)
                        
            elif child.type == 'reference_declarator':
                # Function declarator might be inside reference_declarator for reference return types
                for ref_child in child.children:
                    if ref_child.type == 'function_declarator':
                        function_declarator = ref_child
                        # Collect return type info using unified system
                        if not return_type_info:
                            return_type_info = self._collect_return_type_info(node, source)
                
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
                member.pointer_depth = return_type_info.pointer_depth
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
                            return_type_info = self._collect_return_type_info(node, source)
                            
            elif child.type == 'reference_declarator':
                # Function declarator might be inside reference_declarator for reference return types
                for ref_child in child.children:
                    if ref_child.type == 'function_declarator':
                        function_declarator = ref_child
                        # Collect return type using unified system
                        if not return_type_info:
                            return_type_info = self._collect_return_type_info(node, source)
                
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
                member.pointer_depth = return_type_info.pointer_depth
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
    
    def _parse_field_members(self, node: Node, source: bytes,
                           access_level: AccessLevel) -> Optional[Union[Member, List[Member]]]:
        """Parse field members - handles comma-separated declarations
        e.g., static F32 msfR, msfG, msfB, msfA;
        """
        members = []
        
        # Check for nested class/struct definition first
        for child in node.children:
            if child.type in ['class_specifier', 'struct_specifier']:
                # This is a nested type definition
                type_name = self._extract_nested_type_name(child, source)
                if type_name:
                    member = Member(name=type_name, member_type=MemberType.NESTED_TYPE)
                    member.access_level = access_level
                    member.data_type = child.type.replace('_specifier', '')
                    member.line_number = source[:node.start_byte].count(b'\n') + 1
                    return member
        
        # Use unified type collection for ALL type information
        type_info = self._collect_type_info(node, source)
        
        # Collect all field names in this declaration
        field_names = []
        
        def extract_field_name(node_to_check):
            """Recursively extract field identifier"""
            if node_to_check.type == 'field_identifier':
                return self._extract_text(node_to_check, source)
            for child in node_to_check.children:
                name = extract_field_name(child)
                if name:
                    return name
            return None
        
        # Parse all declarators and field_identifiers  
        initializers = {}  # field_name -> initializer_value
        
        for child in node.children:
            if child.type == 'field_identifier':
                field_names.append(self._extract_text(child, source))
            elif child.type in ['array_declarator', 'pointer_declarator', 'reference_declarator', 'init_declarator']:
                name = extract_field_name(child)
                if name:
                    field_names.append(name)
                    
                    # Check for initializer in init_declarator
                    if child.type == 'init_declarator':
                        # Extract initializer value from init_declarator
                        found_equals = False
                        for init_child in child.children:
                            if found_equals and init_child.type not in [';', ' ', '\n', '\t']:
                                initializers[name] = self._extract_text(init_child, source)
                                break
                            if init_child.type == '=':
                                found_equals = True
        
        # Check for direct field initializers (e.g., static const int field = value;)
        if len(field_names) == 1:
            field_name = field_names[0]
            found_equals = False
            for child in node.children:
                if found_equals and child.type not in [';', ' ', '\n', '\t']:
                    initializers[field_name] = self._extract_text(child, source)
                    break
                if child.type == '=':
                    found_equals = True
        
        # Create a member for each field name
        for field_name in field_names:
            member = Member(name=field_name, member_type=MemberType.FIELD)
            member.access_level = access_level
            
            # Apply type modifiers from TypeInfo
            member.is_static = type_info.is_constexpr or type_info.is_static  # constexpr implies static
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
            
            # Apply initializer value if found
            if field_name in initializers:
                member.value = initializers[field_name]
            
            member.line_number = source[:node.start_byte].count(b'\n') + 1
            members.append(member)
        
        # Return single member or list
        if len(members) == 1:
            return members[0]
        elif len(members) > 1:
            return members
        else:
            return None
    
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
                if child.type == 'operator_name':
                    member.name = self._normalize_operator_name(child, source)
                else:
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
                # param.param_type is already composed by compose_type() in unified type system
                param_str = param.param_type
                
                # Add parameter name if present
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
        """Parse a parameter declaration using unified type system"""
        type_info = self._collect_type_info(node, source)
        
        # Extract parameter name from nested declarators
        param_name = self._extract_parameter_name(node, source)
        
        if type_info.base_type:
            # Use compose_type for authoritative type string generation
            param_type_str = compose_type(type_info)
            param = Parameter(name=param_name, param_type=param_type_str)
            
            # Store unified type system data for future use
            param.is_reference = type_info.is_reference
            param.is_pointer = type_info.pointer_depth > 0
            param.is_const = type_info.is_const
            
            return param
        return None
    
    def _extract_parameter_name(self, node: Node, source: bytes) -> Optional[str]:
        """Extract parameter name from potentially nested declarators"""
        for child in node.children:
            if child.type == 'identifier':
                return self._extract_text(child, source)
            elif child.type in ['reference_declarator', 'pointer_declarator']:
                name = self._extract_parameter_name(child, source)
                if name:
                    return name
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
                    if child.type == 'operator_name':
                        short_name = self._normalize_operator_name(child, source)
                    else:
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
        is_enum_class = False
        uses_crc_enum = False
        base_type = None
        
        # First pass: identify enum class/struct
        for child in node.children:
            if child.type == 'class' or child.type == 'struct':
                is_enum_class = True
                break
        
        # Second pass: get name and base type
        found_colon = False
        for child in node.children:
            if child.type == 'type_identifier':
                if not short_name and not found_colon:
                    # First type_identifier before colon is the enum name
                    short_name = self._extract_text(child, source)
                elif found_colon:
                    # Type identifier after colon is the base type
                    base_type = self._extract_text(child, source)
            elif child.type == ':':
                found_colon = True
        
        if self.verbose and short_name and 'Buffer' in short_name:
            print(f"DEBUG: Processing enum {short_name}, is_enum_class={is_enum_class}, base_type={base_type}")
        
        if short_name:
            # Now create entity with required fields
            full_name = self._build_full_name(short_name)
            entity = Entity(
                canonical_name=full_name,
                short_name=short_name,
                entity_type=EntityType.ENUM
            )
            entity.namespace = namespace
            entity.is_enum_class = is_enum_class
            
            entity.locations.append(Location(
                file_path=str(self.current_file),
                line_number=source[:node.start_byte].count(b'\n') + 1,
                column_number=node.start_point[1] + 1,
                location_type=LocationType.DEFINITION
            ))
            
            # Parse enum values - handle both normal and CrcEnum patterns
            # First check if this is a CrcEnum-style enum
            is_crc_enum = False
            for child in node.children:
                if child.type == 'enumerator_list':
                    # Check if it contains just CrcEnum identifier
                    for enum_item in child.children:
                        if enum_item.type == 'enumerator':
                            for enum_child in enum_item.children:
                                if enum_child.type == 'identifier':
                                    if self._extract_text(enum_child, source) == 'CrcEnum':
                                        is_crc_enum = True
                                        uses_crc_enum = True
                                        break
            
            if self.verbose and short_name and 'Buffer' in short_name:
                print(f"DEBUG: {short_name} is_crc_enum={is_crc_enum}")
            
            # Now parse based on enum type
            if is_crc_enum:
                # For CrcEnum style, the values appear as siblings after enumerator_list
                # Look for parenthesized_declarator and function_declarator nodes
                for child in node.parent.children if node.parent else node.children:
                    if child.type == 'parenthesized_declarator':
                        # Extract value like (R8)
                        for pchild in child.children:
                            if pchild.type == 'identifier':
                                value_name = self._extract_text(pchild, source)
                                member = Member(
                                    name=value_name,
                                    member_type=MemberType.ENUM_VALUE
                                )
                                member.access_level = AccessLevel.PUBLIC
                                member.data_type = "enum_value"
                                member.line_number = source[:child.start_byte].count(b'\n') + 1
                                entity.members.append(member)
                                if self.verbose and short_name and 'Buffer' in short_name:
                                    print(f"  Added CrcEnum value: {value_name}")
                                
                    elif child.type == 'function_declarator':
                        # Extract value like CrcEnum(Y16UI)
                        for fchild in child.children:
                            if fchild.type == 'parameter_list':
                                for param in fchild.children:
                                    if param.type == 'parameter_declaration':
                                        for pdecl in param.children:
                                            if pdecl.type in ['type_identifier', 'identifier']:
                                                value_name = self._extract_text(pdecl, source)
                                                member = Member(
                                                    name=value_name,
                                                    member_type=MemberType.ENUM_VALUE
                                                )
                                                member.access_level = AccessLevel.PUBLIC
                                                member.data_type = "enum_value"
                                                member.line_number = source[:child.start_byte].count(b'\n') + 1
                                                entity.members.append(member)
                                                if self.verbose and short_name and 'Buffer' in short_name:
                                                    print(f"  Added CrcEnum value: {value_name}")
            else:
                # Normal enum parsing
                for child in node.children:
                    if child.type == 'enumerator_list':
                        # Track if we're in CrcEnum mode
                        expecting_crc_value = False
                        
                        for i, enum_item in enumerate(child.children):
                            if enum_item.type == 'enumerator':
                                # Extract enum value name and check for CrcEnum
                                value_name = None
                                value_text = None
                                
                                for enum_child in enum_item.children:
                                    if enum_child.type == 'identifier':
                                        ident_text = self._extract_text(enum_child, source)
                                        if ident_text == 'CrcEnum':
                                            uses_crc_enum = True
                                            expecting_crc_value = True
                                        else:
                                            value_name = ident_text
                                    elif enum_child.type == 'call_expression':
                                        # Check if it's a CrcEnum call
                                        call_text = self._extract_text(enum_child, source)
                                        if call_text.startswith('CrcEnum'):
                                            uses_crc_enum = True
                                            # Extract the actual enum value from CrcEnum(VALUE)
                                            import re
                                            match = re.match(r'CrcEnum\((\w+)\)', call_text)
                                            if match:
                                                value_name = match.group(1)
                                    elif enum_child.type == '=':
                                        # Has explicit value
                                        next_idx = enum_item.children.index(enum_child) + 1
                                        if next_idx < len(enum_item.children):
                                            value_text = self._extract_text(enum_item.children[next_idx], source)
                                
                                if value_name:
                                    # Add as enum value member
                                    member = Member(
                                        name=value_name,
                                        member_type=MemberType.ENUM_VALUE
                                    )
                                    member.access_level = AccessLevel.PUBLIC  # Enum values are always public
                                    member.data_type = "enum_value"
                                    if value_text:
                                        member.value = value_text
                                    member.line_number = source[:enum_item.start_byte].count(b'\n') + 1
                                    entity.members.append(member)
                        
                            # Handle malformed AST from CrcEnum - look for parenthesized_declarator or function_declarator after enumerator
                            elif (expecting_crc_value and 
                                  (enum_item.type == 'parenthesized_declarator' or enum_item.type == 'function_declarator')):
                                # Extract the value name from the malformed node
                                for child_node in enum_item.children:
                                    if child_node.type == 'identifier':
                                        value_name = self._extract_text(child_node, source)
                                        member = Member(
                                            name=value_name,
                                            member_type=MemberType.ENUM_VALUE
                                        )
                                        member.access_level = AccessLevel.PUBLIC
                                        member.data_type = "enum_value"
                                        member.line_number = source[:enum_item.start_byte].count(b'\n') + 1
                                        entity.members.append(member)
                                        expecting_crc_value = False
                                        break
                                    elif child_node.type == 'parameter_list':
                                        # For function_declarator with CrcEnum(VALUE)
                                        for param_child in child_node.children:
                                            if param_child.type == 'parameter_declaration':
                                                for pdecl_child in param_child.children:
                                                    if pdecl_child.type == 'type_identifier' or pdecl_child.type == 'identifier':
                                                        value_name = self._extract_text(pdecl_child, source)
                                                        member = Member(
                                                            name=value_name,
                                                            member_type=MemberType.ENUM_VALUE
                                                        )
                                                        member.access_level = AccessLevel.PUBLIC
                                                        member.data_type = "enum_value"
                                                        member.line_number = source[:enum_item.start_byte].count(b'\n') + 1
                                                        entity.members.append(member)
                                                        expecting_crc_value = False
                                                        break
            
            # Store CrcEnum usage info (could add to entity metadata if needed)
            if uses_crc_enum and self.verbose:
                print(f"Enum {short_name} uses CrcEnum macro")
            
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
        aliased_type = None
        
        # Keep original logic for finding name
        for child in node.children:
            if child.type == 'type_identifier':
                short_name = self._extract_text(child, source)
                break
        
        # Additionally, find what it aliases to (after =)
        found_equals = False
        for child in node.children:
            if child.type == '=':
                found_equals = True
            elif found_equals and child.type != ';':
                # Everything after = and before ; is the aliased type
                if aliased_type is None:
                    aliased_type = self._extract_text(child, source)
        
        if short_name:
            # Now create entity with required fields
            full_name = self._build_full_name(short_name)
            entity = Entity(
                canonical_name=full_name,
                short_name=short_name,
                entity_type=EntityType.TYPEDEF  # Treat as typedef
            )
            entity.namespace = namespace
            entity.aliased_type = aliased_type
            entity.is_using_alias = True
            
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
        # Could be function declaration, variable, enum inside declaration, etc.
        has_function = any(child.type == 'function_declarator' for child in node.children)
        has_enum = any(child.type == 'enum_specifier' for child in node.children)
        
        if has_enum:
            # Enum declaration (like enum struct Foo : base_type { ... };)
            for child in node.children:
                if child.type == 'enum_specifier':
                    entity = self._parse_enum_specifier(child, source)
                    if entity:
                        self.entities.append(entity)
        elif has_function:
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
    
    def _normalize_operator_name(self, node: Node, source: bytes) -> str:
        """Normalize operator name to match Clang format (no spaces around operators)"""
        operator_text = self._extract_text(node, source)
        # Remove spaces around operators to match Clang format
        # e.g., "operator +=" -> "operator+="
        return operator_text.replace(" ", "")
    
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
                elif spec == 'static':
                    type_info.is_static = True
                    
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
    
    def _is_field_with_zero_initializer(self, node: Node, source: bytes) -> bool:
        """
        Detect if a function_definition node is actually a field with = 0 initializer
        due to tree-sitter-cpp grammar bug.
        
        TREE-SITTER-CPP BUG DETECTION LOGIC
        GitHub Issue: https://github.com/tree-sitter/tree-sitter-cpp/issues/273
        
        The bug causes this AST pattern for fields with '= 0' initializers:
        
        Incorrect AST (what we get):
            function_definition
              primitive_type 'size_t'
              field_identifier '_width'
              pure_virtual_clause '= 0;'
        
        Expected AST (what it should be):
            field_declaration
              primitive_type 'size_t'
              field_identifier '_width'
              init_declarator '= 0'
        
        This method detects the incorrect pattern so we can handle it properly.
        """
        # Look for the telltale pattern: pure_virtual_clause containing "= 0" 
        has_pure_virtual = False
        has_simple_declarator = False
        has_function_declarator = False
        
        for child in node.children:
            if child.type == 'pure_virtual_clause':
                # Extract the text of the pure_virtual_clause
                clause_text = self._extract_text(child, source).strip()
                
                # CRITICAL FIX: The pure_virtual_clause includes the trailing semicolon
                # in the AST, so we get "= 0;" instead of "= 0". We must strip the
                # semicolon to properly detect the pattern.
                clause_text = clause_text.rstrip(';')
                
                # Check if this is actually a field initializer (= 0) rather than
                # a real pure virtual method declaration
                if clause_text in ['= 0', '0']:
                    has_pure_virtual = True
            
            # Check if we have a simple identifier (not a function_declarator)
            # Fields have simple identifiers like '_width' or 'count'
            elif child.type in ['identifier', 'field_identifier']:
                has_simple_declarator = True
                
            # If we find a function_declarator, this is likely a real function/method
            # Real pure virtual methods will have function_declarator nodes
            elif child.type == 'function_declarator':
                has_function_declarator = True
                
            # Also check nested in pointer_declarator and reference_declarator
            # for cases like: virtual void* foo() = 0; or virtual int& bar() = 0;
            elif child.type in ['pointer_declarator', 'reference_declarator']:
                for nested_child in child.children:
                    if nested_child.type == 'function_declarator':
                        has_function_declarator = True
        
        # DETECTION LOGIC: It's a misclassified field if:
        # 1. Has a pure_virtual_clause with "= 0" (not a real pure virtual method)
        # 2. Has a simple identifier (field name, not a function signature)
        # 3. Does NOT have a function_declarator (not a real method)
        return has_pure_virtual and has_simple_declarator and not has_function_declarator

    def _parse_misclassified_field(self, node: Node, source: bytes, 
                                  access_level: AccessLevel) -> Optional[Member]:
        """
        Parse a field that was misclassified as function_definition due to = 0 initializer.
        
        TREE-SITTER-CPP BUG RECOVERY LOGIC
        GitHub Issue: https://github.com/tree-sitter/tree-sitter-cpp/issues/273
        
        This method recovers the field information from the incorrectly parsed AST.
        We extract the field name, type, and initializer value from the misclassified
        function_definition node and create a proper field Member object.
        
        Example recovery:
            Input AST: function_definition with pure_virtual_clause "= 0;"
            Output: Field member with name="_width", type="size_t", initializer="0"
        """
        member = Member(name="", member_type=MemberType.FIELD)
        member.access_level = access_level
        
        field_name = None
        field_type_parts = []
        initializer = None
        
        # Extract field information from the misclassified function_definition node
        for child in node.children:
            # Extract the field name
            if child.type in ['identifier', 'field_identifier']:
                field_name = self._extract_text(child, source)
                
            # Extract the field type (may have multiple parts like 'unsigned int')
            elif child.type in ['primitive_type', 'type_identifier', 'sized_type_specifier']:
                field_type_parts.append(self._extract_text(child, source))
                
            # Extract the initializer value from the pure_virtual_clause
            elif child.type == 'pure_virtual_clause':
                # Get the text of the initializer (e.g., "= 0;")
                initializer_text = self._extract_text(child, source).strip()
                
                # CRITICAL FIX: Remove trailing semicolon that's included in the AST
                # The pure_virtual_clause includes ";", giving us "= 0;" instead of "= 0"
                initializer_text = initializer_text.rstrip(';')
                
                # Extract just the value part (remove the "= " prefix)
                if initializer_text.startswith('= '):
                    initializer = initializer_text[2:]  # Get just "0" from "= 0"
                else:
                    initializer = initializer_text
        
        # Create the field member if we successfully extracted the necessary information
        if field_name and field_type_parts:
            member.name = field_name
            member.data_type = ' '.join(field_type_parts)
            if initializer:
                member.initializer = initializer
            member.line_number = source[:node.start_byte].count(b'\n') + 1
            return member
        
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