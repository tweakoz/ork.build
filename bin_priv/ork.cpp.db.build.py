#!/usr/bin/env python3
"""
Build C++ entity database V2 for Orkid codebase
Orkid-specific with module shortcuts and predetermined paths
Uses normalized database design with tree-sitter parsing
"""

import os
import sys
import argparse
from pathlib import Path
import time
import json

# Add obt to path
import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType
from obt import ork_cppdb
from obt import cpp_ingest
from obt import cpp_parser_descent
from obt import host
from concurrent.futures import ProcessPoolExecutor, as_completed

deco = obt.deco.Deco()


def parse_single_file_v3(args):
    """
    Parse a single file from the database (for parallel processing)
    Returns tuple of (file_path, entities, parse_time, error)
    """
    file_path, db_path = args
    start_time = time.time()
    
    try:
        # Connect to database
        db = CppDatabaseV2(db_path)
        with db.connect() as conn:
            # Get trimmed source
            cursor = conn.execute("""
                SELECT trimmed_source FROM source_files 
                WHERE file_path = ?
            """, (file_path,))
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return file_path, [], 0, f"No trimmed source found"
            
            trimmed_source = row[0]
            
        # Parse with recursive descent parser, passing db_path for TypeRegistry
        parser = cpp_parser_descent.RecursiveDescentCppParser(db_path=db_path)
        entities = parser.parse_source(trimmed_source.encode('utf-8'), file_path)
        
        parse_time = time.time() - start_time
        return file_path, entities, parse_time, None
        
    except Exception as e:
        parse_time = time.time() - start_time
        return file_path, [], parse_time, str(e)


def analyze_single_file_worker(args):
    """
    Analyze a single file for access tracking (for parallel processing)
    Returns list of tuples ready for batch insert
    """
    file_path, db_path = args
    
    try:
        # Import everything needed in worker process
        import json
        from pathlib import Path
        from obt.cpp_database_v2 import CppDatabaseV2
        from obt.cpp_stack_analyzer import StackBasedAccessAnalyzer
        
        # Create database connection in worker process
        db = CppDatabaseV2(db_path)
        
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # Read trimmed source and line mapping from database
            cursor.execute("""
                SELECT id, trimmed_source, line_mapping 
                FROM source_files WHERE file_path = ?
            """, (str(file_path),))
            
            result = cursor.fetchone()
            if not result or not result[1]:
                return None
                
            file_id = result[0]
            trimmed_source = result[1]
            
            # Parse line mapping from JSON
            line_mapping = {}
            if result[2]:
                line_mapping_raw = json.loads(result[2])
                # Convert string keys to int
                line_mapping = {int(k): v for k, v in line_mapping_raw.items()}
        
        # Create analyzer and analyze file
        analyzer = StackBasedAccessAnalyzer(db_path=db_path, track_operators=False)
        accesses = analyzer.analyze_file(
            Path(file_path), 
            trimmed_source, 
            line_mapping
        )
        
        # Resolve accesses to database entities
        resolved_accesses = analyzer.resolve_accesses(accesses)
        
        # Convert to tuples for batch insert
        insert_rows = []
        for access in resolved_accesses:
            insert_rows.append((
                access.entity_id,           # Can be None if not resolved
                access.member_id,           # Can be None if not resolved
                access.access_type.value,   # Convert enum to string
                file_id,
                access.original_line,
                access.trimmed_line,
                access.column,
                None,                       # accessing_function_id
                access.context_snippet,
                access.raw_identifier       # Always store raw identifier
            ))
        
        return insert_rows
        
    except Exception as e:
        # Return error info for debugging
        return f"ERROR: {file_path}: {str(e)}"


