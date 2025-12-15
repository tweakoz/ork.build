#!/usr/bin/env python3

import argparse
from obt import systemd
from obt.deco import Deco
from obt import command

def main():
    parser = argparse.ArgumentParser(description="Restart a systemd service")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Verify service module exists
        svc = systemd.requires(args.service_name)

        print(deco.inf(f"Restarting service: {args.service_name}"))
        command.run(["systemctl", "--user", "restart", f"{args.service_name}.service"])

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
