#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from obt import systemd
from obt.systemd_helpers import create_systemd_service
from obt.deco import Deco
from obt import command

def main():
    parser = argparse.ArgumentParser(description="Start (and optionally create/enable) a systemd service")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")
    parser.add_argument("--create", action="store_true", help="Create service files first")
    parser.add_argument("--enable", action="store_true", help="Enable the service to start on boot")
    parser.add_argument("--dest", help="Destination folder for service files (default: ${OBT_STAGE}/systemd/<service_name>)")
    parser.add_argument("--command", help="Override command from service module (only with --create)")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Load service module
        svc = systemd.requires(args.service_name)
        info = svc.info()

        # Create service if requested
        if args.create:
            command_str = args.command if args.command else info['command']

            if args.dest:
                dest_folder = args.dest
            else:
                obt_stage = os.environ.get("OBT_STAGE")
                if not obt_stage:
                    print(deco.err("OBT_STAGE environment variable not set"))
                    exit(1)
                dest_folder = str(Path(obt_stage) / "systemd" / args.service_name)

            create_systemd_service(
                args.service_name,
                dest_folder,
                command_str,
                deploy=True,
                start=True,
                enable=args.enable,
                requires=info.get('requires', []),
                prefers=info.get('prefers', []),
                after=info.get('after', []),
                before=info.get('before', []),
                requires_deps=info.get('requires_deps', []),
                requires_dockers=info.get('requires_dockers', []),
                requires_pips=info.get('requires_pips', []),
                requires_tty=info.get('requires_tty', None),
                as_system_service=info.get('as_system_service', False)
            )
        else:
            # Just start (restart) the service
            print(deco.inf(f"Starting service: {args.service_name}"))

            # Use sudo systemctl for system services, systemctl --user for user services
            if info.get('as_system_service', False):
                command.run(["sudo", "systemctl", "restart", f"{args.service_name}.service"])
                if args.enable:
                    print(deco.inf(f"Enabling service: {args.service_name}"))
                    command.run(["sudo", "systemctl", "enable", f"{args.service_name}.service"])
            else:
                command.run(["systemctl", "--user", "restart", f"{args.service_name}.service"])
                if args.enable:
                    print(deco.inf(f"Enabling service: {args.service_name}"))
                    command.run(["systemctl", "--user", "enable", f"{args.service_name}.service"])

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
