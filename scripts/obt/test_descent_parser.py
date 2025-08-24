#!/usr/bin/env python3
"""
Test the recursive descent parser on ICastable
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from obt.cpp_parser_descent import RecursiveDescentCppParser
from obt.cpp_database_v2 import CppDatabaseV2
import obt.path

def test_icastable():
    """Test parser on ICastable struct"""
    
    # Get database and preprocessed source
    db_path = obt.path.stage() / 'cpp_db_v2_orkid.db'
    db = CppDatabaseV2(db_path)
    
    # Get preprocessed source for ICastable
    with db.connect() as conn:
        cursor = conn.execute("""
            SELECT preprocessed_source, file_path
            FROM source_files 
            WHERE file_path LIKE '%ICastable.h'
        """)
        result = cursor.fetchone()
    
    if not result or not result[0]:
        print("ICastable.h not found in database")
        return
    
    source_code = result[0]
    filepath = Path(result[1])
    
    print(f"Testing on: {filepath}")
    print(f"Source size: {len(source_code)} bytes")
    
    # Parse with recursive descent parser
    parser = RecursiveDescentCppParser(verbose=False)
    entities = parser.parse_preprocessed(source_code, filepath)
    
    print(f"\nFound {len(entities)} entities")
    
    # Find ICastable
    for entity in entities:
        if entity.short_name == 'ICastable':
            print(f"\n{'='*60}")
            print(f"Entity: {entity.short_name} ({entity.entity_type.value})")
            print(f"Namespace: {entity.namespace or 'global'}")
            print(f"Members: {len(entity.members)}")
            print(f"{'='*60}")
            
            # Group members by type
            by_type = {}
            for member in entity.members:
                mtype = member.member_type.value
                if mtype not in by_type:
                    by_type[mtype] = []
                by_type[mtype].append(member)
            
            for mtype, members in sorted(by_type.items()):
                print(f"\n{mtype.upper()}S ({len(members)}):")
                for member in members:
                    print(f"  • {member.name}", end='')
                    
                    # Add attributes
                    attrs = []
                    if member.is_static:
                        attrs.append('static')
                    if member.is_virtual:
                        attrs.append('virtual')
                    if member.is_pure_virtual:
                        attrs.append('PURE VIRTUAL')
                    if member.is_const:
                        attrs.append('const')
                    if member.access_level:
                        attrs.append(member.access_level.value)
                    
                    if attrs:
                        print(f" [{', '.join(attrs)}]", end='')
                    
                    if member.data_type:
                        print(f" : {member.data_type}", end='')
                    
                    print()
            
            print(f"\n{'='*60}")
            break
    else:
        print("ICastable not found in parsed entities")
        print("Found entities:", [e.short_name for e in entities])

if __name__ == '__main__':
    test_icastable()