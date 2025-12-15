# OBT Systemd Service Management

A complete module-based infrastructure for managing systemd user services in the Orkid Build Tools (OBT) environment.

## Overview

The OBT systemd infrastructure provides a consistent, module-based approach to creating and managing systemd user services. It follows the same patterns as OBT's `dep/` and `docker/` module systems, with 243+ existing modules across the ecosystem.

### Key Features

- **Module-based architecture**: Service definitions stored as Python modules
- **Automatic dependency realization**: Build deps, docker images, and install pip packages before service creation
- **Environment inheritance**: Services automatically inherit the OBT build environment
- **Service dependency management**: Express dependencies between services (both OBT and system services)
- **Idempotent operations**: Safe to run multiple times
- **User service support**: Services run without root privileges using `systemctl --user`
- **Boot persistence**: Optional lingering support to run services even when not logged in

## Architecture

### Module System

Service modules are stored in `$OBT_MODULES_PATH/systemd/` directories and follow this structure:

```
modules/systemd/
├── ork_logger_http.py
├── ork_database.py
└── my_custom_service.py
```

Each module contains a `serviceinfo` class that defines the service metadata and dependencies.

### Service Module Template

```python
###############################################################################
# Orkid Build System
# Copyright 2010-2025, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

class serviceinfo:
    """
    Systemd service module for MyService.
    """
    def __init__(self):
        # Basic service configuration
        self._name = "my_service"
        self._command = "my.service.script.py --port 8080"
        self._description = "My custom service description"

        # Systemd service dependencies
        self._requires = []  # Hard dependencies (Requires=)
        self._prefers = []   # Soft dependencies (Wants=)
        self._after = []     # Start after these (After=)
        self._before = []    # Start before these (Before=)

        # Dependency realization (built/installed before service creation)
        self._requires_deps = []     # OBT dep modules
        self._requires_dockers = []  # Docker modules
        self._requires_pips = []     # Python packages

    def info(self):
        """Return service metadata dictionary."""
        return {
            "name": self._name,
            "command": self._command,
            "description": self._description,
            "requires": self._requires,
            "prefers": self._prefers,
            "after": self._after,
            "before": self._before,
            "requires_deps": self._requires_deps,
            "requires_dockers": self._requires_dockers,
            "requires_pips": self._requires_pips,
        }
```

## Commands

### Discovery Commands

#### `obt.systemd.list.py`
List all available service modules.

```bash
$ obt.systemd.list.py
Available Systemd Services:
  ork_logger_http
  ork_database
  my_custom_service
```

#### `obt.systemd.info.py <service_name>`
Show detailed information about a service module.

```bash
$ obt.systemd.info.py ork_logger_http
Service Information:
  Name: ork_logger_http
  Command: ork.logger.httpserver.py
  Description: Orkid HTTP Logger Service - Receives and displays log messages
  Requires Pips: flask, websockets
```

### Service Management Commands

#### `obt.systemd.create.py <service_name> [options]`
Create systemd service files from a module.

**Options:**
- `--deploy` - Deploy to `~/.config/systemd/user/`
- `--start` - Start the service (requires `--deploy`)
- `--enable` - Enable service to start on boot (requires `--deploy`)
- `--dest <path>` - Custom destination folder (default: `${OBT_STAGE}/systemd/<service_name>`)
- `--command <cmd>` - Override command from module

**Examples:**
```bash
# Create service files only
obt.systemd.create.py ork_logger_http

# Create, deploy, start, and enable
obt.systemd.create.py ork_logger_http --deploy --start --enable

# Override command
obt.systemd.create.py ork_logger_http --command "ork.logger.httpserver.py --port 9999" --deploy
```

#### `obt.systemd.start.py <service_name> [options]`
Start (restart) a service.

**Options:**
- `--create` - Create and deploy service files first
- `--enable` - Enable service to start on boot
- `--dest <path>` - Custom destination folder (only with `--create`)
- `--command <cmd>` - Override command (only with `--create`)

**Examples:**
```bash
# Start existing service
obt.systemd.start.py ork_logger_http

# Create, deploy, start, and enable in one command
obt.systemd.start.py ork_logger_http --create --enable
```

#### `obt.systemd.stop.py <service_name>`
Stop a running service.

```bash
obt.systemd.stop.py ork_logger_http
```

#### `obt.systemd.restart.py <service_name>`
Restart a service.

```bash
obt.systemd.restart.py ork_logger_http
```

