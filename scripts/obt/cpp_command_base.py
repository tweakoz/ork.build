#!/usr/bin/env python3
"""
Base infrastructure for C++ database commands.
Provides common functionality for all cpp analysis commands.
"""

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
import time

from obt.path import stage
from obt.deco import Deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt import host

deco = Deco()


class CppCommandBase:
    """Base class for C++ analysis commands"""
    
    def __init__(self, command_name: str, description: str):
        self.command_name = command_name
        self.description = description
        self.deco = Deco()
        self.db_path = None
        self.db = None
        self.temp_db = None
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create base argument parser - subclasses can extend this"""
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Database source group (mutually exclusive)
        source_group = parser.add_mutually_exclusive_group()
        source_group.add_argument(
            '--db', '--database',
            type=Path,
            help='Path to existing C++ database'
        )
        source_group.add_argument(
            '--source', '-s',
            type=Path,
            help='Source file or directory to analyze (builds temporary database)'
        )
        
        # Common options
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Verbose output'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of results (0 = unlimited)'
        )
        
        return parser
    
    def get_or_build_database(self, args) -> CppDatabaseV2:
        """Get existing database or build temporary one from source"""
        
        if args.source:
            # Build temporary database from source
            return self._build_temp_database(args.source, args.verbose)
        elif args.db:
            # Use existing database
            if not args.db.exists():
                print(f"{self.deco.red(f'Database not found: {args.db}')}")
                sys.exit(1)
            self.db_path = args.db
            return CppDatabaseV2(self.db_path)
        else:
            # No source specified - subclasses should handle default
            return None
    
    def _build_temp_database(self, source_path: Path, verbose: bool) -> CppDatabaseV2:
        """Build a temporary database from source files"""
        
        if verbose:
            print(f"{self.deco.yellow('Building temporary database from source...')}")
        
        # Create temp database
        temp_dir = tempfile.mkdtemp(prefix='cpp_db_')
        self.temp_db = Path(temp_dir) / 'temp.db'
        
        if verbose:
            print(f"Temporary database: {self.temp_db}")
        
        # Import here to avoid circular dependencies
        from obt.cpp_ingest import CppIngestor
        from obt.cpp_parser_descent import RecursiveDescentCppParser
        from obt import ork_cppdb
        from concurrent.futures import ProcessPoolExecutor, as_completed
        
        # Find source files
        if source_path.is_file():
            files = [source_path]
        else:
            files = ork_cppdb.find_source_files([source_path])
        
        if verbose:
            print(f"Found {len(files)} source files")
        
        # Create database
        db = CppDatabaseV2(self.temp_db)
        
        # Phase 1: Ingest files
        ingestor = CppIngestor()
        results = ingestor.ingest_files_parallel(files, max_workers=host.NumCores)
        
        # Store in database
        with db.connect() as conn:
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
                    None  # No line mapping for temp DB
                ))
            conn.commit()
        
        # Phase 2: Parse entities
        if verbose:
            print(f"{self.deco.yellow('Parsing entities...')}")
        
        for item in results['success']:
            file_path = str(item['path'])
            trimmed_source = item['trimmed_source']
            
            # Parse with recursive descent parser
            parser = RecursiveDescentCppParser(db_path=self.temp_db)
            entities = parser.parse_source(trimmed_source, file_path)
            
            # Store entities
            for entity in entities:
                db.add_entity(entity)
            
            # Track file
            db.add_file(item['path'])
        
        if verbose:
            stats = db.get_statistics()
            print(f"{self.deco.green(f'Built temporary database with {stats.get("total_entities", 0)} entities')}")
        
        self.db_path = self.temp_db
        return db
    
    def cleanup(self):
        """Clean up temporary database if created"""
        if self.temp_db and self.temp_db.exists():
            import shutil
            shutil.rmtree(self.temp_db.parent)
            if hasattr(self, 'verbose') and self.verbose:
                print(f"{self.deco.cyan('Cleaned up temporary database')}")
    
    def run(self):
        """Main entry point - subclasses should override this"""
        raise NotImplementedError("Subclasses must implement run()")


def create_orkid_wrapper(obt_module_name: str, command_name: str):
    """
    Create a thin wrapper that uses Orkid's default database.
    This is a helper for generating the ork.* command variants.
    """
    def main():
        # Add default Orkid database to arguments
        import sys
        from pathlib import Path
        
        # Insert --db argument if not already specified
        if '--db' not in sys.argv and '--database' not in sys.argv and '--source' not in sys.argv:
            db_path = stage() / "cpp_db_v2_orkid.db"
            if not db_path.exists():
                deco = Deco()
                print(f"{deco.red('Orkid database not found!')}")
                print(f"Expected at: {db_path}")
                print(f"Run 'ork.cpp.db.build.py -m <modules>' to build it first")
                sys.exit(1)
            sys.argv.extend(['--db', str(db_path)])
        
        # Import and run the obt variant
        import importlib
        module = importlib.import_module(f'obt.{obt_module_name}')
        module.main()
    
    return main