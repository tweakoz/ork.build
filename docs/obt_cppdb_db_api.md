# C++ Database V2 API Documentation

## Overview

The `CppDatabaseV2` class provides a comprehensive API for storing, querying, and managing C++ code entities in a SQLite database. This document details all public methods, their signatures, parameters, return types, and usage examples.

## Class: `CppDatabaseV2`

Located in: `obt.cpp_database_v2`

### Constructor

```python
def __init__(self, db_path: str)
```

**Purpose**: Initialize a new database connection and create schema if needed.

**Parameters**:
- `db_path` (str): Path to the SQLite database file

**Example**:
```python
from obt.cpp_database_v2 import CppDatabaseV2
db = CppDatabaseV2("/path/to/database.db")
```

## Core Entity Management

### `add_entity`

```python
def add_entity(self, entity: Entity) -> int
```

**Purpose**: Add or update an entity and all its associated data (locations, members, implementations).

**Parameters**:
- `entity` (Entity): The entity object to add/update

**Returns**: 
- `int`: The entity ID in the database

**Behavior**:
- If entity exists (by canonical_name), updates it
- Adds all locations with INSERT OR IGNORE (prevents duplicates)
- Adds all members with INSERT OR REPLACE (updates existing)
- Adds member implementation locations

**Example**:
```python
entity = Entity(
    canonical_name="ork::lev2::Context",
    short_name="Context",
    entity_type=EntityType.CLASS,
    namespace="ork::lev2"
)
entity_id = db.add_entity(entity)
```

### `get_entity`

```python
def get_entity(self, canonical_name: str) -> Optional[Entity]
```

**Purpose**: Retrieve a single entity by its canonical name.

**Parameters**:
- `canonical_name` (str): Full canonical name of the entity

**Returns**:
- `Optional[Entity]`: Entity object if found, None otherwise

**Example**:
```python
entity = db.get_entity("ork::lev2::Context")
if entity:
    print(f"Found: {entity.short_name}")
```

### `delete_entity`

```python
def delete_entity(self, canonical_name: str) -> bool
```

**Purpose**: Delete an entity and all its associated data (cascades to locations, members, etc.).

**Parameters**:
- `canonical_name` (str): Full canonical name of the entity to delete

**Returns**:
- `bool`: True if entity was deleted, False if not found

**Example**:
```python
deleted = db.delete_entity("MyNamespace::MyClass")
```

## Search Methods

### `search_entities`

```python
def search_entities(self, 
                   entity_type: Optional[str] = None,
                   name: Optional[str] = None,
                   namespace: Optional[str] = None,
                   pattern: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Entity]
```

**Purpose**: Search for entities with various filters. Primary search method for most use cases.

**Parameters**:
- `entity_type` (Optional[str]): Entity type(s) to filter. Supports comma-separated values: "CLASS,STRUCT"
- `name` (Optional[str]): Exact short name to match
- `namespace` (Optional[str]): Namespace to filter by
- `pattern` (Optional[str]): Pattern for wildcard matching (uses SQL LIKE with %)
- `limit` (Optional[int]): Maximum number of results

**Returns**:
- `List[Entity]`: List of matching entities

**Notes**:
- `name` and `pattern` are mutually exclusive - `name` takes precedence for exact matching
- Results are ordered by namespace, then short_name

**Examples**:
```python
# Search for all classes
classes = db.search_entities(entity_type="CLASS")

# Search for classes and structs
entities = db.search_entities(entity_type="CLASS,STRUCT")

# Search by exact name
context = db.search_entities(name="Context")

# Search by pattern
materials = db.search_entities(pattern="Material")

# Search in specific namespace
lev2_entities = db.search_entities(namespace="ork::lev2")

# Combined search with limit
results = db.search_entities(
    entity_type="CLASS",
    namespace="ork::lev2",
    pattern="Gfx",
    limit=10
)
```

### `search_entities_by_canonical_name`

```python
def search_entities_by_canonical_name(self, 
                                     entity_type: Optional[str] = None,
                                     canonical_name: Optional[str] = None,
                                     limit: Optional[int] = None) -> List[Entity]
```

**Purpose**: Search for entities by their full canonical name (exact match).

