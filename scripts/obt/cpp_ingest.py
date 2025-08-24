"""
C++ Source File Ingestion Module
Reads raw files, preprocesses them, and stores in database
Designed for parallel execution
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Set
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import obt.deco

class CppIngestor:
    """Handles ingestion of C++ source files into database"""
    
    def __init__(self, 
                 defines: Optional[Dict[str, str]] = None,
                 include_paths: Optional[List[str]] = None,
                 defines_preset: Optional[str] = None):
        self.defines = defines or {}
        self.include_paths = include_paths or []
        self.defines_preset = defines_preset
        self.deco = obt.deco.Deco()
        
    def preprocess_file(self, filepath: Path) -> tuple[Path, bytes, bytes, bytes, float]:
        """
        Preprocess a single file and trim to target file content only
        Returns: (filepath, raw_source, preprocessed_source, trimmed_source, preprocess_time)
        """
        import time
        start_time = time.perf_counter()
        
        # Read raw source
        with open(filepath, 'rb') as f:
            raw_source = f.read()
            
        # Build preprocessor command
        cmd = ['clang', '-E', '-x', 'c++', '-std=c++20']
        
        # Add defines
        for key, value in self.defines.items():
            if value:
                cmd.append(f'-D{key}={value}')
            else:
                cmd.append(f'-D{key}')
                
        # Add include paths
        for inc_path in self.include_paths:
            cmd.append(f'-I{inc_path}')
            
        # Add the file
        cmd.append(str(filepath))
        
        try:
            # Run preprocessor
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.stdout:
                preprocessed = result.stdout
            else:
                # Fallback to raw if preprocessing fails
                preprocessed = raw_source
                
        except subprocess.TimeoutExpired:
            print(f"Warning: Preprocessing timeout for {filepath}")
            preprocessed = raw_source
        except Exception as e:
            print(f"Warning: Preprocessing error for {filepath}: {e}")
            preprocessed = raw_source
            
        # Trim to target file content only
        trimmed = self._trim_to_target_file(preprocessed, filepath)
        
        preprocess_time = time.perf_counter() - start_time
            
        return filepath, raw_source, preprocessed, trimmed, preprocess_time
    
    def _trim_to_target_file(self, source_code: bytes, target_file: Path) -> bytes:
        """
        Remove all content from included files, keeping only the target file's content.
        This dramatically reduces the amount of code to parse.
        """
        import re
        
        # Normalize target file path for comparison
        target_file_str = str(target_file.resolve())
        target_file_name = target_file.name
        
        # Parse line directives: # linenum "filename" flags
        line_directive_pattern = re.compile(rb'^#\s+(\d+)\s+"([^"]+)".*?$', re.MULTILINE)
        
        result = []
        lines = source_code.split(b'\n')
        current_file = target_file_str
        keep_lines = True
        
        for line in lines:
            match = line_directive_pattern.match(line)
            if match:
                # This is a line directive
                filename = match.group(2).decode('utf-8', errors='ignore')
                
                # Check if we're entering or leaving the target file
                if filename == target_file_str or filename.endswith('/' + target_file_name) or filename == target_file_name:
                    keep_lines = True
                else:
                    keep_lines = False
                
                # Skip the directive itself
                continue
            
            # Only keep lines from the target file
            if keep_lines:
                result.append(line)
        
        return b'\n'.join(result)
    
    def ingest_files_parallel(self, filepaths: List[Path], 
                            max_workers: Optional[int] = None) -> Dict:
        """
        Ingest multiple files in parallel
        Returns dict of results
        """
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
            
        results = {
            'success': [],
            'failed': [],
            'stats': {
                'total_raw_bytes': 0,
                'total_preprocessed_bytes': 0,
                'time_seconds': 0
            }
        }
        
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all files for processing
            futures = {
                executor.submit(self.preprocess_file, fp): fp 
                for fp in filepaths
            }
            
            # Process results as they complete
            completed = 0
            total = len(futures)
            
            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    path, raw, preprocessed, trimmed, preprocess_time = future.result()
                    results['success'].append({
                        'path': path,
                        'raw_size': len(raw),
                        'preprocessed_size': len(preprocessed),
                        'trimmed_size': len(trimmed),
                        'raw_source': raw,
                        'preprocessed_source': preprocessed,
                        'trimmed_source': trimmed,
                        'preprocess_time': preprocess_time
                    })
                    results['stats']['total_raw_bytes'] += len(raw)
                    results['stats']['total_preprocessed_bytes'] += len(preprocessed)
                    
                except Exception as e:
                    results['failed'].append({
                        'path': filepath,
                        'error': str(e)
                    })
                
                completed += 1
                if completed % 10 == 0 or completed == total:
                    percent = (completed / total) * 100
                    deco = obt.deco.Deco()
                    # Orange for "Ingestion progress", white for percent, yellow for counter
                    progress_text = f"{deco.orange('Ingestion progress:')} {deco.white(f'{percent:.1f}%')} {deco.yellow(f'({completed}/{total})')}"
                    print(f"\r{progress_text}", end='', flush=True)
                    
        # Print newline after completion
        if completed == total:
            print()
            
        results['stats']['time_seconds'] = time.time() - start_time
        return results


def ingest_to_database(files: List[Path], db_path: Path, 
                       max_workers: Optional[int] = None) -> None:
    """
    Ingest files and store in database
    """
    from obt.cpp_database_v2 import CppDatabaseV2
    
    # Create ingestor
    ingestor = CppIngestor()
    
    # Process files in parallel
    print(f"Ingesting {len(files)} files with {max_workers or multiprocessing.cpu_count()} workers...")
    results = ingestor.ingest_files_parallel(files, max_workers)
    
    # Store in database
    db = CppDatabaseV2(db_path)
    
    with db.connect() as conn:
        for item in results['success']:
            # Store source file
            conn.execute("""
                INSERT OR REPLACE INTO source_files 
                (file_path, file_name, raw_source, preprocessed_source, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(item['path']),
                item['path'].name,
                item['raw_source'].decode('utf-8', errors='ignore'),
                item['preprocessed_source'].decode('utf-8', errors='ignore'),
                item['raw_size']
            ))
        conn.commit()
    
    # Print stats
    print(f"\nIngestion complete:")
    print(f"  Success: {len(results['success'])} files")
    print(f"  Failed: {len(results['failed'])} files")
    print(f"  Raw size: {results['stats']['total_raw_bytes']:,} bytes")
    print(f"  Preprocessed size: {results['stats']['total_preprocessed_bytes']:,} bytes")
    print(f"  Time: {results['stats']['time_seconds']:.2f} seconds")
    print(f"  Rate: {len(results['success']) / results['stats']['time_seconds']:.1f} files/second")


# Module exports
__all__ = ['CppIngestor', 'ingest_to_database']