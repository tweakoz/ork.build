#!/usr/bin/env python3
"""
Search for C++ entities in database.
Part of the OBT C++ analysis toolkit.
"""

import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from obt.cpp_command_base import CppCommandBase
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_search_v2 import search_database, build_search_parameters
from obt.cpp_display_v2 import CppEntityDisplayV2
from obt.deco import Deco

deco = Deco()


class SearchCommand(CppCommandBase):
    """Command for searching C++ entities"""
    
    def __init__(self):
        super().__init__(
            "obt.cpp.search",
            "Search for C++ entities in database"
        )
    
    def create_parser(self):
        parser = super().create_parser()
        
        # Search pattern (optional for search)
        parser.add_argument(
            'pattern',
            nargs='?',
            help='Pattern to search for in entity names'
        )
        
        # Entity type filtering
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
            '--json',
            action='store_true',
            help='Output results as JSON'
        )
        
        
        parser.add_argument(
            '--show-type',
            action='store_true',
            help='Show type information for functions'
        )
        
        return parser
    
    def run(self, args):
        """Execute the search command"""
        
        # Get or build database
        db = self.get_or_build_database(args)
        if not db:
            print(f"{deco.red('No database specified. Use --db or --source')}")
            sys.exit(1)
        
        try:
            # Perform search using the functional API
            results = search_database(db, args)
            
            if not results:
                print(f"{deco.yellow('No results found')}")
                sys.exit(0)
            
            # Display results
            if args.json:
                # JSON output
                json_results = []
                for entity in results[:args.limit] if args.limit else results:
                    json_results.append({
                        'name': entity.short_name,
                        'canonical_name': entity.canonical_name,
                        'type': entity.entity_type.value,
                        'namespace': entity.namespace,
                        'is_template': entity.is_template,
                        'base_classes': entity.base_classes or [],
                    })
                print(json.dumps(json_results, indent=2))
            else:
                # Standard display
                display = CppEntityDisplayV2()
                display.display_entities(
                    results[:args.limit] if args.limit else results
                )
                
                print(f"\n{deco.green(f'Found {len(results)} entities')}")
            
        except Exception as e:
            print(f"{deco.red(f'Error: {e}')}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    cmd = SearchCommand()
    parser = cmd.create_parser()
    args = parser.parse_args()
    cmd.run(args)


if __name__ == '__main__':
    main()