################################################################################
# Orkid Build Tools (OBT)
# Shared C++ entity database V2 build engine.
#
# Reusable core used by BOTH the generic per-project builder
#   obt.cpp.db.build.py --project <name> <dirs>
# and the Orkid preset
#   ork.cpp.db.build.py -m <modules>
# Frontends resolve source paths / db path / defines, then call
# build_database() here. Three-phase: parallel ingest+trim ->
# parallel parse -> optional parallel access tracking.
################################################################################

import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt import cpp_ingest
from obt import cpp_parser_descent
from obt import host

deco = obt.deco.Deco()

# C++ source file extensions used for discovery
_CPP_EXTENSIONS = {'.h', '.hpp', '.hxx', '.H', '.hh',
                   '.c', '.cpp', '.cxx', '.cc', '.C',
                   '.inl', '.inc'}


def find_source_files(paths, extensions=None):
    """Find all C++ source files under the given files/dirs (sorted, unique)."""
    if extensions is None:
        extensions = _CPP_EXTENSIONS
    files = []
    for p in paths:
        p = Path(p)
        if p.is_file():
            if p.suffix in extensions:
                files.append(p)
        elif p.is_dir():
            for ext in extensions:
                files.extend(p.rglob(f'*{ext}'))
    return sorted(set(files))


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
    
    files = find_source_files(source_paths)
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
        n_ok = len(results["success"])
        print(f"{deco.green(f'Ingested {n_ok} files in {ingestion_time:.1f}s')}")
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