**Parameters**:
- `entity_type` (Optional[str]): Entity type(s) to filter. Supports comma-separated values
- `canonical_name` (Optional[str]): Exact canonical name to match
- `limit` (Optional[int]): Maximum number of results

**Returns**:
- `List[Entity]`: List of matching entities

**Example**:
```python
# Find specific class by canonical name
entity = db.search_entities_by_canonical_name(
    canonical_name="ork::lev2::Context"
)

# Find all functions with limit
functions = db.search_entities_by_canonical_name(
    entity_type="FUNCTION",
    limit=100
)
```

## Relationship and Resolution Methods

### `resolve_typedef`

```python
def resolve_typedef(self, typedef_entity: Entity) -> Optional[Entity]
```

**Purpose**: Resolve a typedef/alias to its underlying entity. Handles template instantiation.

**Parameters**:
- `typedef_entity` (Entity): The typedef entity to resolve

**Returns**:
- `Optional[Entity]`: The resolved entity, or None if not found

**Behavior**:
- Returns input if not a typedef
- Handles template instantiation (e.g., "Vector3<float>" → "Vector3")
- Searches in same namespace first, then parent namespaces

**Example**:
```python
typedef = db.get_entity("fvec3")
if typedef:
    actual = db.resolve_typedef(typedef)
    if actual:
        print(f"fvec3 is actually {actual.canonical_name}")
```

### `find_derived_classes`

```python
def find_derived_classes(self, base_class_name: str) -> List[Entity]
```

**Purpose**: Find all classes/structs that derive from the given base class.

**Parameters**:
- `base_class_name` (str): Name of base class (short or canonical)

**Returns**:
- `List[Entity]`: List of entities that inherit from the base class

**Example**:
```python
drawables = db.find_derived_classes("Drawable")
for derived in drawables:
    print(f"{derived.canonical_name} inherits from Drawable")
```

### `get_effective_members`

```python
def get_effective_members(self, entity: Entity) -> List[Member]
```

**Purpose**: Get members of an entity, resolving through typedefs if necessary.

**Parameters**:
- `entity` (Entity): The entity to get members for

**Returns**:
- `List[Member]`: List of members (resolved through typedef if applicable)

**Example**:
```python
entity = db.get_entity("fvec3")  # typedef
members = db.get_effective_members(entity)  # Gets Vector3 members
```

## Source File Management

### `store_source_file`

```python
def store_source_file(self, file_path: Union[str, Path], raw_source: str, 
                     preprocessed_source: Optional[str] = None) -> int
```

**Purpose**: Store complete source file content in the database.

**Parameters**:
- `file_path` (Union[str, Path]): Absolute path to the file
- `raw_source` (str): Raw source code content
- `preprocessed_source` (Optional[str]): Preprocessed source code

**Returns**:
- `int`: File ID in database

**Example**:
```python
with open("myfile.cpp", "r") as f:
    raw = f.read()
file_id = db.store_source_file("/path/to/myfile.cpp", raw, preprocessed)
```

### `get_source_file`

```python
def get_source_file(self, file_path: str) -> Optional[Dict[str, Any]]
```

**Purpose**: Get complete source file information by exact path.

**Parameters**:
- `file_path` (str): Exact file path to search for

**Returns**:
- `Optional[Dict[str, Any]]`: Dictionary with all file data, or None

**Dictionary Keys**:
- `id`, `file_path`, `relative_path`, `file_name`, `file_extension`
- `file_size`, `raw_source`, `preprocessed_source`
- `created_at`, `updated_at`

**Example**:
```python
file_data = db.get_source_file("/path/to/myfile.cpp")
if file_data:
    print(f"File size: {file_data['file_size']}")
    raw = file_data['raw_source']
```

### `get_source_file_by_name`

```python
def get_source_file_by_name(self, file_name: str) -> List[Dict[str, Any]]
```

**Purpose**: Get source files by filename only (may return multiple).

**Parameters**:
- `file_name` (str): Just the filename to search for

**Returns**:
- `List[Dict[str, Any]]`: List of file dictionaries

**Example**:
```python
files = db.get_source_file_by_name("context.h")
for f in files:
    print(f"Found at: {f['file_path']}")
```

### `search_source_files`

```python
def search_source_files(self, pattern: str) -> List[Dict[str, Any]]
```

**Purpose**: Search for source files by pattern in path, relative_path, or filename.

