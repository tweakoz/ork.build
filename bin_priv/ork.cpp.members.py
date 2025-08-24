#!/usr/bin/env python3
"""
Display members of Orkid C++ classes/structs.
Wrapper that uses the default Orkid database.
"""

import sys
from pathlib import Path

# Add OBT to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from obt.path import stage
from obt.deco import Deco

def main():
    """Main entry point - add Orkid database and delegate to obt variant"""
    deco = Deco()
    
    # Check if Orkid database exists
    db_path = stage() / "cpp_db_v2_orkid.db"
    if not db_path.exists():
        print(f"{deco.red('Orkid database not found!')}")
        print(f"Expected at: {db_path}")
        print(f"Run 'ork.cpp.db.build.py -m <modules>' to build it first")
        sys.exit(1)
    
    # Add database argument if not specified
    if '--db' not in sys.argv and '--database' not in sys.argv and '--source' not in sys.argv:
        sys.argv.extend(['--db', str(db_path)])
    
    # Run the obt variant as subprocess
    import subprocess
    import os
    script_path = Path(__file__).parent / 'obt.cpp.members.py'
    result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:], env=os.environ)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()