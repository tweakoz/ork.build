"""
C++ Entity Display Module for V2 Database
Standalone implementation for displaying C++ entities with formatting and colors
"""

from collections import defaultdict
from typing import List, Optional
from pathlib import Path
from obt.deco import Deco
from obt.cpp_formatter import CppFormatter
from obt.cpp_entities_v2 import Entity, EntityType, MemberType, AccessLevel
import obt.path
import json

class CppEntityDisplayV2:
    """Handles display of C++ entities with formatting and colors"""
    
    def __init__(self, line_length: int = 148):
        self.LINE_LENGTH = line_length
        self.deco = Deco()
        
        # Define column widths
        self.line_col_width = 8   # Line number
        self.type_col_width = 10  # Match type
        self.kind_col_width = 12  # Entity kind
        self.namespace_col_width = 30  # Namespace
        self.identifier_col_width = self.LINE_LENGTH - (
            self.line_col_width + self.type_col_width + 
            self.kind_col_width + self.namespace_col_width
        )  # Identifier gets the rest
    
    def get_match_type(self, entity: Entity) -> str:
        """Determine the match type for an entity"""
        # For V2, we primarily have definitions
        # Could extend to check location types if needed
        return 'DEF'
    
    def get_entity_kind(self, entity: Entity) -> str:
        """Get the entity kind for display"""
        if entity.entity_type == EntityType.FUNCTION:
            if entity.is_method:
                return "method"
            else:
                return "function"
        else:
            return entity.entity_type.value.lower()
    
    def _render_tagged_string(self, tagged_string) -> str:
        """Render a TaggedString with appropriate colors"""
        result = ""
        for text, tag in tagged_string.parts:
            if tag == 'keyword':
                result += self.deco.magenta(text)
            elif tag == 'type':
                result += self.deco.cyan(text)
            elif tag == 'param':
                result += self.deco.green(text)
            elif tag == 'default':
                result += self.deco.yellow(text)
            elif tag == 'template':
                result += self.deco.orange(text)
            elif tag == 'name':
                result += self.deco.white(text)
            else:
                result += self.deco.white(text)
        return result
    
    def get_kind_color(self, kind: str):
        """Get color function for entity kind"""
        kind_colors = {
            'class': self.deco.cyan,
            'struct': self.deco.cyan,
            'function': self.deco.cyan,
            'method': self.deco.cyan,
            'enum': self.deco.magenta,
            'typedef': self.deco.yellow,
            'alias': self.deco.yellow,
            'namespace': self.deco.blue,
            'variable': self.deco.green,
            'union': self.deco.orange,
        }
        return kind_colors.get(kind, self.deco.white)
    
    def display_entities(self, entities: List[Entity], root_path: Optional[Path] = None, 
                        sepfiles: bool = False, show_base_class: Optional[str] = None):
        """Display entities with full formatting
        
        Args:
            entities: List of entities to display
            root_path: Root path for relative display
            sepfiles: Add separator between files
            show_base_class: If set, show inheritance from this base class
        """
        if not entities:
            print("// No matching entities found")
            return
        
        # Group by file
        by_file = defaultdict(list)
        for entity in entities:
            if entity.locations:
                filepath = entity.locations[0].file_path
            else:
                filepath = "unknown"
            by_file[filepath].append(entity)
        
        print("/////////////////////////////////////////////////////////////")
        print(f"// Found {len(entities)} entities")
        print("/////////")
        
        file_count = 0
        
        for filepath in sorted(by_file.keys()):
            file_entities = by_file[filepath]
            
            # Add separator between files if requested
            if sepfiles and file_count > 0:
                print()
            
            # Print filename header (pink on grey1 background, centered)
            print()
            display_path = str(obt.path.Path(filepath).sanitized) if filepath != "unknown" else "unknown"
            filename_padded = display_path.center(self.LINE_LENGTH)
            print(self.deco.bg('grey1') + self.deco.fg('pink') + 
                  filename_padded + self.deco.reset())
            
            file_count += 1
            
            # Sort entities by line number
            sorted_entities = sorted(file_entities, 
                                    key=lambda x: x.locations[0].line_number if x.locations else 0)
            
            for entity in sorted_entities:
                # Build display components
                line = entity.locations[0].line_number if entity.locations else 0
                match_type = self.get_match_type(entity)
                kind = self.get_entity_kind(entity)
                namespace_text = entity.namespace if entity.namespace else "-"
                
                # Truncate namespace if too long
                if len(namespace_text) > self.namespace_col_width - 2:
                    keep_start = 8
                    keep_end = self.namespace_col_width - 4 - keep_start
                    namespace_text = namespace_text[:keep_start] + "..." + namespace_text[-keep_end:]
                
                # Build identifier
                if entity.entity_type == EntityType.FUNCTION:
                    formatter = CppFormatter(deco=None)
                    formatter.set_namespace_context(entity.namespace or "")
                    
                    # Create a compatible object for formatter
                    class FuncEntity:
                        pass
                    func = FuncEntity()
                    func.name = entity.short_name
                    func.return_type = entity.return_type or ""
                    func.is_template = entity.is_template
                    func.template_params = entity.template_params or ""
                    func.is_virtual = entity.is_virtual
                    func.is_static = entity.is_static
                    func.is_const = entity.is_const
                    func.is_method = entity.is_method
                    
                    # Convert parameters
                    if entity.parameters:
                        params_list = []
                        for p in entity.parameters:
                            param_dict = {
                                'type': p.param_type,
                                'name': p.name or '',
                                'default': p.default_value or ''
                            }
                            params_list.append(param_dict)
                        func.parameters = params_list
                    else:
                        func.parameters = []
                    
                    identifier = formatter.format_function_signature(func)
                else:
                    identifier = entity.short_name
                    if entity.is_template and entity.template_params:
                        identifier = f"template{entity.template_params} {identifier}"
                    
                    # Add inheritance info if requested
                    if show_base_class and entity.base_classes:
                        for base in entity.base_classes:
                            # Clean up base class name
                            base_clean = base.replace('public ', '').replace('private ', '').replace('protected ', '')
                            base_short = base_clean.split('::')[-1] if '::' in base_clean else base_clean
                            search_short = show_base_class.split('::')[-1] if '::' in show_base_class else show_base_class
                            if base_clean == show_base_class or base_short == search_short:
                                identifier += f" : {base}"
                                break
                
                # Format columns
                line_str = str(line).center(self.line_col_width)
                type_str = match_type.center(self.type_col_width)
                kind_str = kind.center(self.kind_col_width)
                namespace_str = namespace_text.center(self.namespace_col_width)
                
                # Get colors
                kind_color = self.get_kind_color(kind)
                
                # Handle the identifier display
                if hasattr(identifier, 'parts'):
                    # It's a TaggedString from CppFormatter - render it with colors
                    identifier_text = self._render_tagged_string(identifier)
                    plain_len = len(identifier.plain_text())
                    if plain_len < self.identifier_col_width:
                        padding = ' ' * (self.identifier_col_width - plain_len)
                        identifier_rendered = self.deco.bg('grey2') + identifier_text + padding + self.deco.reset()
                    else:
                        identifier_rendered = self.deco.bg('grey2') + identifier_text + self.deco.reset()
                else:
                    # Simple string identifier
                    padded_identifier = str(identifier).ljust(self.identifier_col_width) if len(str(identifier)) < self.identifier_col_width else str(identifier)
                    identifier_rendered = self.deco.bg('grey2') + self.deco.white(padded_identifier) + self.deco.reset()
                
                colored_columns = [
                    self.deco.bg('black') + self.deco.yellow(line_str) + self.deco.reset(),
                    self.deco.bg('grey2') + self.deco.green(type_str) + self.deco.reset(),
                    self.deco.bg('grey4') + kind_color(kind_str) + self.deco.reset(),
                    self.deco.bg('grey1') + self.deco.brightgreen(namespace_str) + self.deco.reset(),
                    identifier_rendered
                ]
                
                print(''.join(colored_columns))