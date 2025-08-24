"""
Unified Type System for C++ Database
Provides orthogonal type composition and flyweight type registry
"""
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import sqlite3
from pathlib import Path

@dataclass
class TypeInfo:
    """Complete type metadata for orthogonal composition"""
    base_type: str = ""                    # "orkmap<const rend_shader*, TriangleMetaBucket*>"
    
    # Qualifiers applied to type
    is_const: bool = False                 # const T
    is_volatile: bool = False              # volatile T  
    is_constexpr: bool = False             # constexpr T
    is_mutable: bool = False               # mutable T
    
    # Pointer/reference semantics
    pointer_depth: int = 0                 # 0=value, 1=*, 2=**, etc.
    is_reference: bool = False             # T&
    is_rvalue_reference: bool = False      # T&&
    
    # Array information
    array_dimensions: List[str] = field(default_factory=list)  # ["10", "kAABUFTILES"]
    
    # Type categorization
    is_primitive: bool = False             # int, float, char, etc.
    is_template: bool = False              # Has template parameters
    namespace: Optional[str] = None        # "ork::lev2"
    
    def get_canonical_form(self) -> str:
        """Get canonical form for flyweight deduplication"""
        # Just the base type without modifiers for flyweight
        return self.base_type
    
    def get_base_name(self) -> str:
        """Extract base name from type (e.g., 'orkmap' from 'orkmap<...>')"""
        if '<' in self.base_type:
            return self.base_type[:self.base_type.index('<')]
        return self.base_type
    
    def get_template_args(self) -> Optional[str]:
        """Extract template arguments if present"""
        if '<' in self.base_type and '>' in self.base_type:
            start = self.base_type.index('<')
            # Find matching closing bracket
            depth = 0
            for i, char in enumerate(self.base_type[start:], start):
                if char == '<':
                    depth += 1
                elif char == '>':
                    depth -= 1
                    if depth == 0:
                        return self.base_type[start:i+1]
        return None


def compose_type(type_info: TypeInfo) -> str:
    """
    THE single authoritative type composition function.
    Composes complete type string from TypeInfo metadata.
    
    Examples:
        int -> "int"
        const int& -> "const int&"
        const orkmap<K,V>*& -> "const orkmap<K,V>*&"
        int[10][20] -> "int[10][20]"
    """
    parts = []
    
    # Leading qualifiers (order matters for C++)
    qualifiers = []
    if type_info.is_constexpr:
        qualifiers.append("constexpr")
    if type_info.is_mutable:
        qualifiers.append("mutable")
    if type_info.is_const:
        qualifiers.append("const")
    if type_info.is_volatile:
        qualifiers.append("volatile")
    
    if qualifiers:
        parts.extend(qualifiers)
    
    # Base type
    parts.append(type_info.base_type)
    
    # Pointer indirection
    if type_info.pointer_depth > 0:
        parts.append("*" * type_info.pointer_depth)
    
    # Reference (mutually exclusive)
    if type_info.is_rvalue_reference:
        parts.append("&&")
    elif type_info.is_reference:
        parts.append("&")
    
    # Join with appropriate spacing
    result = " ".join(parts[:len(qualifiers)+1])  # Qualifiers + base type
    if type_info.pointer_depth > 0 or type_info.is_reference or type_info.is_rvalue_reference:
        # Add pointer/reference without space
        result = parts[0] if len(parts) == 1 else " ".join(parts[:len(qualifiers)+1])
        for i in range(len(qualifiers)+1, len(parts)):
            result += parts[i]
    
    # Array dimensions (always at the end)
    if type_info.array_dimensions:
        for dim in type_info.array_dimensions:
            result += f"[{dim}]"
    
    return result