**Parameters**:
- `pattern` (str): Pattern to search for (SQL LIKE wildcards added automatically)

**Returns**:
- `List[Dict[str, Any]]`: List of matching file dictionaries

**Example**:
```python
gfx_files = db.search_source_files("gfx")
material_files = db.search_source_files("material")
```

### `list_source_files`

```python
def list_source_files(self, limit: Optional[int] = None) -> List[Dict[str, Any]]
```

**Purpose**: List all source files in the database (without content for performance).

**Parameters**:
- `limit` (Optional[int]): Maximum number of files to return

**Returns**:
- `List[Dict[str, Any]]`: List of file info dictionaries (no source content)

**Example**:
```python
all_files = db.list_source_files()
first_10 = db.list_source_files(limit=10)
```

### `get_raw_source`

```python
def get_raw_source(self, file_path: str) -> Optional[str]
```

**Purpose**: Get just the raw source code for a file.

**Parameters**:
- `file_path` (str): Exact file path

**Returns**:
- `Optional[str]`: Raw source code, or None if not found

**Example**:
```python
source = db.get_raw_source("/path/to/file.cpp")
```

### `get_preprocessed_source`

```python
def get_preprocessed_source(self, file_path: str) -> Optional[str]
```

**Purpose**: Get just the preprocessed source code for a file.

**Parameters**:
- `file_path` (str): Exact file path

**Returns**:
- `Optional[str]`: Preprocessed source code, or None if not found

**Example**:
```python
preprocessed = db.get_preprocessed_source("/path/to/file.cpp")
```

## File Tracking (Incremental Updates)

### `add_file`

```python
def add_file(self, file_path: Union[str, Path]) -> str
```

**Purpose**: Add or update a file tracking record with current modification time.

**Parameters**:
- `file_path` (Union[str, Path]): Path to the file

**Returns**:
- `str`: SHA-256 hash of the file

**Example**:
```python
file_hash = db.add_file("/path/to/myfile.cpp")
```

### `update_file_record`

```python
def update_file_record(self, file_path: str, mtime: float) -> str
```

**Purpose**: Update file tracking with specific modification time.

**Parameters**:
- `file_path` (str): Path to the file
- `mtime` (float): Modification time (from os.path.getmtime)

**Returns**:
- `str`: SHA-256 hash of the file

**Example**:
```python
mtime = os.path.getmtime(file_path)
file_hash = db.update_file_record(file_path, mtime)
```

### `is_file_modified`

```python
def is_file_modified(self, file_path: str, mtime: float) -> bool
```

**Purpose**: Check if file has been modified since last parse.

**Parameters**:
- `file_path` (str): Path to the file
- `mtime` (float): Current modification time

**Returns**:
- `bool`: True if file needs reparsing, False otherwise

**Example**:
```python
mtime = os.path.getmtime(file_path)
if db.is_file_modified(file_path, mtime):
    # Reparse the file
    pass
```

## Post-Processing

### `process_method_implementations`

```python
def process_method_implementations(self)
```

**Purpose**: Match method implementation functions to their class member declarations. This is a post-processing step that should be called after parsing all files.

**Behavior**:
- Finds all function entities marked as methods (is_method=True)
- Matches them to class members by parsing qualified names
- Moves implementation locations to member_implementation_locations table
- Deletes the standalone method implementation function entities

**Example**:
```python
# After parsing all files
db.process_method_implementations()
```

## Database Management

### `clear_database`

```python
def clear_database(self)
```

**Purpose**: Remove all data from the database (keeps schema).

**Warning**: This is destructive and cannot be undone.

**Example**:
```python
db.clear_database()  # All data deleted
```

### `get_statistics`

```python
def get_statistics(self) -> Dict[str, int]
```

**Purpose**: Get comprehensive database statistics.

**Returns**:
- `Dict[str, int]`: Statistics dictionary

**Dictionary Keys**:
- `total_entities`: Total entity count
- `entities_<type>`: Count per entity type (e.g., `entities_CLASS`)
- `total_locations`: Total location records
- `total_members`: Total member records
- `total_member_implementations`: Total implementation locations
- `total_files`: Total source files
- `files_with_preprocessed`: Files with preprocessed source
- `total_source_size_mb`: Total size of source files in MB
- `files_<ext>`: Count per file extension (e.g., `files_cpp`)
- `files_<ext>_size_mb`: Size per extension in MB
- `template_entities`: Count of template entities

