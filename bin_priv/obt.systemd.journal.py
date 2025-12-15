#!/usr/bin/env python3

import argparse
from obt import systemd
from obt.deco import Deco
from obt import command

def main():
    parser = argparse.ArgumentParser(description="Show journal logs for a systemd service")
    parser.add_argument("service_name", help="Service module name (e.g., ork_logger_http)")
    parser.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show (default: 50)")
    parser.add_argument("-f", "--follow", action="store_true", help="Follow log output")

    args = parser.parse_args()
    deco = Deco()

    try:
        # Verify service module exists
        svc = systemd.requires(args.service_name)
        info = svc.info()

        print(deco.inf(f"Journal logs for service: {args.service_name}"))

        # Build journalctl command based on service type
        journal_cmd = ["journalctl"]

        # Add --user flag only if NOT a system service
        if not info.get('as_system_service', False):
            journal_cmd.append("--user")

        journal_cmd.extend(["-u", f"{args.service_name}.service"])

        if args.follow:
            journal_cmd.append("-f")
        else:
            journal_cmd.extend(["-n", str(args.lines)])

        journal_cmd.append("--no-pager")

        # Run journalctl
        command.run(journal_cmd)

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