class TypeRegistry:
    """Flyweight registry for all C++ types"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._cache: Dict[str, int] = {}  # type_hash -> type_id cache
        self._reverse_cache: Dict[int, str] = {}  # type_id -> canonical_form cache
    
    def connect(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path, timeout=30.0)
    
    def get_or_create_type(self, type_info: TypeInfo) -> int:
        """Get existing type_id or create new flyweight entry"""
        canonical = type_info.get_canonical_form()
        type_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        
        # Check cache first
        if type_hash in self._cache:
            return self._cache[type_hash]
        
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            
            # Check if exists in database
            row = conn.execute(
                "SELECT id FROM canonical_types WHERE type_hash = ?", 
                (type_hash,)
            ).fetchone()
            
            if row:
                type_id = row['id']
            else:
                # Create new flyweight entry (using INSERT OR IGNORE to handle race conditions)
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO canonical_types (
                        type_hash, canonical_form, base_name, template_args,
                        is_primitive, is_template, namespace
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    type_hash, 
                    canonical,
                    type_info.get_base_name(),
                    type_info.get_template_args(),
                    type_info.is_primitive,
                    type_info.is_template,
                    type_info.namespace
                ))
                
                if cursor.rowcount == 0:
                    # Another process inserted it, fetch the existing one
                    row = conn.execute(
                        "SELECT id FROM canonical_types WHERE type_hash = ?", 
                        (type_hash,)
                    ).fetchone()
                    type_id = row['id'] if row else None
                else:
                    type_id = cursor.lastrowid
                
                conn.commit()
            
            # Update caches
            self._cache[type_hash] = type_id
            self._reverse_cache[type_id] = canonical
            return type_id
    
    def get_canonical_form(self, type_id: int) -> Optional[str]:
        """Get canonical form string from type_id"""
        # Check cache first
        if type_id in self._reverse_cache:
            return self._reverse_cache[type_id]
        
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT canonical_form FROM canonical_types WHERE id = ?",
                (type_id,)
            ).fetchone()
            
            if row:
                canonical = row['canonical_form']
                self._reverse_cache[type_id] = canonical
                return canonical
        
        return None
    
    def compose_type_with_modifiers(self, type_id: int, modifiers: Dict[str, Any]) -> str:
        """
        Compose complete type string from flyweight type_id and modifiers.
        
        Args:
            type_id: Reference to canonical_types.id
            modifiers: Dictionary with keys like 'is_const', 'is_reference', 'pointer_depth', etc.
        """
        canonical_form = self.get_canonical_form(type_id)
        if not canonical_form:
            return "unknown"
        
        # Build TypeInfo from canonical form and modifiers
        type_info = TypeInfo(
            base_type=canonical_form,
            is_const=modifiers.get('is_const', False),
            is_volatile=modifiers.get('is_volatile', False),
            is_constexpr=modifiers.get('is_constexpr', False),
            is_mutable=modifiers.get('is_mutable', False),
            pointer_depth=modifiers.get('pointer_depth', 0),
            is_reference=modifiers.get('is_reference', False),
            is_rvalue_reference=modifiers.get('is_rvalue_reference', False),
            array_dimensions=modifiers.get('array_dimensions', [])
        )
        
        return compose_type(type_info)
    
    def add_type_alias(self, alias_name: str, target_type_id: int, 
                      namespace: Optional[str] = None, is_using: bool = False,
                      entity_id: Optional[int] = None):
        """Add a typedef or using alias mapping"""
        with self.connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO type_aliases (
                        alias_name, target_type_id, namespace, 
                        is_using_alias, entity_id
                    ) VALUES (?, ?, ?, ?, ?)
                """, (alias_name, target_type_id, namespace, is_using, entity_id))
                conn.commit()
            except sqlite3.IntegrityError:
                # Alias already exists, update it
                conn.execute("""
                    UPDATE type_aliases 
                    SET target_type_id = ?, is_using_alias = ?, entity_id = ?
                    WHERE alias_name = ? AND 
                          (namespace = ? OR (namespace IS NULL AND ? IS NULL))
                """, (target_type_id, is_using, entity_id, alias_name, namespace, namespace))
                conn.commit()
    
    def resolve_alias_chain(self, alias_name: str, namespace: Optional[str] = None) -> Optional[int]:
        """
        Resolve typedef/alias chain to canonical type_id.
        Handles chains like: MyType -> Vector3f -> Vector3<float> -> canonical_id
        """
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            visited = set()  # Prevent circular references
            current_name = alias_name
            
            while current_name and current_name not in visited:
                visited.add(current_name)
                
                # First check if it's an alias
                row = conn.execute("""
                    SELECT target_type_id FROM type_aliases 
                    WHERE alias_name = ? AND 
                          (namespace = ? OR namespace IS NULL)
                    ORDER BY namespace DESC LIMIT 1
                """, (current_name, namespace)).fetchone()
                
                if row:
                    return row['target_type_id']
                
                # Check if it's already a canonical type
                row = conn.execute("""
                    SELECT id FROM canonical_types 
                    WHERE canonical_form = ? OR base_name = ?
                    LIMIT 1
                """, (current_name, current_name)).fetchone()
                
                if row:
                    return row['id']
                
                # Not found
                break
            
            return None
    
    def get_type_stats(self) -> Dict[str, int]:
        """Get statistics about the type registry"""
        with self.connect() as conn:
            stats = {}
            
            stats['total_canonical_types'] = conn.execute(
                "SELECT COUNT(*) FROM canonical_types"
            ).fetchone()[0]
            
            stats['total_aliases'] = conn.execute(
                "SELECT COUNT(*) FROM type_aliases"
            ).fetchone()[0]
            
            stats['template_types'] = conn.execute(
                "SELECT COUNT(*) FROM canonical_types WHERE is_template = 1"
            ).fetchone()[0]
            
            stats['primitive_types'] = conn.execute(
                "SELECT COUNT(*) FROM canonical_types WHERE is_primitive = 1"
            ).fetchone()[0]
            
            return stats


# Primitive type detection helper
PRIMITIVE_TYPES = {
    'void', 'bool', 'char', 'signed char', 'unsigned char',
    'short', 'unsigned short', 'int', 'unsigned int', 
    'long', 'unsigned long', 'long long', 'unsigned long long',
    'float', 'double', 'long double',
    'size_t', 'ssize_t', 'ptrdiff_t', 'intptr_t', 'uintptr_t',
    'int8_t', 'uint8_t', 'int16_t', 'uint16_t', 
    'int32_t', 'uint32_t', 'int64_t', 'uint64_t',
    'wchar_t', 'char16_t', 'char32_t', 'char8_t'
}

def is_primitive_type(type_name: str) -> bool:
    """Check if a type is a primitive/built-in type"""
    # Remove qualifiers and check base type
    base = type_name.replace('const', '').replace('volatile', '').strip()
    return base in PRIMITIVE_TYPES