**Example**:
```python
stats = db.get_statistics()
print(f"Total entities: {stats['total_entities']}")
print(f"Classes: {stats.get('entities_CLASS', 0)}")
print(f"Functions: {stats.get('entities_FUNCTION', 0)}")
print(f"Files: {stats['total_files']}")
```

## High-Level Operations

### `build_from_directory`

```python
def build_from_directory(self, directory: Path, extensions: Optional[List[str]] = None,
                       defines: Optional[List[str]] = None,
                       defines_preset: Optional[str] = None, 
                       include_paths: Optional[List[Path]] = None)
```

**Purpose**: Build database from all C++ files in a directory tree.

**Parameters**:
- `directory` (Path): Root directory to scan
- `extensions` (Optional[List[str]]): File extensions to include (default: common C++ extensions)
- `defines` (Optional[List[str]]): Preprocessor defines
- `defines_preset` (Optional[str]): Preset defines ('macos', 'linux', 'minimal')
- `include_paths` (Optional[List[Path]]): Include paths for preprocessor

**Example**:
```python
from pathlib import Path
db.build_from_directory(
    Path("/path/to/project"),
    extensions=['.cpp', '.h'],
    defines_preset='macos'
)
```

## Context Manager

### `connect`

```python
@contextmanager
def connect(self)
```

**Purpose**: Context manager for database connections with automatic commit/rollback.

**Internal Use**: Most public methods use this internally. Advanced users can use it directly.

**Example**:
```python
with db.connect() as conn:
    # Direct SQL queries
    rows = conn.execute("SELECT * FROM entities LIMIT 10").fetchall()
```

## Entity Type Values

Valid values for `entity_type` parameter:
- `"CLASS"` - C++ classes
- `"STRUCT"` - C++ structs  
- `"ENUM"` - Enumerations
- `"FUNCTION"` - Free functions
- `"TYPEDEF"` - Type aliases
- `"NAMESPACE"` - Namespaces
- `"VARIABLE"` - Global variables
- `"UNION"` - Unions

## Common Usage Patterns

### Pattern 1: Search and Inspect
```python
# Find a class and examine its members
entities = db.search_entities(name="GfxMaterial")
if entities:
    entity = entities[0]
    for member in entity.members:
        print(f"  {member.access_level.value}: {member.name}")
```

### Pattern 2: Trace Inheritance
```python
# Find all classes derived from a base
base_name = "Drawable"
derived = db.find_derived_classes(base_name)
for d in derived:
    print(f"{d.canonical_name} inherits from {base_name}")
```

### Pattern 3: Incremental Updates
```python
# Only reparse modified files
for file_path in source_files:
    mtime = os.path.getmtime(file_path)
    if db.is_file_modified(file_path, mtime):
        # Parse and update
        entities = parser.parse_file(file_path)
        for entity in entities:
            db.add_entity(entity)
        db.update_file_record(file_path, mtime)
```

### Pattern 4: File Content Access
```python
# Get preprocessed source for analysis
file_data = db.get_source_file("/path/to/complex.h")
if file_data and file_data['preprocessed_source']:
    # Analyze preprocessed content
    analyze(file_data['preprocessed_source'])
```

## Error Handling

Most methods handle errors gracefully:
- Missing entities return `None` or empty lists
- Database operations use transactions (automatic rollback on error)
- File operations handle missing files
- Invalid enum values raise exceptions

## Thread Safety

The database uses WAL mode for better concurrency. Each method creates its own connection, so multiple threads can read simultaneously. However, writes should be serialized for best performance.

## Performance Considerations

1. **Batch Operations**: Use `add_entity` in loops with a single commit
2. **Search Optimization**: Use specific filters to reduce result sets
3. **File Storage**: Large preprocessed sources can consume significant space
4. **Indexing**: The schema includes indices on common search fields
5. **Incremental Updates**: Use file tracking to avoid unnecessary reparsing

## Migration from V1

Key differences from hypothetical V1:
- Normalized schema (no duplicate entities)
- Separate source file storage
- Member implementation tracking
- Support for comma-separated entity types
- Canonical name resolution
- Built-in typedef resolution