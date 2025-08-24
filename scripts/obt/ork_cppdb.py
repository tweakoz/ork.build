"""
Orkid C++ Database Utilities
Orkid-specific module definitions and path utilities
"""

from pathlib import Path
from typing import List, Optional, Set

# Available Orkid modules
ORKID_MODULES = {
    'core': ['ork.core'],
    'lev2': ['ork.lev2'],
    'ecs': ['ork.ecs'],
    'tool': ['ork.tool'],
    'bullet': ['ext.bullet', 'ork.bullet'],
    'opengl': ['ork.lev2/src/gfx/gl'],
    'vulkan': ['ork.lev2/src/gfx/vulkan'],
    'renderer': ['ork.lev2/src/gfx/renderer'],
    'gfx': ['ork.lev2/inc/ork/lev2/gfx', 'ork.lev2/src/gfx'],
    'ui': ['ork.lev2/src/ui', 'ork.lev2/inc/ork/lev2/ui'],
    'aud': ['ork.lev2/src/aud', 'ork.lev2/inc/ork/lev2/aud'],
    'singularity': ['ork.lev2/src/aud/singularity', 'ork.lev2/inc/ork/lev2/aud/singularity'],
    'shadlang': ['ork.lev2/inc/ork/lev2/gfx/shadlang_nodes.h', 
                 'ork.lev2/src/gfx/gl/glfx/glslfxi_parser.h'],
    'kernel': ['ork.core/inc/ork/kernel', 'ork.core/src/kernel'],
    'util': ['ork.core/inc/ork/util', 'ork.core/src/util'],
    'utils': ['ork.core/inc/ork/util', 'ork.core/src/util'],  # Alias
    'rtti': ['ork.core/inc/ork/rtti', 'ork.core/src/rtti'],
}

def get_orkid_root() -> Path:
    """Get Orkid root directory"""
    from ork import path as ork_path
    return ork_path.root

def get_orkid_paths(modules: Optional[List[str]] = None, 
                    inc_only: bool = False, 
                    src_only: bool = False) -> List[Path]:
    """
    Get Orkid source paths based on modules
    
    Args:
        modules: List of module names or None for default modules
        inc_only: Only return include directories
        src_only: Only return source directories
        
    Returns:
        List of Path objects for the requested modules
    """
    paths = []
    orkid_root = get_orkid_root()
    
    if modules:
        # Specific modules requested
        for module in modules:
            if module in ORKID_MODULES:
                for subpath in ORKID_MODULES[module]:
                    full_path = orkid_root / subpath
                    if full_path.exists():
                        paths.append(full_path)
            else:
                # Try as direct path
                module_path = orkid_root / module
                if module_path.exists():
                    paths.append(module_path)
                else:
                    print(f"Warning: Unknown module or path: {module}")
    else:
        # Default to main modules
        for module in ['core', 'lev2', 'ecs', 'tool']:
            for subpath in ORKID_MODULES[module]:
                full_path = orkid_root / subpath
                if full_path.exists():
                    paths.append(full_path)
    
    # Filter by inc/src if requested
    if inc_only:
        filtered = []
        for path in paths:
            if path.is_dir():
                # Add inc subdirs
                inc_dirs = list(path.rglob('inc'))
                inc_dirs.extend(list(path.rglob('include')))
                if 'inc' in str(path) or 'include' in str(path):
                    filtered.append(path)
                filtered.extend(inc_dirs)
        paths = filtered
    elif src_only:
        filtered = []
        for path in paths:
            if path.is_dir():
                # Add src subdirs
                src_dirs = list(path.rglob('src'))
                if 'src' in str(path):
                    filtered.append(path)
                filtered.extend(src_dirs)
        paths = filtered
    
    return list(set(paths))  # Remove duplicates

def find_source_files(paths: List[Path], 
                     extensions: Optional[Set[str]] = None) -> List[Path]:
    """
    Find all C++ source files in given paths
    
    Args:
        paths: List of paths to search
        extensions: Set of file extensions to include
        
    Returns:
        Sorted list of unique source files
    """
    if extensions is None:
        # C++ extensions
        extensions = {'.h', '.hpp', '.hxx', '.H', '.hh', 
                     '.c', '.cpp', '.cxx', '.cc', '.C',
                     '.inl', '.inc'}
    
    files = []
    for path in paths:
        if path.is_file():
            if path.suffix in extensions:
                files.append(path)
        elif path.is_dir():
            for ext in extensions:
                files.extend(path.rglob(f'*{ext}'))
    
    return sorted(set(files))

def get_orkid_include_paths() -> List[str]:
    """Get standard Orkid include paths for preprocessing"""
    orkid_root = get_orkid_root()
    return [
        str(orkid_root / "ork.core" / "inc"),
        str(orkid_root / "ork.lev2" / "inc"),
        str(orkid_root / "ork.ecs" / "inc"),
        str(orkid_root / "ork.tool" / "inc"),
        str(orkid_root / "ext"),
    ]

def get_module_description(module: str) -> str:
    """Get human-readable description of a module"""
    descriptions = {
        'core': 'Core functionality',
        'lev2': 'Level 2 - Graphics and UI',
        'ecs': 'Entity Component System',
        'tool': 'Tools and utilities',
        'bullet': 'Bullet physics integration',
        'opengl': 'OpenGL renderer',
        'vulkan': 'Vulkan renderer',
        'renderer': 'Renderer abstraction',
        'gfx': 'Graphics subsystem',
        'ui': 'User interface',
        'aud': 'Audio subsystem',
        'singularity': 'Singularity audio synthesizer',
        'shadlang': 'Shader language',
        'kernel': 'Core kernel functionality',
        'util': 'Core utilities',
        'utils': 'Core utilities',
        'rtti': 'Runtime type information',
    }
    return descriptions.get(module, f'Module: {module}')

def list_available_modules() -> List[str]:
    """Get list of all available module names"""
    return sorted(ORKID_MODULES.keys())

# Module exports
__all__ = [
    'ORKID_MODULES',
    'get_orkid_root',
    'get_orkid_paths', 
    'find_source_files',
    'get_orkid_include_paths',
    'get_module_description',
    'list_available_modules'
]