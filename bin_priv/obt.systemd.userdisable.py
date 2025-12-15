#!/usr/bin/env python3

from obt.deco import Deco
from obt import command

def main():
    deco = Deco()

    print(deco.inf("Disabling systemd user instance from starting on boot (unlinger)"))
    print(deco.inf("User services will only run when logged in"))

    # Disable linger for the current user
    exit_code = command.run(["loginctl", "disable-linger"])

    if exit_code == 0:
        print(deco.key("User systemd instance disabled from boot"))
    else:
        print(deco.err("Failed to disable user systemd instance"))
        exit(1)

if __name__ == "__main__":
    main()
