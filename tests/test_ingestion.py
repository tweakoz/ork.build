#!/usr/bin/env python3
"""
Test script for parallel ingestion and parsing
"""

import sys
import argparse
import time
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

from obt import cpp_ingest
from obt import cpp_database_v2
from obt import ork_cppdb
from obt import cpp_parser_descent
from obt import host

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def parse_single_file(args):
    """
    Parse a single file from the database
    Returns tuple of (file_path, parse_time, entity_count, error)
    """
    file_path, db_path = args
    start_time = time.perf_counter()
    
    try:
        # Connect to database
        db = cpp_database_v2.CppDatabaseV2(db_path)
        with db.connect() as conn:
            # Get trimmed source
            cursor = conn.execute("""
                SELECT trimmed_source FROM source_files 
                WHERE file_path = ?
            """, (file_path,))
            row = cursor.fetchone()
            
            if not row:
                return file_path, 0, 0, f"File not found in database"
            
            trimmed_source = row[0]
            
        # Parse with recursive descent parser
        parser = cpp_parser_descent.CppParser()
        entities = parser.parse_source(trimmed_source.encode('utf-8'), file_path)
        
        parse_time = time.perf_counter() - start_time
        return file_path, parse_time, len(entities), None
        
    except Exception as e:
        parse_time = time.perf_counter() - start_time
        return file_path, parse_time, 0, str(e)

def parallel_parse_phase(db_path: Path, max_workers: int = 4):
    """
    Parse all ingested files in parallel
    """
    logger.info("=" * 60)
    logger.info("Starting parallel parsing phase")
    
    phase_start = time.perf_counter()
    
    # Get list of files to parse
    db = cpp_database_v2.CppDatabaseV2(db_path)
    with db.connect() as conn:
        cursor = conn.execute("SELECT file_path FROM source_files")
        file_paths = [row[0] for row in cursor.fetchall()]
    
    logger.info(f"Found {len(file_paths)} files to parse")
    
    # Prepare arguments for parallel processing
    parse_args = [(fp, db_path) for fp in file_paths]
    
    # Parse in parallel
    results = {
        'success': [],
        'failed': [],
        'total_entities': 0,
        'total_parse_time': 0
    }
    
    completed = 0
    total = len(file_paths)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(parse_single_file, args): args[0]
            for args in parse_args
        }
        
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                fp, parse_time, entity_count, error = future.result(timeout=30)
                
                if error:
                    results['failed'].append({
                        'path': fp,
                        'error': error,
                        'time': parse_time
                    })
                else:
                    results['success'].append({
                        'path': fp,
                        'entities': entity_count,
                        'time': parse_time
                    })
                    results['total_entities'] += entity_count
                    results['total_parse_time'] += parse_time
                    
            except Exception as e:
                results['failed'].append({
                    'path': file_path,
                    'error': str(e),
                    'time': 0
                })
            
            completed += 1
            if completed % 10 == 0 or completed == total:
                percent = (completed / total) * 100
                elapsed = time.perf_counter() - phase_start
                rate = completed / elapsed if elapsed > 0 else 0
                logger.info(f"  Parse progress: {completed}/{total} files ({percent:.1f}%) - {rate:.1f} files/sec")
    
    phase_time = time.perf_counter() - phase_start
    
    # Report results
    logger.info("=" * 60)
    logger.info("Parsing Phase Statistics:")
    logger.info(f"  Files parsed: {len(results['success'])}")
    logger.info(f"  Files failed: {len(results['failed'])}")
    logger.info(f"  Total entities found: {results['total_entities']:,}")
    
    if results['success']:
        avg_parse_time = results['total_parse_time'] / len(results['success'])
        avg_entities = results['total_entities'] / len(results['success'])
        logger.info(f"  Average parse time: {avg_parse_time:.3f}s per file")
        logger.info(f"  Average entities per file: {avg_entities:.1f}")
        logger.info(f"  Total CPU time: {results['total_parse_time']:.1f}s")
        logger.info(f"  Wall time: {phase_time:.1f}s")
        logger.info(f"  Speedup: {results['total_parse_time']/phase_time:.1f}x")
    
    # Show some failed files if any
    if results['failed']:
        logger.warning(f"Failed to parse {len(results['failed'])} files:")
        for item in results['failed'][:5]:
            logger.warning(f"  {item['path']}: {item['error']}")
        if len(results['failed']) > 5:
            logger.warning(f"  ... and {len(results['failed']) - 5} more")
    
    return results

