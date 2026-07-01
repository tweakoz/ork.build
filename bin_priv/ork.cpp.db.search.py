#!/usr/bin/env python3
"""
Search C++ entity database V2 for Orkid
Fast database-based searches with typedef resolution
"""

import os
import sys
import argparse
import json
import re
from pathlib import Path

# Add obt to path
import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType, MemberType, AccessLevel
from obt.cpp_display_v2 import CppEntityDisplayV2
from obt.cpp_search_v2 import search_database, format_json_results
from obt.cpp_argparse_v2 import create_search_parser

deco = obt.deco.Deco()
display = CppEntityDisplayV2()

# Note: search and display helper functions moved to cpp_search_v2.py and cpp_display_v2.py
# Exception: namespaces are stored as a column (not typed entity rows), so they need a
# bespoke distinct-namespace query + display, ported here from the retired ork.cpp.search.py.

def format_namespace_json(results):
    """Format namespace results as JSON"""
    json_results = []
    for entity in results:
        json_obj = {
            'name': entity.short_name,
            'canonical_name': entity.canonical_name,
            'type': 'namespace',
            'namespace': None,
            'is_template': False,
            'template_params': None,
            'locations': []
        }
        json_results.append(json_obj)
    return json_results

def display_namespaces(results):
    """Display namespace results using column formatter"""
    if not results:
        print("// No matching namespaces found")
        return

    # Print header
    print("/////////////////////////////////////////////////////////////")
    print(f"// Found {len(results)} namespace{'s' if len(results) != 1 else ''}")
    print("/////////")
    print()

    # Column configuration
    LINE_LENGTH = 148
    depth_col_width = 8
    type_col_width = 12
    namespace_col_width = LINE_LENGTH - (depth_col_width + type_col_width)

    # Print header with reverse video
    header_configs = [
        (depth_col_width, 'left'),
        (type_col_width, 'left'),
        (namespace_col_width, 'left')
    ]
    header_texts = [
        'Depth',
        'Type',
        'Namespace'
    ]

    # Format the header
    header_line = deco.formatColumns(header_configs, header_texts)
    print(deco.reverseVideo(header_line.ljust(LINE_LENGTH)))

    # Sort namespaces by canonical name for hierarchical display
    sorted_results = sorted(results, key=lambda x: x.canonical_name)

    for entity in sorted_results:
        # Calculate namespace depth
        depth = entity.canonical_name.count('::')

        # Format columns
        depth_col = deco.white(str(depth).ljust(depth_col_width))
        type_col = deco.green('namespace'.ljust(type_col_width))

        # Add indentation based on depth for visual hierarchy
        indent = '  ' * min(depth, 5)  # Cap indentation at 5 levels
        namespace_col = deco.inf(indent + entity.canonical_name)

        # Use formatColumns for aligned output
        column_configs = [
            (depth_col_width, 'left'),
            (type_col_width, 'left'),
            (namespace_col_width, 'left')
        ]
        column_texts = [depth_col, type_col, namespace_col]
        output = deco.formatColumns(column_configs, column_texts)

        print(output)

def search_namespaces(db, pattern=None, limit=0):
    """Search for namespaces in the database"""
    with db.connect() as conn:
        cursor = conn.cursor()

        # Build query for distinct namespaces
        if pattern:
            # Support wildcards
            if '*' in pattern:
                pattern = pattern.replace('*', '%')
                query = """
                    SELECT DISTINCT namespace
                    FROM entities
                    WHERE namespace LIKE ?
                    AND namespace IS NOT NULL
                    ORDER BY namespace
                """
            else:
                query = """
                    SELECT DISTINCT namespace
                    FROM entities
                    WHERE namespace LIKE '%' || ? || '%'
                    AND namespace IS NOT NULL
                    ORDER BY namespace
                """
            params = (pattern,)
        else:
            query = """
                SELECT DISTINCT namespace
                FROM entities
                WHERE namespace IS NOT NULL
                ORDER BY namespace
            """
            params = ()

        if limit > 0:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)

        # Create pseudo-entities for namespaces
        results = []
        for row in cursor.fetchall():
            namespace = row[0]
            if namespace:  # Skip empty namespaces
                # Create a simple namespace entity
                from types import SimpleNamespace
                entity = SimpleNamespace()
                entity.name = namespace
                entity.short_name = namespace.split('::')[-1] if '::' in namespace else namespace
                entity.canonical_name = namespace
                entity.entity_type = 'namespace'
                entity.namespace = None  # Namespaces don't have parent namespaces in our model
                entity.is_template = False
                entity.template_params = None
                entity.locations = []
                entity.file_path = ''
                entity.line_number = 0
                results.append(entity)

        return results

