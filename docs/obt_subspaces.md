# OBT Subspaces

---

## Overview

Subspaces are isolated execution environments within the OBT staging directory. They allow different toolchains and runtime environments to coexist without conflicts.

---

## Available Subspaces

### host (Default)
The default subspace for native development:
- Custom-built Python from source
- Native libraries and tools
- Direct hardware access
- Best performance for compiled code

### conda
Anaconda-based Python environment:
- Data science and ML tools
- Inherits most paths from host subspace
- Separate Python environment
- Useful for Python-heavy workflows

### ios
iOS development environment:
- [Details needed about iOS toolchain setup]
- [Cross-compilation support]

### xros
visionOS development environment:
- [Details needed about xros/visionOS support]

---

## Working with Subspaces

### List Available Subspaces

```bash
obt.subspace.list.py
```

### Build a Subspace

```bash
obt.subspace.build.py <subspace_name>
```

### Launch Subspace Shell

```bash
obt.subspace.launch.py <subspace_name>
```

This launches a new shell with the subspace environment active.

---

## Subspace Structure

Subspaces are stored in `${OBT_STAGE}/subspaces/`:

```
${OBT_STAGE}/
└── subspaces/
    ├── host/
    ├── conda/
    ├── ios/
    └── xros/
```

---

## Python API

Execute commands in a subspace without entering it:

```python
from obt import subspace

# Run conda list in the conda subspace
subspace.descriptor("conda").command(["list"])
```

---

## Creating Custom Subspaces

Subspace modules are defined in `modules/subspace/` and inherit from the base subspace class.

[Details needed about subspace implementation]

---

## Environment Inheritance

Subspaces can:
- Inherit paths from the host subspace
- Override specific environment variables
- Maintain separate Python environments
- Share compiled libraries

---

## Use Cases

### Host Subspace
- Game engines
- Real-time applications
- System programming
- Performance-critical code

### Conda Subspace
- Data analysis
- Machine learning
- Scientific computing
- Jupyter notebooks

### Mobile Subspaces (ios/xros)
- Cross-platform mobile development
- [Specific use cases needed]

---

## Switching Between Subspaces

You can only be in one subspace at a time. To switch:

1. Exit current subspace shell
2. Launch new subspace:
```bash
obt.subspace.launch.py <new_subspace>
```

---

## Notes

- Subspaces share the same staging directory
- Binary compatibility depends on the specific subspace configuration
- The active subspace is indicated by `OBT_SUBSPACE` environment variable