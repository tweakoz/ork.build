# C++ Database Command-Line Tools Documentation

## Overview

The C++ Database provides a comprehensive suite of command-line tools for searching, analyzing, and exploring C++ codebases. These tools leverage a pre-built SQLite database of parsed entities with 99.1% overall accuracy.

## Prerequisites

### Building the Database

Before using any search tools, build the C++ entity database:

```bash
# Build specific modules
ork.cpp.db.build.py -m core lev2 ecs

# Build all default modules
ork.cpp.db.build.py -m gfx

# The database is stored at:
# ~/.staging-aug18/cpp_db_v2_orkid.db
```

## Core Search Tools

### ork.cpp.search.py

Advanced entity search with multiple filters and output formats.

#### Basic Usage

```bash
# Search for entities by name pattern
ork.cpp.search.py Camera              # Find all entities with "Camera"
ork.cpp.search.py "^Camera$"          # Exact match using regex
ork.cpp.search.py "Camera.*Data"      # Regex pattern matching

# Search by entity type
ork.cpp.search.py -t class UiCamera        # Only classes
ork.cpp.search.py -t struct CameraData     # Only structs
ork.cpp.search.py -t enum EBufferFormat    # Only enums
ork.cpp.search.py -t typedef "_ptr"        # Only typedefs
ork.cpp.search.py -t namespace lev2        # Find namespaces
ork.cpp.search.py -t objects Camera        # Both classes AND structs (special alias)

# Search within specific namespace
ork.cpp.search.py -n ork::lev2 Camera      # Search in ork::lev2 namespace
ork.cpp.search.py -n ork::ecs Component    # Search in ork::ecs namespace

# Output formats
ork.cpp.search.py Camera --json            # JSON output for scripting
ork.cpp.search.py Camera --files           # Show only file paths
ork.cpp.search.py Camera --summary         # Minimal summary view
```

#### Advanced Features

```bash
# Combine filters
ork.cpp.search.py -t class -n ork::lev2 Context

# Case-insensitive search
ork.cpp.search.py -i camera

# Show all entities of a type
ork.cpp.search.py -t enum

# Limit results
ork.cpp.search.py Camera --limit 10
```

### ork.cpp.members.py

Display members of a specific class or struct with detailed information.

#### Usage

```bash
# Show members of a class
ork.cpp.members.py CameraData              # Find by short name
ork.cpp.members.py ork::lev2::Context      # Use full canonical name

# Output formats
ork.cpp.members.py CameraData --json       # JSON format for scripting
ork.cpp.members.py CameraData              # Standard colored output
```

#### Features

- Shows all public, protected, and private members
- Displays member types (method, field, constructor, etc.)
- Shows method signatures with parameter types
- Indicates const, noexcept, override, virtual qualifiers
- Shows default values for fields
- Displays typedef aliases with resolved types
- Color-coded access levels (green=public, yellow=protected, red=private)

### ork.cpp.references.py

Find all references to an entity or member in the codebase.

#### Usage

```bash
# Find references to a class
ork.cpp.references.py ork::lev2::Context

# Find references to a specific member
ork.cpp.references.py "ork::lev2::CameraMatrices::_frustum"

# Output formats
ork.cpp.references.py "ork::lev2::Context" --json       # JSON for scripting
ork.cpp.references.py "ork::lev2::Context" --limit 10   # Limit results
```

#### Output Information

- Shows file location and line number for each reference
- Distinguishes between definitions, implementations, reads, writes, and calls
- Provides summary statistics of reference types
- Supports JSON output for programmatic analysis

### ork.cpp.inhtree.py

Display inheritance hierarchy for classes and structs.

#### Usage

```bash
# Show inheritance tree
ork.cpp.inhtree.py ork::lev2::Context

# JSON output for scripting
ork.cpp.inhtree.py ork::lev2::Context --json
```

#### Output

- Shows base classes (upward inheritance tree)
- Shows derived classes (downward inheritance tree)
- Displays multiple inheritance paths
- Indicates access levels for inheritance
- Shows both immediate and transitive relationships

## Enum Analysis Tools

### ork.cpp.enums.py

Specialized tool for exploring enum definitions and values, with special support for Orkid's CrcEnum macro.

#### Basic Usage

```bash
# Display enum values
ork.cpp.enums.py EBufferFormat         # Show specific enum
ork.cpp.enums.py "ork::lev2::*"       # Pattern matching with wildcards
ork.cpp.enums.py                      # Show all enums in database

# Search by CRC32 hash value (for CrcEnum enums)
ork.cpp.enums.py --hash 0xE15695B7    # Search by hex hash
ork.cpp.enums.py --hash 3780548023    # Search by decimal hash
ork.cpp.enums.py --hash 0xe15695b7    # Lowercase hex works too

# Output formats
ork.cpp.enums.py EBufferFormat --json  # JSON output for scripting
```

#### Features

