"""
C++ Entity Search Module for V2 Database
Provides common search functionality used by both obt and ork search commands
"""

import re
from typing import List, Dict, Any, Optional
from obt.cpp_database_v2 import CppDatabaseV2
from obt.cpp_entities_v2 import Entity, EntityType

def build_search_parameters(args) -> tuple[Dict[str, Any], List[str]]:
    """
    Build search parameters from command line arguments
    Returns: (search_kwargs, function_subtypes)
    """
    search_kwargs = {}
    function_subtypes = []
    
    # Entity type filter with function sub-types
    if args.types:
        # Check for special 'files' type
        if args.types.lower() == 'files':
            # Signal to use file listing mode
            search_kwargs['files_mode'] = True
            return search_kwargs, []
        
        # Map user-friendly names to EntityType values
        type_map = {
            'class': EntityType.CLASS.value,
            'struct': EntityType.STRUCT.value,
            'enum': EntityType.ENUM.value,
            'function': EntityType.FUNCTION.value,  # Free functions only
            'memberfn': 'memberfn',  # Member functions
            'staticfn': 'staticfn',  # Static member functions
            'allfn': EntityType.FUNCTION.value,  # All functions
            'typedef': EntityType.TYPEDEF.value,
            'alias': 'alias',  # Using aliases
            'union': EntityType.UNION.value,
            'namespace': EntityType.NAMESPACE.value,
            'files': 'files',  # Special type for file listing
        }
        
        types = []
        for t in args.types.split(','):
            t = t.strip().lower()
            if t in type_map:
                if t in ['memberfn', 'staticfn', 'function', 'allfn']:
                    # Track function subtypes for later filtering
                    function_subtypes.append(t)
                    if t == 'allfn' or len(function_subtypes) > 1:
                        types.append(EntityType.FUNCTION.value)
                    else:
                        types.append(EntityType.FUNCTION.value)
                elif t == 'alias':
                    types.append(EntityType.TYPEDEF.value)
                else:
                    types.append(type_map[t])
            else:
                from obt.deco import Deco
                deco = Deco()
                print(f"{deco.red(f'Unknown type: {t}')}")
                import sys
                sys.exit(1)
        
        if len(types) == 1:
            search_kwargs['entity_type'] = types[0]
        elif types:
            # Remove duplicates
            types = list(set(types))
            search_kwargs['entity_type'] = ','.join(types)
    
    # Name pattern
    if args.pattern:
        if hasattr(args, 'exact') and args.exact:
            search_kwargs['name'] = args.pattern
        else:
            search_kwargs['pattern'] = args.pattern
    
    # Namespace filter
    if hasattr(args, 'namespace') and args.namespace:
        search_kwargs['namespace'] = args.namespace
    
    # Limit (0 means unlimited, don't pass it to search)
    if hasattr(args, 'limit') and args.limit > 0:
        search_kwargs['limit'] = args.limit
    
    return search_kwargs, function_subtypes

def filter_results(results: List[Entity], args, function_subtypes: List[str]) -> List[Entity]:
    """
    Apply additional filtering to search results
    """
    # Filter by function subtype if specified
    if function_subtypes and 'allfn' not in function_subtypes:
        filtered = []
        for entity in results:
            if entity.entity_type == EntityType.FUNCTION:
                if 'function' in function_subtypes and not entity.is_method:
                    filtered.append(entity)
                elif 'memberfn' in function_subtypes and entity.is_method and not entity.is_static:
                    filtered.append(entity)
                elif 'staticfn' in function_subtypes and entity.is_method and entity.is_static:
                    filtered.append(entity)
            else:
                # Non-function entities pass through
                filtered.append(entity)
        results = filtered
    
    # Filter for aliases if specified
    if hasattr(args, 'types') and args.types and 'alias' in args.types:
        results = [e for e in results if e.entity_type == EntityType.TYPEDEF and e.is_using_alias]
    
    # Additional filtering based on args
    if hasattr(args, 'templates_only') and args.templates_only:
        results = [e for e in results if e.is_template]
    
    if hasattr(args, 'derived_only') and args.derived_only:
        results = [e for e in results if e.base_classes]
    
    # Case-insensitive filtering if pattern provided and case-insensitive mode
    if hasattr(args, 'pattern') and args.pattern and \
       hasattr(args, 'case_insensitive') and args.case_insensitive and \
       not (hasattr(args, 'exact') and args.exact):
        pattern = re.compile(args.pattern, re.IGNORECASE)
        results = [e for e in results if pattern.search(e.short_name)]
    
    return results

def search_database(db: CppDatabaseV2, args):
    """
    Perform a search on the database with given arguments
    Returns either List[Entity] or List[Dict] for files mode
    """
    # Build search parameters
    search_kwargs, function_subtypes = build_search_parameters(args)
    
    # Check for files mode
    if search_kwargs.get('files_mode'):
        # Search for files instead of entities
        if hasattr(args, 'pattern') and args.pattern:
            # Search files by pattern
            return db.search_source_files(args.pattern)
        else:
            # List all files
            limit = getattr(args, 'limit', None)
            return db.list_source_files(limit)
    
    # Special case: searching for derived classes
    if hasattr(args, 'derived_from') and args.derived_from:
        results = db.find_derived_classes(args.derived_from)
    else:
        # Remove files_mode from kwargs if present
        search_kwargs.pop('files_mode', None)
        
        # Perform search
        results = db.search_entities(**search_kwargs)
        
        # Apply additional filtering
        results = filter_results(results, args, function_subtypes)
    
    return results

def format_json_results(results: List[Entity]) -> List[Dict]:
    """
    Format search results as JSON-serializable dictionaries
    """
    json_results = []
    for entity in results:
        json_obj = {
            'name': entity.short_name,
            'canonical_name': entity.canonical_name,
            'type': entity.entity_type.value,
            'namespace': entity.namespace,
            'is_template': entity.is_template,
            'template_params': entity.template_params,
            'locations': [
                {
                    'file': loc.file_path,
                    'line': loc.line_number,
                    'type': loc.location_type.value
                }
                for loc in entity.locations
            ]
        }
        
        if entity.entity_type == EntityType.TYPEDEF:
            json_obj['aliased_type'] = entity.aliased_type
        
        if entity.base_classes:
            json_obj['base_classes'] = entity.base_classes
        
        json_results.append(json_obj)
    
    return json_results