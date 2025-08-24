#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import argparse

def parse_search_args(description, require_dep=False):
    """
    Common argument parser for search commands.
    Returns parsed args and processed options.
    """
    parser = argparse.ArgumentParser(description=description)
    
    # Add dep argument if required
    if require_dep:
        parser.add_argument('--dep', help='dep to search', required=True)
    
    # File filtering options
    parser.add_argument('--filetypes', 
                       help='File extensions to search (e.g., ".cpp:.h:.py")',
                       type=str,
                       default=None)
    
    # Search mode options
    parser.add_argument('-i', '--case-insensitive',
                       help='Case-insensitive search (useful for finding API usage regardless of naming)',
                       action='store_true')
    
    parser.add_argument('-l', '--files-only',
                       help='List only filenames with matches, not the matching lines (faster for overview)',
                       action='store_true')
    
    parser.add_argument('-r', '--regex',
                       help='Treat pattern as regular expression instead of literal string (can specify multiple for AND logic)',
                       action='append',
                       dest='regex_patterns')
    
    parser.add_argument('-w', '--whole-word',
                       help='Match whole words only (avoid partial matches like "get" in "getAsset")',
                       action='store_true')
    
    parser.add_argument('-v', '--invert-match',
                       help='Show lines that do NOT match the pattern (useful for filtering)',
                       action='store_true')
    
    # Context options
    parser.add_argument('-C', '--context',
                       help='Show N lines of context around matches (highlighted with delimiters)',
                       type=int,
                       default=0,
                       metavar='N')
    
    parser.add_argument('-B', '--before-context',
                       help='Show N lines before each match',
                       type=int,
                       default=0,
                       metavar='N')
    
    parser.add_argument('-A', '--after-context', 
                       help='Show N lines after each match',
                       type=int,
                       default=0,
                       metavar='N')
    
    # Required positional argument (unless -r is used)
    parser.add_argument('keywords', 
                       metavar='KEYWORD', 
                       type=str, 
                       nargs='*',  # Changed to * to make optional when -r is used
                       help='search keywords or patterns')
    
    args = parser.parse_args()
    
    # Process filetypes into ext_set
    ext_set = None
    if args.filetypes:
        # Split by colon and ensure each has a dot
        extensions = args.filetypes.split(':')
        ext_set = set()
        for ext in extensions:
            # Add dot if not present
            if not ext.startswith('.'):
                ext = '.' + ext
            ext_set.add(ext)
    
    # Process context options
    # If -C is specified, it overrides -A and -B
    if args.context > 0:
        args.before_context = args.context
        args.after_context = args.context
    
    # Process regex patterns
    # For backward compatibility, set args.regex based on whether patterns were provided
    args.regex = bool(args.regex_patterns)
    
    # If regex patterns are provided, use them as the keywords
    # Otherwise use the positional arguments
    if args.regex_patterns:
        # Multiple regex patterns will be ANDed together
        args.keywords = args.regex_patterns
        args.multiple_regex_and = True  # Flag to indicate AND logic
    else:
        # Ensure we have keywords from positional args
        if not args.keywords:
            parser.error("Either provide keywords as positional arguments or use -r option(s)")
        args.multiple_regex_and = False
    
    return args, ext_set