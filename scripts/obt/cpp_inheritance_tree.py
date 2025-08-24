"""
Display C++ inheritance hierarchies as tree structures
"""
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import obt.deco as deco
import obt.path
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import Entity, EntityType
from obt.cpp_search_utils import find_entities_by_name, group_entities_by_namespace

class InheritanceTreeDisplay:
    """Display inheritance hierarchies with tree-like visualization"""
    
    def __init__(self, db: CppDatabaseV2):
        self.db = db
        self.deco = deco.Deco()
        self._cache = {}  # Cache for performance
        
    
    def _build_inheritance_tree_for_entity(self, entity: Entity) -> Dict:
        """Build inheritance tree for a specific entity (prevents namespace conflicts)"""
        tree = {
            'name': entity.short_name,
            'entity': entity,
            'parents': [],
            'children': []
        }
        
        # Get parents (base classes)
        if entity.base_classes:
            for base in entity.base_classes:
                # Clean up base class name (remove 'public', 'private', 'protected')
                base_name = base.replace('public ', '').replace('private ', '').replace('protected ', '').strip()
                # Skip generic base classes that are likely not in our database
                if base_name not in ['Object', 'object']:
                    # Find parent entity and recurse
                    parent_entities = find_entities_by_name(self.db, base_name)
                    if parent_entities:
                        parent_tree = self._build_inheritance_tree_for_entity(parent_entities[0])
                    else:
                        # Parent not found in database - create placeholder
                        parent_tree = {
                            'name': base_name,
                            'entity': None,
                            'parents': [],
                            'children': []
                        }
                    tree['parents'].append(parent_tree)
        
        # Get children (derived classes) - only look for classes in same namespace
        namespace = entity.namespace
        derived = self.db.find_derived_classes(entity.short_name)
        for child_entity in derived:
            # Only include derived classes from the same namespace to avoid mixing hierarchies
            if child_entity.namespace == namespace:
                child_tree = {
                    'name': child_entity.short_name,
                    'entity': child_entity,
                    'parents': [],  # Don't recurse up from children
                    'children': []   # Optionally recurse down
                }
                # Recursively get grandchildren (with namespace filtering)
                child_tree['children'] = self._get_children_trees_filtered(
                    child_entity.short_name, {entity.short_name}, namespace)
                tree['children'].append(child_tree)
        
        return tree
    
    def _get_children_trees_filtered(self, class_name: str, visited: Set[str], namespace: str) -> List[Dict]:
        """Recursively get children, avoiding cycles and filtering by namespace"""
        if class_name in visited:
            return []
        visited.add(class_name)
        
        children = []
        derived = self.db.find_derived_classes(class_name)
        for child_entity in derived:
            if child_entity.short_name not in visited and child_entity.namespace == namespace:
                child_tree = {
                    'name': child_entity.short_name,
                    'entity': child_entity,
                    'parents': [],
                    'children': self._get_children_trees_filtered(child_entity.short_name, visited.copy(), namespace)
                }
                children.append(child_tree)
        return children
    
    
    def display_tree(self, class_name: str, show_namespaces: bool = True, 
                    show_files: bool = False, root_path: Optional[Path] = None):
        """Display the inheritance tree with formatting"""
        # Find all entities with this name (handles both short and canonical names)
        entities = find_entities_by_name(self.db, class_name)
        
        if not entities:
            print(f"{self.deco.red(f'Class/struct not found: {class_name}')}")
            return
        
        # Group by namespace to separate different base classes
        entities_by_ns = group_entities_by_namespace(entities)
        
        # If only one namespace, use single tree display
        if len(entities_by_ns) == 1:
            # Use the first entity from the single namespace
            entity = list(entities_by_ns.values())[0][0]
            tree = self._build_inheritance_tree_for_entity(entity)
            self._display_single_tree(tree, class_name, show_namespaces, show_files, root_path)
        else:
            # Multiple namespaces - display each separately
            self._display_multiple_trees(entities_by_ns, class_name, show_namespaces, show_files, root_path)
    
    def _display_single_tree(self, tree: Dict, class_name: str, show_namespaces: bool, 
                            show_files: bool, root_path: Optional[Path]):
        """Display a single inheritance tree"""
        if not tree['entity']:
            print(f"{self.deco.red(f'Class/struct not found: {class_name}')}")
            return
        
        # Get the main file path for header
        main_file = None
        if tree['entity'] and tree['entity'].locations:
            main_file = tree['entity'].locations[0].file_path
            # Use obt.path.Path for sanitized path
            main_file = str(obt.path.Path(main_file).sanitized)
        
        # Display header with file path like standard display
        print(f"\n/////////////////////////////////////////////////////////////")
        print(f"// Inheritance Tree for {class_name}")
        if main_file:
            print(f"// {main_file}")
        print(f"/////////\n")
        
        # Display parent hierarchy (ancestors)
        if tree['parents']:
            print(f"\n{self.deco.cyan('BASE CLASSES:')}")
            self._display_parents(tree['parents'], "", True, show_namespaces, show_files, root_path)
        
        # Display the class itself 
        print(f"\n{self.deco.yellow('TARGET:')}")
        ns_str = tree['entity'].namespace if tree['entity'].namespace else "-"
        type_str = "struct" if tree['entity'].entity_type == EntityType.STRUCT else "class"
        name_str = tree['entity'].short_name
        ns_colored = f"\033[48;5;233m\033[38;5;120m{ns_str:^20}\033[m"
        type_colored = f"\033[48;5;236m\033[38;5;51m{type_str:^6}\033[m"
        name_colored = f"\033[48;5;234m\033[38;5;226m{name_str}\033[m"  # Yellow for target
        print(f"{ns_colored}     {type_colored} {name_colored}")
        
        # Display children hierarchy (descendants)
        if tree['children']:
            print(f"\n{self.deco.cyan('DERIVED CLASSES:')}")
            self._display_children(tree['children'], "", True, show_namespaces, show_files, root_path)
        
        # Summary
        parent_count = self._count_ancestors(tree['parents'])
        child_count = self._count_descendants(tree['children'])
        print(f"\n{self.deco.cyan('SUMMARY:')}")
        print(f"  Ancestors: {parent_count}")
        print(f"  Descendants: {child_count}")
    
    def _display_multiple_trees(self, entities_by_ns: Dict, class_name: str, show_namespaces: bool, 
                               show_files: bool, root_path: Optional[Path]):
        """Display multiple inheritance trees grouped by namespace"""
        print(f"\n/////////////////////////////////////////////////////////////")
        print(f"// Multiple {class_name} classes found in different namespaces")
        print(f"/////////\n")
        
        for i, (namespace, entities) in enumerate(sorted(entities_by_ns.items())):
            if i > 0:
                print("\n" + "="*80 + "\n")
            
            # Build tree for the first entity in this namespace
            entity = entities[0]
            qualified_name = f"{namespace}::{class_name}" if namespace != "-" else class_name
            
            print(f"{self.deco.cyan(f'NAMESPACE: {namespace}')}")
            
            # Build inheritance tree for this specific entity
            tree = self._build_inheritance_tree_for_entity(entity)
            
            # Get the main file path for header
            main_file = None
            if entity.locations:
                main_file = entity.locations[0].file_path
                main_file = str(obt.path.Path(main_file).sanitized)
            
            if main_file:
                print(f"// {main_file}")
            
            # Display parent hierarchy (ancestors)
            if tree['parents']:
                print(f"\n{self.deco.cyan('BASE CLASSES:')}")
                self._display_parents(tree['parents'], "", True, show_namespaces, show_files, root_path)
            
            # Display the class itself 
            print(f"\n{self.deco.yellow('TARGET:')}")
            print(f"{self._format_entity(entity, show_namespaces, show_files, root_path, is_target=True)}")
            
            # Display children hierarchy (descendants)
            if tree['children']:
                print(f"\n{self.deco.cyan('DERIVED CLASSES:')}")
                self._display_children(tree['children'], "", True, show_namespaces, show_files, root_path)
            
            # Summary
            parent_count = self._count_ancestors(tree['parents'])
            child_count = self._count_descendants(tree['children'])
            print(f"\n{self.deco.cyan('SUMMARY:')}")
            print(f"  Ancestors: {parent_count}")
            print(f"  Descendants: {child_count}")
    
    def _display_parents(self, parents: List[Dict], prefix: str, is_last: bool,
                        show_namespaces: bool, show_files: bool, root_path: Optional[Path]):
        """Display parent classes with tree structure"""
        for i, parent in enumerate(parents):
            is_last_parent = (i == len(parents) - 1)
            
            # Tree characters
            if prefix == "":
                tree_char = "╰── " if is_last_parent else "├── "
                next_prefix = "    " if is_last_parent else "│   "
            else:
                tree_char = "└── " if is_last_parent else "├── "
                next_prefix = prefix + ("    " if is_last_parent else "│   ")
            
            # Display this parent
            if parent['entity']:
                ns_str = parent['entity'].namespace if parent['entity'].namespace else "-"
                type_str = "struct" if parent['entity'].entity_type == EntityType.STRUCT else "class"
                name_str = parent['entity'].short_name
                ns_colored = f"\033[48;5;233m\033[38;5;120m{ns_str:^20}\033[m"
                type_colored = f"\033[48;5;236m\033[38;5;51m{type_str:^6}\033[m"
                name_colored = f"\033[48;5;234m\033[38;5;231m{name_str}\033[m"
                print(f"{ns_colored} {prefix}{tree_char}{type_colored} {name_colored}")
            else:
                print(f"{'<unknown>':>20} {prefix}{tree_char}??? {parent['name']}")
            
            # Recursively display grandparents
            if parent['parents']:
                self._display_parents(parent['parents'], next_prefix, True, 
                                     show_namespaces, show_files, root_path)
    
    def _display_children(self, children: List[Dict], prefix: str, is_last: bool,
                         show_namespaces: bool, show_files: bool, root_path: Optional[Path]):
        """Display child classes with tree structure"""
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            
            # Tree characters
            tree_char = "└── " if is_last_child else "├── "
            next_prefix = prefix + ("    " if is_last_child else "│   ")
            
            # Display this child
            ns_str = child['entity'].namespace if child['entity'].namespace else "-"
            type_str = "struct" if child['entity'].entity_type == EntityType.STRUCT else "class"
            name_str = child['entity'].short_name
            ns_colored = f"\033[48;5;233m\033[38;5;120m{ns_str:^20}\033[m"
            type_colored = f"\033[48;5;236m\033[38;5;51m{type_str:^6}\033[m"
            name_colored = f"\033[48;5;234m\033[38;5;231m{name_str}\033[m"
            print(f"{ns_colored} {prefix}{tree_char}{type_colored} {name_colored}")
            
            # Recursively display grandchildren
            if child['children']:
                self._display_children(child['children'], next_prefix, True,
                                     show_namespaces, show_files, root_path)
    
    def _format_entity(self, entity: Optional[Entity], show_namespaces: bool, 
                      show_files: bool, root_path: Optional[Path], is_target: bool = False) -> str:
        """Format an entity for display matching standard display colors"""
        if not entity:
            return ""
        
        # Build the display string with namespace first
        parts = []
        
        # Namespace column (green on dark bg) 
        ns_str = entity.namespace if entity.namespace else "-"
        # Pad/truncate to fixed width
        ns_display = f"{ns_str:^20}"[:20]
        parts.append(f"\033[48;5;233m\033[38;5;120m{ns_display}\033[m")
        
        # Type column (cyan on dark bg)
        type_str = "struct" if entity.entity_type == EntityType.STRUCT else "class"
        parts.append(f"\033[48;5;236m\033[38;5;51m {type_str:^6} \033[m")
        
        # Name (white on dark bg, or yellow if target)
        name_color = "226" if is_target else "231"
        name_str = entity.short_name
        if entity.is_template and entity.template_params:
            name_str += f"<{entity.template_params}>"
        parts.append(f"\033[48;5;234m\033[38;5;{name_color}m{name_str}\033[m")
        
        return "".join(parts)
    
    def _count_ancestors(self, parents: List[Dict]) -> int:
        """Count total number of ancestor classes"""
        count = len(parents)
        for parent in parents:
            count += self._count_ancestors(parent['parents'])
        return count
    
    def _count_descendants(self, children: List[Dict]) -> int:
        """Count total number of descendant classes"""
        count = len(children)
        for child in children:
            count += self._count_descendants(child['children'])
        return count