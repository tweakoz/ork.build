"""
Shared utilities for C++ entity searching
"""
from typing import List
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import Entity

def find_entities_by_name(db: CppDatabaseV2, name: str, 
                          entity_types: List[str] = None) -> List[Entity]:
    """
    Find entities by name, handling both short names and canonical names.
    
    Args:
        db: Database instance
        name: Entity name (short or canonical)
        entity_types: List of entity types to search (default: ['class', 'struct'])
    
    Returns:
        List of matching entities
    """
    if entity_types is None:
        entity_types = ['class', 'struct']
    
    entities = []
    
    # Check if this is a fully qualified name (contains ::)
    if '::' in name:
        # Search by canonical name for fully qualified names
        for entity_type in entity_types:
            found = db.search_entities_by_canonical_name(
                entity_type=entity_type, 
                canonical_name=name
            )
            entities.extend(found)
    else:
        # Search by short name for simple names
        for entity_type in entity_types:
            found = db.search_entities(
                entity_type=entity_type, 
                name=name
            )
            entities.extend(found)
    
    return entities

def group_entities_by_namespace(entities: List[Entity]) -> dict:
    """
    Group entities by their namespace.
    
    Args:
        entities: List of entities to group
    
    Returns:
        Dictionary mapping namespace to list of entities
    """
    entities_by_ns = {}
    for entity in entities:
        ns = entity.namespace or "-"
        if ns not in entities_by_ns:
            entities_by_ns[ns] = []
        entities_by_ns[ns].append(entity)
    return entities_by_ns