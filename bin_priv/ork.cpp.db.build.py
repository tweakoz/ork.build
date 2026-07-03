#!/bin/sh
# Relocatable trampoline: re-exec under THIS venv's interpreter (bin_priv/../../bin/python3),
# not whatever `python3` PATH resolves to (which is ork.python 3.14t and incompatible here).
"exec" "$(dirname $0)/../../bin/python3" "$0" "$@"
"""
Build C++ entity database V2 for Orkid codebase
Orkid preset: module shortcuts (-m core/lev2/ecs) + predetermined source paths.
Delegates the actual build to the shared obt.cpp_build engine.
"""

import sys
import argparse
from pathlib import Path

import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt import ork_cppdb
from obt import cpp_build

deco = obt.deco.Deco()


def main():
    parser = argparse.ArgumentParser(
        description='Build C++ entity database V2 for Orkid codebase'
    )
    
    # Module selection
    parser.add_argument('-m', '--module', action='append', nargs='+',
                       help='Modules to index (core, lev2, ecs, tool, gfx, ...). Accepts '
                            '`-m core lev2 ecs`, `-m core -m lev2`, or a mix.')
    
    parser.add_argument('--all', action='store_true',
                       help='Index all modules')
    
    # Other options
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    parser.add_argument('--no-progress', action='store_true',
                       help='Disable progress indicator')

    parser.add_argument('--porcelain', action='store_true',
                       help='Terse machine output: key<TAB>value summary only (no color/progress)')

    parser.add_argument('--incremental', '-i', action='store_true',
                       help='Incremental update - only reparse changed files')
    
    parser.add_argument('--stats-only', action='store_true',
                       help='Show database statistics without rebuilding')
    
    # Preprocessing options
    parser.add_argument('-D', '--define', action='append', dest='defines',
                       help='Define macro for preprocessor (can be used multiple times)')
    
    parser.add_argument('--defines-preset', choices=['macos', 'linux', 'minimal'],
                       default='macos',
                       help='Use preset set of defines for preprocessor (default: macos)')
    
    parser.add_argument('-I', '--include', action='append', dest='include_paths',
                       help='Include path for preprocessor (can be used multiple times)')
    
    # Access tracking options
    parser.add_argument('--no-track-accesses', action='store_true',
                       help='Disable access tracking (skips reference analysis phase)')
    
    args = parser.parse_args()
    
    # Database is always in stage directory with fixed name
    import obt.path as obt_path
    db_path = obt_path.stage() / "cpp_db_v2_orkid.db"
    if not args.porcelain:
        print(f"Database file: {db_path}")

    # If stats only, show stats and exit
    if args.stats_only:
        if not db_path.exists():
            print(f"{deco.red(f'Database not found: {db_path}')}")
            print("Run without --stats-only to build the database first")
            sys.exit(1)

        db = CppDatabaseV2(db_path)
        stats = db.get_statistics()

        if args.porcelain:
            print(f"db\t{db_path}")
            for key in ('total_entities', 'entities_class', 'entities_struct',
                        'entities_function', 'entities_enum', 'entities_typedef',
                        'template_entities', 'total_locations', 'total_members',
                        'total_files'):
                print(f"{key}\t{stats.get(key, 0)}")
            sys.exit(0)

        print(f"{deco.green('=== Orkid Database Statistics ===')}")
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
    
    # Get source paths
    if args.all:
        modules = ork_cppdb.list_available_modules()
    else:
        # nargs='+' + append -> list-of-lists; flatten to a flat module list
        modules = [m for group in (args.module or []) for m in group]
    
    source_paths = ork_cppdb.get_orkid_paths(
        modules=modules
    )
    
    if not source_paths:
        print(f"{deco.red('No source paths found!')}")
        print("Use -m <module> or --all to specify what to index")
        sys.exit(1)
    
    if args.verbose:
        print(f"{deco.yellow('Source paths:')}")
        for p in source_paths:
            print(f"  {p}")
    
    # Convert include paths to Path objects if provided
    include_paths = None
    if args.include_paths:
        include_paths = [Path(p) for p in args.include_paths]
    
    # Build database
    cpp_build.build_database(
        db_path,
        source_paths,
        verbose=args.verbose,
        show_progress=not args.no_progress,
        incremental=args.incremental,
        defines=args.defines,
        defines_preset=args.defines_preset,
        include_paths=include_paths,
        track_accesses=not args.no_track_accesses,  # Default to True unless disabled
        porcelain=args.porcelain
    )

if __name__ == '__main__':
    main()