#### `obt.systemd.enable.py <service_name>`
Enable service to start on boot.

```bash
obt.systemd.enable.py ork_logger_http
```

#### `obt.systemd.disable.py <service_name>`
Disable service from starting on boot.

```bash
obt.systemd.disable.py ork_logger_http
```

#### `obt.systemd.status.py <service_name>`
Show service status.

```bash
obt.systemd.status.py ork_logger_http
```

### User Linger Commands

#### `obt.systemd.userenable.py`
Enable systemd user instance to start on boot (linger).

This allows user services to run even when not logged in - essential for server processes.

```bash
obt.systemd.userenable.py
```

#### `obt.systemd.userdisable.py`
Disable systemd user instance from starting on boot.

User services will only run when logged in (default desktop behavior).

```bash
obt.systemd.userdisable.py
```

## Dependency Management

### Systemd Service Dependencies

Control service start ordering and requirements using standard systemd dependency directives.

```python
class serviceinfo:
    def __init__(self):
        # Hard dependency - fails if dependency fails
        self._requires = ["postgresql.service"]

        # Soft dependency - doesn't fail if missing (prefers over wants for clarity)
        self._prefers = ["network-online.target"]

        # Ordering - start after these services
        self._after = ["postgresql.service", "network-online.target"]

        # Ordering - start before these services
        self._before = ["my_app.service"]
```

**Systemd directives mapping:**
- `requires` → `Requires=` (hard dependency)
- `prefers` → `Wants=` (soft dependency)
- `after` → `After=` (ordering)
- `before` → `Before=` (ordering)

**Example use cases:**
```python
# Database service depends on system postgres
self._requires = ["postgresql.service"]
self._after = ["postgresql.service"]

# App server depends on logger service
self._requires = ["ork_logger_http.service"]
self._after = ["ork_logger_http.service"]

# Prefer network but don't fail without it
self._prefers = ["network-online.target"]
self._after = ["network-online.target"]
```

### Dependency Realization

Automatically build, install, and prepare dependencies **before** the service is created.

#### OBT Dep Modules (`requires_deps`)

Build and install OBT dependency modules to `${OBT_STAGE}/`.

```python
self._requires_deps = ["lua", "vulkan", "qt5"]
```

**How it works:**
- Calls `obt.dep.require(dep_name)` for each dep
- Checks if already built (manifest exists)
- Builds from source and installs to staging if needed
- Fails service creation if dep build fails

#### Docker Modules (`requires_dockers`)

Build docker containers/images before service starts.

```python
self._requires_dockers = ["postgres_dev", "redis_cache"]
```

**How it works:**
- Calls `obt.docker.descriptor(docker_name).build([])` for each module
- Builds docker container/image
- Fails service creation if docker build fails

#### Python Packages (`requires_pips`)

Install Python packages into the staging Python environment.

```python
self._requires_pips = ["flask", "redis", "sqlalchemy"]
```

**How it works:**
- Runs `ork.python -m pip install <packages>`
- Uses Orkid's Python wrapper (staging venv)
- Installs all packages in a single command
- Fails service creation if pip install fails

#### Complete Example

```python
class serviceinfo:
    def __init__(self):
        self._name = "ork_web_app"
        self._command = "ork.web.server.py"
        self._description = "Orkid Web Application Server"

        # Systemd dependencies
        self._requires = ["ork_logger_http.service"]
        self._after = ["ork_logger_http.service", "postgresql.service"]

        # Realization dependencies
        self._requires_deps = ["qt5", "vulkan"]        # Build these first
        self._requires_dockers = ["postgres_dev"]      # Build this docker first
        self._requires_pips = ["flask", "psycopg2"]    # Install these packages first
```

When creating this service:
1. Qt5 and Vulkan are built/installed to `${OBT_STAGE}/`
2. `postgres_dev` docker image is built
3. Flask and psycopg2 are installed via pip
4. Service file is created with dependencies on logger and postgres services
5. Service is deployed and started

## Environment Handling

Services automatically inherit the OBT build environment through a two-layer approach:

### Layer 1: Static Environment Variables

Environment variables from `${OBT_STAGE}/obt-launch-env` are injected into the service file as `Environment=` directives. Only uncommented `export` statements are included.

**Example from obt-launch-env:**
```bash
export ORKID_VULKAN_VALIDATE=1
export ORKID_GRAPHICS_API=VULKAN
# export DEBUG_MODE=1  # This is ignored (commented)
```

