#!/usr/bin/env python3
"""
Display inheritance tree for C++ classes/structs.
Part of the OBT C++ analysis toolkit.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from obt.cpp_command_base import CppCommandBase
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_inheritance_tree import InheritanceTreeDisplay
from obt.deco import Deco

deco = Deco()


class InhTreeCommand(CppCommandBase):
    """Command for displaying inheritance trees"""
    
    def __init__(self):
        super().__init__(
            "obt.cpp.inhtree",
            "Display inheritance tree for C++ classes/structs"
        )
    
    def create_parser(self):
        parser = super().create_parser()
        
        # Add tree-specific arguments
        parser.add_argument(
            'pattern',
            help='Class/struct name or pattern to display tree for'
        )
        
        parser.add_argument(
            '--no-namespaces',
            action='store_true',
            help='Hide namespace information'
        )
        
        parser.add_argument(
            '--no-files',
            action='store_true',
            help='Hide file location information'
        )
        
        
        return parser
    
    def run(self, args):
        """Execute the tree command"""
        
        # Get or build database
        db = self.get_or_build_database(args)
        if not db:
            print(f"{deco.red('No database specified. Use --db or --source')}")
            sys.exit(1)
        
        try:
            # Create tree display
            tree_display = InheritanceTreeDisplay(db)
            
            # Display the tree
            tree_display.display_tree(
                args.pattern,
                show_namespaces=not args.no_namespaces,
                show_files=not args.no_files
            )
            
        except Exception as e:
            print(f"{deco.red(f'Error: {e}')}")
            sys.exit(1)
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    cmd = InhTreeCommand()
    parser = cmd.create_parser()
    args = parser.parse_args()
    cmd.run(args)


if __name__ == '__main__':
    main()