def add_ork_specific_args(parser):
    """Add Orkid-specific arguments to the parser"""
    # Database selection (optional with default)
    parser.add_argument('--project', '-p', default='orkid',
                       help='Project database to search (default: orkid)')
    
    return parser

def main():
    # Create parser with common arguments and ork-specific arguments
    parser = create_search_parser(
        description='Search C++ entity database V2 for Orkid',
        add_custom_args=add_ork_specific_args
    )
    
    args = parser.parse_args()
    
    # Get database path
    import obt.path as obt_path
    db_path = obt_path.stage() / f"cpp_db_v2_{args.project}.db"
    
    if not db_path.exists():
        print(f"{deco.red(f'Database not found: {db_path}')}")
        print(f"Run ork.cpp.db.build.py to build the database first")
        sys.exit(1)
    
    # Open database
    db = CppDatabaseV2(db_path)
    
    # Output results based on display mode
    # Namespace search: bespoke distinct-namespace query (namespaces are a column, not typed entity rows)
    if args.types and 'namespace' in args.types.lower():
        results = search_namespaces(db, args.pattern, args.limit)
        if args.json:
            print(json.dumps(format_namespace_json(results), indent=2))
        elif not results:
            print(f"{deco.yellow('No matching namespaces found')}")
        else:
            display_namespaces(results)
    elif args.display_mode == 'inhtree':
        # Inheritance tree display
        from obt.cpp_inheritance_tree import InheritanceTreeDisplay
        tree_display = InheritanceTreeDisplay(db)
        
        # For inheritance tree, we need a specific class name
        if args.pattern:
            tree_display.display_tree(args.pattern, show_namespaces=True, show_files=True)
        else:
            print(f"{deco.red('Please specify a class/struct name for inheritance tree display')}")
            sys.exit(1)
    elif args.display_mode == 'details':
        # Class details display
        from obt.cpp_class_details import ClassDetailsDisplay
        details_display = ClassDetailsDisplay(db)
        
        # For class details, we need a specific class name
        if args.pattern:
            details_display.display_details(args.pattern, show_files=True)
        else:
            print(f"{deco.red('Please specify a class/struct name for details display')}")
            sys.exit(1)
    else:
        # Standard mode - perform search first
        results = search_database(db, args)
        
        if not results:
            print(f"{deco.yellow('No results found')}")
            sys.exit(0)
        
        # Check if we're in files mode (results are dicts not Entity objects)
        if results and isinstance(results[0], dict):
            # File listing mode
            print(f"Found {len(results)} files:")
            print("=" * 80)
            for file_info in results:
                size_kb = file_info['file_size'] / 1024 if file_info.get('file_size') else 0
                relative_path = file_info.get('relative_path', file_info['file_path'])
                print(f"{relative_path:<60} {size_kb:>8.1f} KB")
        elif args.json:
            # JSON output for tool integration
            json_results = format_json_results(results)
            print(json.dumps(json_results, indent=2))
        else:
            # Standard file-based display
            # Pass the base class if we're showing derived classes
            show_base = args.derived_from if hasattr(args, 'derived_from') and args.derived_from else None
            display.display_entities(results, root_path=None, sepfiles=args.sepfiles, show_base_class=show_base)
            
            if args.limit > 0 and len(results) == args.limit:
                print(f"\n{deco.yellow(f'Results limited to {args.limit}. Use --limit to see more.')}")

if __name__ == '__main__':
    main()