- **CrcEnum Detection**: Automatically detects enums using the CrcEnum macro
- **Hash Computation**: Computes and displays CRC32 hash values for CrcEnum values
- **Hash Search**: Find which enum value corresponds to a hash value (useful for debugging)
- **Pattern Matching**: Support for wildcard patterns in enum names
- **Type Information**: Shows enum class vs regular enum, base types

#### Output Format

The tool displays a columnar format with:
- **Name**: Enum value name (yellow)
- **Namespace**: C++ namespace (magenta)
- **Type**: enum/enum class and base type (green)
- **Value**: Actual value or CrcEnum notation (cyan)
- **Hash**: For CrcEnum - hex (orange) and decimal (darker orange)

Example output:
```
ork::lev2::EBufferFormat
Name          Namespace    Type         Value              Hash
R8            ork::lev2    enum class   CrcEnum(R8)       0xE15695B7 (3780548023)
RGB8          ork::lev2    enum class   CrcEnum(RGB8)     0xDFD81669 (3755480681)
```

## File Management Tools

### ork.cpp.db.files.py

Manage and explore source files stored in the database.

#### Commands

```bash
# List files in database
ork.cpp.db.files.py list --limit 20       # List first 20 files

# Search for files by pattern
ork.cpp.db.files.py search "*.cpp"        # Find all cpp files
ork.cpp.db.files.py search "texture"      # Find files with "texture" in path

# Find specific file by name
ork.cpp.db.files.py find txi.cpp          # Find by filename

# Show file content with line numbers
ork.cpp.db.files.py show txi.cpp          # Display file (works with just filename)
ork.cpp.db.files.py show /full/path.cpp   # Display file by full path
```

#### Features

- Shows file metadata (size, update time)
- Supports both raw and preprocessed source viewing
- Can search by filename or full path
- Displays content with line numbers for easy navigation

## Utility Tools

### ork.crcstring.py

Compute CRC32 hash for strings (useful for validating CrcEnum values).

```bash
ork.crcstring.py R8
# Output: str(R8) -> CrcString(0xe15695b7:3780548023)
```

## Common Usage Patterns

### 1. Understanding a Class

```bash
# Step 1: Find the class
ork.cpp.search.py TextureInterface

# Step 2: See its members
ork.cpp.members.py ork::lev2::TextureInterface

# Step 3: Check inheritance
ork.cpp.inhtree.py ork::lev2::TextureInterface

# Step 4: Find usage
ork.cpp.references.py "ork::lev2::TextureInterface"
```

### 2. Exploring Enums

```bash
# Find buffer-related enums
ork.cpp.search.py -t enum Buffer

# See enum values and hashes
ork.cpp.enums.py EBufferFormat

# Reverse lookup a hash from logs
ork.cpp.enums.py --hash 0xE15695B7
```

### 3. Tracing Field Usage

```bash
# Find field references
ork.cpp.references.py "ork::lev2::CameraMatrices::_frustum"

# See the class that contains it
ork.cpp.members.py ork::lev2::CameraMatrices
```

### 4. Finding Implementations

```bash
# Search for all renderer-related entities
ork.cpp.search.py Renderer

# Find IRenderer implementations
ork.cpp.inhtree.py ork::lev2::IRenderer
```

## Output Formats

### Standard Output

- **Colorized**: Uses ANSI colors for better readability
- **Columnar**: Aligned columns for easy scanning
- **Hierarchical**: Tree structures for inheritance

### JSON Output

Most tools support `--json` flag for scripting:

```bash
# Get JSON for further processing
ork.cpp.search.py Camera --json | jq '.entities[].canonical_name'

# Chain with other tools
ork.cpp.enums.py EBufferFormat --json | jq '.enums[0].values[] | select(.name=="R8")'
```

## Performance Tips

1. **Use Exact Names When Possible**: Faster than pattern matching
2. **Specify Entity Type**: Reduces search space with `-t` flag
3. **Use Namespace Filters**: Narrow scope with `-n` flag
4. **Limit Results**: Use `--limit` for large result sets
5. **Build Database First**: Ensure database is current before searching

## Troubleshooting

### Database Not Found

```
Orkid database not found!
Expected at: ~/.staging-aug18/cpp_db_v2_orkid.db
Run 'ork.cpp.db.build.py -m <modules>' to build it first
```

**Solution**: Build the database with required modules.

### No Results Found

- Check spelling and namespace qualification
- Try without namespace prefix first
- Use wildcards: `*Camera*`
- Verify the module was included in database build

### Stale Database

If code has changed:
```bash
ork.cpp.db.build.py -m <modules>  # Rebuild affected modules
```

## Color Reference

The tools use consistent color coding:

- **Yellow**: Names, identifiers
- **Magenta**: Namespaces
- **Green**: Public access
- **Yellow**: Protected access
- **Red**: Private access
- **Cyan**: Types, values
- **Orange**: Hash values
- **Blue**: Keywords (virtual, static, const)
- **Grey**: File paths and line numbers