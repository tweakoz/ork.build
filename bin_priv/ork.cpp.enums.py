#!/usr/bin/env python3
"""
Display enum values for C++ enums.
Orkid-specific tool for exploring enum definitions.
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Add OBT to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from obt.path import stage
from obt.deco import Deco
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import EntityType, MemberType

deco = Deco()


def find_enums_by_pattern(db: CppDatabaseV2, pattern: str) -> List[Dict[str, Any]]:
    """Find enums matching a pattern (supports wildcards)"""
    with db.connect() as conn:
        cursor = conn.cursor()
        
        # Convert wildcard pattern to SQL LIKE pattern
        sql_pattern = pattern.replace('*', '%')
        
        cursor.execute("""
            SELECT id, canonical_name, short_name, namespace, is_enum_class
            FROM entities 
            WHERE entity_type = 'enum' AND canonical_name LIKE ?
            ORDER BY canonical_name
        """, (sql_pattern,))
        
        return [dict(row) for row in cursor.fetchall()]


def display_enum_values_columnar(db: CppDatabaseV2, enum_info: Dict[str, Any]):
    """Display a single enum's values in columnar format"""
    enum_id = enum_info['id']
    canonical_name = enum_info['canonical_name']
    namespace = enum_info['namespace'] or '-'
    is_enum_class = bool(enum_info.get('is_enum_class', False))
    
    # Check if this is a CrcEnum (base type is crc_enum_t)
    is_crc_enum = False
    with db.connect() as conn:
        cursor = conn.cursor()
        # Check if any member has CrcEnum pattern or if base type suggests it
        cursor.execute("""
            SELECT COUNT(*) FROM entity_members 
            WHERE entity_id = ? AND member_type = 'enum_value' AND value IS NULL
        """, (enum_id,))
        null_count = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM entity_members 
            WHERE entity_id = ? AND member_type = 'enum_value'
        """, (enum_id,))
        total_count = cursor.fetchone()[0]
        # If all values are NULL, likely a CrcEnum
        is_crc_enum = (null_count == total_count and total_count > 0)
    
    # Get enum values
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, value, line_number
            FROM entity_members
            WHERE entity_id = ? AND member_type = 'enum_value'
            ORDER BY line_number
        """, (enum_id,))
        
        values = cursor.fetchall()
    
    if not values:
        return
    
    # Print header for this enum
    print()
    filename_padded = canonical_name.center(148)
    print(deco.bg('grey1') + deco.fg('pink') + filename_padded + deco.reset())
    
    # Column configuration  
    LINE_LENGTH = 148
    name_col_width = 25
    namespace_col_width = 20
    type_col_width = 20
    value_col_width = 35
    hash_col_width = LINE_LENGTH - (name_col_width + namespace_col_width + type_col_width + value_col_width)
    
    # Print column headers with dark background and white text
    header_configs = [
        (name_col_width, 'left'),
        (namespace_col_width, 'left'),
        (type_col_width, 'left'),
        (value_col_width, 'left'),
        (hash_col_width, 'left')
    ]
    
    # Create header texts with black bg and white fg for each column
    header_texts = [
        deco.bg('black') + deco.white('Name'.ljust(name_col_width)),
        deco.bg('black') + deco.white('Namespace'.ljust(namespace_col_width)),
        deco.bg('black') + deco.white('Type'.ljust(type_col_width)),
        deco.bg('black') + deco.white('Value'.ljust(value_col_width)),
        deco.bg('black') + deco.white('Hash'.ljust(hash_col_width))
    ]
    
    # Format the header - concatenate the colored columns
    header_line = ''.join(header_texts)
    print(header_line + deco.reset())
    
    # Determine enum type string
    # TODO: Extract base type from parsing (e.g., : crc_enum_t)
    base_type = ""  # Would need to be captured during parsing
    
    if is_enum_class:
        if base_type:
            type_str = f'enum class : {base_type}'
        else:
            type_str = 'enum class'
    else:
        if base_type:
            type_str = f'enum : {base_type}'
        else:
            type_str = 'enum'
    
    # Check if any value uses CrcEnum (simplified check)
    uses_crc = False  # Would need to track this during parsing
    
    # Display each enum value
    for i, val in enumerate(values):
        name = val['name']
        value = val['value'] if val['value'] else None
        
        # Format value and hash
        hash_str = ""
        hash_hex = ""
        hash_dec = ""
        if value:
            value_str = f"= {value}"
        elif is_crc_enum:
            # CrcEnum macro value
            value_str = f"CrcEnum({name})"
            # Compute CRC32 hash
            import zlib
            crc_value = zlib.crc32(name.encode('utf-8')) & 0xffffffff
            hash_hex = f"0x{crc_value:08X}"
            hash_dec = f"({crc_value})"
        else:
            # Auto-incremented
            value_str = f"(= {i})"
        
        # Color coding
        name_col = deco.yellow(name.ljust(name_col_width))
        namespace_col = deco.magenta(namespace.ljust(namespace_col_width))
        type_col = deco.green(type_str.ljust(type_col_width))
        value_col = deco.cyan(value_str.ljust(value_col_width))
        if hash_hex:
            hash_col = deco.orange(hash_hex) + " " + deco.fg('ora2') + hash_dec + deco.reset()
        else:
            hash_col = ""
        
        # Use formatColumns for aligned output
        column_configs = [
            (name_col_width, 'left'),
            (namespace_col_width, 'left'),
            (type_col_width, 'left'),
            (value_col_width, 'left'),
            (hash_col_width, 'left')
        ]
        column_texts = [name_col, namespace_col, type_col, value_col, hash_col]
        output = deco.formatColumns(column_configs, column_texts)
        
        print(output)


