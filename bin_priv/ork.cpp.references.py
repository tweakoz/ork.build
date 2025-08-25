#!/usr/bin/env python3
"""
Search for references (reads, writes, calls) to C++ entities
Find where entities are accessed throughout the codebase
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Add obt to path
import obt.path
import obt.deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType

deco = obt.deco.Deco()

def parse_entity_spec(spec: str) -> tuple[str, str, str]:
    """
    Parse an entity specification like "ork::lev2::CompressedImageMipChain::_width"
    
    Returns:
        (namespace, class_name, member_name) or (namespace, "", function_name)
    """
    parts = spec.split('::')
    
    if len(parts) < 2:
        # Just a simple name
        return "", "", spec
    
    # Check if last part looks like a member (starts with _ or lowercase)
    last_part = parts[-1]
    if len(parts) >= 3 and (last_part.startswith('_') or last_part[0].islower()):
        # Likely a member: namespace::class::member
        member = parts[-1]
        class_name = parts[-2]
        namespace = '::'.join(parts[:-2]) if len(parts) > 2 else ""
        return namespace, class_name, member
    else:
        # Likely a function or class: namespace::function
        namespace = '::'.join(parts[:-1])
        return namespace, "", parts[-1]

def find_entity_id(db: CppDatabaseV2, namespace: str, class_name: str, member_or_func: str) -> tuple[int, int]:
    """
    Find the entity ID and optionally member ID for the given specification
    
    Returns:
        (entity_id, member_id) where member_id may be None
    """
    with db.connect() as conn:
        cursor = conn.cursor()
        
        if class_name:
            # Looking for a class member
            # First find the class
            if namespace:
                cursor.execute("""
                    SELECT id FROM entities 
                    WHERE short_name = ? AND namespace = ? 
                    AND entity_type IN (?, ?)
                """, (class_name, namespace, EntityType.CLASS.value, EntityType.STRUCT.value))
            else:
                cursor.execute("""
                    SELECT id FROM entities 
                    WHERE short_name = ? 
                    AND entity_type IN (?, ?)
                """, (class_name, EntityType.CLASS.value, EntityType.STRUCT.value))
            
            class_result = cursor.fetchone()
            if not class_result:
                return None, None
            
            class_id = class_result[0]
            
            # Now find the member
            cursor.execute("""
                SELECT id FROM entity_members
                WHERE entity_id = ? AND name = ?
            """, (class_id, member_or_func))
            
            member_result = cursor.fetchone()
            if member_result:
                return class_id, member_result[0]
            else:
                return class_id, None
        else:
            # Looking for a function or global variable
            if namespace:
                cursor.execute("""
                    SELECT id FROM entities
                    WHERE short_name = ? AND namespace = ?
                """, (member_or_func, namespace))
            else:
                cursor.execute("""
                    SELECT id FROM entities
                    WHERE short_name = ?
                """, (member_or_func,))
            
            entity_result = cursor.fetchone()
            if entity_result:
                return entity_result[0], None
            else:
                return None, None

def display_references(db: CppDatabaseV2, entity_id: int, member_id: int = None, 
                      access_type: str = None, limit: int = 0):
    """Display references to an entity or member"""
    
    # Get the entity/member info for display
    with db.connect() as conn:
        cursor = conn.cursor()
        
        if member_id:
            cursor.execute("""
                SELECT e.canonical_name, m.name, m.member_type
                FROM entities e
                JOIN entity_members m ON e.id = m.entity_id
                WHERE e.id = ? AND m.id = ?
            """, (entity_id, member_id))
            result = cursor.fetchone()
            if result:
                entity_name = f"{result[0]}::{result[1]}"
                print(f"\nReferences to member: {deco.cyan(entity_name)}")
                print(f"Member type: {result[2]}")
        else:
            cursor.execute("""
                SELECT canonical_name, entity_type
                FROM entities
                WHERE id = ?
            """, (entity_id,))
            result = cursor.fetchone()
            if result:
                entity_name = result[0]
                print(f"\nReferences to entity: {deco.cyan(entity_name)}")
                print(f"Entity type: {result[1]}")
    
    print("=" * 80)
    
    # Get accesses from database
    accesses = db.get_entity_accesses(
        entity_id=entity_id if not member_id else None,
        member_id=member_id,
        access_type=access_type
    )
    
    if not accesses:
        print(f"{deco.yellow('No references found')}")
        print("\nNote: Access tracking may not have been enabled during the last database build.")
        print("Rebuild with: ork.cpp.db.build.py --track-accesses")
        return
    
    # Group by file for better display
    by_file = {}
    for access in accesses:
        file_path = access['file_path']
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(access)
    
    # Display results using column format
    total_count = 0
    
    # Print header with reverse video
    # Create header text that spans the full width (8+8+6+80 = 102 chars)
    header_configs = [
        (8, 'left'),   # access type
        (8, 'left'),   # line number
        (6, 'left'),   # column
        (80, 'left')   # filename
    ]
    header_texts = [
        "Type",
        "Line",
        "Col",
        "File"
    ]
    # Format the header and pad to full width
    header_line = deco.formatColumns(header_configs, header_texts)
    # Apply reverse video to the entire header line (padded to 102 chars)
    print(deco.reverseVideo(header_line.ljust(102)))
    
    for file_path, file_accesses in sorted(by_file.items()):
        # Sort by line number
        file_accesses.sort(key=lambda a: a['line_number'])
        
        for access in file_accesses:
            if limit > 0 and total_count >= limit:
                break
            
            # Color the access type
            access_type = access['access_type']
            if access_type == 'read':
                access_col = deco.green(access_type.ljust(8))
            elif access_type == 'write':
                access_col = deco.red(access_type.ljust(8))
            elif access_type == 'call':
                access_col = deco.yellow(access_type.ljust(8))
            elif access_type == 'impl':
                access_col = deco.blue(access_type.ljust(8))
            else:
                access_col = access_type.ljust(8)
            
            # Format line number
            line_col = deco.cyan(str(access['line_number']).ljust(8))
            
            # Format column number
            col_col = deco.white(str(access.get('column_number', 0)).ljust(6))
            
            # Sanitize file path using obt.path
            from pathlib import Path as PathlibPath
            import obt.path
            sanitized_path = obt.path.Path(PathlibPath(file_path)).sanitized
            
            # Make filename pink
            file_col = deco.magenta(sanitized_path)
            
            # Use formatColumns for aligned output
            column_configs = [
                (8, 'left'),   # access type
                (8, 'left'),   # line number
                (6, 'left'),   # column
                (80, 'left')   # filename with full path
            ]
            column_texts = [access_col, line_col, col_col, file_col]
            output = deco.formatColumns(column_configs, column_texts)
            
            print(output)
            total_count += 1
        
        if limit > 0 and total_count >= limit:
            print(f"\n{deco.yellow(f'Results limited to {limit}. Use --limit to see more.')}")
            break
    
    # Summary
    read_count = sum(1 for a in accesses if a['access_type'] == 'read')
    write_count = sum(1 for a in accesses if a['access_type'] == 'write')
    call_count = sum(1 for a in accesses if a['access_type'] == 'call')
    def_count = sum(1 for a in accesses if a['access_type'] == 'def')
    impl_count = sum(1 for a in accesses if a['access_type'] == 'impl')
    
    print("\n" + "=" * 80)
    print(f"Total references: {len(accesses)}")
    print(f"  Definitions: {def_count}")
    print(f"  Implementations: {impl_count}")
    print(f"  Reads:  {read_count}")
    print(f"  Writes: {write_count}")
    print(f"  Calls:  {call_count}")

def output_references_json(db: CppDatabaseV2, entity_id: int, member_id: int = None, 
                          access_type: str = None, limit: int = 0) -> str:
    """Generate JSON output for references (optimized for AI readability)"""
    
    # Get entity/member info
    entity_info = {}
    with db.connect() as conn:
        cursor = conn.cursor()
        
        if member_id:
            cursor.execute("""
                SELECT e.canonical_name, m.name, m.member_type, e.entity_type
                FROM entities e
                JOIN entity_members m ON e.id = m.entity_id
                WHERE e.id = ? AND m.id = ?
            """, (entity_id, member_id))
            result = cursor.fetchone()
            if result:
                entity_info = {
                    "type": "member",
                    "class_name": result[0],
                    "member_name": result[1],
                    "member_type": result[2],
                    "full_name": f"{result[0]}::{result[1]}",
                    "entity_type": result[3]
                }
        else:
            cursor.execute("""
                SELECT canonical_name, entity_type, short_name, namespace
                FROM entities
                WHERE id = ?
            """, (entity_id,))
            result = cursor.fetchone()
            if result:
                entity_info = {
                    "type": "entity",
                    "full_name": result[0],
                    "entity_type": result[1],
                    "short_name": result[2],
                    "namespace": result[3]
                }
    
    # Get accesses from database
    accesses = db.get_entity_accesses(
        entity_id=entity_id if not member_id else None,
        member_id=member_id,
        access_type=access_type
    )
    
    # Build structured output
    references = []
    access_counts = {"read": 0, "write": 0, "call": 0, "def": 0, "impl": 0}
    
    for access in accesses[:limit] if limit > 0 else accesses:
        # Sanitize file path
        from pathlib import Path as PathlibPath
        sanitized_path = obt.path.Path(PathlibPath(access['file_path'])).sanitized
        
        ref_entry = {
            "access_type": access['access_type'],
            "file_path": sanitized_path,
            "line_number": access['line_number'],
            "column_number": access.get('column_number', 0)
        }
        references.append(ref_entry)
        
        # Count access types
        access_type_key = access['access_type']
        if access_type_key in access_counts:
            access_counts[access_type_key] += 1
    
    # Calculate total counts from all accesses (not just limited ones)
    total_counts = {"read": 0, "write": 0, "call": 0, "def": 0, "impl": 0}
    for access in accesses:
        access_type_key = access['access_type']
        if access_type_key in total_counts:
            total_counts[access_type_key] += 1
    
    result = {
        "query": {
            "entity": entity_info,
            "filters": {
                "access_type": access_type,
                "limit": limit if limit > 0 else None
            }
        },
        "references": references,
        "summary": {
            "total_found": len(accesses),
            "displayed": len(references),
            "access_counts": total_counts,
            "limited": len(references) < len(accesses)
        }
    }
    
    return json.dumps(result, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description='Find references to C++ entities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find all references to a member variable
  ork.cpp.references.py ork::lev2::CompressedImageMipChain::_width
  
  # Find only write accesses to a member
  ork.cpp.references.py ork::lev2::CompressedImageMipChain::_width --writes
  
  # Find all calls to a method
  ork.cpp.references.py ork::lev2::CompressedImageMipChain::readDDS --calls
  
  # Find references to a function
  ork.cpp.references.py ork::lev2::initTextureLoaders
  
  # JSON output for AI parsing (structured data)
  ork.cpp.references.py ork::lev2::Context::SetDisplayMode --json
  
  # JSON with filtering (only calls, limited to 10 results)
  ork.cpp.references.py ork::lev2::Context::SetDisplayMode --calls --limit 10 --json
"""
    )
    
    parser.add_argument('entity',
                       help='Entity to find references for (e.g., namespace::class::member)')
    
    parser.add_argument('--reads', action='store_true',
                       help='Show only read accesses')
    
    parser.add_argument('--writes', action='store_true',
                       help='Show only write accesses')
    
    parser.add_argument('--calls', action='store_true',
                       help='Show only function/method calls')
    
    parser.add_argument('--limit', type=int, default=0,
                       help='Maximum number of references to show (0 = unlimited)')
    
    parser.add_argument('--json', action='store_true',
                       help='Output in JSON format (optimized for AI parsing)')
    
    parser.add_argument('--project', '-p', default='orkid',
                       help='Project database to search (default: orkid)')
    
    args = parser.parse_args()
    
    # Determine access type filter
    access_type = None
    if args.reads:
        access_type = 'read'
    elif args.writes:
        access_type = 'write'
    elif args.calls:
        access_type = 'call'
    
    # Get database path
    import obt.path as obt_path
    db_path = obt_path.stage() / f"cpp_db_v2_{args.project}.db"
    
    if not db_path.exists():
        print(f"{deco.red(f'Database not found: {db_path}')}")
        print(f"Run ork.cpp.db.build.py --track-accesses to build the database with access tracking")
        sys.exit(1)
    
    # Open database
    db = CppDatabaseV2(db_path)
    
    # Parse the entity specification
    namespace, class_name, member_or_func = parse_entity_spec(args.entity)
    
    # Find the entity in the database
    entity_id, member_id = find_entity_id(db, namespace, class_name, member_or_func)
    
    if entity_id is None:
        print(f"{deco.red(f'Entity not found: {args.entity}')}")
        print("\nTry searching for it first:")
        print(f"  ork.cpp.search.py {member_or_func}")
        sys.exit(1)
    
    if class_name and member_or_func and member_id is None:
        print(f"{deco.red(f'Member not found: {member_or_func} in {namespace}::{class_name}')}")
        print("\nNote: The member might be inherited. Try searching for the base class.")
        sys.exit(1)
    
    # Display the references
    if args.json:
        json_output = output_references_json(db, entity_id, member_id, access_type, args.limit)
        print(json_output)
    else:
        display_references(db, entity_id, member_id, access_type, args.limit)

if __name__ == '__main__':
    main()