#!/usr/bin/env python3

import argparse
from obt import systemd
from obt.deco import Deco
from obt import command

def main():
    parser = argparse.ArgumentParser(description="Stop a systemd service")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Verify service module exists
        svc = systemd.requires(args.service_name)
        info = svc.info()

        print(deco.inf(f"Stopping service: {args.service_name}"))

        # Use sudo systemctl for system services, systemctl --user for user services
        if info.get('as_system_service', False):
            command.run(["sudo", "systemctl", "stop", f"{args.service_name}.service"])
        else:
            command.run(["systemctl", "--user", "stop", f"{args.service_name}.service"])

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
