#!/usr/bin/env python3
"""
Search for C++ entities in Orkid database.
Simplified wrapper for Orkid-specific searching.
"""

import sys
import argparse
from pathlib import Path

# Add OBT to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from obt.path import stage
from obt.deco import Deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_search_v2 import search_database

deco = Deco()

def create_parser():
    """Create argument parser for Orkid search"""
    parser = argparse.ArgumentParser(
        description='Search for C++ entities in Orkid database',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Search pattern (optional)
    parser.add_argument(
        'pattern',
        nargs='?',
        help='Pattern to search for in entity names'
    )
    
    # Filtering options
    parser.add_argument(
        '-t', '--types', '--type',
        help='Entity types to search (comma-separated: class,struct,enum,function,typedef,alias)'
    )
    
    parser.add_argument(
        '-n', '--namespace',
        help='Filter by namespace'
    )
    
    parser.add_argument(
        '--exact',
        action='store_true',
        help='Exact name match instead of pattern match'
    )
    
    parser.add_argument(
        '-i', '--case-insensitive',
        action='store_true',
        help='Case-insensitive pattern matching'
    )
    
    parser.add_argument(
        '--templates-only',
        action='store_true',
        help='Show only template entities'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Limit number of results (0 = unlimited)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Check if Orkid database exists
    db_path = stage() / "cpp_db_v2_orkid.db"
    if not db_path.exists():
        print(f"{deco.red('Orkid database not found!')}")
        print(f"Expected at: {db_path}")
        print(f"Run 'ork.cpp.db.build.py -m <modules>' to build it first")
        sys.exit(1)
    
    # Open database and search
    try:
        db = CppDatabaseV2(db_path)
        
        # Add database to args for search function
        args.db = str(db_path)
        
        # Perform search
        results = search_database(db, args)
        
        if args.json:
            # Import JSON functionality from search_v2
            from obt.cpp_search_v2 import format_json_results
            import json
            json_results = format_json_results(results)
            print(json.dumps(json_results, indent=2))
        else:
            # Use display functionality
            from obt.cpp_display_v2 import CppEntityDisplayV2
            display = CppEntityDisplayV2()
            display.display_search_results(results, args.verbose)
            
    except Exception as e:
        print(f"{deco.red(f'Error: {e}')}")
        sys.exit(1)

if __name__ == '__main__':
    main()