def search_by_hash(db: CppDatabaseV2, hash_value: str, show_json: bool = False):
    """Search for enum values by CRC32 hash"""
    import zlib
    
    # Parse hash value (support hex or decimal)
    if hash_value.startswith('0x') or hash_value.startswith('0X'):
        target_hash = int(hash_value, 16)
    else:
        target_hash = int(hash_value)
    
    results = []
    
    # Get all enums that might be CrcEnum-based
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT e.id, e.canonical_name, e.short_name, e.namespace, e.is_enum_class
            FROM entities e
            JOIN entity_members m ON e.id = m.entity_id
            WHERE e.entity_type = 'enum' 
            AND m.member_type = 'enum_value'
            AND m.value IS NULL
            GROUP BY e.id
        """)
        
        for enum_row in cursor.fetchall():
            enum_info = dict(enum_row)
            
            # Get all values for this enum
            cursor2 = conn.cursor()
            cursor2.execute("""
                SELECT name FROM entity_members
                WHERE entity_id = ? AND member_type = 'enum_value'
                ORDER BY line_number
            """, (enum_info['id'],))
            
            for val_row in cursor2.fetchall():
                value_name = val_row['name']
                # Compute CRC32 for this value
                crc_value = zlib.crc32(value_name.encode('utf-8')) & 0xffffffff
                
                if crc_value == target_hash:
                    results.append({
                        'enum': enum_info['canonical_name'],
                        'value': value_name,
                        'hash_hex': f'0x{crc_value:08X}',
                        'hash_dec': crc_value
                    })
    
    if show_json:
        import json
        print(json.dumps({'results': results}, indent=2))
    else:
        if results:
            print(f"/////////////////////////////////////////////////////////////")
            print(f"// Found {len(results)} match{'es' if len(results) != 1 else ''} for hash {hash_value}")
            print(f"/////////")
            print()
            
            for result in results:
                print(f"{deco.yellow(result['enum'])}::{deco.cyan(result['value'])} = {deco.orange(result['hash_hex'])} {deco.fg('ora2')}({result['hash_dec']}){deco.reset()}")
        else:
            print(f"{deco.red(f'No CrcEnum values found with hash: {hash_value}')}")


def display_enums(db: CppDatabaseV2, pattern: str, show_json: bool = False):
    """Display enums matching pattern"""
    
    # Check if pattern has wildcards
    if '*' in pattern or '%' in pattern:
        # Pattern search
        enums = find_enums_by_pattern(db, pattern)
    else:
        # Exact search - try both short and canonical name
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # Try canonical name first if it has ::
            if '::' in pattern:
                cursor.execute("""
                    SELECT id, canonical_name, short_name, namespace, is_enum_class
                    FROM entities 
                    WHERE canonical_name = ? AND entity_type = 'enum'
                """, (pattern,))
            else:
                # Try short name
                cursor.execute("""
                    SELECT id, canonical_name, short_name, namespace, is_enum_class
                    FROM entities 
                    WHERE short_name = ? AND entity_type = 'enum'
                """, (pattern,))
            
            enums = [dict(row) for row in cursor.fetchall()]
    
    if not enums:
        if show_json:
            print(json.dumps({"error": f"No enums matching '{pattern}'"}, indent=2))
        else:
            print(f"{deco.red(f'No enums matching: {pattern}')}")
        return
    
    if show_json:
        # JSON output for all matching enums
        result = {"enums": []}
        
        for enum_info in enums:
            enum_data = {
                "canonical_name": enum_info['canonical_name'],
                "short_name": enum_info['short_name'],
                "namespace": enum_info['namespace'],
                "is_enum_class": bool(enum_info.get('is_enum_class', False)),
                "values": []
            }
            
            # Get values
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, value, line_number
                    FROM entity_members
                    WHERE entity_id = ? AND member_type = 'enum_value'
                    ORDER BY line_number
                """, (enum_info['id'],))
                
                for val in cursor.fetchall():
                    enum_data["values"].append({
                        "name": val['name'],
                        "value": val['value'] if val['value'] else None,
                        "line": val['line_number']
                    })
            
            result["enums"].append(enum_data)
        
        print(json.dumps(result, indent=2))
    else:
        # Columnar display
        print("/////////////////////////////////////////////////////////////")
        print(f"// Found {len(enums)} enum{'s' if len(enums) != 1 else ''}")
        print("/////////")
        
        for enum_info in enums:
            display_enum_values_columnar(db, enum_info)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Display enum values for C++ enums in Orkid'
    )
    
    parser.add_argument(
        'pattern',
        nargs='?',
        help='Enum name or pattern (supports wildcards like "ork::lev2::*")'
    )
    
    parser.add_argument(
        '--match',
        help='Pattern to match enums (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--hash',
        help='Search for enum value by hash (hex like 0xE15695B7 or decimal like 3780548023)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all enums'
    )
    
    args = parser.parse_args()
    
    # Check if Orkid database exists
    db_path = stage() / "cpp_db_v2_orkid.db"
    if not db_path.exists():
        print(f"{deco.red('Orkid database not found!')}")
        print(f"Expected at: {db_path}")
        print(f"Run 'ork.cpp.db.build.py -m <modules>' to build it first")
        sys.exit(1)
    
    # Open database
    try:
        db = CppDatabaseV2(db_path)
        
        # Check if searching by hash
        if args.hash:
            search_by_hash(db, args.hash, args.json)
        else:
            # Determine pattern for regular enum display
            if args.all:
                pattern = '*'
            elif args.match:
                pattern = args.match
            elif args.pattern:
                pattern = args.pattern
            else:
                parser.error('Either provide a pattern, use --match, --hash, or use --all')
            
            display_enums(db, pattern, args.json)
    except Exception as e:
        print(f"{deco.red(f'Error: {e}')}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()