def build_database(db_path, source_paths, verbose=False, show_progress=True, incremental=False,
                  defines=None, defines_preset=None, include_paths=None, track_accesses=False):
    """Build the C++ entity database using two-phase approach: ingestion then parsing"""
    
    # Delete and recreate database unless incremental
    if not incremental:
        if db_path.exists():
            if verbose:
                print(f"{deco.yellow('Deleting existing database...')}")
            db_path.unlink()
    elif verbose:
        print(f"{deco.yellow('Incremental update - keeping existing data...')}")
    
    # Create database
    db = CppDatabaseV2(db_path)
    
    # Find all source files
    if verbose:
        print(f"{deco.yellow('Finding source files...')}")
    
    files = ork_cppdb.find_source_files(source_paths)
    total_files = len(files)
    
    if verbose:
        print(f"{deco.green(f'Found {total_files} source files')}")
    
    # Phase 1: Parallel Ingestion
    if verbose:
        print(f"{deco.yellow('Phase 1: Parallel ingestion with preprocessing and trimming...')}")
    
    ingestion_start = time.time()
    
    # Create ingestor
    ingestor = cpp_ingest.CppIngestor(
        defines=defines or {},
        include_paths=include_paths or [],
        defines_preset=defines_preset
    )
    
    # Ingest files in parallel
    results = ingestor.ingest_files_parallel(files, max_workers=host.NumCores)
    
    ingestion_time = time.time() - ingestion_start
    
    if verbose:
        total_raw = sum(item['raw_size'] for item in results['success'])
        total_trimmed = sum(item['trimmed_size'] for item in results['success'])
        print(f"{deco.green(f'Ingested {len(results["success"])} files in {ingestion_time:.1f}s')}")
        print(f"  Raw size: {total_raw/(1024*1024):.1f} MB")
        print(f"  Trimmed size: {total_trimmed/(1024*1024):.1f} MB")
        print(f"  Reduction: {(1 - total_trimmed/total_raw)*100:.1f}%")
    
    # Store ingested files in database
    db_store_start = time.time()
    with db.connect() as conn:
        # Ensure trimmed_source column exists
        cursor = conn.execute("PRAGMA table_info(source_files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'trimmed_source' not in columns:
            conn.execute("ALTER TABLE source_files ADD COLUMN trimmed_source TEXT")
        
        for item in results['success']:
            conn.execute("""
                INSERT OR REPLACE INTO source_files 
                (file_path, file_name, raw_source, preprocessed_source, trimmed_source, file_size, line_mapping)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(item['path']),
                item['path'].name,
                item['raw_source'].decode('utf-8', errors='ignore'),
                item['preprocessed_source'].decode('utf-8', errors='ignore'),
                item['trimmed_source'].decode('utf-8', errors='ignore'),
                item['raw_size'],
                json.dumps(item['line_mapping'])  # Store line mapping as JSON
            ))
        conn.commit()
    
    db_store_time = time.time() - db_store_start
    if verbose:
        print(f"{deco.green(f'Stored in database in {db_store_time:.1f}s')}")
    
    # Phase 2: Parallel Parsing
    if verbose:
        print(f"{deco.yellow('Phase 2: Parallel parsing of trimmed source...')}")
    
    parse_start = time.time()
    
    # Prepare arguments for parallel parsing
    parse_args = [(str(item['path']), db_path) for item in results['success']]
    
    parsed_count = 0
    entity_count = 0
    error_count = 0
    last_progress_time = time.time()
    
    with ProcessPoolExecutor(max_workers=host.NumCores) as executor:
        futures = {
            executor.submit(parse_single_file_v3, args): args[0]
            for args in parse_args
        }
        
        completed = 0
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                fp, entities, parse_time, error = future.result(timeout=30)
                
                if error:
                    error_count += 1
                    if verbose:
                        print(f"{deco.red(f'Error parsing {fp}: {error}')}")
                else:
                    # Store entities in database
                    for entity in entities:
                        db.add_entity(entity)
                        entity_count += 1
                    
                    # Track parsed file
                    db.add_file(Path(fp))
                    parsed_count += 1
                    
            except Exception as e:
                error_count += 1
                if verbose:
                    print(f"{deco.red(f'Error processing {file_path}: {e}')}")
            
            completed += 1
            if show_progress:
                current_time = time.time()
                # Only update progress every 2 seconds
                if current_time - last_progress_time >= 2.0:
                    progress = completed / len(parse_args) * 100
                    # Magenta for "Parsing progress", white for percent, yellow for counter
                    progress_text = f"{deco.magenta('Parsing progress:')} {deco.white(f'{progress:.1f}%')} {deco.yellow(f'({completed}/{len(parse_args)})')}"
                    print(f"\r{progress_text}", end='', flush=True)
                    last_progress_time = current_time
    
    parse_time = time.time() - parse_start
    
    if show_progress:
        # Show final 100% progress
        progress_text = f"{deco.magenta('Parsing progress:')} {deco.white('100.0%')} {deco.yellow(f'({len(parse_args)}/{len(parse_args)})')}"
        print(f"\r{progress_text}")  # Final update with newline
    
    # Phase 3: Access Tracking (optional)
    access_time = 0
    access_count = 0
    if track_accesses:
        if verbose:
            print(f"{deco.yellow('Phase 3: Parallel access tracking (analyzing entity references)...')}")
        
        access_start = time.time()
        
        # Clear existing access records before rebuilding
        with db.connect() as conn:
            conn.execute("DELETE FROM entity_accesses")
            conn.commit()
            if verbose:
                print(f"{deco.cyan('Cleared existing access records')}")
        
        # Prepare arguments for parallel access tracking
        access_args = [(str(item['path']), db_path) for item in results['success']]
        
        # Process files in parallel
        all_insert_rows = []
        processed_files = 0
        access_error_count = 0
        last_access_progress_time = time.time()
        
        with ProcessPoolExecutor(max_workers=host.NumCores) as executor:
            futures = {
                executor.submit(analyze_single_file_worker, args): args[0]
                for args in access_args
            }
            
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result(timeout=30)
                    
                    if result is None:
                        # File had no trimmed source
                        pass
                    elif isinstance(result, str) and result.startswith("ERROR:"):
                        # Worker returned an error
                        access_error_count += 1
                        if verbose:
                            print(f"{deco.red(result)}")
                    else:
                        # Got valid insert rows
                        all_insert_rows.extend(result)
                    
                except Exception as e:
                    access_error_count += 1
                    if verbose:
                        print(f"{deco.red(f'Error processing {file_path}: {e}')}")
                
                processed_files += 1
                if show_progress:
                    current_time = time.time()
                    # Only update progress every 2 seconds
                    if current_time - last_access_progress_time >= 2.0:
                        progress = processed_files / len(access_args) * 100
                        # Use consistent coloring with other phases
                        progress_text = f"{deco.blue('Access tracking progress:')} {deco.white(f'{progress:.1f}%')} {deco.yellow(f'({processed_files}/{len(access_args)})')}"
                        print(f"\r{progress_text}", end='', flush=True)
                        last_access_progress_time = current_time
        
        # Batch insert all accesses in a single transaction
        if all_insert_rows:
            with db.connect() as conn:
                conn.executemany("""
                    INSERT INTO entity_accesses 
                    (entity_id, member_id, access_type, file_id, 
                     original_line, trimmed_line, column_number,
                     accessing_function_id, context_snippet, raw_identifier)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, all_insert_rows)
                conn.commit()
                access_count = len(all_insert_rows)
        
        access_time = time.time() - access_start
        
        if show_progress:
            # Show final 100% progress
            progress_text = f"{deco.blue('Access tracking progress:')} {deco.white('100.0%')} {deco.yellow(f'({len(access_args)}/{len(access_args)})')}"
            print(f"\r{progress_text}")  # Final update with newline
        
        if verbose:
            print(f"{deco.green(f'Access tracking complete: {access_count} accesses tracked')}")
            if access_error_count > 0:
                print(f"{deco.yellow(f'Files with access tracking errors: {access_error_count}')}")
    
    # Report summary
    total_time = time.time() - ingestion_start
    
    print(f"\n{deco.green('=== Build Complete ===')}")
    print(f"Total time: {total_time:.1f}s")
    print(f"  Ingestion: {ingestion_time:.1f}s ({ingestion_time/total_time*100:.0f}%)")
    print(f"  DB storage: {db_store_time:.1f}s ({db_store_time/total_time*100:.0f}%)")
    print(f"  Parsing: {parse_time:.1f}s ({parse_time/total_time*100:.0f}%)")
    if track_accesses:
        print(f"  Access tracking: {access_time:.1f}s ({access_time/total_time*100:.0f}%)")
    print(f"Files processed: {parsed_count}/{total_files}")
    if error_count > 0:
        print(f"Files with errors: {error_count}")
    print(f"Entities found: {entity_count}")
    if track_accesses:
        print(f"Accesses tracked: {access_count}")
    print(f"Database: {db_path}")
    
    return parsed_count, entity_count


def main():
    parser = argparse.ArgumentParser(
        description='Build C++ entity database V2 for Orkid codebase'
    )
    
    # Module selection
    parser.add_argument('-m', '--module', action='append',
                       help='Specific modules to index (core, lev2, ecs, tool, gfx, etc.)')
    
    parser.add_argument('--all', action='store_true',
                       help='Index all modules')
    
    # Other options
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    parser.add_argument('--no-progress', action='store_true',
                       help='Disable progress indicator')
    
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
    print(f"Database file: {db_path}")
    
    # If stats only, show stats and exit
    if args.stats_only:
        if not db_path.exists():
            print(f"{deco.red(f'Database not found: {db_path}')}")
            print("Run without --stats-only to build the database first")
            sys.exit(1)
        
        db = CppDatabaseV2(db_path)
        stats = db.get_statistics()
        
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
        modules = args.module
    
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
    build_database(
        db_path,
        source_paths,
        verbose=args.verbose,
        show_progress=not args.no_progress,
        incremental=args.incremental,
        defines=args.defines,
        defines_preset=args.defines_preset,
        include_paths=include_paths,
        track_accesses=not args.no_track_accesses  # Default to True unless disabled
    )

if __name__ == '__main__':
    main()