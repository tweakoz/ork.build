#!/usr/bin/env python3

import os
import re
import shutil
from obt import path, pathtools, command
from obt.debug_helpers import find_executable, is_python_script
from obt.deco import Deco
import obt.dep
import obt.docker

def parse_obt_launch_env():
    """
    Parse ${OBT_STAGE}/obt-launch-env and extract uncommented export statements and project list.
    Returns a tuple of (env_vars dict, projects list, numcores int or None).
    """
    obt_stage = os.environ.get("OBT_STAGE")
    if not obt_stage:
        raise RuntimeError("OBT_STAGE environment variable not set")

    launch_env_file = path.Path(obt_stage) / "obt-launch-env"
    if not launch_env_file.exists():
        raise RuntimeError(f"obt-launch-env file not found at {launch_env_file}")

    env_vars = {}
    projects = []
    numcores = None
    export_pattern = re.compile(r'^\s*export\s+([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$')

    with open(launch_env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Check for obt.env.launch.py line with --project and --numcores args
            if 'obt.env.launch.py' in line:
                # Extract all --project arguments
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == '--project' and i + 1 < len(parts):
                        projects.append(parts[i + 1])
                    elif part == '--numcores' and i + 1 < len(parts):
                        numcores = int(parts[i + 1])
                continue

            match = export_pattern.match(line)
            if match:
                var_name = match.group(1)
                var_value = match.group(2)
                # Remove quotes if present
                var_value = var_value.strip('"').strip("'")
                env_vars[var_name] = var_value

    return env_vars, projects, numcores

def realize_dependencies(service_name, requires_deps, requires_dockers, requires_pips):
    """
    Realize (build/install) all dependencies before creating the service.

    Args:
        service_name: Name of the service (for logging)
        requires_deps: List of OBT dep modules to build/install
        requires_dockers: List of Docker modules to build
        requires_pips: List of Python packages to pip install

    Returns:
        True if all dependencies were successfully realized, False otherwise
    """
    deco = Deco()

    # Realize OBT dep modules
    if requires_deps:
        print(deco.inf(f"Realizing OBT dependencies for {service_name}: {', '.join(requires_deps)}"))
        for dep_name in requires_deps:
            print(deco.key(f"  Building/installing dep: {dep_name}"))
            success = obt.dep.require(dep_name)
            if not success:
                print(deco.err(f"Failed to realize dep: {dep_name}"))
                return False

    # Build Docker modules
    if requires_dockers:
        print(deco.inf(f"Building Docker modules for {service_name}: {', '.join(requires_dockers)}"))
        for docker_name in requires_dockers:
            print(deco.key(f"  Building docker: {docker_name}"))
            try:
                docker_module = obt.docker.descriptor(docker_name)
                if docker_module is None:
                    print(deco.err(f"Docker module not found: {docker_name}"))
                    return False
                docker_module.build([])
            except Exception as e:
                print(deco.err(f"Failed to build docker module {docker_name}: {e}"))
                return False

    # Install pip packages
    if requires_pips:
        print(deco.inf(f"Installing pip packages for {service_name}: {', '.join(requires_pips)}"))
        ork_python = find_executable("ork.python")
        if not ork_python:
            print(deco.err("ork.python not found in PATH"))
            return False

        # Install all packages in a single pip command
        pip_cmd = [ork_python, "-m", "pip", "install"] + requires_pips
        print(deco.key(f"  Running: {' '.join(pip_cmd)}"))
        exit_code = command.run(pip_cmd)
        if exit_code != 0:
            print(deco.err(f"Failed to install pip packages"))
            return False

    return True

def create_service_from_args(args):
    """
    Thin wrapper to call create_systemd_service from argparse args.

    Args:
        args: argparse.Namespace with attributes: name, dest, command, deploy, start, enable
    """
    create_systemd_service(
        service_name=args.name,
        dest_folder=args.dest,
        command_str=args.command,
        deploy=getattr(args, 'deploy', False),
        start=getattr(args, 'start', False),
        enable=getattr(args, 'enable', False)
    )

def create_systemd_service(service_name, dest_folder, command_str, **kwargs):
    """
    Create a systemd user service file.

    Args:
        service_name: Name of the service
        dest_folder: Destination folder for service files
        command_str: Command to run in the service
        **kwargs: Optional keyword arguments:
            deploy (bool): If True, also deploy to ~/.config/systemd/user/
            start (bool): If True, restart the service (requires deploy)
            enable (bool): If True, enable the service to start on boot (requires deploy)
            requires (list): Hard dependencies (Requires=)
            prefers (list): Soft dependencies (Wants=)
            after (list): Start after these services (After=)
            before (list): Start before these services (Before=)
            requires_deps (list): OBT dep modules to realize
            requires_dockers (list): Docker modules to build
            requires_pips (list): Python packages to pip install
            requires_tty (int): TTY number for graphical daemons (e.g., 7 for /dev/tty7)
            as_system_service (bool): Install as system service (requires sudo)
    """
    deploy = kwargs.get('deploy', False)
    start = kwargs.get('start', False)
    enable = kwargs.get('enable', False)
    requires = kwargs.get('requires', [])
    prefers = kwargs.get('prefers', [])
    after = kwargs.get('after', [])
    before = kwargs.get('before', [])
    requires_deps = kwargs.get('requires_deps', [])
    requires_dockers = kwargs.get('requires_dockers', [])
    requires_pips = kwargs.get('requires_pips', [])
    requires_tty = kwargs.get('requires_tty', None)
    as_system_service = kwargs.get('as_system_service', False)

    # Realize dependencies before creating service
    if requires_deps or requires_dockers or requires_pips:
        success = realize_dependencies(service_name, requires_deps, requires_dockers, requires_pips)
        if not success:
            raise RuntimeError(f"Failed to realize dependencies for service: {service_name}")
    # Ensure dest folder exists (including parents)
    dest_path = path.Path(dest_folder)
    dest_path.mkdir(parents=True, exist_ok=True)

    # Parse environment and projects from obt-launch-env
    env_vars, projects, numcores = parse_obt_launch_env()

    # Add critical OBT environment variables
    if "VIRTUAL_ENV" in os.environ:
        env_vars["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]

    obt_stage = os.environ.get("OBT_STAGE")
    if not obt_stage:
        raise RuntimeError("OBT_STAGE environment variable not set")
    env_vars["OBT_STAGE"] = obt_stage

    # Find obt.env.launch.py in PATH
    obt_env_launch = shutil.which("obt.env.launch.py")
    if not obt_env_launch:
        raise RuntimeError("obt.env.launch.py not found in PATH")

    # Resolve the command path and handle Python scripts
    # First expand any environment variables in the command string
    command_str = os.path.expandvars(command_str)

    # Extract just the command name (first word before any arguments)
    command_parts = command_str.split(None, 1)  # Split on whitespace, max 1 split
    command_name = command_parts[0]
    command_args = command_parts[1] if len(command_parts) > 1 else ""

    # Find the executable
    resolved_command = find_executable(command_name)
    if not resolved_command:
        raise RuntimeError(f"Command '{command_name}' not found in PATH")

    # If it's a Python script, extract python interpreter from shebang
    if is_python_script(resolved_command):
        # Read shebang to get the python interpreter
        with open(resolved_command) as f:
            shebang = f.readline().strip()

        # Extract python interpreter (e.g., "ork.python" or "python3")
        # Shebang format: #!/usr/bin/env ork.python or #!/usr/bin/python3
        shebang_parts = shebang.split()
        if len(shebang_parts) >= 2:
            if 'env' in shebang_parts[-2]:
                # #!/usr/bin/env ork.python
                python_name = shebang_parts[-1]
            else:
                # #!/usr/bin/python3
                python_name = shebang_parts[-1].split('/')[-1]
        else:
            python_name = "python3"  # fallback

        python_path = find_executable(python_name)
        if not python_path:
            raise RuntimeError(f"{python_name} not found in PATH")
        # Rebuild command: <python> /full/path/to/script.py args...
        full_command = f"{python_path} {resolved_command}"
        if command_args:
            full_command += f" {command_args}"
    else:
        # Use resolved path with original args
        full_command = resolved_command
        if command_args:
            full_command += f" {command_args}"

    # Build service file content
    service_content = f"[Unit]\n"
    service_content += f"Description={service_name} service\n"

    # Add dependency directives
    if requires:
        service_content += f"Requires={' '.join(requires)}\n"
    if prefers:
        service_content += f"Wants={' '.join(prefers)}\n"

    # Build After= line (always include network.target)
    after_list = ["network.target"]
    after_list.extend(after)
    service_content += f"After={' '.join(after_list)}\n"

    # Add Before= if specified
    if before:
        service_content += f"Before={' '.join(before)}\n"

    # Add getty conflict for TTY services
    if requires_tty is not None:
        service_content += f"Conflicts=getty@tty{requires_tty}.service\n"
        service_content += f"After=getty@tty{requires_tty}.service\n"

    service_content += "\n[Service]\n"
    service_content += "Type=simple\n"

    # For system services, specify which user to run as
    if as_system_service:
        import getpass
        current_user = getpass.getuser()
        service_content += f"User={current_user}\n"

    # Add TTY configuration for graphical daemons
    if requires_tty is not None:
        # Don't use StandardInput=tty for user services (permission denied)
        # The app will open the DRM device directly
        service_content += "StandardOutput=journal\n"
        service_content += "StandardError=journal\n"

    # Add environment variables
    for var_name, var_value in env_vars.items():
        service_content += f'Environment="{var_name}={var_value}"\n'

    # Add ExecStart with obt.env.launch.py wrapper (always needs --stagedir)
    # Build arguments from parsed obt-launch-env
    launch_args = f"--stagedir {obt_stage}"

    if numcores is not None:
        launch_args += f" --numcores {numcores}"

    for project in projects:
        # Expand ~ to full path for systemd compatibility
        expanded_project = str(path.Path(project).expanduser())
        launch_args += f" --project {expanded_project}"

    service_content += f'\nExecStart={obt_env_launch} {launch_args} --command "{full_command}"\n'
    service_content += """Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""

    # Write to dest folder
    service_file = dest_path / f"{service_name}.service"
    with open(service_file, 'w') as f:
        f.write(service_content)

    print(f"Created service file: {service_file}")

    # Deploy if requested
    if deploy:
        if as_system_service:
            # System service: deploy to /etc/systemd/system (requires sudo)
            deco = Deco()
            system_folder = path.Path("/etc/systemd/system")
            deployed_service_file = system_folder / f"{service_name}.service"

            print(deco.inf(f"Installing system service (requires sudo)"))
            # Use sudo to copy
            exit_code = command.run(["sudo", "cp", str(service_file), str(deployed_service_file)])
            if exit_code != 0:
                raise RuntimeError(f"Failed to deploy system service (sudo required)")
            print(f"Deployed service file: {deployed_service_file}")

            # Reload systemd (system)
            command.run(["sudo", "systemctl", "daemon-reload"])
            print(f"System daemon reloaded")
        else:
            # User service: deploy to ~/.config/systemd/user
            user_systemd_folder = path.home() / ".config" / "systemd" / "user"
            user_systemd_folder.mkdir(parents=True, exist_ok=True)

            deployed_service_file = user_systemd_folder / f"{service_name}.service"
            shutil.copy(service_file, deployed_service_file)
            print(f"Deployed service file: {deployed_service_file}")

            # Reload systemd (user)
            command.run(["systemctl", "--user", "daemon-reload"])
            print(f"User daemon reloaded")

    # Start if requested (requires deploy)
    if start:
        if not deploy:
            print("Warning: --start requires --deploy, skipping start")
        else:
            # Restart the service (idempotent: starts if stopped, restarts if running)
            print(f"Restarting service: {service_name}.service")
            if as_system_service:
                command.run(["sudo", "systemctl", "restart", f"{service_name}.service"])
                command.run(["sudo", "systemctl", "status", f"{service_name}.service", "--no-pager"])
            else:
                command.run(["systemctl", "--user", "restart", f"{service_name}.service"])
                command.run(["systemctl", "--user", "status", f"{service_name}.service", "--no-pager"])

    # Enable if requested (requires deploy)
    if enable:
        if not deploy:
            print("Warning: --enable requires --deploy, skipping enable")
        else:
            print(f"Enabling service: {service_name}.service")
            if as_system_service:
                command.run(["sudo", "systemctl", "enable", f"{service_name}.service"])
            else:
                command.run(["systemctl", "--user", "enable", f"{service_name}.service"])
