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
        help='Entity types to search (comma-separated: class,struct,enum,function,typedef,alias,namespace)'
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
        
        # Check if searching for namespaces specifically
        is_namespace_search = args.types and 'namespace' in args.types.lower()
        
        if is_namespace_search:
            # Search for namespaces
            results = search_namespaces(db, args.pattern, args.limit)
        else:
            # Add database to args for normal search function
            args.db = str(db_path)
            
            # Perform normal search
            results = search_database(db, args)
        
        if args.json:
            import json
            if is_namespace_search:
                # Use custom formatter for namespaces
                json_results = format_namespace_json(results)
            else:
                # Import JSON functionality from search_v2
                from obt.cpp_search_v2 import format_json_results
                json_results = format_json_results(results)
            print(json.dumps(json_results, indent=2))
        else:
            if is_namespace_search:
                # Custom display for namespaces
                display_namespaces(results)
            else:
                # Use display functionality
                from obt.cpp_display_v2 import CppEntityDisplayV2
                display = CppEntityDisplayV2()
                display.display_entities(results)
            
    except Exception as e:
        print(f"{deco.red(f'Error: {e}')}")
        sys.exit(1)

if __name__ == '__main__':
    main()