#!/usr/bin/env python3

import argparse
import os
import subprocess
from pathlib import Path
from obt import systemd
from obt.deco import Deco

def main():
    parser = argparse.ArgumentParser(description="Run a systemd service in foreground with its environment")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")
    parser.add_argument("--user", action="store_true", help="Use user service file (~/.config/systemd/user/)")
    parser.add_argument("--system", action="store_true", help="Use system service file (/etc/systemd/system/)")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Verify service module exists
        svc = systemd.requires(args.service_name)
        info = svc.info()

        # Determine service file location
        if args.system:
            service_file = Path(f"/etc/systemd/system/{args.service_name}.service")
        elif args.user:
            service_file = Path.home() / ".config" / "systemd" / "user" / f"{args.service_name}.service"
        else:
            # Auto-detect based on module config
            if info.get('as_system_service', False):
                service_file = Path(f"/etc/systemd/system/{args.service_name}.service")
            else:
                service_file = Path.home() / ".config" / "systemd" / "user" / f"{args.service_name}.service"

        if not service_file.exists():
            print(deco.err(f"Service file not found: {service_file}"))
            print(deco.inf("Run 'obt.systemd.create.py --deploy' first"))
            exit(1)

        # Parse service file
        env_vars = {}
        exec_start = None

        with open(service_file) as f:
            for line in f:
                line = line.strip()
                # Parse Environment= lines
                if line.startswith('Environment='):
                    # Extract: Environment="VAR=value"
                    env_str = line[len('Environment='):].strip()
                    # Remove quotes
                    if env_str.startswith('"') and env_str.endswith('"'):
                        env_str = env_str[1:-1]
                    # Split on first =
                    if '=' in env_str:
                        var_name, var_value = env_str.split('=', 1)
                        env_vars[var_name] = var_value
                # Parse ExecStart= line
                elif line.startswith('ExecStart='):
                    exec_start = line[len('ExecStart='):].strip()

        if not exec_start:
            print(deco.err("No ExecStart found in service file"))
            exit(1)

        print(deco.key(f"Running service: {args.service_name}"))
        print(deco.inf(f"Service file: {service_file}"))
        print(deco.inf(f"Setting {len(env_vars)} environment variables"))
        print(deco.key(f"Command: {exec_start}"))
        print(deco.val("=" * 80))

        # Set environment and run command
        env = os.environ.copy()
        env.update(env_vars)

        # Run the command in foreground
        subprocess.run(exec_start, shell=True, env=env)

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)
    except KeyboardInterrupt:
        print(deco.inf("\nInterrupted"))
        exit(0)

if __name__ == "__main__":
    main()
