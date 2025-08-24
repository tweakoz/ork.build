"""
Common argument parsing for C++ search commands
Provides shared argument definitions while allowing command-specific customization
"""

import argparse

def add_common_search_arguments(parser: argparse.ArgumentParser):
    """
    Add common search arguments to an argument parser
    These are shared between obt.cpp.db.search.py and ork.cpp.db.search.py
    """
    
    # Search pattern (positional, optional)
    parser.add_argument('pattern', nargs='?',
                       help='Pattern to search for in entity names')
    
    # Filter options
    parser.add_argument('-t', '--types', '--type',
                       help='Entity types to search (comma-separated: class,struct,enum,function,memberfn,staticfn,typedef,alias,files)')
    
    parser.add_argument('-n', '--namespace',
                       help='Filter by namespace')
    
    parser.add_argument('--exact', action='store_true',
                       help='Exact name match instead of pattern match')
    
    parser.add_argument('-i', '--case-insensitive', action='store_true',
                       help='Case-insensitive pattern matching')
    
    parser.add_argument('--templates-only', action='store_true',
                       help='Show only template entities')
    
    parser.add_argument('--derived-only', action='store_true',
                       help='Show only derived classes')
    
    parser.add_argument('-d', '--derived-from',
                       help='Show classes/structs derived from the specified base class')
    
    # Display options
    parser.add_argument('--display-mode', choices=['std', 'inhtree', 'details'], default='std',
                       help='Display mode: std (standard file-based listing), inhtree (inheritance tree), or details (class details)')
    
    parser.add_argument('--show-inheritance', action='store_true',
                       help='Show base classes')
    
    parser.add_argument('--show-type', action='store_true',
                       help='Show declaration/definition type')
    
    parser.add_argument('--members', action='store_true',
                       help='Show class/struct members')
    
    parser.add_argument('--values', action='store_true',
                       help='Show enum values')
    
    parser.add_argument('--params', action='store_true',
                       help='Show function parameters')
    
    parser.add_argument('--resolve-typedefs', action='store_true',
                       help='Show what typedefs resolve to')
    
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    
    parser.add_argument('--limit', type=int, default=0,
                       help='Maximum results to show (0 = unlimited)')
    
    parser.add_argument('--sepfiles', action='store_true',
                       help='Add separator between different files')
    
    return parser

def create_search_parser(description: str, add_custom_args=None):
    """
    Create a complete argument parser with common search arguments
    
    Args:
        description: Description for the argument parser
        add_custom_args: Optional function to add command-specific arguments
                        Takes parser as argument and returns parser
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(description=description)
    
    # Add common arguments
    add_common_search_arguments(parser)
    
    # Add custom arguments if provided
    if add_custom_args:
        parser = add_custom_args(parser)
    
    return parser