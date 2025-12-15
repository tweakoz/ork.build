#!/usr/bin/env python3

from obt.deco import Deco
from obt import command

def main():
    deco = Deco()

    print(deco.inf("Enabling systemd user instance to start on boot (linger)"))
    print(deco.inf("This allows user services to run even when not logged in"))

    # Enable linger for the current user
    exit_code = command.run(["loginctl", "enable-linger"])

    if exit_code == 0:
        print(deco.key("User systemd instance enabled on boot"))
    else:
        print(deco.err("Failed to enable user systemd instance"))
        exit(1)

if __name__ == "__main__":
    main()
