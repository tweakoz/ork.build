# OBT Detailed Examples

---

## Example 1: Multi-Project Game Development

Setting up a game development environment with engine, shared libraries, and game project:

```bash
# Create and launch environment with multiple projects
obt.env.launch.py --stagedir ~/.game-dev \
  --numcores 16 \
  --project ~/projects/orkid \
  --project ~/projects/shared-assets \
  --project ~/projects/mygame
```

### Project Structure

**orkid/** (Game Engine)
```
orkid/
├── obt.project/
│   ├── obt.manifest
│   └── scripts/
│       └── init_env.py  # Sets up ORKID_ROOT, paths
```

**shared-assets/** (Shared Resources)
```
shared-assets/
├── obt.project/
│   ├── obt.manifest
│   └── scripts/
│       └── init_env.py  # Adds asset paths
```

**mygame/** (Game Project)
```
mygame/
├── obt.project/
│   ├── obt.manifest
│   ├── scripts/
│   │   └── init_env.py  # Game-specific setup
│   └── modules/
│       └── dep/
│           └── game_physics.py  # Custom dependency
```

---

## Example 2: Building Complex Dependencies

Building OpenVDB with all its dependencies:

```bash
# Check what will be built
obt.dep.status.py openvdb

# Build OpenVDB and dependencies
obt.dep.build.py openvdb

# The above automatically builds in order:
# - python
# - cmake  
# - boost
# - blosc
# - openexr
# - tbb
# - openvdb
```

---

## Example 3: Custom Dependency Provider

Creating a custom dependency for your project:

**myproject/obt.project/modules/dep/custom_lib.py:**
```python
from obt import dep, path
import os

class custom_lib(dep.StdProvider):
    name = "custom_lib"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__(custom_lib.name)
        self.github_repo = "myorg/custom_lib"
        self.revision = "main"
        
    def build(self):
        build_dir = self.build_dir / "build"
        build_dir.mkdir(exist_ok=True)
        
        # Configure
        dep.cmake_build(self,
            build_dir=build_dir,
            prefix=path.stage(),
            cmake_defines={
                "BUILD_SHARED_LIBS": "ON",
                "CMAKE_BUILD_TYPE": "Release"
            })
```

---

## Example 4: Python Development with Conda Subspace

Working with data science tools:

```bash
# Build conda subspace
obt.subspace.build.py conda

# Launch conda environment
obt.subspace.launch.py conda

# Now you can use conda commands
conda install numpy pandas scikit-learn

# Or from Python
python -c "from obt import subspace; subspace.descriptor('conda').command(['list'])"
```

---

## Example 5: Cross-Compilation Setup

Building for embedded targets:

```bash
# Build ARM64 toolchain
obt.dep.build.py arm64_binutils
obt.dep.build.py arm64_gcc

# Build AVR toolchain for Arduino
obt.dep.build.py avr_binutils
obt.dep.build.py avr_gcc
obt.dep.build.py avr_libc
```

---

## Example 6: CI/CD Integration

Using OBT in continuous integration:

**.github/workflows/build.yml:**
```yaml
name: Build
on: [push]

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v2
      
      - name: Install OBT
        run: |
          python3 -m venv venv
          source venv/bin/activate
          pip install ork.build
          
      - name: Setup environment
        run: |
          source venv/bin/activate
          obt.env.create.py --stagedir staging --inplace
          
      - name: Build project
        run: |
          source venv/bin/activate
          obt.env.launch.py --stagedir staging \
            --project . \
            --command "make test"
```

---

## Example 7: Docker Module Usage

Using the PS1 development environment:

```bash
# Build PS1 dev container
obt.docker.build.py ps1dev

# Launch interactive container
obt.docker.launch.py ps1dev

# You're now in a container with PS1 SDK
```

---

## Example 8: Incremental Dependency Development

Debugging and modifying a dependency:

```bash
# Initial build
obt.dep.build.py opencv

# Make changes to source
cd $OBT_BUILDS/opencv
# ... edit files ...

# Incremental rebuild
obt.dep.build.py opencv --incremental

# If you need to start fresh
obt.dep.build.py opencv --force --wipe
```

---

## Example 9: Project-Specific Commands

Adding custom commands to your project:

**myproject/obt.project/bin/myproject.build.py:**
```python
#!/usr/bin/env python3

import obt.dep
import obt.path
import subprocess

# Ensure dependencies
obt.dep.require(["boost", "opencv"])

# Build project
project_root = obt.path.project()
build_dir = project_root / "build"
build_dir.mkdir(exist_ok=True)

subprocess.run(["cmake", ".."], cwd=build_dir)
subprocess.run(["make", "-j8"], cwd=build_dir)
```

---

## Example 10: Environment Variable Usage

Accessing OBT environment in scripts:

```python
import os
import obt.path

# Get staging directory
stage = obt.path.stage()  # or os.environ["OBT_STAGE"]

# Get list of projects
projects = os.environ.get("OBT_PROJECTS_LIST", "").split(":")

# Check current subspace
subspace = os.environ.get("OBT_SUBSPACE", "host")

# Access build directory
builds = obt.path.builds()  # or os.environ["OBT_BUILDS"]
```

---

## Tips and Best Practices

1. **Dependency Order**: Always check with `obt.dep.status.py` before building
2. **Project Composition**: Load foundational projects first (they get path priority)
3. **Incremental Builds**: Use `--incremental` when developing dependencies
4. **Clean Builds**: Use `--force --wipe` when switching branches or major changes
5. **Subspace Isolation**: Use conda subspace for Python-heavy work
6. **Custom Modules**: Put project-specific deps in `obt.project/modules/dep/`
7. **Environment Scripts**: Use `init_env.py` for complex project setup
8. **CI/CD**: Keep staging directories cached between builds when possible