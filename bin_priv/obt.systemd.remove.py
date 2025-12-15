#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from obt import systemd
from obt.deco import Deco
from obt import command

def main():
    parser = argparse.ArgumentParser(description="Remove a systemd service unit file")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")
    parser.add_argument("--force", action="store_true", help="Remove without confirmation")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Verify service module exists
        svc = systemd.requires(args.service_name)
        info = svc.info()

        # Determine service file location
        if info.get('as_system_service', False):
            service_file = Path(f"/etc/systemd/system/{args.service_name}.service")
            is_system = True
        else:
            service_file = Path.home() / ".config" / "systemd" / "user" / f"{args.service_name}.service"
            is_system = False

        if not service_file.exists():
            print(deco.err(f"Service file not found: {service_file}"))
            exit(1)

        # Confirm removal unless --force
        if not args.force:
            response = input(f"Remove {service_file}? [y/N] ")
            if response.lower() != 'y':
                print(deco.inf("Cancelled"))
                exit(0)

        print(deco.inf(f"Removing service file: {service_file}"))

        # Stop and disable service first
        if is_system:
            command.run(["sudo", "systemctl", "stop", f"{args.service_name}.service"])
            command.run(["sudo", "systemctl", "disable", f"{args.service_name}.service"])
            command.run(["sudo", "rm", str(service_file)])
            command.run(["sudo", "systemctl", "daemon-reload"])
        else:
            command.run(["systemctl", "--user", "stop", f"{args.service_name}.service"])
            command.run(["systemctl", "--user", "disable", f"{args.service_name}.service"])
            service_file.unlink()
            command.run(["systemctl", "--user", "daemon-reload"])

        print(deco.key(f"Service {args.service_name} removed"))

        # Also remove staging folder if it exists
        obt_stage = os.environ.get("OBT_STAGE")
        if obt_stage:
            staging_dir = Path(obt_stage) / "systemd" / args.service_name
            if staging_dir.exists():
                print(deco.inf(f"Removing staging folder: {staging_dir}"))
                import shutil
                shutil.rmtree(staging_dir)

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
