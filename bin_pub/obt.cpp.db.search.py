#!/usr/bin/env python3
"""
Search C++ entity database V2
General-purpose database search tool
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
from obt.deco import Deco

deco = obt.deco.Deco()
display = CppEntityDisplayV2()

# Note: search and display helper functions moved to cpp_search_v2.py and cpp_display_v2.py

def add_obt_specific_args(parser):
    """Add obt-specific arguments to the parser"""
    # Required project argument
    parser.add_argument('-p', '--project',
                       required=True,
                       help='Project name (database to search)')
    
    # Database info
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics instead of searching')
    
    return parser

def main():
    # Create parser with common arguments and obt-specific arguments
    parser = create_search_parser(
        description='Search C++ entity database V2 (general-purpose)',
        add_custom_args=add_obt_specific_args
    )
    
    args = parser.parse_args()
    
    # Get database path
    import obt.path as obt_path
    db_path = obt_path.stage() / f"cpp_db_v2_{args.project}.db"
    
    if not db_path.exists():
        print(f"{deco.red(f'Database not found: {db_path}')}")
        print(f"Project: {args.project}")
        print(f"Run obt.cpp.db.build.py -p {args.project} <directories> to build the database first")
        sys.exit(1)
    
    # Open database
    db = CppDatabaseV2(db_path)
    
    # Show stats if requested
    if args.stats:
        stats = db.get_statistics()
        print(f"{deco.green(f'=== Database Statistics for {args.project} ===')}")
        print(f"Database: {db_path}")
        print(f"\n{deco.cyan('Entity counts:')}")
        print(f"  Total entities: {stats.get('total_entities', 0)}")
        print(f"  Classes: {stats.get('entities_class', 0)}")
        print(f"  Structs: {stats.get('entities_struct', 0)}")
        print(f"  Functions: {stats.get('entities_function', 0)}")
        print(f"  Enums: {stats.get('entities_enum', 0)}")
        print(f"  Typedefs: {stats.get('entities_typedef', 0)}")
        print(f"  Templates: {stats.get('template_entities', 0)}")
        print(f"\n{deco.cyan('Other stats:')}")
        print(f"  Total locations: {stats.get('total_locations', 0)}")
        print(f"  Total members: {stats.get('total_members', 0)}")
        print(f"  Files tracked: {stats.get('total_files', 0)}")
        sys.exit(0)
    
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
    else:
        # Standard mode - perform search first
        results = search_database(db, args)
        
        if not results:
            print(f"{deco.yellow('No results found')}")
            sys.exit(0)
        
        if args.json:
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