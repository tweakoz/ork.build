#!/usr/bin/env python3
"""
Patch virtual environment to use repository code directly via symlinks for specific files.
This allows testing local changes without reinstalling packages.

Usage:
    python twine/_test_from_repo.py
    
Environment variables:
    VIRTUAL_ENV: Path to the virtual environment (automatically set when venv is activated)
    
The script will:
1. Replace specific installed files with symlinks to repository versions
2. Focus on C++ database modules and scripts
"""

import os
import sys
import shutil
from pathlib import Path

# Define files to patch - C++ database related modules and scripts
CPP_DB_FILES = [
    # Core C++ database modules
    'scripts/obt/cpp_database_v2.py',
    'scripts/obt/cpp_parser_descent.py',
    'scripts/obt/cpp_entities_v2.py',
    'scripts/obt/cpp_display_v2.py',
    'scripts/obt/cpp_search_v2.py',
    'scripts/obt/cpp_formatter.py',
    'scripts/obt/cpp_argparse_v2.py',
    'scripts/obt/cpp_type_system.py',
    'scripts/obt/cpp_inheritance_tree.py',
    'scripts/obt/cpp_class_details.py',
    
    # C++ database bin scripts
    'bin_priv/ork.cpp.db.build.py',
    'bin_priv/ork.cpp.db.search.py',
    'bin_priv/ork.cpp.db.files.py',
    'bin_priv/ork.cpp.db.astdump.py',
]

def get_venv_dir():
    """Get virtual environment directory from environment variable."""
    venv_dir = os.environ.get('VIRTUAL_ENV')
    if not venv_dir:
        print("ERROR: VIRTUAL_ENV environment variable not set.", file=sys.stderr)
        print("       Please activate your virtual environment first.", file=sys.stderr)
        sys.exit(1)
    return Path(venv_dir)

def get_repo_dir():
    """Get repository directory from current working directory."""
    repo_dir = Path.cwd()
    
    # Verify we're in the ork.build directory
    if not (repo_dir / 'scripts' / 'obt').exists():
        print(f"ERROR: Current directory {repo_dir} doesn't appear to be ork.build", file=sys.stderr)
        print("       Expected to find scripts/obt directory", file=sys.stderr)
        sys.exit(1)
    
    return repo_dir

def find_installed_file(venv_dir, relative_path):
    """Find where a file is installed in the virtual environment."""
    # For scripts/obt/* files, they go to site-packages/obt/
    if relative_path.startswith('scripts/obt/'):
        filename = Path(relative_path).name
        # Try to find site-packages
        patterns = [
            f'lib/python*/site-packages/obt/{filename}',
            f'lib/python*/dist-packages/obt/{filename}',
            f'Lib/site-packages/obt/{filename}',  # Windows
        ]
        for pattern in patterns:
            matches = list(venv_dir.glob(pattern))
            if matches:
                return matches[0]
    
    # For bin_priv/* files, they go to obt/bin_priv/
    elif relative_path.startswith('bin_priv/'):
        filename = Path(relative_path).name
        installed_path = venv_dir / 'obt' / 'bin_priv' / filename
        if installed_path.exists():
            return installed_path
    
    return None

def create_file_symlink(repo_file, installed_file):
    """Create a symlink for a single file."""
    print(f"  {repo_file.name}:")
    print(f"    Repo:      {repo_file}")
    print(f"    Installed: {installed_file}")
    
    if not repo_file.exists():
        print(f"    ✗ Source file not found in repo")
        return False
    
    # Remove existing file/symlink
    if installed_file.exists() or installed_file.is_symlink():
        installed_file.unlink()
    
    # Create symlink
    installed_file.symlink_to(repo_file)
    print(f"    ✓ Created symlink")
    return True

def main():
    print("Virtual Environment File Patcher for C++ Database")
    print("=" * 60)
    
    # Get directories
    venv_dir = get_venv_dir()
    repo_dir = get_repo_dir()
    
    print(f"Virtual Environment: {venv_dir}")
    print(f"Repository:          {repo_dir}")
    print()
    
    # Process each file
    print("Patching files:")
    success_count = 0
    fail_count = 0
    
    for relative_path in CPP_DB_FILES:
        repo_file = repo_dir / relative_path
        installed_file = find_installed_file(venv_dir, relative_path)
        
        if installed_file:
            if create_file_symlink(repo_file, installed_file):
                success_count += 1
            else:
                fail_count += 1
        else:
            print(f"  {Path(relative_path).name}:")
            print(f"    ✗ Could not find installed location")
            fail_count += 1
    
    print()
    print(f"✓ Successfully patched {success_count} files")
    if fail_count > 0:
        print(f"✗ Failed to patch {fail_count} files")
    print()
    print("Your virtual environment now uses repository versions of C++ database files.")
    print("Any changes you make to these files will be immediately reflected.")
    print()
    print("To add more files to patch, edit the CPP_DB_FILES list in this script.")

if __name__ == '__main__':
    main()