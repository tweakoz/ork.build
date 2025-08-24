"""
Display detailed information about C++ classes and structs
"""
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import obt.deco as deco
import obt.path
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import Entity, EntityType, Member, MemberType, AccessLevel, LocationType
from obt.cpp_formatter import CppFormatter
from obt.cpp_search_utils import find_entities_by_name, group_entities_by_namespace

class ClassDetailsDisplay:
    """Display detailed class/struct information"""
    
    def __init__(self, db: CppDatabaseV2):
        self.db = db
        self.deco = deco.Deco()
        
    def display_details(self, class_name: str, show_files: bool = True, root_path: Optional[Path] = None):
        """Display detailed information about a class/struct"""
        # Find all entities with this name (handles both short and canonical names)
        entities = find_entities_by_name(self.db, class_name)
        
        if not entities:
            print(f"{self.deco.red(f'Class/struct not found: {class_name}')}")
            return
        
        # Group by namespace to handle multiple classes with same name
        entities_by_ns = group_entities_by_namespace(entities)
        
        # Display each namespace separately if multiple
        for i, (namespace, namespace_entities) in enumerate(sorted(entities_by_ns.items())):
            if len(entities_by_ns) > 1:
                if i > 0:
                    print("\n" + "="*80 + "\n")
                print(f"{self.deco.cyan(f'NAMESPACE: {namespace}')}")
            
            # Use the first entity in this namespace (should be the most complete)
            entity = namespace_entities[0]
            self._display_single_class(entity, show_files, root_path)
    
    def _display_single_class(self, entity: Entity, show_files: bool, root_path: Optional[Path]):
        """Display details for a single class"""
        # Header
        primary_loc = entity.get_primary_location()
        file_path = None
        if primary_loc:
            file_path = str(obt.path.Path(primary_loc.file_path).sanitized)
        
        print(f"\n/////////////////////////////////////////////////////////////")
        print(f"// {entity.entity_type.value.title()} Details: {entity.short_name}")
        if file_path:
            print(f"// {file_path}")
        print(f"/////////\n")
        
        # Basic information
        self._display_basic_info(entity)
        
        # Base classes
        if entity.base_classes:
            self._display_base_classes(entity)
        
        # Template information
        if entity.is_template:
            self._display_template_info(entity)
        
        # Members by access level
        self._display_members(entity, show_files, root_path)
        
        # Method implementations
        if show_files:
            self._display_method_implementations(entity, root_path)
        
        # Locations
        if show_files and entity.locations:
            self._display_locations(entity, root_path)
    
    def _display_basic_info(self, entity: Entity):
        """Display basic class information"""
        print(f"{self.deco.yellow('BASIC INFO:')}")
        
        # Type and name
        type_str = entity.entity_type.value
        name_str = entity.canonical_name
        if entity.is_template and entity.template_params:
            name_str += entity.template_params
        print(f"  Type: {self.deco.cyan(type_str)} {self.deco.white(name_str)}")
        
        # Namespace
        ns_str = entity.namespace if entity.namespace else "(global)"
        print(f"  Namespace: {self.deco.green(ns_str)}")
        
        # Flags
        flags = []
        if entity.is_abstract:
            flags.append("abstract")
        if entity.is_final:
            flags.append("final")
        if entity.is_pod:
            flags.append("POD")
        if entity.is_template:
            flags.append("template")
        if entity.is_template_specialization:
            flags.append("specialization")
        
        if flags:
            print(f"  Attributes: {self.deco.magenta(', '.join(flags))}")
    
    def _display_base_classes(self, entity: Entity):
        """Display base class information"""
        print(f"\n{self.deco.yellow('BASE CLASSES:')}")
        for i, base in enumerate(entity.base_classes, 1):
            # Try to find the base class in the database
            base_clean = base.replace('public ', '').replace('private ', '').replace('protected ', '').strip()
            base_entities = []
            for entity_type in ['class', 'struct']:
                found = self.db.search_entities(entity_type=entity_type, name=base_clean)
                base_entities.extend(found)
            
            access_color = self.deco.green if 'public' in base else self.deco.red if 'private' in base else self.deco.yellow
            
            if base_entities:
                base_entity = base_entities[0]
                base_loc = base_entity.get_primary_location()
                if base_loc:
                    file_path = str(obt.path.Path(base_loc.file_path).sanitized)
                    print(f"  {i}. {access_color(base)} → {self.deco.cyan(file_path)}:{base_loc.line_number}")
                else:
                    print(f"  {i}. {access_color(base)} → {self.deco.white('(location unknown)')}")
            else:
                print(f"  {i}. {access_color(base)} → {self.deco.red('(not found in database)')}")
    
    def _display_template_info(self, entity: Entity):
        """Display template information"""
        print(f"\n{self.deco.yellow('TEMPLATE INFO:')}")
        if entity.template_params:
            print(f"  Parameters: {self.deco.cyan(entity.template_params)}")
        if entity.is_template_specialization and entity.specialized_from:
            print(f"  Specialized from: {self.deco.magenta(entity.specialized_from)}")
    
    def _display_members(self, entity: Entity, show_files: bool, root_path: Optional[Path]):
        """Display class members organized by access level"""
        if not entity.members:
            print(f"\n{self.deco.yellow('MEMBERS:')} {self.deco.gray('(none found)')}")
            return
        
        # Group members by access level
        public_members = entity.get_members_by_access(AccessLevel.PUBLIC)
        protected_members = entity.get_members_by_access(AccessLevel.PROTECTED)
        private_members = entity.get_members_by_access(AccessLevel.PRIVATE)
        
        # Display each access level
        for access_level, members, color_func in [
            ("PUBLIC", public_members, self.deco.green),
            ("PROTECTED", protected_members, self.deco.yellow),
            ("PRIVATE", private_members, self.deco.red)
        ]:
            if members:
                print(f"\n{self.deco.yellow(f'{access_level} MEMBERS:')} ({len(members)})")
                self._display_member_group(members, color_func, show_files, root_path, entity)
    
    def _display_member_group(self, members: List[Member], access_color_func, show_files: bool, root_path: Optional[Path], entity: Entity):
        """Display a group of members with the same access level"""
        # Group by member type
        fields = [m for m in members if m.member_type == MemberType.FIELD]
        methods = [m for m in members if m.member_type == MemberType.METHOD]
        constructors = [m for m in members if m.member_type == MemberType.CONSTRUCTOR]
        destructors = [m for m in members if m.member_type == MemberType.DESTRUCTOR]
        nested_types = [m for m in members if m.member_type == MemberType.NESTED_TYPE]
        enums = [m for m in members if m.member_type == MemberType.ENUM_VALUE]
        typedefs = [m for m in members if m.member_type == MemberType.TYPEDEF]
        
        # Display each type group
        for group_name, group_members in [
            ("Fields", fields),
            ("Constructors", constructors),
            ("Destructors", destructors),
            ("Methods", methods),
            ("Nested Types", nested_types),
            ("Enums", enums),
            ("Typedefs", typedefs)
        ]:
            if group_members:
                print(f"  {self.deco.cyan(group_name)}:")
                for member in sorted(group_members, key=lambda m: m.name):
                    self._display_member(member, access_color_func, show_files, root_path, entity)
    
    def _display_member(self, member: Member, access_color_func, show_files: bool, root_path: Optional[Path], entity: Entity):
        """Display a single member"""
        # Build member description
        parts = []
        
        # Handle method signatures with proper coloring
        if member.member_type == MemberType.METHOD and member.signature:
            # Apply basic coloring to the signature while preserving all content
            signature = member.signature
            
            # Simple approach: colorize based on basic patterns in the signature
            # This preserves all parameters while adding colors like function view
            colored_signature = self._colorize_method_signature(signature)
            parts.append(colored_signature)
            
            # Add additional modifiers that aren't part of the signature (like override, final, etc.)
            modifiers = []
            if member.is_override:
                modifiers.append("override")
            if member.is_final:
                modifiers.append("final")
            if member.is_deleted:
                modifiers.append("= delete")
            if member.is_default:
                modifiers.append("= default")
            
            if modifiers:
                parts.append(" " + self.deco.magenta(" ".join(modifiers)))
        else:
            # For non-methods, show modifiers first
            modifiers = []
            if member.is_static:
                modifiers.append("static")
            if member.is_const:
                modifiers.append("const")
            if hasattr(member, 'is_constexpr') and member.is_constexpr:
                modifiers.append("constexpr")
            if member.is_inline:
                modifiers.append("inline")
            if member.is_explicit:
                modifiers.append("explicit")
            
            if modifiers:
                parts.append(self.deco.magenta(" ".join(modifiers)))
            
        # Handle non-method types
        if member.member_type != MemberType.METHOD:
            if member.member_type == MemberType.ENUM_VALUE and member.value:
                name_display = f"{member.name} = {member.value}"
                parts.append(self.deco.white(name_display))
            elif member.member_type == MemberType.FIELD and member.value:
                # For fields with initialization values
                if member.data_type:
                    parts.append(self.deco.cyan(member.data_type))
                # Show field name with array dimensions and initialization value
                name_display = member.name
                if hasattr(member, 'array_dimensions') and member.array_dimensions:
                    name_display += member.array_dimensions
                parts.append(self.deco.white(name_display))
                parts.append(self.deco.white(" = "))
                parts.append(self.deco.green(member.value))
            else:
                # For fields and other members without initialization, show type and name
                if member.data_type:
                    parts.append(self.deco.cyan(member.data_type))
                
                # Show field name with array dimensions if present
                name_display = member.name
                if hasattr(member, 'array_dimensions') and member.array_dimensions:
                    name_display += member.array_dimensions
                parts.append(self.deco.white(name_display))
        
        # Line number if available
        if show_files and member.line_number > 0:
            parts.append(self.deco.gray(f":{member.line_number}"))
        
        print(f"    • {' '.join(parts)}")
    
    def _find_method_implementations(self, member: Member) -> List[object]:
        """Find implementation locations for a method from the member's own implementation_locations"""
        if not member.name or member.member_type != MemberType.METHOD:
            return []
        
        # Return the implementation locations stored in the member
        return member.implementation_locations
    
    def _colorize_signature(self, signature: str) -> str:
        """Apply colors to signature components like function view"""
        # Simple colorization - can be enhanced later
        # For now, just return the signature as-is since we're putting it in gray parentheses
        return signature
    
    def _colorize_method_signature(self, signature: str) -> str:
        """Apply colors to method signature to match function view"""
        import re
        
        # Pattern to match C++ function signatures
        # This regex captures: [modifiers] return_type function_name(parameters) [const/noexcept/etc]
        pattern = r'^((?:virtual\s+|static\s+|inline\s+|explicit\s+)*)(.*?)\s+(\w+)\s*(\([^)]*\))\s*(.*?)$'
        
        match = re.match(pattern, signature.strip())
        if not match:
            # Fallback: just color the whole thing white if we can't parse it
            return self.deco.white(signature)
        
        modifiers, return_type, func_name, params, trailing = match.groups()
        
        result_parts = []
        
        # Modifiers (virtual, static, etc.) - white like in function view
        if modifiers:
            result_parts.append(self.deco.white(modifiers))
        
        # Return type - magenta like in function view  
        if return_type:
            result_parts.append(self.deco.magenta(return_type.strip()))
            result_parts.append(self.deco.white(' '))
        
        # Function name - white
        result_parts.append(self.deco.white(func_name))
        
        # Parameters - color them like function view
        if params:
            colored_params = self._colorize_parameters(params)
            result_parts.append(colored_params)
        
        # Trailing modifiers (const, noexcept, etc.) - white
        if trailing:
            result_parts.append(self.deco.white(' ' + trailing.strip()))
        
        return ''.join(result_parts)
    
    def _colorize_parameters(self, params_str: str) -> str:
        """Color parameters like the function view: types in yellow, names in orange"""
        import re
        
        # Handle empty or void parameters
        if not params_str or params_str.strip() in ['()', '(void)']:
            return self.deco.white(params_str)
        
        # Extract content inside parentheses
        if params_str.startswith('(') and params_str.endswith(')'):
            inner = params_str[1:-1].strip()
            if not inner or inner == 'void':
                return self.deco.white(params_str)
            
            # Split parameters by comma
            param_parts = []
            current_param = []
            paren_depth = 0
            angle_depth = 0
            
            for char in inner:
                if char == '(' :
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == '<':
                    angle_depth += 1
                elif char == '>':
                    angle_depth -= 1
                elif char == ',' and paren_depth == 0 and angle_depth == 0:
                    param_parts.append(''.join(current_param).strip())
                    current_param = []
                    continue
                current_param.append(char)
            
            if current_param:
                param_parts.append(''.join(current_param).strip())
            
            # Color each parameter
            colored_params = []
            for param in param_parts:
                colored_params.append(self._colorize_single_parameter(param.strip()))
            
            return self.deco.white('(') + ', '.join(colored_params) + self.deco.white(')')
        
        return self.deco.white(params_str)
    
    def _colorize_single_parameter(self, param: str) -> str:
        """Color a single parameter: type in yellow, name in orange"""
        import re
        
        # Pattern to match type and optional name
        # This handles cases like: "int x", "const char* name", "std::vector<int> vec", "Context"
        match = re.match(r'^(.*?)(\s+\w+)?$', param.strip())
        if not match:
            return self.deco.white(param)
        
        type_part = match.group(1).strip()
        name_part = match.group(2)
        
        result = []
        if type_part:
            result.append(self.deco.yellow(type_part))
        
        if name_part:
            result.append(self.deco.orange(name_part))
        
        return ''.join(result) if result else self.deco.white(param)
    
    def _display_method_implementations(self, entity: Entity, root_path: Optional[Path]):
        """Display method implementation locations in a separate section, grouped by signature"""
        # Collect all method implementations grouped by signature
        method_implementations = {}
        
        for member in entity.members:
            if member.member_type == MemberType.METHOD:
                impl_locations = self._find_method_implementations(member)
                if impl_locations:
                    # Use the full signature as the key to separate overloads
                    signature_key = member.signature if member.signature else f"{member.name}()"
                    method_key = f"{member.name}::{signature_key}"
                    
                    # Each unique signature gets its own entry
                    if method_key not in method_implementations:
                        method_implementations[method_key] = {
                            'name': member.name,
                            'signature': member.signature or f"{member.name}()",
                            'locations': impl_locations
                        }
                    else:
                        # If we have the same signature, add the locations
                        method_implementations[method_key]['locations'].extend(impl_locations)
        
        if not method_implementations:
            return
        
        print(f"\n{self.deco.yellow('METHOD IMPLEMENTATIONS:')}")
        
        for method_key, method_data in sorted(method_implementations.items(), key=lambda x: (x[1]['name'], x[1]['signature'])):
            method_name = method_data['name']
            signature = method_data['signature']
            impl_locations = method_data['locations']
            
            # Display method name and signature (using same colors as function view)
            if signature and signature != method_name:
                # Use the same colorized signature approach as the methods section
                colored_signature = self._colorize_method_signature(signature)
                print(f"  {colored_signature}:")
            else:
                print(f"  {self.deco.white(method_name)}:")
            
            # Display implementation locations (same color scheme as standard view)
            for impl_loc in impl_locations:
                file_path = str(obt.path.Path(impl_loc.file_path).sanitized)
                print(f"    {self.deco.fg('grey7')}{file_path}{self.deco.reset()}:{self.deco.fg('grey9')}{str(impl_loc.line_number)}{self.deco.reset()}")
    
    def _display_locations(self, entity: Entity, root_path: Optional[Path]):
        """Display all locations where this entity appears"""
        print(f"\n{self.deco.yellow('LOCATIONS:')}")
        
        # Group by location type
        definitions = [loc for loc in entity.locations if loc.location_type == LocationType.DEFINITION]
        declarations = [loc for loc in entity.locations if loc.location_type == LocationType.DECLARATION]
        forward_decls = [loc for loc in entity.locations if loc.location_type == LocationType.FORWARD_DECLARATION]
        
        for loc_type, locations, color_func in [
            ("Definitions", definitions, self.deco.green),
            ("Declarations", declarations, self.deco.cyan),
            ("Forward Declarations", forward_decls, self.deco.yellow)
        ]:
            if locations:
                print(f"  {color_func(loc_type)}:")
                for loc in sorted(locations, key=lambda l: (l.file_path, l.line_number)):
                    file_path = str(obt.path.Path(loc.file_path).sanitized)
                    body_indicator = " [has body]" if loc.has_body else ""
                    print(f"    {self.deco.white(file_path)}:{self.deco.yellow(str(loc.line_number))}{self.deco.gray(body_indicator)}")
                    if loc.context:
                        # Show a snippet of the context
                        context_lines = loc.context.strip().split('\n')[:3]  # Show first 3 lines
                        for line in context_lines:
                            print(f"      {self.deco.gray(line.strip())}")
                        if len(loc.context.strip().split('\n')) > 3:
                            print(f"      {self.deco.gray('...')}")