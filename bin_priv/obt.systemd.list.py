#!/usr/bin/env python3

from obt import systemd
from obt.deco import Deco

def main():
    deco = Deco()
    services = systemd.enumerate()

    if not services:
        print("No systemd service modules found.")
        return

    print(deco.key("Available Systemd Services:"))
    for service_name in services:
        print(f"  {deco.val(service_name)}")

if __name__ == "__main__":
    main()
