#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from obt import systemd
from obt.systemd_helpers import create_systemd_service
from obt.deco import Deco

def main():
    parser = argparse.ArgumentParser(description="Create systemd user service for OBT/Uni projects")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")
    parser.add_argument("--dest", help="Destination folder for service files (default: ${OBT_STAGE}/systemd/<service_name>)")
    parser.add_argument("--command", help="Override command from service module")
    parser.add_argument("--deploy", action="store_true", help="Deploy to ~/.config/systemd/user/")
    parser.add_argument("--start", action="store_true", help="Restart the service (requires --deploy)")
    parser.add_argument("--enable", action="store_true", help="Enable the service to start on boot (requires --deploy)")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Load service module
        svc = systemd.requires(args.service_name)
        info = svc.info()

        # Use command from module unless overridden
        command_str = args.command if args.command else info['command']

        # Default dest to ${OBT_STAGE}/systemd/<service_name>
        if args.dest:
            dest_folder = args.dest
        else:
            obt_stage = os.environ.get("OBT_STAGE")
            if not obt_stage:
                print(deco.err("OBT_STAGE environment variable not set"))
                exit(1)
            dest_folder = str(Path(obt_stage) / "systemd" / args.service_name)

        # Create the service
        create_systemd_service(
            args.service_name,
            dest_folder,
            command_str,
            deploy=args.deploy,
            start=args.start,
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

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
