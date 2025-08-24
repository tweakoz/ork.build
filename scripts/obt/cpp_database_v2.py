"""
Normalized database interface for C++ entities
Clean room implementation with proper relational structure
"""
import sqlite3
import json
import hashlib
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Union
from contextlib import contextmanager
from datetime import datetime

from obt.cpp_entities_v2 import (
    Entity, Location, Member, Parameter,
    EntityType, LocationType, AccessLevel, MemberType
)

class CppDatabaseV2:
    """Normalized database for C++ entities with no duplicates"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()
    
    @contextmanager
    def connect(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize normalized database schema"""
        with self.connect() as conn:
            conn.executescript("""
                -- Canonical entities (one per unique entity)
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_name TEXT UNIQUE NOT NULL,
                    short_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    namespace TEXT,
                    
                    -- Template info
                    is_template BOOLEAN DEFAULT 0,
                    template_params TEXT,
                    is_template_specialization BOOLEAN DEFAULT 0,
                    specialized_from TEXT,
                    
                    -- Class/struct flags
                    is_abstract BOOLEAN DEFAULT 0,
                    is_final BOOLEAN DEFAULT 0,
                    is_pod BOOLEAN DEFAULT 0,
                    base_classes TEXT,  -- JSON array
                    
                    -- Function flags
                    return_type TEXT,
                    parameters TEXT,  -- JSON array
                    is_method BOOLEAN DEFAULT 0,
                    is_virtual BOOLEAN DEFAULT 0,
                    is_static BOOLEAN DEFAULT 0,
                    is_const BOOLEAN DEFAULT 0,
                    is_inline BOOLEAN DEFAULT 0,
                    is_constexpr BOOLEAN DEFAULT 0,
                    is_noexcept BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    is_default BOOLEAN DEFAULT 0,
                    is_override BOOLEAN DEFAULT 0,
                    is_final_method BOOLEAN DEFAULT 0,
                    
                    -- Enum info
                    underlying_type TEXT,
                    is_enum_class BOOLEAN DEFAULT 0,
                    
                    -- Typedef/alias info
                    aliased_type TEXT,
                    is_using_alias BOOLEAN DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Source files table
                CREATE TABLE IF NOT EXISTS source_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    relative_path TEXT,
                    file_name TEXT NOT NULL,
                    file_extension TEXT,
                    file_size INTEGER DEFAULT 0,
                    raw_source TEXT NOT NULL,
                    preprocessed_source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Index for fast file searching
                CREATE INDEX IF NOT EXISTS idx_source_files_name ON source_files(file_name);
                CREATE INDEX IF NOT EXISTS idx_source_files_path ON source_files(file_path);
                CREATE INDEX IF NOT EXISTS idx_source_files_relative ON source_files(relative_path);
                
                -- Entity locations (multiple per entity)
                CREATE TABLE IF NOT EXISTS entity_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER DEFAULT 0,
                    location_type TEXT NOT NULL,
                    has_body BOOLEAN DEFAULT 0,
                    context TEXT,
                    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                    UNIQUE(entity_id, file_path, line_number)  -- Prevent duplicate locations
                );
                
                -- Entity members (fields, methods, enum values)
                CREATE TABLE IF NOT EXISTS entity_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    member_type TEXT NOT NULL,
                    data_type TEXT,
                    signature TEXT,  -- Critical for overload differentiation
                    access_level TEXT DEFAULT 'private',
                    is_static BOOLEAN DEFAULT 0,
                    is_virtual BOOLEAN DEFAULT 0,
                    is_const BOOLEAN DEFAULT 0,
                    is_inline BOOLEAN DEFAULT 0,
                    is_explicit BOOLEAN DEFAULT 0,
                    is_override BOOLEAN DEFAULT 0,
                    is_final BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    is_default BOOLEAN DEFAULT 0,
                    is_pure_virtual BOOLEAN DEFAULT 0,  -- Added for = 0
                    is_noexcept BOOLEAN DEFAULT 0,      -- Added for noexcept
                    is_mutable BOOLEAN DEFAULT 0,       -- NEW: For mutable fields
                    is_constexpr BOOLEAN DEFAULT 0,     -- NEW: For constexpr fields  
                    array_dimensions TEXT,               -- NEW: Store "[10][20]" for arrays
                    pointer_depth INTEGER DEFAULT 0,     -- NEW: Count of * indirections
                    line_number INTEGER DEFAULT 0,
                    value TEXT,  -- Initialization value or enum value
                    -- UNIFIED TYPE SYSTEM FIELDS
                    base_type_id INTEGER,                -- Reference to canonical_types.id
                    is_reference BOOLEAN DEFAULT 0,      -- T& reference type
                    is_rvalue_reference BOOLEAN DEFAULT 0, -- T&& rvalue reference
                    is_volatile BOOLEAN DEFAULT 0,       -- volatile qualifier
                    return_const BOOLEAN DEFAULT 0,      -- const return type (for methods)
                    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                    FOREIGN KEY (base_type_id) REFERENCES canonical_types(id),
                    UNIQUE(entity_id, name, member_type, signature)  -- Fixed to handle overloads
                );
                
                -- Member implementation locations (method bodies, static member instantiations, template instantiations)
                CREATE TABLE IF NOT EXISTS member_implementation_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER DEFAULT 0,
                    location_type TEXT NOT NULL,
                    has_body BOOLEAN DEFAULT 0,
                    context TEXT,
                    FOREIGN KEY (member_id) REFERENCES entity_members(id) ON DELETE CASCADE,
                    UNIQUE(member_id, file_path, line_number)  -- Prevent duplicate locations
                );
                
                -- File tracking for incremental updates
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    last_modified REAL NOT NULL,
                    file_hash TEXT NOT NULL,
                    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Reference tracking (for future use)
                CREATE TABLE IF NOT EXISTS entity_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_entity_id INTEGER,
                    from_file TEXT NOT NULL,
                    from_line INTEGER NOT NULL,
                    to_entity_id INTEGER NOT NULL,
                    reference_type TEXT NOT NULL,  -- 'call', 'instantiation', 'inheritance', etc.
                    FOREIGN KEY (from_entity_id) REFERENCES entities(id) ON DELETE SET NULL,
                    FOREIGN KEY (to_entity_id) REFERENCES entities(id) ON DELETE CASCADE
                );
                
                -- Indices for performance
                CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(short_name);
                CREATE INDEX IF NOT EXISTS idx_entity_namespace ON entities(namespace);
                CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type);
                CREATE INDEX IF NOT EXISTS idx_entity_canonical ON entities(canonical_name);
                
                CREATE INDEX IF NOT EXISTS idx_location_file ON entity_locations(file_path);
                CREATE INDEX IF NOT EXISTS idx_location_entity ON entity_locations(entity_id);
                
                CREATE INDEX IF NOT EXISTS idx_member_entity ON entity_members(entity_id);
                CREATE INDEX IF NOT EXISTS idx_member_name ON entity_members(name);
                
                CREATE INDEX IF NOT EXISTS idx_member_impl_member ON member_implementation_locations(member_id);
                CREATE INDEX IF NOT EXISTS idx_member_impl_file ON member_implementation_locations(file_path);
                
                CREATE INDEX IF NOT EXISTS idx_ref_from ON entity_references(from_entity_id);
                CREATE INDEX IF NOT EXISTS idx_ref_to ON entity_references(to_entity_id);
                
                -- ============================================================
                -- UNIFIED TYPE SYSTEM TABLES
                -- ============================================================
                
                -- Flyweight type registry
                CREATE TABLE IF NOT EXISTS canonical_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_hash TEXT UNIQUE NOT NULL,     -- Hash of canonical form for deduplication
                    canonical_form TEXT NOT NULL,       -- e.g. "orkmap<const rend_shader*, TriangleMetaBucket*>"
                    base_name TEXT NOT NULL,           -- e.g. "orkmap"
                    template_args TEXT,                -- e.g. "<const rend_shader*, TriangleMetaBucket*>"
                    is_primitive BOOLEAN DEFAULT 0,    -- int, float, char, etc.
                    is_template BOOLEAN DEFAULT 0,     -- Has template parameters
                    namespace TEXT,                    -- e.g. "ork::lev2"
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Typedef/alias mappings
                CREATE TABLE IF NOT EXISTS type_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias_name TEXT NOT NULL,          -- e.g. "Vector3f"
                    target_type_id INTEGER NOT NULL,   -- -> canonical_types.id
                    namespace TEXT,                    -- Where alias is defined
                    is_using_alias BOOLEAN DEFAULT 0,  -- using vs typedef
                    entity_id INTEGER,                 -- Entity that defines this alias
                    FOREIGN KEY (target_type_id) REFERENCES canonical_types(id),
                    FOREIGN KEY (entity_id) REFERENCES entities(id),
                    UNIQUE(alias_name, namespace)
                );
                
                -- Indexes for type system
                CREATE INDEX IF NOT EXISTS idx_canonical_types_hash ON canonical_types(type_hash);
                CREATE INDEX IF NOT EXISTS idx_canonical_types_base ON canonical_types(base_name);
                CREATE INDEX IF NOT EXISTS idx_type_aliases_name ON type_aliases(alias_name);
                CREATE INDEX IF NOT EXISTS idx_type_aliases_target ON type_aliases(target_type_id);
                
                -- Trigger to update timestamp
                CREATE TRIGGER IF NOT EXISTS update_entity_timestamp 
                AFTER UPDATE ON entities
                BEGIN
                    UPDATE entities SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            """)
    
    def add_entity(self, entity: Entity) -> int:
        """
        Add or update an entity and all its data.
        Returns the entity ID.
        """
        with self.connect() as conn:
            # Check if entity already exists
            existing = conn.execute(
                "SELECT id FROM entities WHERE canonical_name = ?",
                (entity.canonical_name,)
            ).fetchone()
            
            # Prepare JSON data
            base_classes_json = json.dumps(entity.base_classes) if entity.base_classes else None
            parameters_json = None
            if entity.parameters:
                parameters_json = json.dumps([
                    {
                        'name': p.name,
                        'type': p.param_type,
                        'default': p.default_value,
                        'is_const': p.is_const,
                        'is_reference': p.is_reference,
                        'is_pointer': p.is_pointer,
                        'is_rvalue_ref': p.is_rvalue_ref
                    }
                    for p in entity.parameters
                ])
            
            if existing:
                entity_id = existing['id']
                # Update entity with new information
                conn.execute("""
                    UPDATE entities SET
                        short_name = ?,
                        entity_type = ?,
                        namespace = ?,
                        is_template = ?,
                        template_params = ?,
                        is_template_specialization = ?,
                        specialized_from = ?,
                        is_abstract = ?,
                        is_final = ?,
                        is_pod = ?,
                        base_classes = ?,
                        return_type = ?,
                        parameters = ?,
                        is_method = ?,
                        is_virtual = ?,
                        is_static = ?,
                        is_const = ?,
                        is_inline = ?,
                        is_constexpr = ?,
                        is_noexcept = ?,
                        is_deleted = ?,
                        is_default = ?,
                        is_override = ?,
                        is_final_method = ?,
                        underlying_type = ?,
                        is_enum_class = ?,
                        aliased_type = ?,
                        is_using_alias = ?
                    WHERE id = ?
                """, (
                    entity.short_name,
                    entity.entity_type.value,
                    entity.namespace,
                    entity.is_template,
                    entity.template_params,
                    entity.is_template_specialization,
                    entity.specialized_from,
                    entity.is_abstract,
                    entity.is_final,
                    entity.is_pod,
                    base_classes_json,
                    entity.return_type,
                    parameters_json,
                    entity.is_method,
                    entity.is_virtual,
                    entity.is_static,
                    entity.is_const,
                    entity.is_inline,
                    entity.is_constexpr,
                    entity.is_noexcept,
                    entity.is_deleted,
                    entity.is_default,
                    entity.is_override,
                    entity.is_final_method,
                    entity.underlying_type,
                    entity.is_enum_class,
                    entity.aliased_type,
                    entity.is_using_alias,
                    entity_id
                ))
            else:
                # Insert new entity
                cursor = conn.execute("""
                    INSERT INTO entities (
                        canonical_name, short_name, entity_type, namespace,
                        is_template, template_params, is_template_specialization, specialized_from,
                        is_abstract, is_final, is_pod, base_classes,
                        return_type, parameters, is_method, is_virtual, is_static, is_const,
                        is_inline, is_constexpr, is_noexcept, is_deleted, is_default,
                        is_override, is_final_method,
                        underlying_type, is_enum_class,
                        aliased_type, is_using_alias
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity.canonical_name,
                    entity.short_name,
                    entity.entity_type.value,
                    entity.namespace,
                    entity.is_template,
                    entity.template_params,
                    entity.is_template_specialization,
                    entity.specialized_from,
                    entity.is_abstract,
                    entity.is_final,
                    entity.is_pod,
                    base_classes_json,
                    entity.return_type,
                    parameters_json,
                    entity.is_method,
                    entity.is_virtual,
                    entity.is_static,
                    entity.is_const,
                    entity.is_inline,
                    entity.is_constexpr,
                    entity.is_noexcept,
                    entity.is_deleted,
                    entity.is_default,
                    entity.is_override,
                    entity.is_final_method,
                    entity.underlying_type,
                    entity.is_enum_class,
                    entity.aliased_type,
                    entity.is_using_alias
                ))
                entity_id = cursor.lastrowid
            
            # Add locations (using INSERT OR IGNORE for uniqueness)
            for location in entity.locations:
                conn.execute("""
                    INSERT OR IGNORE INTO entity_locations (
                        entity_id, file_path, line_number, column_number,
                        location_type, has_body, context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    location.file_path,
                    location.line_number,
                    location.column_number,
                    location.location_type.value,
                    location.has_body,
                    location.context
                ))
            
            # Add members (using INSERT OR REPLACE to update existing)
            for member in entity.members:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO entity_members (
                        entity_id, name, member_type, data_type,
                        signature, access_level, is_static, is_virtual, is_const,
                        is_inline, is_explicit, is_override, is_final,
                        is_deleted, is_default, is_pure_virtual, is_noexcept,
                        array_dimensions, pointer_depth,
                        line_number, value,
                        base_type_id, is_reference, is_rvalue_reference, is_volatile, return_const
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    member.name,
                    member.member_type.value,
                    member.data_type,
                    member.signature,
                    member.access_level.value,
                    member.is_static,
                    member.is_virtual,
                    member.is_const,
                    member.is_inline,
                    member.is_explicit,
                    member.is_override,
                    member.is_final,
                    member.is_deleted,
                    member.is_default,
                    getattr(member, 'is_pure_virtual', False),
                    getattr(member, 'is_noexcept', False),
                    getattr(member, 'array_dimensions', None),
                    getattr(member, 'pointer_depth', 0),
                    member.line_number,
                    member.value,
                    getattr(member, 'base_type_id', None),
                    getattr(member, 'is_reference', False),
                    getattr(member, 'is_rvalue_reference', False),
                    getattr(member, 'is_volatile', False),
                    getattr(member, 'return_const', False)
                ))
                
                member_id = cursor.lastrowid
                
                # Add member implementation locations
                for impl_loc in member.implementation_locations:
                    conn.execute("""
                        INSERT OR REPLACE INTO member_implementation_locations (
                            member_id, file_path, line_number, column_number,
                            location_type, has_body, context
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        member_id,
                        impl_loc.file_path,
                        impl_loc.line_number,
                        impl_loc.column_number,
                        impl_loc.location_type.value,
                        impl_loc.has_body,
                        impl_loc.context
                    ))
            
            return entity_id
    
    def process_method_implementations(self):
        """
        Post-processing step to match method implementation function entities 
        to their corresponding class members and move locations
        """
        with self.connect() as conn:
            # Find all method implementation functions (marked with is_method=True)
            method_impls = conn.execute("""
                SELECT e.id as entity_id, e.canonical_name, 
                       l.file_path, l.line_number, l.column_number, 
                       l.location_type, l.has_body, l.context
                FROM entities e 
                JOIN entity_locations l ON e.id = l.entity_id
                WHERE e.entity_type = 'function' 
                AND e.is_method = 1 
                AND e.canonical_name LIKE '%::%'
            """).fetchall()
            
            for impl_row in method_impls:
                canonical_name = impl_row['canonical_name']
                
                # Parse class name and method name
                if '::' in canonical_name:
                    # Handle cases like "ork::lev2::GfxMaterial::BeginBlock"
                    parts = canonical_name.rsplit('::', 1)
                    if len(parts) == 2:
                        class_canonical, method_name = parts
                        
                        # Find the class entity
                        class_row = conn.execute(
                            "SELECT id FROM entities WHERE canonical_name = ? AND entity_type IN ('class', 'struct')",
                            (class_canonical,)
                        ).fetchone()
                        
                        if class_row:
                            # Find the corresponding member in the class by name only for now
                            # TODO: Match by signature to handle overloads properly
                            member_row = conn.execute("""
                                SELECT id FROM entity_members 
                                WHERE entity_id = ? AND name = ? AND member_type = 'method'
                            """, (class_row['id'], method_name)).fetchone()
                            
                            if member_row:
                                # Move the implementation location to the member
                                conn.execute("""
                                    INSERT OR REPLACE INTO member_implementation_locations (
                                        member_id, file_path, line_number, column_number,
                                        location_type, has_body, context
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    member_row['id'],
                                    impl_row['file_path'],
                                    impl_row['line_number'],
                                    impl_row['column_number'],
                                    impl_row['location_type'],
                                    impl_row['has_body'],
                                    impl_row['context']
                                ))
                                
                                # Remove the method implementation function entity
                                conn.execute("DELETE FROM entities WHERE id = ?", (impl_row['entity_id'],))
                                print(f"Moved method implementation: {canonical_name}")
    
    def get_entity(self, canonical_name: str) -> Optional[Entity]:
        """Get a single entity by its canonical name"""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM entities WHERE canonical_name = ?",
                (canonical_name,)
            ).fetchone()
            
            if row:
                return self._row_to_entity(row, conn)
            return None
    
    def search_entities_by_canonical_name(self, 
                                         entity_type: Optional[str] = None,
                                         canonical_name: Optional[str] = None,
                                         limit: Optional[int] = None) -> List[Entity]:
        """
        Search for entities by canonical name (exact match).
        """
        query = """
            SELECT DISTINCT e.* FROM entities e
            WHERE 1=1
        """
        params = []
        
        # Entity type filter
        if entity_type:
            if ',' in entity_type:
                types = [t.strip() for t in entity_type.split(',')]
                placeholders = ','.join(['?' for _ in types])
                query += f" AND e.entity_type IN ({placeholders})"
                params.extend(types)
            else:
                query += " AND e.entity_type = ?"
                params.append(entity_type)
        
        # Canonical name filter (exact match)
        if canonical_name:
            query += " AND e.canonical_name = ?"
            params.append(canonical_name)
        
        query += " ORDER BY e.namespace, e.short_name"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        entities = []
        with self.connect() as conn:
            for row in conn.execute(query, params):
                entity = self._row_to_entity(row, conn)
                entities.append(entity)
        
        return entities
    
    def search_entities(self, 
                       entity_type: Optional[str] = None,
                       name: Optional[str] = None,
                       namespace: Optional[str] = None,
                       pattern: Optional[str] = None,
                       limit: Optional[int] = None) -> List[Entity]:
        """
        Search for entities with various filters.
        Supports exact name match or pattern matching.
        """
        query = """
            SELECT DISTINCT e.* FROM entities e
            WHERE 1=1
        """
        params = []
        
        # Entity type filter (supports comma-separated types)
        if entity_type:
            if ',' in entity_type:
                types = [t.strip() for t in entity_type.split(',')]
                placeholders = ','.join(['?' for _ in types])
                query += f" AND e.entity_type IN ({placeholders})"
                params.extend(types)
            else:
                query += " AND e.entity_type = ?"
                params.append(entity_type)
        
        # Name filter (exact match)
        if name:
            query += " AND e.short_name = ?"
            params.append(name)
        # Pattern filter (wildcard match)
        elif pattern:
            query += " AND e.short_name LIKE ?"
            params.append(f"%{pattern}%")
        
        # Namespace filter
        if namespace:
            query += " AND e.namespace = ?"
            params.append(namespace)
        
        query += " ORDER BY e.namespace, e.short_name"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        entities = []
        with self.connect() as conn:
            for row in conn.execute(query, params):
                entity = self._row_to_entity(row, conn)
                entities.append(entity)
        
        return entities
    
    def _row_to_entity(self, row: sqlite3.Row, conn: sqlite3.Connection) -> Entity:
        """Convert database row to Entity object"""
        # Create entity with basic info
        entity = Entity(
            canonical_name=row['canonical_name'],
            short_name=row['short_name'],
            entity_type=EntityType(row['entity_type']),
            namespace=row['namespace']
        )
        
        # Set template info
        entity.is_template = bool(row['is_template'])
        entity.template_params = row['template_params']
        entity.is_template_specialization = bool(row['is_template_specialization'])
        entity.specialized_from = row['specialized_from']
        
        # Set class/struct info
        entity.is_abstract = bool(row['is_abstract'])
        entity.is_final = bool(row['is_final'])
        entity.is_pod = bool(row['is_pod'])
        if row['base_classes']:
            entity.base_classes = json.loads(row['base_classes'])
        
        # Set function info
        entity.return_type = row['return_type']
        if row['parameters']:
            params_data = json.loads(row['parameters'])
            entity.parameters = [
                Parameter(
                    name=p.get('name'),
                    param_type=p['type'],
                    default_value=p.get('default'),
                    is_const=p.get('is_const', False),
                    is_reference=p.get('is_reference', False),
                    is_pointer=p.get('is_pointer', False),
                    is_rvalue_ref=p.get('is_rvalue_ref', False)
                )
                for p in params_data
            ]
        
        entity.is_method = bool(row['is_method'])
        entity.is_virtual = bool(row['is_virtual'])
        entity.is_static = bool(row['is_static'])
        entity.is_const = bool(row['is_const'])
        entity.is_inline = bool(row['is_inline'])
        entity.is_constexpr = bool(row['is_constexpr'])
        entity.is_noexcept = bool(row['is_noexcept'])
        entity.is_deleted = bool(row['is_deleted'])
        entity.is_default = bool(row['is_default'])
        entity.is_override = bool(row['is_override'])
        entity.is_final_method = bool(row['is_final_method'])
        
        # Set enum info
        entity.underlying_type = row['underlying_type']
        entity.is_enum_class = bool(row['is_enum_class'])
        
        # Set typedef/alias info
        entity.aliased_type = row['aliased_type']
        entity.is_using_alias = bool(row['is_using_alias'])
        
        # Load locations
        for loc_row in conn.execute(
            """SELECT * FROM entity_locations 
               WHERE entity_id = ? 
               ORDER BY location_type DESC, line_number""",
            (row['id'],)
        ):
            location = Location(
                file_path=loc_row['file_path'],
                line_number=loc_row['line_number'],
                column_number=loc_row['column_number'],
                location_type=LocationType(loc_row['location_type']),
                has_body=bool(loc_row['has_body']),
                context=loc_row['context']
            )
            entity.locations.append(location)
        
        # Load members
        for mem_row in conn.execute(
            """SELECT * FROM entity_members 
               WHERE entity_id = ? 
               ORDER BY access_level, line_number""",
            (row['id'],)
        ):
            member = Member(
                name=mem_row['name'],
                member_type=MemberType(mem_row['member_type']),
                data_type=mem_row['data_type'],
                access_level=AccessLevel(mem_row['access_level']),
                is_static=bool(mem_row['is_static']),
                is_virtual=bool(mem_row['is_virtual']),
                is_const=bool(mem_row['is_const']),
                is_inline=bool(mem_row['is_inline']),
                is_explicit=bool(mem_row['is_explicit']),
                is_override=bool(mem_row['is_override']),
                is_final=bool(mem_row['is_final']),
                is_deleted=bool(mem_row['is_deleted']),
                is_default=bool(mem_row['is_default']),
                line_number=mem_row['line_number'],
                signature=mem_row['signature'],
                value=mem_row['value'],
                array_dimensions=mem_row['array_dimensions'],
                pointer_depth=mem_row['pointer_depth'] or 0,
                is_pure_virtual=bool(mem_row['is_pure_virtual']),
                is_noexcept=bool(mem_row['is_noexcept']),
                is_mutable=bool(mem_row['is_mutable']),
                is_constexpr=bool(mem_row['is_constexpr'])
            )
            
            # Load member implementation locations
            for impl_row in conn.execute(
                """SELECT * FROM member_implementation_locations 
                   WHERE member_id = ? 
                   ORDER BY line_number""",
                (mem_row['id'],)
            ):
                impl_location = Location(
                    file_path=impl_row['file_path'],
                    line_number=impl_row['line_number'],
                    column_number=impl_row['column_number'],
                    location_type=LocationType(impl_row['location_type']),
                    has_body=bool(impl_row['has_body']),
                    context=impl_row['context']
                )
                member.implementation_locations.append(impl_location)
            
            entity.members.append(member)
        
        return entity
    
    def delete_entity(self, canonical_name: str) -> bool:
        """Delete an entity and all its associated data"""
        with self.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM entities WHERE canonical_name = ?",
                (canonical_name,)
            )
            return cursor.rowcount > 0
    
    def clear_database(self):
        """Clear all data from the database"""
        with self.connect() as conn:
            conn.execute("DELETE FROM entity_references")
            conn.execute("DELETE FROM member_implementation_locations")
            conn.execute("DELETE FROM entity_members")
            conn.execute("DELETE FROM entity_locations")
            conn.execute("DELETE FROM entities")
            conn.execute("DELETE FROM files")
            conn.execute("DELETE FROM source_files")  # Also clear source file content
    
    def resolve_typedef(self, typedef_entity: Entity) -> Optional[Entity]:
        """
        Resolve a typedef/alias to its underlying entity.
        Returns the actual class/struct that the typedef points to.
        Handles template instantiation (e.g., Vector3<float> -> Vector3 template).
        """
        if typedef_entity.entity_type != EntityType.TYPEDEF:
            return typedef_entity  # Not a typedef, return as-is
        
        if not typedef_entity.aliased_type:
            return None  # No target type specified
        
        aliased_type = typedef_entity.aliased_type
        
        # Handle template instantiation (e.g., "Vector3<float>" -> "Vector3")
        base_type = aliased_type
        template_args = None
        if '<' in aliased_type:
            base_type = aliased_type[:aliased_type.index('<')]
            template_args = aliased_type[aliased_type.index('<'):]
        
        # Try to find the target entity
        # First try with namespace
        if typedef_entity.namespace:
            # Try in same namespace
            target = self.search_entities(name=base_type, 
                                         namespace=typedef_entity.namespace)
            if target:
                return target[0]
            
            # Try parent namespaces
            namespace_parts = typedef_entity.namespace.split('::')
            while namespace_parts:
                namespace_parts.pop()
                parent_ns = '::'.join(namespace_parts) if namespace_parts else None
                target = self.search_entities(name=base_type, 
                                             namespace=parent_ns)
                if target:
                    return target[0]
        
        # Try without namespace (global scope)
        target = self.search_entities(name=base_type)
        if target:
            return target[0]
        
        return None
    
    def find_derived_classes(self, base_class_name: str) -> List:
        """
        Find all classes/structs that derive from the given base class
        
        Args:
            base_class_name: Name of the base class (can be short name or canonical)
        
        Returns:
            List of entities that inherit from the base class
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Search for entities that have this class in their base_classes
            # We need to handle both short names and fully qualified names
            results = []
            
            # Get all entities with base classes
            query = """
                SELECT * FROM entities 
                WHERE base_classes IS NOT NULL AND base_classes != '[]'
                AND (entity_type = 'class' OR entity_type = 'struct')
            """
            
            for row in conn.execute(query):
                base_classes = json.loads(row['base_classes']) if row['base_classes'] else []
                
                # Check if any base class matches our search
                for base in base_classes:
                    # Handle different naming formats
                    # base might be "GfxMaterial" or "ork::lev2::GfxMaterial"
                    base_short = base.split('::')[-1] if '::' in base else base
                    search_short = base_class_name.split('::')[-1] if '::' in base_class_name else base_class_name
                    
                    if base == base_class_name or base_short == search_short:
                        entity = self._row_to_entity(row, conn)
                        results.append(entity)
                        break
            
            return results
    
    def get_effective_members(self, entity: Entity) -> List:
        """
        Get the effective members of an entity, resolving through typedefs if necessary.
        """
        # If it's a typedef, resolve to the underlying type
        if entity.entity_type == EntityType.TYPEDEF:
            resolved = self.resolve_typedef(entity)
            if resolved:
                return resolved.members
        
        return entity.members
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.connect() as conn:
            stats = {}
            
            # Count entities by type
            for row in conn.execute(
                """SELECT entity_type, COUNT(*) as count 
                   FROM entities 
                   GROUP BY entity_type"""
            ):
                stats[f"entities_{row['entity_type']}"] = row['count']
            
            # Total counts
            stats['total_entities'] = conn.execute(
                "SELECT COUNT(*) FROM entities"
            ).fetchone()[0]
            
            stats['total_locations'] = conn.execute(
                "SELECT COUNT(*) FROM entity_locations"
            ).fetchone()[0]
            
            stats['total_members'] = conn.execute(
                "SELECT COUNT(*) FROM entity_members"
            ).fetchone()[0]
            
            stats['total_member_implementations'] = conn.execute(
                "SELECT COUNT(*) FROM member_implementation_locations"
            ).fetchone()[0]
            
            # File statistics from source_files table
            stats['total_files'] = conn.execute(
                "SELECT COUNT(*) FROM source_files"
            ).fetchone()[0]
            
            stats['files_with_preprocessed'] = conn.execute(
                "SELECT COUNT(*) FROM source_files WHERE preprocessed_source IS NOT NULL"
            ).fetchone()[0]
            
            total_size = conn.execute(
                "SELECT SUM(file_size) FROM source_files"
            ).fetchone()[0] or 0
            stats['total_source_size_mb'] = round(total_size / (1024 * 1024), 2) if total_size else 0
            
            # File breakdown by extension
            for row in conn.execute(
                """SELECT file_extension, COUNT(*) as count, SUM(file_size) as total_size
                   FROM source_files 
                   WHERE file_extension IS NOT NULL
                   GROUP BY file_extension
                   ORDER BY count DESC"""
            ):
                ext = row['file_extension'].lstrip('.') if row['file_extension'] else 'no_ext'
                stats[f"files_{ext}"] = row['count']
                if row['total_size']:
                    stats[f"files_{ext}_size_mb"] = round(row['total_size'] / (1024 * 1024), 2)
            
            # Template statistics
            stats['template_entities'] = conn.execute(
                "SELECT COUNT(*) FROM entities WHERE is_template = 1"
            ).fetchone()[0]
            
            return stats
    
    def add_file(self, file_path: Union[str, Path]) -> str:
        """
        Add or update a file record in the database.
        This is a convenience method that gets the file's modification time.
        Returns the file hash.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)
        
        # Get file modification time
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            mtime = time.time()
        
        return self.update_file_record(file_path, mtime)
    
    def update_file_record(self, file_path: str, mtime: float) -> str:
        """
        Update file tracking record.
        Returns the file hash.
        """
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        with self.connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO files (file_path, last_modified, file_hash)
                VALUES (?, ?, ?)
            """, (file_path, mtime, file_hash))
        
        return file_hash
    
    def is_file_modified(self, file_path: str, mtime: float) -> bool:
        """Check if file has been modified since last parse"""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT last_modified FROM files WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            
            if not row:
                return True  # File not in database, needs parsing
            
            return mtime > row['last_modified']
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file contents"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def store_source_file(self, file_path: Union[str, Path], raw_source: str, 
                         preprocessed_source: Optional[str] = None) -> int:
        """
        Store source file content in the database.
        
        Args:
            file_path: Absolute path to the file
            raw_source: Raw source code content
            preprocessed_source: Preprocessed source code content (optional)
        
        Returns:
            File ID in database
        """
        file_path = str(file_path)
        file_name = Path(file_path).name
        file_extension = Path(file_path).suffix
        file_size = len(raw_source.encode('utf-8'))
        
        # Try to calculate relative path if possible
        relative_path = None
        try:
            # Try to make it relative to current working directory
            relative_path = str(Path(file_path).relative_to(Path.cwd()))
        except ValueError:
            # If that fails, just use the filename
            relative_path = file_name
        
        with self.connect() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO source_files (
                    file_path, relative_path, file_name, file_extension, 
                    file_size, raw_source, preprocessed_source, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (file_path, relative_path, file_name, file_extension, 
                  file_size, raw_source, preprocessed_source))
            return cursor.lastrowid
    
    def get_source_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get source file content by exact file path.
        
        Args:
            file_path: Exact file path to search for
            
        Returns:
            Dictionary with file information and content, or None if not found
        """
        with self.connect() as conn:
            row = conn.execute("""
                SELECT * FROM source_files WHERE file_path = ?
            """, (file_path,)).fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_source_file_by_name(self, file_name: str) -> List[Dict[str, Any]]:
        """
        Get source files by filename (may return multiple matches).
        
        Args:
            file_name: Just the filename to search for
            
        Returns:
            List of dictionaries with file information and content
        """
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT * FROM source_files WHERE file_name = ?
                ORDER BY file_path
            """, (file_name,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def search_source_files(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Search for source files by pattern (searches path, relative_path, and filename).
        
        Args:
            pattern: Pattern to search for (uses SQL LIKE with % wildcards)
            
        Returns:
            List of dictionaries with file information and content
        """
        search_pattern = f"%{pattern}%"
        
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT * FROM source_files 
                WHERE file_path LIKE ? OR relative_path LIKE ? OR file_name LIKE ?
                ORDER BY file_path
            """, (search_pattern, search_pattern, search_pattern)).fetchall()
            
            return [dict(row) for row in rows]
    
    def list_source_files(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all source files in the database.
        
        Args:
            limit: Optional limit on number of files returned
            
        Returns:
            List of dictionaries with file information (without content for performance)
        """
        query = """
            SELECT id, file_path, relative_path, file_name, file_extension, 
                   file_size, created_at, updated_at 
            FROM source_files 
            ORDER BY file_path
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.connect() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]
    
    def get_raw_source(self, file_path: str) -> Optional[str]:
        """Get just the raw source code for a file."""
        with self.connect() as conn:
            row = conn.execute("""
                SELECT raw_source FROM source_files WHERE file_path = ?
            """, (file_path,)).fetchone()
            
            return row['raw_source'] if row else None
    
    def get_preprocessed_source(self, file_path: str) -> Optional[str]:
        """Get just the preprocessed source code for a file."""
        with self.connect() as conn:
            row = conn.execute("""
                SELECT preprocessed_source FROM source_files WHERE file_path = ?
            """, (file_path,)).fetchone()
            
            return row['preprocessed_source'] if row else None
    
    def build_from_directory(self, directory: Path, extensions: Optional[List[str]] = None,
                           defines: Optional[List[str]] = None,
                           defines_preset: Optional[str] = None, include_paths: Optional[List[Path]] = None):
        """
        Build database from all C++ files in a directory.
        
        Args:
            directory: Directory to scan
            extensions: File extensions to include (default: common C++ extensions)
            defines: List of -D defines for preprocessor
            defines_preset: Preset set of defines ('macos', 'linux', 'minimal')
            include_paths: List of include paths for preprocessor
        """
        from obt.cpp_parser_descent import RecursiveDescentCppParser
        
        if not extensions:
            extensions = ['.cpp', '.cc', '.cxx', '.c++', '.C', '.c',
                         '.hpp', '.h', '.hh', '.hxx', '.h++', '.H']
        
        # Create parser (descent parser doesn't need these preprocessor args)
        parser = RecursiveDescentCppParser()
        
        # Find all C++ files
        cpp_files = []
        for ext in extensions:
            cpp_files.extend(directory.rglob(f'*{ext}'))
        
        # Parse and add entities
        for file_path in cpp_files:
            try:
                # Check if file needs reparsing
                mtime = os.path.getmtime(file_path)
                if not self.is_file_modified(str(file_path), mtime):
                    continue
                
                # Read raw source
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_source = f.read()
                
                # Parse file (this may preprocess the source internally)
                entities = parser.parse_file(file_path)
                
                # Get preprocessed source
                preprocessed_source = None
                if hasattr(parser, 'get_last_preprocessed_source'):
                    preprocessed_source = parser.get_last_preprocessed_source()
                
                # Store source file content
                self.store_source_file(str(file_path), raw_source, preprocessed_source)
                
                # Add entities to database
                for entity in entities:
                    self.add_entity(entity)
                
                # Update file record
                self.update_file_record(str(file_path), mtime)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")