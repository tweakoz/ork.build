#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from obt import systemd
from obt.deco import Deco

def main():
    parser = argparse.ArgumentParser(description="Generate a standalone shell script to run a systemd service")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")
    parser.add_argument("-o", "--output", required=True, help="Output shell script path")
    parser.add_argument("--user", action="store_true", help="Use user service file (~/.config/systemd/user/)")
    parser.add_argument("--system", action="store_true", help="Use system service file (/etc/systemd/system/)")
    parser.add_argument("--from", dest="from_file", help="Read from specific service file path")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Determine service file location
        if args.from_file:
            service_file = Path(args.from_file).expanduser()
        else:
            # Verify service module exists
            svc = systemd.requires(args.service_name)
            info = svc.info()

            # First try to find in staging folder (most up-to-date)
            obt_stage = os.environ.get("OBT_STAGE")
            if obt_stage:
                staging_service_file = Path(obt_stage) / "systemd" / args.service_name / f"{args.service_name}.service"
                if staging_service_file.exists():
                    service_file = staging_service_file
                elif args.system:
                    service_file = Path(f"/etc/systemd/system/{args.service_name}.service")
                elif args.user:
                    service_file = Path.home() / ".config" / "systemd" / "user" / f"{args.service_name}.service"
                else:
                    # Auto-detect based on module config
                    if info.get('as_system_service', False):
                        service_file = Path(f"/etc/systemd/system/{args.service_name}.service")
                    else:
                        service_file = Path.home() / ".config" / "systemd" / "user" / f"{args.service_name}.service"
            else:
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
            print(deco.inf("Run 'obt.systemd.create.py' first"))
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

        # Generate shell script
        output_path = Path(args.output).expanduser()

        with open(output_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Generated runner script for {args.service_name} service\n")
            f.write(f"# Source service file: {service_file}\n")
            f.write("\n")

            # Export environment variables
            for var_name, var_value in env_vars.items():
                # Escape single quotes in value
                escaped_value = var_value.replace("'", "'\\''")
                f.write(f"export {var_name}='{escaped_value}'\n")

            f.write("\n")
            f.write("# Execute service command\n")
            f.write(f"{exec_start}\n")

        # Make executable
        output_path.chmod(0o755)

        print(deco.key(f"Created runner script: {output_path}"))
        print(deco.inf(f"Service: {args.service_name}"))
        print(deco.inf(f"Exported {len(env_vars)} environment variables"))
        print(deco.val(f"Run with: {output_path}"))

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
