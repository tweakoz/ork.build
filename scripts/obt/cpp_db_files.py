#!/usr/bin/env python3
"""
C++ Database File Management Tool
Search, list, and retrieve source files from the C++ database
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

from obt.cpp_database_v2 import CppDatabaseV2
import obt.path as obt_path


def list_files(db: CppDatabaseV2, limit: int = None) -> None:
    """List all files in the database"""
    files = db.list_source_files(limit)
    
    if not files:
        print("No files found in database")
        return
    
    print(f"Found {len(files)} files:")
    print("=" * 80)
    
    for file_info in files:
        size_kb = file_info['file_size'] / 1024 if file_info['file_size'] else 0
        print(f"{file_info['relative_path']:<50} {size_kb:>8.1f} KB  {file_info['updated_at']}")


def search_files(db: CppDatabaseV2, pattern: str) -> None:
    """Search for files by pattern"""
    files = db.search_source_files(pattern)
    
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    print(f"Found {len(files)} files matching '{pattern}':")
    print("=" * 80)
    
    for file_info in files:
        size_kb = file_info['file_size'] / 1024 if file_info['file_size'] else 0
        print(f"{file_info['relative_path']:<50} {size_kb:>8.1f} KB  {file_info['updated_at']}")


def get_file_by_name(db: CppDatabaseV2, filename: str) -> None:
    """Get files by exact filename"""
    files = db.get_source_file_by_name(filename)
    
    if not files:
        print(f"No files found with name: {filename}")
        return
    
    if len(files) == 1:
        file_info = files[0]
        print(f"File: {file_info['file_path']}")
        print(f"Size: {file_info['file_size']} bytes")
        print(f"Updated: {file_info['updated_at']}")
        print("=" * 80)
    else:
        print(f"Found {len(files)} files with name '{filename}':")
        print("=" * 80)
        for i, file_info in enumerate(files, 1):
            size_kb = file_info['file_size'] / 1024 if file_info['file_size'] else 0
            print(f"{i}. {file_info['file_path']}")
            print(f"   Size: {size_kb:.1f} KB, Updated: {file_info['updated_at']}")


def show_file_content(db: CppDatabaseV2, file_path: str, show_raw: bool = True, 
                     show_preprocessed: bool = False, line_numbers: bool = False) -> None:
    """Show file content"""
    file_info = db.get_source_file(file_path)
    
    if not file_info:
        print(f"File not found in database: {file_path}")
        return
    
    if show_raw:
        print(f"=== RAW SOURCE: {file_info['relative_path']} ===")
        content = file_info['raw_source']
        if line_numbers:
            for i, line in enumerate(content.split('\n'), 1):
                print(f"{i:4d}: {line}")
        else:
            print(content)
    
    if show_preprocessed and file_info['preprocessed_source']:
        print(f"\n=== PREPROCESSED SOURCE: {file_info['relative_path']} ===")
        content = file_info['preprocessed_source']
        if line_numbers:
            for i, line in enumerate(content.split('\n'), 1):
                print(f"{i:4d}: {line}")
        else:
            print(content)
    elif show_preprocessed:
        print(f"No preprocessed source available for: {file_info['relative_path']}")


def main():
    parser = argparse.ArgumentParser(description='C++ Database File Management Tool')
    parser.add_argument('-d', '--database', help='Database file path (default: auto-detect)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all files in database')
    list_parser.add_argument('--limit', type=int, help='Limit number of files shown')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search files by pattern')
    search_parser.add_argument('pattern', help='Search pattern (wildcards supported)')
    
    # Find command
    find_parser = subparsers.add_parser('find', help='Find files by exact filename')
    find_parser.add_argument('filename', help='Exact filename to find')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show file content')
    show_parser.add_argument('file_path', help='Full file path to show')
    show_parser.add_argument('--raw', action='store_true', default=True, 
                           help='Show raw source (default)')
    show_parser.add_argument('--preprocessed', action='store_true', 
                           help='Show preprocessed source')
    show_parser.add_argument('--both', action='store_true', 
                           help='Show both raw and preprocessed')
    show_parser.add_argument('-n', '--line-numbers', action='store_true', 
                           help='Show line numbers')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Determine database path
    if args.database:
        db_path = Path(args.database)
    else:
        # Auto-detect database
        db_path = obt_path.stage() / "cpp_db_v2_orkid.db"
        if not db_path.exists():
            print(f"Database not found at {db_path}")
            print("Run database build first or specify database path with -d")
            return
    
    # Create database connection
    db = CppDatabaseV2(str(db_path))
    
    # Execute command
    try:
        if args.command == 'list':
            list_files(db, args.limit)
        
        elif args.command == 'search':
            search_files(db, args.pattern)
        
        elif args.command == 'find':
            get_file_by_name(db, args.filename)
        
        elif args.command == 'show':
            show_raw = args.raw or not (args.preprocessed or args.both)
            show_preprocessed = args.preprocessed or args.both
            show_file_content(db, args.file_path, show_raw, show_preprocessed, args.line_numbers)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()