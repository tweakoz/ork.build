"""
Display detailed information about C++ classes and structs
"""
from typing import List, Dict, Set, Optional, Tuple, Any
from pathlib import Path
import json
import obt.deco as deco
from obt.deco import CustomTheme
import obt.path
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import Entity, EntityType, Member, MemberType, AccessLevel, LocationType
from obt.cpp_type_system import TypeInfo, compose_type_with_theme
from obt.cpp_formatter import CppFormatter
from obt.cpp_search_utils import find_entities_by_name, group_entities_by_namespace

class ClassDetailsDisplay:
    """Display detailed class/struct information"""
    
    def __init__(self, db: CppDatabaseV2):
        self.db = db
        self.deco = deco.Deco()
        self.theme = self._create_cpp_theme()
    
    def _create_cpp_theme(self):
        """Create a custom theme for C++ member display"""
        theme = CustomTheme("cpp_members")
        
        # Headers and sections
        theme.add_style('section_header', fg='yellow', bold=True)
        theme.add_style('subsection_header', fg='cyan', bold=True)
        
        # Class/struct info
        theme.add_style('class_name', fg='white', bold=True)
        theme.add_style('namespace', fg='green')
        theme.add_style('entity_type', fg='cyan')
        
        # Access levels (using shade progression)
        theme.add_style('public', fg='grn0')      # brightest green
        theme.add_style('protected', fg='grn1')   # 1 shade darker
        theme.add_style('private', fg='grn2')     # 2 shades darker
        
        # Member types and names by access level
        # Public members - brightest
        theme.add_style('public_type', fg='yel0')
        theme.add_style('public_std_type', fg='sata2')  # std:: non-template types (std::string)
        theme.add_style('public_std_template_type', fg='sata3')  # std:: template types (std::vector)
        theme.add_style('public_template_type', fg='blx0')  # template types (non-std)
        theme.add_style('public_int_type', fg='sata1')  # integer types
        theme.add_style('public_float_type', fg='sata2')  # floating point types
        theme.add_style('public_void_bool_type', fg='sata3')  # void/bool types
        theme.add_style('public_name', fg='gry0')
        
        # Protected members - 1 shade darker
        theme.add_style('protected_type', fg='yel1')
        theme.add_style('protected_std_type', fg='ora1')  # std:: non-template types
        theme.add_style('protected_std_template_type', fg='satb3')  # std:: template types
        theme.add_style('protected_template_type', fg='blx1')  # template types (non-std)
        theme.add_style('protected_int_type', fg='satb1')  # integer types
        theme.add_style('protected_float_type', fg='satb2')  # floating point types
        theme.add_style('protected_void_bool_type', fg='satb3')  # void/bool types
        theme.add_style('protected_name', fg='gry1')
        
        # Private members - 2 shades darker
        theme.add_style('private_type', fg='yel2')
        theme.add_style('private_std_type', fg='ora2')  # std:: non-template types
        theme.add_style('private_std_template_type', fg='satc1')  # std:: template types
        theme.add_style('private_template_type', fg='cyn2')  # template types (non-std)
        theme.add_style('private_int_type', fg='grn2')  # integer types
        theme.add_style('private_float_type', fg='yel2')  # floating point types
        theme.add_style('private_void_bool_type', fg='mag2')  # void/bool types
        theme.add_style('private_name', fg='gry2')
        
        # Modifiers - with access level variations
        # Public modifiers - brightest
        theme.add_style('public_static', fg='mag0')
        theme.add_style('public_const', fg='red0')
        theme.add_style('public_virtual', fg='teal0')
        theme.add_style('public_override', fg='teal0')
        theme.add_style('public_final', fg='teal0')
        theme.add_style('public_deleted', fg='red0')
        theme.add_style('public_default', fg='grn0')
        
        # Protected modifiers - 1 shade darker
        theme.add_style('protected_static', fg='mag1')
        theme.add_style('protected_const', fg='red1')
        theme.add_style('protected_virtual', fg='teal0')
        theme.add_style('protected_override', fg='teal0')
        theme.add_style('protected_final', fg='teal0')
        theme.add_style('protected_deleted', fg='red1')
        theme.add_style('protected_default', fg='grn1')
        
        # Private modifiers - 2 shades darker
        theme.add_style('private_static', fg='mag2')
        theme.add_style('private_const', fg='red2')
        theme.add_style('private_virtual', fg='teal2')
        theme.add_style('private_override', fg='teal2')
        theme.add_style('private_final', fg='teal2')
        theme.add_style('private_deleted', fg='red2')
        theme.add_style('private_default', fg='grn2')
        
        # Values and parameters
        theme.add_style('value', fg='grn0')
        
        # Method/function arguments with access level variations
        # Public arguments
        theme.add_style('public_arg_type', fg='yel0')
        theme.add_style('public_arg_identifier', fg='pnk0')
        theme.add_style('public_arg_const', fg='red0')
        
        # Protected arguments - 1 shade darker
        theme.add_style('protected_arg_type', fg='sata1')
        theme.add_style('protected_arg_identifier', fg='pnk1')
        theme.add_style('protected_arg_const', fg='red1')
        
        # Private arguments - 2 shades darker
        theme.add_style('private_arg_type', fg='sata2')
        theme.add_style('private_arg_identifier', fg='pnk2')
        theme.add_style('private_arg_const', fg='red2')
        
        # File locations
        theme.add_style('file_path', fg='cyan')
        theme.add_style('line_number', fg='grey12')
        
        # Inheritance
        theme.add_style('base_class', fg='yellow')
        theme.add_style('inherited_from', fg='grey14', dim=True)
        theme.add_style('local_members', fg='white')
        
        # Special markers
        theme.add_style('not_found', fg='red')
        theme.add_style('none', fg='grey10')
        theme.add_style('count', fg='white')
        
        return theme
        
    def to_json(self, class_name: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Convert class details to JSON format optimized for AI readability.
        
        Schema:
        {
            "entity": {
                "name": "fully::qualified::ClassName",
                "short_name": "ClassName",
                "type": "class|struct",
                "file": "/path/to/file.h",
                "line": 123,
                "namespace": "fully::qualified",
                "is_template": bool,
                "template_params": "template<typename T>",
                "base_classes": ["Base1", "public Base2"],
                "derived_classes": ["Derived1", "Derived2"]
            },
            "members": {
                "public": {
                    "fields": [...],
                    "methods": [...],
                    "constructors": [...],
                    "destructors": [...],
                    "nested_types": [...],
                    "typedefs": [...]
                },
                "protected": {...},
                "private": {...}
            },
            "summary": {
                "total_members": 42,
                "public_count": 20,
                "protected_count": 10,
                "private_count": 12,
                "has_virtual_methods": bool,
                "is_abstract": bool
            }
        }
        
        Filters can include:
        - access_level: "public"|"protected"|"private"|["public","protected"]
        - member_type: "field"|"method"|"constructor"|etc or list
        - is_static: true|false
        - is_virtual: true|false
        - is_const: true|false
        - name_pattern: "regex pattern"
        """
        result = {
            "entity": {},
            "members": {
                "public": {},
                "protected": {},
                "private": {}
            },
            "summary": {}
        }
        
        # Find entities - use same method as display_details for consistency
        entities = find_entities_by_name(self.db, class_name)
        
        if not entities:
            return json.dumps({"error": f"No class or struct named '{class_name}' found"}, indent=2)
        
        entity = entities[0]
        
        # Entity info
        result["entity"] = {
            "name": entity.canonical_name,
            "short_name": entity.short_name,
            "type": entity.entity_type.value,
            "file": getattr(entity, 'file_path', ''),
            "line": getattr(entity, 'line_number', 0),
            "namespace": entity.namespace or "",
            "is_template": entity.is_template,
            "template_params": entity.template_params or "",
            "base_classes": entity.base_classes or [],
            "derived_classes": [e.canonical_name for e in self.db.find_derived_classes(entity.canonical_name)]
        }
        
        # Process members with filtering
        if entity.members:
            members_by_access = self._group_members_for_json(entity.members, filters)
            result["members"] = members_by_access
        
        # Summary statistics
        total = 0
        public_count = 0
        protected_count = 0
        private_count = 0
        has_virtual = False
        
        for member in (entity.members or []):
            if self._should_include_member(member, filters):
                total += 1
                if member.access_level == AccessLevel.PUBLIC:
                    public_count += 1
                elif member.access_level == AccessLevel.PROTECTED:
                    protected_count += 1
                else:
                    private_count += 1
                if member.is_virtual:
                    has_virtual = True
        
        result["summary"] = {
            "total_members": total,
            "public_count": public_count,
            "protected_count": protected_count,
            "private_count": private_count,
            "has_virtual_methods": has_virtual,
            "is_abstract": entity.is_abstract
        }
        
        return json.dumps(result, indent=2, default=str)
    
    def _should_include_member(self, member: Member, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if member passes all filters"""
        if not filters:
            return True
        
        # Access level filter
        if 'access_level' in filters:
            allowed_access = filters['access_level']
            if isinstance(allowed_access, str):
                allowed_access = [allowed_access]
            if member.access_level.name.lower() not in [a.lower() for a in allowed_access]:
                return False
        
        # Member type filter
        if 'member_type' in filters:
            allowed_types = filters['member_type']
            if isinstance(allowed_types, str):
                allowed_types = [allowed_types]
            if member.member_type.value not in allowed_types:
                return False
        
        # Boolean filters
        for attr in ['is_static', 'is_virtual', 'is_const']:
            if attr in filters:
                if getattr(member, attr, False) != filters[attr]:
                    return False
        
        # Name pattern filter (regex)
        if 'name_pattern' in filters:
            import re
            if not re.search(filters['name_pattern'], member.name):
                return False
        
        return True
    
    def _group_members_for_json(self, members: List[Member], filters: Optional[Dict[str, Any]]) -> Dict:
        """Group members by access level and type for JSON output"""
        result = {
            "public": {},
            "protected": {},
            "private": {}
        }
        
        for member in members:
            if not self._should_include_member(member, filters):
                continue
            
            access_key = member.access_level.name.lower()
            type_key = self._get_member_type_key(member.member_type)
            
            if type_key not in result[access_key]:
                result[access_key][type_key] = []
            
            result[access_key][type_key].append(self._member_to_dict(member))
        
        return result
    
    def _get_member_type_key(self, member_type: MemberType) -> str:
        """Get JSON key for member type"""
        type_map = {
            MemberType.FIELD: "fields",
            MemberType.METHOD: "methods",
            MemberType.CONSTRUCTOR: "constructors",
            MemberType.DESTRUCTOR: "destructors",
            MemberType.NESTED_TYPE: "nested_types",
            MemberType.TYPEDEF: "typedefs",
            MemberType.ENUM_VALUE: "enums"
        }
        return type_map.get(member_type, "other")
    
    def _member_to_dict(self, member: Member) -> Dict:
        """Convert member to dictionary for JSON"""
        return {
            "name": member.name,
            "type": member.data_type or "",
            "signature": member.signature or "",
            "line": member.line_number,
            "is_static": member.is_static,
            "is_const": member.is_const,
            "is_virtual": member.is_virtual,
            "is_pure_virtual": member.is_pure_virtual,
            "is_override": member.is_override,
            "is_final": member.is_final,
            "is_inline": member.is_inline,
            "is_explicit": member.is_explicit,
            "is_deleted": member.is_deleted,
            "is_default": member.is_default,
            "value": member.value or "",
            "array_dims": member.array_dimensions or ""
        }
    
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
        """Display class members organized by inheritance, access level, and name"""
        # Collect all inherited members
        inherited_members = self._collect_inherited_members(entity)
        
        # Display local members first
        if entity.members:
            print(f"\n{self.theme.decorate('section_header', 'LOCAL MEMBERS:')}")
            self._display_members_by_access(entity.members, show_files, root_path, entity)
        else:
            print(f"\n{self.theme.decorate('section_header', 'LOCAL MEMBERS:')} {self.theme.decorate('none', '(none)')}")
        
        # Display inherited members by base class
        if inherited_members:
            for base_name, base_members in inherited_members:
                print(f"\n{self.theme.decorate('inherited_from', f'INHERITED FROM {base_name}:')}")
                self._display_members_by_access(base_members, show_files, root_path, entity)
    
    def _collect_inherited_members(self, entity: Entity) -> List[Tuple[str, List[Member]]]:
        """Recursively collect members from all base classes"""
        inherited = []
        
        if not entity.base_classes:
            return inherited
        
        for base in entity.base_classes:
            # Clean up base class name
            base_clean = base.replace('public ', '').replace('private ', '').replace('protected ', '').strip()
            
            # Find base class in database
            base_entities = []
            for entity_type in ['class', 'struct']:
                found = self.db.search_entities(entity_type=entity_type, name=base_clean)
                base_entities.extend(found)
            
            if base_entities:
                base_entity = base_entities[0]
                # Add this base's members
                if base_entity.members:
                    inherited.append((base_clean, base_entity.members))
                # Recursively get members from base's bases
                sub_inherited = self._collect_inherited_members(base_entity)
                for sub_base_name, sub_members in sub_inherited:
                    # Add indication of inheritance chain
                    chain_name = f"{base_clean} → {sub_base_name}"
                    inherited.append((chain_name, sub_members))
            else:
                # Base class not found in database - can't show inherited members
                pass
        
        return inherited
    
    def _display_members_by_access(self, members: List[Member], show_files: bool, root_path: Optional[Path], entity: Entity):
        """Display members grouped by access level"""
        # Group members by access level
        public_members = [m for m in members if m.access_level == AccessLevel.PUBLIC]
        protected_members = [m for m in members if m.access_level == AccessLevel.PROTECTED]
        private_members = [m for m in members if m.access_level == AccessLevel.PRIVATE]
        
        # Display each access level
        for access_level, level_members, style_name in [
            ("PUBLIC", public_members, 'public'),
            ("PROTECTED", protected_members, 'protected'),
            ("PRIVATE", private_members, 'private')
        ]:
            if level_members:
                access_text = self.theme.decorate(style_name, f'{access_level}:')
                count_text = self.theme.decorate('count', f'({len(level_members)})')
                print(f"  {access_text} {count_text}")
                self._display_member_group(level_members, style_name, show_files, root_path, entity)
    
    def _display_member_group(self, members: List[Member], access_style, show_files: bool, root_path: Optional[Path], entity: Entity):
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
                print(f"  {self.theme.decorate('subsection_header', group_name)}:")
                for member in sorted(group_members, key=lambda m: m.name.lower()):
                    self._display_member(member, access_style, show_files, root_path, entity)
    
    def _display_member(self, member: Member, access_style, show_files: bool, root_path: Optional[Path], entity: Entity):
        """Display a single member"""
        # Build member description
        parts = []
        
        # Determine the style names based on access level
        type_style = f"{access_style}_type"
        name_style = f"{access_style}_name"
        
        # Handle method signatures with proper coloring
        if member.member_type == MemberType.METHOD and member.signature:
            # Apply coloring to the signature using access-level-specific styles
            signature = member.signature
            
            # Colorize signature with access-specific styles
            colored_signature = self._colorize_method_signature_with_access(signature, access_style)
            parts.append(colored_signature)
            
            # Don't add modifiers - they should already be in the signature
        else:
            # Don't add modifiers - they should already be in data_type
            pass
            
        # Handle non-method types
        if member.member_type != MemberType.METHOD:
            if member.member_type == MemberType.ENUM_VALUE and member.value:
                name_display = f"{member.name} = {member.value}"
                parts.append(self.theme.decorate(name_style, name_display))
            elif member.member_type == MemberType.FIELD and member.value:
                # For fields with initialization values
                if member.data_type:
                    type_info = self._member_to_type_info(member)
                    parts.append(compose_type_with_theme(type_info, self.theme, access_style))
                # Show field name with array dimensions and initialization value
                name_display = member.name
                if hasattr(member, 'array_dimensions') and member.array_dimensions:
                    name_display += member.array_dimensions
                parts.append(self.theme.decorate(name_style, name_display))
                parts.append(self.deco.white(" = "))
                parts.append(self.theme.decorate("value",member.value))
            else:
                # For fields and other members without initialization, show type and name
                if member.data_type:
                    type_info = self._member_to_type_info(member)
                    parts.append(compose_type_with_theme(type_info, self.theme, access_style))
                
                # Show field name with array dimensions if present
                name_display = member.name
                if hasattr(member, 'array_dimensions') and member.array_dimensions:
                    name_display += member.array_dimensions
                parts.append(self.theme.decorate(name_style, name_display))
        
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
    
    def _colorize_method_signature_with_access(self, signature: str, access_style: str) -> str:
        """Apply colors to method signature using access-level-specific styles"""
        import re
        
        # Get the style names for this access level
        type_style = f"{access_style}_type"
        name_style = f"{access_style}_name"
        
        # Pattern to match C++ function signatures
        # This regex captures: [modifiers] return_type function_name(parameters) [const/noexcept/etc]
        pattern = r'^((?:virtual\s+|static\s+|inline\s+|explicit\s+)*)(.*?)\s+(\w+)\s*(\([^)]*\))\s*(.*?)$'
        
        match = re.match(pattern, signature.strip())
        if not match:
            # Fallback: use name style for the whole signature
            return self.theme.decorate(name_style, signature)
        
        modifiers, return_type, func_name, params, trailing = match.groups()
        
        result_parts = []
        
        # Modifiers (virtual, static, etc.) - use access-specific modifier color
        if modifiers:
            result_parts.append(self.theme.decorate(f'{access_style}_static', modifiers))
        
        # Return type - use template parser if it contains templates
        if return_type:
            return_type = return_type.strip()
            if '<' in return_type:
                # Import at function level to avoid circular dependency
                from obt.cpp_type_system import parse_template_type
                tokens = parse_template_type(return_type)
                for token, token_type, level in tokens:
                    if token_type == 'std_type':
                        result_parts.append(self.theme.decorate(f'{access_style}_std_type', token))
                    elif token_type == 'std_template_type':
                        result_parts.append(self.theme.decorate(f'{access_style}_std_template_type', token))
                    elif token_type == 'template_type':
                        result_parts.append(self.theme.decorate(f'{access_style}_template_type', token))
                    elif token_type in ['type', 'int_type', 'float_type', 'void_bool_type']:
                        # Check if token is a modifier
                        if token in ['const', 'volatile', 'mutable']:
                            result_parts.append(self.theme.decorate(f'{access_style}_const', token))
                        else:
                            # Use specific style for primitive types
                            style = f"{access_style}_{token_type}" if token_type != 'type' else type_style
                            result_parts.append(self.theme.decorate(style, token))
                    else:
                        # Delimiters and separators - no coloring
                        result_parts.append(token)
            elif return_type.startswith('std::'):
                result_parts.append(self.theme.decorate(f'{access_style}_std_type', return_type))
            else:
                # Simple type - might have modifiers
                from obt.cpp_type_system import classify_primitive_type
                tokens = return_type.split()
                for token in tokens:
                    if token in ['const', 'volatile', 'mutable']:
                        result_parts.append(self.theme.decorate(f'{access_style}_const', token))
                        result_parts.append(' ')
                    else:
                        # Check if it's a primitive type
                        prim_type = classify_primitive_type(token)
                        if prim_type != 'type':
                            style = f"{access_style}_{prim_type}"
                        else:
                            style = type_style
                        result_parts.append(self.theme.decorate(style, token))
                        result_parts.append(' ')
            result_parts.append(' ')
        
        # Function name - use name style for this access level
        result_parts.append(self.theme.decorate(name_style, func_name))
        
        # Parameters - color them with access-specific styles
        if params:
            colored_params = self._colorize_parameters_with_access(params, access_style)
            result_parts.append(colored_params)
        
        # Trailing modifiers (const, noexcept, final, etc.) - parse and apply appropriate colors
        if trailing:
            trailing_parts = []
            for token in trailing.strip().split():
                if token == 'final':
                    trailing_parts.append(self.theme.decorate(f'{access_style}_final', token))
                elif token == 'override':
                    trailing_parts.append(self.theme.decorate(f'{access_style}_override', token))
                elif token in ['const', 'noexcept', 'volatile']:
                    trailing_parts.append(self.theme.decorate(f'{access_style}_const', token))
                elif token in ['=', 'delete', 'default', '0']:
                    # Handle = delete, = default, = 0
                    trailing_parts.append(token)
                else:
                    trailing_parts.append(self.theme.decorate(f'{access_style}_const', token))
            result_parts.append(' ' + ' '.join(trailing_parts))
        
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
    
    def _colorize_parameters_with_access(self, params_str: str, access_style: str) -> str:
        """Color parameters using access-level-specific styles"""
        import re
        
        # Handle empty or void parameters
        if not params_str or params_str.strip() in ['()', '(void)']:
            return params_str
        
        # Extract content inside parentheses
        if params_str.startswith('(') and params_str.endswith(')'):
            inner = params_str[1:-1].strip()
            if not inner or inner == 'void':
                return params_str
            
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
            
            # Color each parameter with access-specific styles
            colored_params = []
            for param in param_parts:
                colored_params.append(self._colorize_single_parameter_with_access(param.strip(), access_style))
            
            return '(' + ', '.join(colored_params) + ')'
        
        return params_str
    
    def _member_to_type_info(self, member: Member) -> TypeInfo:
        """Reconstruct TypeInfo from Member fields"""
        # Extract base type from data_type by removing modifiers
        # For now, use data_type as base, but ideally this should come from base_type_id
        base_type = member.data_type or ""
        
        # Remove known modifiers from the beginning to get clean base type
        modifiers = ['static', 'const', 'constexpr', 'volatile', 'mutable', 'inline', 'explicit']
        tokens = base_type.split()
        base_tokens = []
        for token in tokens:
            if token not in modifiers:
                base_tokens.append(token)
        base_type = ' '.join(base_tokens) if base_tokens else base_type
        
        return TypeInfo(
            base_type=base_type,
            is_static=member.is_static,
            is_const=member.is_const,
            is_volatile=member.is_volatile,
            is_constexpr=getattr(member, 'is_constexpr', False),
            is_mutable=getattr(member, 'is_mutable', False),
            pointer_depth=member.pointer_depth,
            is_reference=member.is_reference,
            is_rvalue_reference=member.is_rvalue_reference,
            array_dimensions=[]  # TODO: parse from member.array_dimensions
        )
    
    def _theme_type_string(self, type_str: str, access_style: str) -> str:
        """
        Apply theme colors to a complete type string.
        Recognizes and themes modifiers like static, const, etc.
        """
        import re
        
        # Split type into tokens while preserving spacing
        tokens = type_str.split()
        themed_tokens = []
        
        # Known modifiers to theme
        modifiers = {'static', 'const', 'constexpr', 'volatile', 'mutable', 'inline', 'explicit'}
        
        for token in tokens:
            if token in modifiers:
                # Apply modifier-specific theme
                if token == 'static' or token == 'inline' or token == 'explicit':
                    themed_tokens.append(self.theme.decorate(f'{access_style}_static', token))
                elif token == 'const' or token == 'constexpr' or token == 'volatile' or token == 'mutable':
                    themed_tokens.append(self.theme.decorate(f'{access_style}_const', token))
            else:
                # It's the actual type - apply type theme
                themed_tokens.append(self.theme.decorate(f'{access_style}_type', token))
        
        return ' '.join(themed_tokens)
    
    def _colorize_single_parameter_with_access(self, param: str, access_style: str) -> str:
        """Color a single parameter using access-level-specific styles"""
        import re
        
        # Style names for this access level
        type_style = f"{access_style}_arg_type"
        name_style = f"{access_style}_arg_identifier"
        const_style = f"{access_style}_arg_const"
        
        # Parse the parameter more carefully
        # Handle patterns like: "const Type* name", "Type&& name", "const Type& name"
        param = param.strip()
        
        # Split into tokens and process each
        tokens = param.split()
        if not tokens:
            return param
            
        result_parts = []
        type_tokens = []
        identifier = None
        
        # Process tokens - everything except last token is usually type
        # unless last token has special chars like * or &
        for i, token in enumerate(tokens):
            # Check if this token is a modifier
            if token in ['const', 'volatile', 'mutable']:
                result_parts.append(self.theme.decorate(const_style, token))
            elif i == len(tokens) - 1 and not any(c in token for c in ['*', '&', '<', '>', ':', '[']):
                # Last token without special chars is likely the identifier
                identifier = token
            elif token.startswith('std::'):
                # std:: types get special color
                std_type_style = f"{access_style}_std_type"
                result_parts.append(self.theme.decorate(std_type_style, token))
            else:
                # Check if it's a primitive type
                from obt.cpp_type_system import classify_primitive_type
                prim_type = classify_primitive_type(token)
                if prim_type != 'type':
                    # Use primitive-specific style
                    prim_style = f"{access_style}_{prim_type}"
                    result_parts.append(self.theme.decorate(prim_style, token))
                else:
                    # Regular type
                    result_parts.append(self.theme.decorate(type_style, token))
        
        # Add identifier if found
        if identifier:
            result_parts.append(self.theme.decorate(name_style, identifier))
            
        return ' '.join(result_parts)
    
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