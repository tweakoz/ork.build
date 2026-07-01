#!/usr/bin/env python3
"""
Build C++ entity database V2 for any C++ codebase (general-purpose).

Generic per-project builder: scans the given directories and builds
  <stage>/cpp_db_v2_<project>.db
using the shared obt.cpp_build engine (the same 3-phase ingest / parse /
access-tracking pipeline the Orkid preset ork.cpp.db.build.py uses).
"""

import sys
import argparse
from pathlib import Path

import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt import cpp_build

deco = obt.deco.Deco()


def main():
    parser = argparse.ArgumentParser(
        description='Build C++ entity database V2 for any C++ codebase'
    )

    parser.add_argument('directory', nargs='*',
                        help='Directory or directories to scan for C++ files')
    parser.add_argument('--project', '-p', required=True,
                        help='Project name (db = <stage>/cpp_db_v2_<project>.db)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--no-progress', action='store_true',
                        help='Disable progress indicator')
    parser.add_argument('--incremental', '-i', action='store_true',
                        help='Incremental update - keep existing data')
    parser.add_argument('--stats-only', action='store_true',
                        help='Show database statistics without rebuilding')
    parser.add_argument('-D', '--define', action='append', dest='defines',
                        help='Define macro for preprocessor (can be used multiple times)')
    parser.add_argument('--defines-preset', choices=['macos', 'linux', 'minimal'],
                        default='minimal',
                        help='Preset defines for preprocessor (default: minimal)')
    parser.add_argument('-I', '--include', action='append', dest='include_paths',
                        help='Include path for preprocessor (can be used multiple times)')
    parser.add_argument('--no-track-accesses', action='store_true',
                        help='Disable access tracking (skips reference analysis phase)')

    args = parser.parse_args()

    db_path = obt.path.stage() / f"cpp_db_v2_{args.project}.db"
    print(f"Database file: {db_path}")

    # If stats only, show stats and exit
    if args.stats_only:
        if not db_path.exists():
            print(f"{deco.red(f'Database not found: {db_path}')}")
            print(f"Project: {args.project}")
            sys.exit(1)

        db = CppDatabaseV2(db_path)
        stats = db.get_statistics()

        print(f"{deco.green('=== Database Statistics ===')}")
        print(f"Database: {db_path}")
        print(f"\n{deco.cyan('Entity counts:')}")
        print(f"  Total entities: {stats.get('total_entities', 0)}")
        print(f"  Classes: {stats.get('entities_class', 0)}")
        print(f"  Structs: {stats.get('entities_struct', 0)}")
        print(f"  Functions: {stats.get('entities_function', 0)}")
        print(f"  Enums: {stats.get('entities_enum', 0)}")
        print(f"  Typedefs: {stats.get('entities_typedef', 0)}")
        print(f"  Templates: {stats.get('template_entities', 0)}")
        print(f"  Files: {stats.get('total_files', 0)}")

        file_extensions = ['.h', '.hpp', '.hh', '.hxx', '.c', '.cpp', '.cc', '.cxx', '.inl', '.inc']
        file_breakdown = []
        for ext in file_extensions:
            ext_key = ext.lstrip('.')
            count = stats.get(f'files_{ext_key}', 0)
            if count > 0:
                size_mb = stats.get(f'files_{ext_key}_size_mb', 0)
                file_breakdown.append((ext, count, size_mb))
        if file_breakdown:
            print(f"    Breakdown by type:")
            for ext, count, size_mb in file_breakdown:
                if size_mb > 0:
                    print(f"      {ext:<5} {count:>4} files ({size_mb:.1f} MB)")
                else:
                    print(f"      {ext:<5} {count:>4} files")

        print(f"\n{deco.cyan('Other stats:')}")
        print(f"  Total locations: {stats.get('total_locations', 0)}")
        print(f"  Total members: {stats.get('total_members', 0)}")
        if stats.get('files_with_preprocessed', 0) > 0:
            print(f"  Files with preprocessed: {stats.get('files_with_preprocessed', 0)}")
        if stats.get('total_source_size_mb', 0) > 0:
            print(f"  Total source size: {stats.get('total_source_size_mb', 0)} MB")
        sys.exit(0)

    # Resolve source directories
    if not args.directory:
        print(f"{deco.red('Error: No directories specified (give one or more dirs, or use --stats-only)')}")
        sys.exit(1)

    source_paths = []
    for dir_arg in args.directory:
        path = Path(dir_arg).resolve()
        if path.exists():
            source_paths.append(path)
        else:
            print(f"{deco.red(f'Error: Path not found: {dir_arg}')}")
            sys.exit(1)

    include_paths = [Path(p) for p in args.include_paths] if args.include_paths else None

    if args.verbose:
        print(f"{deco.yellow('Source paths:')}")
        for p in source_paths:
            print(f"  {p}")

    cpp_build.build_database(
        db_path,
        source_paths,
        verbose=args.verbose,
        show_progress=not args.no_progress,
        incremental=args.incremental,
        defines=args.defines,
        defines_preset=args.defines_preset,
        include_paths=include_paths,
        track_accesses=not args.no_track_accesses,
    )


if __name__ == '__main__':
    main()
