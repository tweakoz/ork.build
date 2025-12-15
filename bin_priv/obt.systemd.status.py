#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path
from obt import systemd
from obt.deco import Deco
from obt import command

def get_service_state(service_name, is_system):
    """Check if service is active and enabled."""
    try:
        if is_system:
            active_result = subprocess.run(
                ["systemctl", "is-active", f"{service_name}.service"],
                capture_output=True, text=True
            )
            enabled_result = subprocess.run(
                ["systemctl", "is-enabled", f"{service_name}.service"],
                capture_output=True, text=True
            )
        else:
            active_result = subprocess.run(
                ["systemctl", "--user", "is-active", f"{service_name}.service"],
                capture_output=True, text=True
            )
            enabled_result = subprocess.run(
                ["systemctl", "--user", "is-enabled", f"{service_name}.service"],
                capture_output=True, text=True
            )

        is_active = active_result.stdout.strip() == "active"
        is_enabled = enabled_result.stdout.strip() in ["enabled", "static", "enabled-runtime"]

        return is_active, is_enabled
    except Exception:
        return False, False

def is_deployed(service_name, is_system):
    """Check if service file is deployed."""
    if is_system:
        service_file = Path(f"/etc/systemd/system/{service_name}.service")
    else:
        service_file = Path.home() / ".config" / "systemd" / "user" / f"{service_name}.service"
    return service_file.exists()

def show_all_services():
    """Show table of all enumerated services with their states."""
    deco = Deco()
    services = systemd.enumerate()

    if not services:
        print("No systemd service modules found.")
        return

    # Collect service info
    service_data = []
    for service_name in services:
        try:
            svc = systemd.requires(service_name)
            info = svc.info()
            is_system = info.get('as_system_service', False)
            deployed = is_deployed(service_name, is_system)
            active, enabled = get_service_state(service_name, is_system) if deployed else (False, False)

            service_data.append({
                'name': service_name,
                'type': 'system' if is_system else 'user',
                'deployed': deployed,
                'active': active,
                'enabled': enabled
            })
        except Exception:
            # Skip services that can't be loaded
            continue

    if not service_data:
        print("No valid service modules found.")
        return

    # Calculate column widths
    max_name_len = max(len(s['name']) for s in service_data)
    name_width = max(max_name_len, len("SERVICE"), 24)  # Minimum 24 chars for name

    # Define fixed column widths for alignment (odd numbers for better centering)
    type_width = 9
    state_width = 7  # Odd width for centering checkmarks

    # ANSI color codes for green and red
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

    # Print header (pad headers to match odd widths)
    print(deco.key(f"{'SERVICE':<{name_width}}  {'TYPE':<{type_width}}  {'DEPLOYED':<{state_width}}  {'ACTIVE':<{state_width}}  {'ENABLED':<{state_width}}"))
    print(deco.val("─" * (name_width + type_width + state_width * 3 + 8)))

    # Print service rows
    for s in sorted(service_data, key=lambda x: x['name']):
        # Build row with proper alignment
        name_col = f"{s['name']:<{name_width}}"
        type_col = f"{s['type']:<{type_width}}"

        # Center the symbols within their columns
        left_pad = (state_width - 1) // 2
        right_pad = state_width - 1 - left_pad

        # Color the symbols and center them
        deployed_sym = "✓" if s['deployed'] else "✗"
        deployed_color = GREEN if s['deployed'] else RED
        deployed_col = f"{' ' * left_pad}{deployed_color}{deployed_sym}{RESET}{' ' * right_pad}"

        active_sym = "✓" if s['active'] else "✗"
        active_color = GREEN if s['active'] else RED
        active_col = f"{' ' * left_pad}{active_color}{active_sym}{RESET}{' ' * right_pad}"

        enabled_sym = "✓" if s['enabled'] else "✗"
        enabled_color = GREEN if s['enabled'] else RED
        enabled_col = f"{' ' * left_pad}{enabled_color}{enabled_sym}{RESET}{' ' * right_pad}"

        print(f"{name_col}  {type_col}  {deployed_col}  {active_col}  {enabled_col}")

def main():
    parser = argparse.ArgumentParser(description="Show status of a systemd service")
    parser.add_argument("service_name", nargs='?', help="Service module name (e.g., ork_logger_http). If omitted, shows all services.")

    args = parser.parse_args()
    deco = Deco()

    try:
        if not args.service_name:
            # Show table of all services
            show_all_services()
        else:
            # Show detailed status of specific service
            svc = systemd.requires(args.service_name)
            info = svc.info()

            print(deco.inf(f"Status of service: {args.service_name}"))

            # Use sudo systemctl for system services, systemctl --user for user services
            if info.get('as_system_service', False):
                command.run(["sudo", "systemctl", "status", f"{args.service_name}.service"])
            else:
                command.run(["systemctl", "--user", "status", f"{args.service_name}.service"])

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
