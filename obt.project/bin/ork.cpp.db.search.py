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
    if args.display_mode == 'inhtree':
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