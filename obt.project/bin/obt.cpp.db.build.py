#!/usr/bin/env python3
"""
Build C++ entity database V2 for any C++ codebase
General-purpose tool with directory argument
Uses normalized database design with tree-sitter parsing
"""

import os
import sys
import argparse
from pathlib import Path
import time

# Add obt to path
import obt.path
import obt.deco
from obt.cpp_parser_descent import RecursiveDescentCppParser
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType

deco = obt.deco.Deco()

def find_source_files(paths, extensions=None):
    """Find all C++ source files in given paths"""
    if extensions is None:
        # C++ extensions
        extensions = {'.h', '.hpp', '.hxx', '.H', '.hh', 
                     '.c', '.cpp', '.cxx', '.cc', '.C',
                     '.inl', '.inc'}
    
    files = []
    for path in paths:
        if path.is_file():
            if path.suffix in extensions:
                files.append(path)
        elif path.is_dir():
            for ext in extensions:
                files.extend(path.rglob(f'*{ext}'))
    
    return sorted(set(files))

def build_database(db_path, source_paths, verbose=False, show_progress=True):
    """Build the C++ entity database"""
    
    # Create database
    db = CppDatabaseV2(db_path)
    
    # Clear existing data
    if verbose:
        print(f"{deco.yellow('Clearing existing database...')}")
    db.clear_database()
    
    # Create parser
    parser = RecursiveDescentCppParser()
    
    # Find all source files
    if verbose:
        print(f"{deco.yellow('Finding source files...')}")
    
    files = find_source_files(source_paths)
    total_files = len(files)
    
    if verbose:
        print(f"{deco.green(f'Found {total_files} source files')}")
    
    # Parse files and add to database
    start_time = time.time()
    parsed_count = 0
    entity_count = 0
    error_count = 0
    
    for i, file_path in enumerate(files):
        if show_progress:
            progress = (i + 1) / total_files * 100
            print(f"\r{deco.cyan(f'Progress: {progress:.1f}%')} ({i+1}/{total_files})", end='', flush=True)
        
        try:
            # Parse file
            entities = parser.parse_file(file_path)
            
            # Add entities to database
            for entity in entities:
                db.add_entity(entity)
                entity_count += 1
            
            # Track parsed file
            db.add_file(file_path)
            parsed_count += 1
            
        except Exception as e:
            error_count += 1
            if verbose:
                print(f"\n{deco.red(f'Error parsing {file_path}: {e}')}")
    
    if show_progress:
        print()  # New line after progress
    
    # Get statistics
    elapsed = time.time() - start_time
    stats = db.get_statistics()
    
    # Print summary
    print(f"\n{deco.green('=== Build Complete ===')}")
    print(f"Database: {db_path}")
    print(f"Time: {elapsed:.2f} seconds")
    print(f"Files parsed: {parsed_count}/{total_files}")
    if error_count > 0:
        print(f"Errors: {deco.red(str(error_count))}")
    print(f"\n{deco.cyan('Entity counts:')}")
    print(f"  Total entities: {stats.get('total_entities', 0)}")
    print(f"  Classes: {stats.get('entities_class', 0)}")
    print(f"  Structs: {stats.get('entities_struct', 0)}")
    print(f"  Functions: {stats.get('entities_function', 0)}")
    print(f"  Enums: {stats.get('entities_enum', 0)}")
    print(f"  Typedefs: {stats.get('entities_typedef', 0)}")
    print(f"  Templates: {stats.get('template_entities', 0)}")
    
    return db

def main():
    parser = argparse.ArgumentParser(
        description='Build C++ entity database V2 for any C++ codebase'
    )
    
    parser.add_argument('directory', nargs='*',
                       help='Directory or directories to scan for C++ files')
    
    parser.add_argument('--project', '-p',
                       required=True,
                       help='Project name for database')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    parser.add_argument('--no-progress', action='store_true',
                       help='Disable progress indicator')
    
    parser.add_argument('--stats-only', action='store_true',
                       help='Show database statistics without rebuilding')
    
    args = parser.parse_args()
    
    # Get database path from project name
    import obt.path as obt_path
    db_path = obt_path.stage() / f"cpp_db_v2_{args.project}.db"
    
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
        
        # Show file breakdown by extension
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
    
    # Get source paths from command line
    if not args.directory:
        print(f"{deco.red('Error: No directories specified')}")
        sys.exit(1)
    
    source_paths = []
    for dir_arg in args.directory:
        path = Path(dir_arg).resolve()
        if path.exists():
            source_paths.append(path)
        else:
            print(f"{deco.red(f'Error: Path not found: {dir_arg}')}")
            sys.exit(1)
    
    if args.verbose:
        print(f"{deco.yellow('Source paths:')}")
        for p in source_paths:
            print(f"  {p}")
    
    # Build database
    build_database(
        db_path,
        source_paths,
        verbose=args.verbose,
        show_progress=not args.no_progress
    )

if __name__ == '__main__':
    main()