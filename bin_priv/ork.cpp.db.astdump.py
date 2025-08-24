#!/usr/bin/env python3
"""
AST dump tool for C++ database - foundational debugging tool
Fetches preprocessed source from database and dumps tree-sitter AST
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add obt to path
import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

deco = obt.deco.Deco()

class ASTDumper:
    """Dump AST from preprocessed source in database"""
    
    def __init__(self, db_path: Path):
        self.db = CppDatabaseV2(db_path)
        
        # Initialize tree-sitter
        self.CPP_LANGUAGE = Language(tscpp.language(), "cpp")
        self.parser = Parser()
        self.parser.set_language(self.CPP_LANGUAGE)
    
    def get_preprocessed_source(self, file_path: str) -> Optional[str]:
        """Get preprocessed source from database"""
        source = self.db.get_preprocessed_source(file_path)
        if not source:
            # Try raw source if no preprocessed
            source = self.db.get_raw_source(file_path)
        return source
    
    def find_file_by_pattern(self, pattern: str) -> Optional[str]:
        """Find file path matching pattern"""
        files = self.db.search_source_files(pattern)
        if files:
            return files[0]['file_path']
        return None
    
    def parse_source(self, source_code: str) -> Any:
        """Parse source code and return tree"""
        source_bytes = source_code.encode('utf-8')
        return self.parser.parse(source_bytes)
    
    def node_to_dict(self, node, source_bytes: bytes, include_text: bool = False) -> Dict:
        """Convert AST node to dictionary"""
        result = {
            'type': node.type,
            'start': [node.start_point[0], node.start_point[1]],
            'end': [node.end_point[0], node.end_point[1]],
        }
        
        if include_text or node.child_count == 0:
            text = source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
            if len(text) <= 100:
                result['text'] = text
            else:
                result['text'] = text[:100] + '...'
        
        if node.child_count > 0:
            result['children'] = [
                self.node_to_dict(child, source_bytes, include_text)
                for child in node.children
            ]
        
        return result
    
    def dump_tree(self, node, source_bytes: bytes, indent: int = 0, 
                  max_depth: Optional[int] = None, show_text: bool = True) -> None:
        """Dump AST in tree format with column formatting"""
        if max_depth is not None and indent >= max_depth:
            return
        
        # Column width constants
        COL_TYPE = 40
        COL_TEXT = 76  # 60 + 16 
        COL_COORDS = 25
        COL_ANNOTATIONS = 20
        
        # Build indented node type (preserve indentation within column)
        prefix = "  " * indent
        node_type_col = prefix + deco.cyan(node.type)
        
        # Text content column
        text_col = ""
        if show_text and (node.child_count == 0 or indent < 2):
            text = source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
            text = text.replace('\n', '\\n').replace('\r', '\\r')
            if len(text) > 70:
                text = text[:70] + "..."
            text_col = deco.green(repr(text))
        
        # Coordinates column
        coords_col = deco.gray(f'[{node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]}]')
        
        # Annotations column (child count)
        annotations_col = deco.yellow(f'({node.child_count} children)') if node.child_count > 0 else ""
        
        # Format columns - all left justified
        column_configs = [
            (COL_TYPE, 'left'),
            (COL_TEXT, 'left'),
            (COL_COORDS, 'left'),
            (COL_ANNOTATIONS, 'left')
        ]
        column_texts = [node_type_col, text_col, coords_col, annotations_col]
        formatted = deco.formatColumns(column_configs, column_texts)
        
        print(formatted)
        
        # Recurse
        for child in node.children:
            self.dump_tree(child, source_bytes, indent + 1, max_depth, show_text)
    
    def find_classes_in_tree(self, node, source_bytes: bytes) -> List[Dict]:
        """Find all class/struct definitions in tree"""
        classes = []
        
        if node.type in ['class_specifier', 'struct_specifier']:
            # Extract class name
            name = None
            for child in node.children:
                if child.type == 'type_identifier':
                    name = source_bytes[child.start_byte:child.end_byte].decode('utf-8')
                    break
            
            if name:
                classes.append({
                    'name': name,
                    'type': 'class' if node.type == 'class_specifier' else 'struct',
                    'node': node,
                    'line': node.start_point[0] + 1
                })
        
        # Recurse
        for child in node.children:
            classes.extend(self.find_classes_in_tree(child, source_bytes))
        
        return classes
    
    def dump_class_members(self, class_node, source_bytes: bytes) -> None:
        """Dump members of a class/struct"""
        # Find field_declaration_list
        field_list = None
        for child in class_node.children:
            if child.type == 'field_declaration_list':
                field_list = child
                break
        
        if not field_list:
            print("  No field_declaration_list found")
            return
        
        for child in field_list.children:
            if child.type in ['{', '}', ';']:
                continue
            
            print(f"  {deco.yellow(child.type)}:", end="")
            
            # Extract key info based on node type
            if child.type == 'field_declaration':
                # Could be field or method
                has_function = any(
                    self._find_node_type(c, 'function_declarator') 
                    for c in child.children
                )
                if has_function:
                    print(" [METHOD]", end="")
                else:
                    print(" [FIELD]", end="")
            elif child.type == 'function_definition':
                print(" [METHOD WITH BODY]", end="")
                # Check for pure virtual
                has_pure_virtual = any(
                    c.type == 'pure_virtual_clause'
                    for c in child.children
                )
                if has_pure_virtual:
                    print(" [PURE VIRTUAL]", end="")
            elif child.type == 'access_specifier':
                text = source_bytes[child.start_byte:child.end_byte].decode('utf-8')
                print(f" {text}", end="")
            
            # Show text snippet
            text = source_bytes[child.start_byte:child.end_byte].decode('utf-8')
            text = text.replace('\n', ' ').strip()
            if len(text) > 80:
                text = text[:80] + "..."
            print(f" '{text}'")
    
    def _find_node_type(self, node, node_type: str) -> bool:
        """Recursively check if node or children have given type"""
        if node.type == node_type:
            return True
        for child in node.children:
            if self._find_node_type(child, node_type):
                return True
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Dump AST from C++ database preprocessed source'
    )
    
    # Database selection
    parser.add_argument('--project', '-p', default='orkid',
                       help='Project database (default: orkid)')
    
    # File selection
    parser.add_argument('--file', '-f',
                       help='File path or pattern to dump')
    parser.add_argument('--cls', '-c', dest='class_name',
                       help='Dump specific class/struct (implies finding its file)')
    
    # Output options
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--depth', '-d', type=int,
                       help='Maximum tree depth to show')
    parser.add_argument('--no-text', action='store_true',
                       help='Hide text content')
    parser.add_argument('--members', action='store_true',
                       help='Show class members analysis')
    
    args = parser.parse_args()
    
    # Get database path
    db_path = obt.path.stage() / f"cpp_db_v2_{args.project}.db"
    
    if not db_path.exists():
        print(f"{deco.red(f'Database not found: {db_path}')}")
        sys.exit(1)
    
    dumper = ASTDumper(db_path)
    
    # Handle class lookup which implies file lookup
    if args.class_name:
        # Search for class in database to find its file
        entities = dumper.db.search_entities(name=args.class_name)
        if not entities:
            print(f"{deco.red(f'Class/struct {args.class_name} not found in database')}")
            sys.exit(1)
        
        # Get file from first location
        entity = entities[0]
        if entity.locations:
            args.file = entity.locations[0].file_path
        else:
            print(f"{deco.red(f'No file location found for {args.class_name}')}")
            sys.exit(1)
    
    # Find file
    if not args.file:
        print(f"{deco.red('Please specify --file or --cls')}")
        sys.exit(1)
    
    # Try exact match first
    source = dumper.get_preprocessed_source(args.file)
    file_path = args.file
    
    if not source:
        # Try pattern match
        file_path = dumper.find_file_by_pattern(args.file)
        if file_path:
            source = dumper.get_preprocessed_source(file_path)
    
    if not source:
        print(f"{deco.red(f'File not found: {args.file}')}")
        sys.exit(1)
    
    print(f"{deco.green(f'File: {file_path}')}")
    print(f"Source size: {len(source)} bytes")
    print("=" * 80)
    print(f"{deco.yellow('AST Format:')} node_type [start_row:start_col-end_row:end_col] = 'text' (child_count)")
    print(f"{deco.yellow('Coordinates:')} 0-indexed, byte-precise positions in preprocessed source")
    print("=" * 80)
    
    # Parse source
    tree = dumper.parse_source(source)
    source_bytes = source.encode('utf-8')
    
    if args.class_name:
        # Find and dump ALL instances of specific class (declaration, definition, etc.)
        classes = dumper.find_classes_in_tree(tree.root_node, source_bytes)
        found = False
        instance_count = 0
        
        for cls in classes:
            if cls['name'] == args.class_name:
                found = True
                instance_count += 1
                header = f"{cls['type']} {cls['name']} (instance #{instance_count}) at line {cls['line']}:"
                print(f"\n{deco.magenta(header)}")
                
                if args.members:
                    members_header = f"Members (instance #{instance_count}):"
                    print(f"\n{deco.yellow(members_header)}")
                    dumper.dump_class_members(cls['node'], source_bytes)
                else:
                    if args.json:
                        print(json.dumps(
                            dumper.node_to_dict(cls['node'], source_bytes, not args.no_text),
                            indent=2
                        ))
                    else:
                        dumper.dump_tree(cls['node'], source_bytes, 0, args.depth, not args.no_text)
        
        if not found:
            print(f"{deco.red(f'Class/struct {args.class_name} not found')}")
            print(f"Available classes: {', '.join(c['name'] for c in classes)}")
        else:
            print(f"\n{deco.green(f'Found {instance_count} instances of {args.class_name}')}")
    else:
        # Dump whole file
        if args.json:
            print(json.dumps(
                dumper.node_to_dict(tree.root_node, source_bytes, not args.no_text),
                indent=2
            ))
        else:
            dumper.dump_tree(tree.root_node, source_bytes, 0, args.depth, not args.no_text)

if __name__ == '__main__':
    main()