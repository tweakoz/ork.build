#!/usr/bin/env python3

import argparse
from obt import systemd
from obt.deco import Deco
from obt import command

def main():
    parser = argparse.ArgumentParser(description="Disable a systemd service from starting on boot")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Verify service module exists
        svc = systemd.requires(args.service_name)
        info = svc.info()

        print(deco.inf(f"Disabling service: {args.service_name}"))

        # Use sudo systemctl for system services, systemctl --user for user services
        if info.get('as_system_service', False):
            command.run(["sudo", "systemctl", "disable", f"{args.service_name}.service"])
        else:
            command.run(["systemctl", "--user", "disable", f"{args.service_name}.service"])

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