def test_module_ingestion(module_name):
    """Test ingesting files from a module"""
    
    # Start total timer
    total_start = time.perf_counter()
    
    # Create test database
    db_path = Path.home() / '.staging-aug18' / 'cpp_db_v2_test_ingest.db'
    
    # Get files to test
    logger.info(f"Testing ingestion of module: {module_name}")
    logger.info(f"Database path: {db_path}")
    
    file_discovery_start = time.perf_counter()
    source_paths = ork_cppdb.get_orkid_paths(modules=[module_name])
    files = ork_cppdb.find_source_files(source_paths)
    file_discovery_time = time.perf_counter() - file_discovery_start
    
    logger.info(f"Found {len(files)} files in module {module_name} ({file_discovery_time:.3f}s)")
    
    # Set up include paths for Orkid
    include_paths = ork_cppdb.get_orkid_include_paths()
    logger.info(f"Using {len(include_paths)} include paths")
    
    # Create ingestor with Orkid settings
    ingestor = cpp_ingest.CppIngestor(
        defines={'ORKID_INGEST_TEST': '1'},
        include_paths=include_paths,
        defines_preset='macos'
    )
    
    if not files:
        logger.warning(f"No files found for module {module_name}")
        return
    
    logger.info(f"Starting parallel ingestion of {len(files)} files...")
    
    # Use parallel ingestion
    ingestion_start = time.perf_counter()
    results = ingestor.ingest_files_parallel(files, max_workers=host.NumCores)
    ingestion_time = time.perf_counter() - ingestion_start
    
    # Calculate statistics
    total_raw = sum(item['raw_size'] for item in results['success'])
    total_preprocessed = sum(item['preprocessed_size'] for item in results['success'])
    total_trimmed = sum(item['trimmed_size'] for item in results['success'])
    
    # Performance metrics
    files_per_second = len(results['success']) / ingestion_time if ingestion_time > 0 else 0
    mb_per_second = (total_raw / (1024 * 1024)) / ingestion_time if ingestion_time > 0 else 0
    
    logger.info(f"Ingestion completed in {ingestion_time:.3f}s")
    logger.info(f"Performance: {files_per_second:.1f} files/sec, {mb_per_second:.2f} MB/sec")
    
    logger.info("=" * 60)
    logger.info("Ingestion Statistics:")
    logger.info(f"  Files processed: {len(results['success'])}")
    logger.info(f"  Files failed: {len(results['failed'])}")
    logger.info(f"  Total raw size: {total_raw:,} bytes ({total_raw/(1024*1024):.2f} MB)")
    logger.info(f"  Total preprocessed size: {total_preprocessed:,} bytes ({total_preprocessed/(1024*1024):.2f} MB)")
    logger.info(f"  Total trimmed size: {total_trimmed:,} bytes ({total_trimmed/(1024*1024):.2f} MB)")
    
    if total_raw > 0:
        logger.info(f"  Average expansion: {total_preprocessed / total_raw:.1f}x")
        logger.info(f"  Trimming saved: {(1 - total_trimmed / total_preprocessed) * 100:.2f}% of preprocessed")
        logger.info(f"  Trimming ratio: {total_trimmed / total_raw:.3f}x of original")
    
    # Per-file statistics
    if results['success']:
        preprocess_times = []
        trim_ratios = []
        for item in results['success']:
            if 'preprocess_time' in item:
                preprocess_times.append(item['preprocess_time'])
            if item['preprocessed_size'] > 0:
                trim_ratios.append(item['trimmed_size'] / item['preprocessed_size'])
        
        if preprocess_times:
            avg_preprocess = sum(preprocess_times) / len(preprocess_times)
            logger.info(f"  Avg preprocessing time: {avg_preprocess:.3f}s per file")
        
        if trim_ratios:
            avg_trim_ratio = sum(trim_ratios) / len(trim_ratios)
            logger.info(f"  Avg trim ratio: {(1 - avg_trim_ratio) * 100:.2f}% removed per file")
    
    # Store in database
    logger.info("=" * 60)
    logger.info(f"Storing in database: {db_path}")
    
    db_start = time.perf_counter()
    db = cpp_database_v2.CppDatabaseV2(db_path)
    
    with db.connect() as conn:
        # Ensure trimmed_source column exists
        cursor = conn.execute("PRAGMA table_info(source_files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'trimmed_source' not in columns:
            conn.execute("ALTER TABLE source_files ADD COLUMN trimmed_source TEXT")
        
        # Store each file
        stored_count = 0
        for item in results['success']:
            conn.execute("""
                INSERT OR REPLACE INTO source_files 
                (file_path, file_name, raw_source, preprocessed_source, trimmed_source, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(item['path']),
                item['path'].name,
                item['raw_source'].decode('utf-8', errors='ignore'),
                item['preprocessed_source'].decode('utf-8', errors='ignore'),
                item['trimmed_source'].decode('utf-8', errors='ignore'),
                item['raw_size']
            ))
            stored_count += 1
        
        conn.commit()
    
    db_time = time.perf_counter() - db_start
    logger.info(f"Database storage completed in {db_time:.3f}s")
    logger.info(f"  Stored {stored_count} files ({stored_count/db_time:.1f} files/sec)")
    
    # Show failed files if any
    if results['failed']:
        logger.warning(f"Failed files ({len(results['failed'])} total):")
        for item in results['failed'][:5]:  # Show first 5
            logger.warning(f"  {item['path']}: {item['error']}")
        if len(results['failed']) > 5:
            logger.warning(f"  ... and {len(results['failed']) - 5} more")
    
    # Total time
    total_time = time.perf_counter() - total_start
    logger.info("=" * 60)
    logger.info("Overall Performance Summary:")
    logger.info(f"  Total time: {total_time:.3f}s")
    logger.info(f"  File discovery: {file_discovery_time:.3f}s ({file_discovery_time/total_time*100:.1f}%)")
    logger.info(f"  Ingestion: {ingestion_time:.3f}s ({ingestion_time/total_time*100:.1f}%)")
    logger.info(f"  Database storage: {db_time:.3f}s ({db_time/total_time*100:.1f}%)")
    logger.info(f"  Overall throughput: {len(results['success'])/total_time:.1f} files/sec")
    
    return db_path

def main():
    parser = argparse.ArgumentParser(description='Test C++ file ingestion and parsing')
    
    # Get available modules for help text
    available = ', '.join(ork_cppdb.list_available_modules())
    
    parser.add_argument('-m', '--module',
                       help=f'Module name to test. Available: {available}')
    parser.add_argument('--list-modules', action='store_true',
                       help='List available modules with descriptions')
    parser.add_argument('--parse', action='store_true',
                       help='Also run parallel parsing phase after ingestion')
    parser.add_argument('--parse-workers', type=int, default=host.NumCores,
                       help=f'Number of parallel workers for parsing (default: {host.NumCores})')
    
    args = parser.parse_args()
    
    if args.list_modules:
        print("Available modules:")
        for module in ork_cppdb.list_available_modules():
            desc = ork_cppdb.get_module_description(module)
            print(f"  {module:12} - {desc}")
        sys.exit(0)
    
    if not args.module:
        parser.error("Module name required (use -m MODULE)")
    
    # Run ingestion
    db_path = test_module_ingestion(args.module)
    
    # Run parsing if requested
    if args.parse and db_path:
        parallel_parse_phase(db_path, max_workers=args.parse_workers)

if __name__ == '__main__':
    main()