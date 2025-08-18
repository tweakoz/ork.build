# OBT Quick Start Guide

This guide will get you up and running with OBT in minutes.

---

## Shell Environment Best Practices

OBT works best with a clean base shell environment. While personal customizations are valuable for productivity, they can sometimes interfere with build tools. We recommend:

### Recommended Approach
- **Keep your login shell minimal**: Core system paths and essential tools only
- **Use launch scripts**: Put customizations in dedicated development environment scripts
- **Isolate tool-specific configs**: Use virtual environments, direnv, or similar tools
- **Document dependencies**: If your customizations require specific tools, note them

### Common Issues to Avoid
- Custom `PYTHONPATH` exports in `.bashrc`/`.zshrc` can conflict with OBT's Python management
- Modified `LD_LIBRARY_PATH` or `DYLD_LIBRARY_PATH` may cause library conflicts  
- Aliasing standard commands (`alias python=python3.12`) can break dependency detection
- Auto-activated environments (conda, pyenv) should be disabled for OBT shells
- User-global Python packages in `~/.local` (Linux) or `~/Library/Python` (macOS) can conflict with PEP-668 compliant systems
- use Bash, not Zsh. Zsh support will be added at some point.

### Quick Check
Before installing OBT, check your environment:
```bash
# See what's modifying your paths
echo $PATH | tr ':' '\n' | head -10
echo $PYTHONPATH
echo $LD_LIBRARY_PATH

# If these are heavily customized, consider using a clean shell for OBT
```

### Clean Shell Launch
If you need a clean environment:
```bash
# Launch bash without reading startup files
env -i HOME=$HOME TERM=$TERM bash --noprofile --norc

# Or temporarily move configs
mv ~/.bashrc ~/.bashrc.backup
# ... work with OBT ...
mv ~/.bashrc.backup ~/.bashrc
```

---

## Prerequisites

### Python Requirements
- **Python 3.10 or higher** is required for OBT
- Must comply with PEP-668 (use virtual environments, not user-global packages)

### macOS
- Xcode (from App Store)
- Homebrew (https://brew.sh)
- Python 3.10+ from Homebrew: `brew install python@3.12`
- Homebrew's bin directory (`/opt/homebrew/bin` on Apple Silicon, `/usr/local/bin` on Intel) must be in your base shell PATH
- Clean up any user-global packages in `~/Library/Python` (these can interfere with OBT), move to venvs

### Linux
- Python 3.10+ (usually pre-installed on modern distros)
- Basic build tools (gcc, make, etc.)
- sudo access for system dependencies
- Clean up any user-global packages in `~/.local` if present - move to venvs

### Windows
- WSL2 with Ubuntu
- Follow Linux instructions within WSL2

### PEP-668 Compliance
Modern Python installations (3.12+ on Homebrew, recent Linux distros) follow PEP-668, which prevents installing packages outside virtual environments. This is why OBT requires using a virtual environment. If you have existing user-global packages:

```bash
# Check for user-global packages
ls -la ~/Library/Python  # macOS
ls -la ~/.local/lib/python*/site-packages  # Linux

# Consider backing up and removing these directories if they exist, move them to venvs.
# They can cause conflicts with OBT's Python packages
```

---

## Installation

### 1. Create Python Virtual Environment

```bash
python3 -m venv ~/obt-venv
```

### 2. Create Launch Script

Create `~/bin/obt-launch`:

```bash
#!/usr/bin/env bash
prepend_to_python_path() {
  if [ -z "$PYTHONPATH" ]; then
    export PYTHONPATH="$1"
  elif ! echo "$PYTHONPATH" | grep -Eq "(^|:)$1($|:)"; then
    export PYTHONPATH="$1:$PYTHONPATH"
  fi
}

# Replace 3.x with your Python version (e.g., 3.10)
prepend_to_python_path ~/obt-venv/lib/python3.x/site-packages

bash --rcfile <(echo "source ~/obt-venv/bin/activate")
```

Make it executable:
```bash
chmod +x ~/bin/obt-launch
```

### 3. Install OBT

```bash
# Launch virtual environment
~/bin/obt-launch

# Upgrade pip
python3 -m pip install --upgrade pip

# Install OBT
pip3 install ork.build
```

### 4. Install System Dependencies

#### macOS
```bash
obt.osx.installdeps.py
```

#### Linux (Ubuntu/Debian)
```bash
# Will ask for sudo
obt.ix.installdeps.ubuntu_x86_64.py
```

---

## Creating Your First Environment

### 1. Create Staging Environment

```bash
obt.env.create.py --stagedir ~/.obt-staging 
```

This builds essential dependencies including Python 3.12 and creates the staging structure.

### 2. Launch Environment

```bash
obt.env.launch.py --stagedir ~/.obt-staging --numcores 8
```

You'll see your prompt change to indicate you're in the OBT environment.

---

## Working with Projects

### Making a Project OBT-Aware

Create this structure in your project:

```
myproject/
├── obt.project/
│   ├── obt.manifest
│   └── scripts/
│       └── init_env.py
```

**obt.manifest:**
```json
{
  "name": "myproject",
  "version": "1.0.0",
  "autoexec": "scripts/init_env.py"
}
```

**scripts/init_env.py:**
```python
import obt.path
import obt.env

def setup():
    project_root = obt.path.project()
    # Add your project setup here
    obt.env.prepend_to_path(project_root/"bin")
    print(f"Initialized project: myproject")
```

### Launching with Projects

```bash
obt.env.launch.py --stagedir ~/.obt-staging --numcores 8 \
  --project ~/projects/myproject \
  --project ~/projects/another_project
```

---

## Working with Dependencies

### List Available Dependencies

```bash
obt.dep.list.py
```

### Build a Dependency

```bash
# Build boost
obt.dep.build.py boost

# Force rebuild
obt.dep.build.py boost --force --wipe

# Incremental build (for development)
obt.dep.build.py boost --incremental
```

### Check Dependency Status

```bash
obt.dep.status.py boost
```

---

## Essential Commands

| Command | Description |
|---------|------------|
| `obt.env.launch.py` | Launch staging environment |
| `obt.dep.list.py` | List available dependencies |
| `obt.dep.build.py <name>` | Build a dependency |
| `obt.dep.status.py <name>` | Check dependency status |
| `obt.find.py <pattern>` | Search files across projects |
| `obt.host.info.py` | Show system information |

---

## Command Discovery

Use tab completion to discover commands:

```bash
obt.<TAB><TAB>
```

---

## Environment Variables

Once in an OBT environment, these are set:

- `OBT_STAGE`: Staging directory root
- `OBT_BUILDS`: Where sources are built
- `OBT_PROJECTS_LIST`: Loaded projects
- `OBT_SEARCH_PATH`: Search paths for obt.find.py

---

## Tips

1. **Check your environment**: Run `obt.host.info.py` to verify setup
2. **Use tab completion**: Most commands support bash completion
3. **Project order matters**: First project takes precedence for conflicts
4. **Exit environment**: Just type `exit` to return to parent shell

---

## Next Steps

- Read the [Technical Design Document](obt_tdd.md) for deeper understanding
- Explore [Docker support](obt_docker.md) for containerized workflows
- Learn about [Subspaces](obt_subspaces.md) for isolated environments
- Check [Examples](obt_examples.md) for real-world usage patterns