**Result in service file:**
```ini
[Service]
Environment="ORKID_VULKAN_VALIDATE=1"
Environment="ORKID_GRAPHICS_API=VULKAN"
Environment="VIRTUAL_ENV=/home/user/.venv"
Environment="OBT_STAGE=/home/user/.staging"
```

### Layer 2: Dynamic Environment Setup

The service command is wrapped in `obt.env.launch.py` which regenerates auto-generated environment variables at runtime:

```ini
ExecStart=/path/to/obt.env.launch.py --stagedir /home/user/.staging --command "..."
```

This ensures:
- `PATH`, `LD_LIBRARY_PATH`, `PYTHONPATH` are correctly configured
- SDK locations are registered
- Build tool paths are available
- Environment is consistent with interactive OBT shell

### Command Resolution

Python scripts are automatically resolved and transformed:

**Service module:**
```python
self._command = "ork.logger.httpserver.py --port 8080"
```

**Result in service file:**
```ini
ExecStart=/path/to/obt.env.launch.py --stagedir /home/user/.staging \
  --command "/home/user/.staging/pyvenv/bin/python3 /full/path/to/ork.logger.httpserver.py --port 8080"
```

## Generated Service Files

Service files are created at:
- Default: `${OBT_STAGE}/systemd/<service_name>/<service_name>.service`
- Deployed: `~/.config/systemd/user/<service_name>.service`

### Example Service File

```ini
[Unit]
Description=ork_logger_http service
Requires=postgresql.service
Wants=network-online.target
After=network.target postgresql.service network-online.target

[Service]
Type=simple
Environment="VK_LAYER_PATH=/usr/share/vulkan/explicit_layer.d:..."
Environment="ORKID_VULKAN_VALIDATE=1"
Environment="ORKID_GRAPHICS_API=VULKAN"
Environment="VIRTUAL_ENV=/home/user/.venv"
Environment="OBT_STAGE=/home/user/.staging"

ExecStart=/home/user/.venv/bin/obt.env.launch.py --stagedir /home/user/.staging \
  --command "/home/user/.staging/pyvenv/bin/python3 /path/to/ork.logger.httpserver.py"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## Common Workflows

### Creating a New Service

1. **Create the service module** at `~/.venv/obt/modules/systemd/my_service.py`:

```python
class serviceinfo:
    def __init__(self):
        self._name = "my_service"
        self._command = "my.script.py"
        self._description = "My custom service"
        self._requires = []
        self._prefers = []
        self._after = []
        self._before = []
        self._requires_deps = []
        self._requires_dockers = []
        self._requires_pips = []

    def info(self):
        return {
            "name": self._name,
            "command": self._command,
            "description": self._description,
            "requires": self._requires,
            "prefers": self._prefers,
            "after": self._after,
            "before": self._before,
            "requires_deps": self._requires_deps,
            "requires_dockers": self._requires_dockers,
            "requires_pips": self._requires_pips,
        }
```

2. **Verify the module** is discovered:

```bash
obt.systemd.list.py
obt.systemd.info.py my_service
```

3. **Create and deploy** the service:

```bash
# Option 1: Create, deploy, start, and enable
obt.systemd.create.py my_service --deploy --start --enable

# Option 2: Use start command with --create
obt.systemd.start.py my_service --create --enable
```

4. **Check status**:

```bash
obt.systemd.status.py my_service
```

### Running Services on Boot

1. **Enable user linger** (allows services to run when not logged in):

```bash
obt.systemd.userenable.py
```

2. **Enable the service**:

```bash
obt.systemd.enable.py my_service
```

3. **Verify** after reboot:

```bash
obt.systemd.status.py my_service
```

### Service with Dependencies

```python
class serviceinfo:
    def __init__(self):
        self._name = "my_web_app"
        self._command = "my.web.server.py"
        self._description = "Web application with full dependency stack"

        # Wait for these systemd services
        self._requires = ["ork_logger_http.service", "postgresql.service"]
        self._after = ["ork_logger_http.service", "postgresql.service"]

        # Build these before creating service
        self._requires_deps = ["qt5", "vulkan"]
        self._requires_dockers = ["postgres_dev"]
        self._requires_pips = ["flask", "jinja2", "sqlalchemy"]
