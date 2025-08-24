#!/usr/bin/env python3
"""
Display members of C++ classes/structs.
Part of the OBT C++ analysis toolkit.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from obt.cpp_command_base import CppCommandBase
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_class_details import ClassDetailsDisplay
from obt.deco import Deco

deco = Deco()


class MembersCommand(CppCommandBase):
    """Command for displaying class/struct members"""
    
    def __init__(self):
        super().__init__(
            "obt.cpp.members",
            "Display members of C++ classes/structs"
        )
    
    def create_parser(self):
        parser = super().create_parser()
        
        # Add members-specific arguments
        parser.add_argument(
            'pattern',
            help='Class/struct name or pattern to show members for'
        )
        
        parser.add_argument(
            '--no-files',
            action='store_true',
            help='Hide file location information'
        )
        
        
        return parser
    
    def run(self, args):
        """Execute the members command"""
        
        # Get or build database
        db = self.get_or_build_database(args)
        if not db:
            print(f"{deco.red('No database specified. Use --db or --source')}")
            sys.exit(1)
        
        try:
            # Create details display (which shows members)
            details_display = ClassDetailsDisplay(db)
            
            # Display the details/members
            details_display.display_details(
                args.pattern,
                show_files=not args.no_files
            )
            
        except Exception as e:
            print(f"{deco.red(f'Error: {e}')}")
            sys.exit(1)
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    cmd = MembersCommand()
    parser = cmd.create_parser()
    args = parser.parse_args()
    cmd.run(args)


if __name__ == '__main__':
    main()