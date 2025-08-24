#!/usr/bin/env python3
"""
Test trimming validation on larger files
"""

import sys
from pathlib import Path

from obt import cpp_database_v2

def analyze_trimming_for_all_files():
    """Analyze trimming effectiveness and correctness for all files in database"""
    
    # Connect to test database
    db_path = Path.home() / '.staging-aug18' / 'cpp_db_v2_test_ingest.db'
    db = cpp_database_v2.CppDatabaseV2(db_path)
    
    with db.connect() as conn:
        cursor = conn.execute("""
            SELECT file_path, 
                   LENGTH(raw_source) as raw_size,
                   LENGTH(preprocessed_source) as prep_size, 
                   LENGTH(trimmed_source) as trim_size,
                   raw_source,
                   trimmed_source
            FROM source_files 
            WHERE trimmed_source IS NOT NULL
            ORDER BY LENGTH(raw_source) DESC
        """)
        
        files = cursor.fetchall()
    
    if not files:
        print("No files with trimmed source found in database")
        return
    
    print(f"Found {len(files)} files with trimmed source\n")
    print("Top 5 largest raw files:")
    print("-" * 80)
    
    for i, (filepath, raw_size, prep_size, trim_size, raw_source, trimmed_source) in enumerate(files[:5]):
        filename = Path(filepath).name
        
        # Calculate ratios
        expansion = prep_size / raw_size if raw_size > 0 else 0
        trim_reduction = (1 - trim_size / prep_size) * 100 if prep_size > 0 else 0
        raw_vs_trim = trim_size / raw_size if raw_size > 0 else 0
        
        print(f"\n{i+1}. {filename}")
        print(f"   Path: {filepath}")
        print(f"   Raw size: {raw_size:,} bytes")
        print(f"   Preprocessed: {prep_size:,} bytes ({expansion:.1f}x expansion)")
        print(f"   Trimmed: {trim_size:,} bytes ({trim_reduction:.1f}% reduction from preprocessed)")
        print(f"   Trimmed vs Raw: {raw_vs_trim:.2f}x")
        
        # Validate content preservation
        if raw_source and trimmed_source:
            # Count actual code constructs
            constructs = {
                'classes': (raw_source.count('class '), trimmed_source.count('class ')),
                'structs': (raw_source.count('struct '), trimmed_source.count('struct ')),
                'functions': (raw_source.count('(') - raw_source.count('#include'), 
                             trimmed_source.count('(')),
                'virtuals': (raw_source.count('virtual '), trimmed_source.count('virtual ')),
                'statics': (raw_source.count('static '), trimmed_source.count('static ')),
                'typedefs': (raw_source.count('typedef '), trimmed_source.count('typedef ')),
                'usings': (raw_source.count('using '), trimmed_source.count('using ')),
                'templates': (raw_source.count('template'), trimmed_source.count('template')),
            }
            
            print("   Content comparison (raw → trimmed):")
            for construct, (raw_count, trim_count) in constructs.items():
                if raw_count > 0 or trim_count > 0:
                    if raw_count == trim_count:
                        status = "✓"
                    elif trim_count > raw_count:
                        status = "⚠️ increased"
                    else:
                        status = "⚠️ decreased"
                    print(f"     {construct:10}: {raw_count:3} → {trim_count:3} {status}")
    
    # Overall statistics
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    
    total_raw = sum(f[1] for f in files)
    total_prep = sum(f[2] for f in files)
    total_trim = sum(f[3] for f in files)
    
    print(f"Total files: {len(files)}")
    print(f"Total raw size: {total_raw:,} bytes")
    print(f"Total preprocessed: {total_prep:,} bytes")
    print(f"Total trimmed: {total_trim:,} bytes")
    print(f"Average expansion: {total_prep/total_raw:.1f}x")
    print(f"Average trimming reduction: {(1 - total_trim/total_prep)*100:.1f}%")
    print(f"Trimmed vs Raw ratio: {total_trim/total_raw:.2f}x")
    
    # Find files where trimmed > raw (shouldn't happen)
    anomalies = [(f[0], f[1], f[3]) for f in files if f[3] > f[1]]
    if anomalies:
        print(f"\n⚠️  WARNING: {len(anomalies)} files have trimmed > raw size:")
        for filepath, raw_size, trim_size in anomalies[:5]:
            print(f"  {Path(filepath).name}: raw={raw_size}, trimmed={trim_size}")

def check_specific_large_file():
    """Deep dive into a specific large file"""
    
    # Connect to test database
    db_path = Path.home() / '.staging-aug18' / 'cpp_db_v2_test_ingest.db'
    db = cpp_database_v2.CppDatabaseV2(db_path)
    
    # Get the largest file
    with db.connect() as conn:
        cursor = conn.execute("""
            SELECT file_path, raw_source, trimmed_source
            FROM source_files 
            WHERE trimmed_source IS NOT NULL
            ORDER BY LENGTH(raw_source) DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("No files found")
            return
        
        filepath, raw_source, trimmed_source = row
    
    print(f"\nDetailed analysis of largest file: {Path(filepath).name}")
    print("=" * 80)
    
    # Extract meaningful code patterns
    patterns_to_check = [
        ("Pure virtual methods", r"= 0;"),
        ("Namespace declarations", r"namespace \w+"),
        ("Include guards", r"#ifndef|#define.*_H_?"),
        ("Forward declarations", r"^\s*(class|struct)\s+\w+\s*;"),
        ("Friend declarations", r"friend\s+(class|struct)"),
        ("Inline functions", r"inline\s+"),
        ("Const methods", r"\) const"),
        ("Override specifiers", r"\) override"),
    ]
    
    import re
    
    for pattern_name, pattern in patterns_to_check:
        raw_matches = len(re.findall(pattern, raw_source, re.MULTILINE))
        trim_matches = len(re.findall(pattern, trimmed_source, re.MULTILINE))
        
        if raw_matches > 0 or trim_matches > 0:
            if raw_matches == trim_matches:
                status = "✓ preserved"
            elif trim_matches == 0:
                status = "✗ lost"
            else:
                status = f"⚠️  {raw_matches} → {trim_matches}"
            
            print(f"  {pattern_name:25}: {status}")
    
    # Show first few lines of each
    print("\nFirst 10 lines of raw source:")
    print("-" * 40)
    for i, line in enumerate(raw_source.split('\n')[:10], 1):
        print(f"{i:3}: {line[:70]}")
    
    print("\nFirst 10 lines of trimmed source:")
    print("-" * 40)
    for i, line in enumerate(trimmed_source.split('\n')[:10], 1):
        if line.strip():  # Skip empty lines for readability
            print(f"{i:3}: {line[:70]}")

if __name__ == '__main__':
    print("TRIMMING VALIDATION FOR ALL FILES")
    print("=" * 80)
    analyze_trimming_for_all_files()
    print("\n")
    check_specific_large_file()