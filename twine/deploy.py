#!/usr/bin/env python3
import os
import sys
import subprocess
import pathlib


this_dir = pathlib.PosixPath(os.path.dirname(os.path.realpath(__file__)))
os.chdir(str(this_dir/".."))

# Check if git repo is clean before proceeding
print("Checking git status...")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)

if result.stdout.strip():
    print("\n❌ ERROR: Git repository is not clean!")
    print("The following files have uncommitted changes:\n")
    print(result.stdout)
    print("\nPlease commit or stash your changes before deploying.")
    print("This prevents losing work when 'git clean -fdx' runs.")
    sys.exit(1)

# Also check for untracked files that would be removed
result = subprocess.run(['git', 'clean', '-fdn'], capture_output=True, text=True)
if result.stdout.strip():
    print("\n⚠️  WARNING: The following untracked files will be removed:")
    print(result.stdout)
    response = input("\nProceed anyway? (y/N): ")
    if response.lower() != 'y':
        print("Deployment cancelled.")
        sys.exit(1)

print("✓ Git repository is clean, proceeding with deployment...\n")
os.system("git clean -fdx")
os.system("rm -rf %s" % str(this_dir/"../dist"))

os.system("python3 -m build")
os.system("twine check dist/*.whl")
os.system("twine upload --verbose dist/*")