```

Create this service:
```bash
obt.systemd.start.py my_web_app --create --enable
```

This will:
1. Build Qt5 and Vulkan (if not already built)
2. Build postgres_dev docker image
3. Install Flask, Jinja2, and SQLAlchemy via pip
4. Create service file with systemd dependencies
5. Deploy, start, and enable the service

## Implementation Details

### Module Discovery

The system searches `$OBT_MODULES_PATH` (colon-delimited) for service modules:

```python
# From obt/systemd.py
def enumerate():
    services = set()
    module_paths = os.environ.get("OBT_MODULES_PATH", "").split(":")
    for base_path in module_paths:
        systemd_dir = Path(base_path) / "systemd"
        if systemd_dir.exists():
            for py_file in systemd_dir.glob("*.py"):
                if py_file.stem != "__init__":
                    services.add(py_file.stem)
    return sorted(services)
```

### Module Loading

Services are loaded dynamically using `importlib`:

```python
def requires(service_name):
    module_paths = os.environ.get("OBT_MODULES_PATH", "").split(":")
    for base_path in module_paths:
        systemd_dir = Path(base_path) / "systemd"
        module_file = systemd_dir / f"{service_name}.py"
        if module_file.exists():
            spec = importlib.util.spec_from_file_location(...)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.serviceinfo()
    raise RuntimeError(f"Service module '{service_name}' not found")
```

### Idempotence

All operations are idempotent:
- Service file creation overwrites existing files
- `--deploy` copies to systemd user directory (overwrites)
- `--start` uses `systemctl --user restart` (not stop+start)
- `--enable` is safe to run multiple times
- Dependency realization checks if already built before rebuilding

## File Locations

- **Service modules**: `$OBT_MODULES_PATH/systemd/*.py`
- **Development modules**: `~/.venv/obt/modules/systemd/`
- **Git repository**: `~/ork.build/modules/systemd/`
- **Service files (staging)**: `${OBT_STAGE}/systemd/<service_name>/`
- **Service files (deployed)**: `~/.config/systemd/user/`
- **Commands**: `~/.venv/obt/bin_priv/obt.systemd.*.py`
- **Core module**: `~/.venv/lib/python3.12/site-packages/obt/systemd.py`
- **Helper functions**: `~/.venv/lib/python3.12/site-packages/obt/systemd_helpers.py`

## Integration with OBT Ecosystem

The systemd infrastructure integrates seamlessly with existing OBT systems:

- **Dep modules**: 243+ dependency modules in `dep/` directories
- **Docker modules**: Docker container definitions in `docker/` directories
- **Environment system**: `obt-launch-env` and `obt.env.launch.py`
- **Command patterns**: Follows reverse DNS naming (`obt.systemd.*.py`)
- **Module patterns**: Same discovery/loading as `dep/` and `docker/`
- **Deco system**: Consistent colored output using `obt.deco`

## Troubleshooting

### Service won't start

1. **Check status**:
   ```bash
   obt.systemd.status.py <service_name>
   ```

2. **View logs**:
   ```bash
   journalctl --user -u <service_name>.service
   ```

3. **Verify command resolves**:
   ```bash
   which <command_name>
   ```

4. **Test command manually**:
   ```bash
   obt.env.launch.py --stagedir ${OBT_STAGE} --command "<full_command>"
   ```

### Dependencies not realizing

Check that:
- `OBT_MODULES_PATH` is set and includes module directories
- Dep/docker modules exist: `obt.dep.list.py`, `obt.docker.list.py`
- `ork.python` is in PATH for pip installs

### Service not starting on boot

1. **Check linger is enabled**:
   ```bash
   loginctl show-user $USER | grep Linger
   ```
   Should show `Linger=yes`

2. **Enable linger if needed**:
   ```bash
   obt.systemd.userenable.py
   ```

3. **Verify service is enabled**:
   ```bash
   systemctl --user is-enabled <service_name>.service
   ```

### Environment variables missing

- User-configured vars go in `${OBT_STAGE}/obt-launch-env` as `export VAR=value`
- Auto-generated vars (PATH, etc.) come from `obt.env.launch.py` wrapper
- Both `VIRTUAL_ENV` and `OBT_STAGE` are automatically added

## Future Enhancements

Potential improvements for future versions:

- Service groups/targets for managing related services together
- Log aggregation integration with ork.logger.httpserver
- Health check definitions and monitoring
- Resource limits (memory, CPU) in service modules
- Template-based service generation for common patterns
- Integration with CI/CD pipelines
- Service migration tools for moving between environments
