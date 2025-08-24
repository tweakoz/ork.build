#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os
import sys
import site
import obt.search
from pathlib import Path

#################################################################################

def find_obt_paths():
    """Find OBT installation paths in a cross-platform way"""
    paths = []
    
    # Get site-packages path for obt module
    import obt
    obt_module_path = Path(obt.__file__).parent
    paths.append(obt_module_path)
    
    # Find the venv OBT directory (bin_priv, modules, etc.)
    # This works for both Linux and macOS venv structures
    site_packages = obt_module_path.parent
    venv_root = site_packages.parent.parent.parent  # Go up to venv root
    
    # Check for OBT directories in venv
    obt_venv_dir = venv_root / "obt"
    if obt_venv_dir.exists():
        # Add subdirectories if they exist
        for subdir in ["bin_priv", "bin_pub", "modules", "examples", "tests", "scripts"]:
            subpath = obt_venv_dir / subdir
            if subpath.exists():
                paths.append(subpath)
    
    # Also check for bin_priv in the venv bin directory (some installations)
    bin_priv_alt = venv_root / "bin_priv"
    if bin_priv_alt.exists():
        paths.append(bin_priv_alt)
    
    return paths

#################################################################################

if __name__ == "__main__":
    import obt.search_args
    
    args, ext_set = obt.search_args.parse_search_args(
        description='Search text in OBT codebase (modules, scripts, examples, tests)',
        require_dep=False
    )
    
    words = args.keywords
    
    # Get OBT search paths
    search_paths = find_obt_paths()
    
    if not search_paths:
        print("ERROR: Could not find OBT installation paths")
        sys.exit(1)
    
    # Debug: Show what paths we're searching
    if os.environ.get("OBT_DEBUG"):
        print("// DEBUG: Searching OBT paths:")
        for p in search_paths:
            print(f"//   {p}")
    
    # Use the improved obt.search.execute_at API with all options
    obt.search.execute_at(words, search_paths, 
                         remove_root=None, 
                         ext_set=ext_set,
                         case_insensitive=args.case_insensitive,
                         regex=args.regex,
                         whole_word=args.whole_word,
                         invert_match=args.invert_match,
                         files_only=args.files_only,
                         before_context=args.before_context,
                         after_context=args.after_context)