#!/usr/bin/env python3

import argparse
from obt import systemd
from obt.deco import Deco

def main():
    parser = argparse.ArgumentParser(description="Show information about a systemd service module")
    parser.add_argument("service_name", help="Name of the service module")
    args = parser.parse_args()

    deco = Deco()

    try:
        svc = systemd.requires(args.service_name)
        info = svc.info()

        print(deco.key("Service Information:"))
        print(f"  {deco.key('Name')}: {deco.val(info['name'])}")
        print(f"  {deco.key('Command')}: {deco.val(info['command'])}")
        print(f"  {deco.key('Description')}: {deco.val(info['description'])}")

        # Display systemd dependencies if any
        if info.get('requires'):
            print(f"  {deco.key('Requires')}: {deco.val(', '.join(info['requires']))}")
        if info.get('prefers'):
            print(f"  {deco.key('Prefers')}: {deco.val(', '.join(info['prefers']))}")
        if info.get('after'):
            print(f"  {deco.key('After')}: {deco.val(', '.join(info['after']))}")
        if info.get('before'):
            print(f"  {deco.key('Before')}: {deco.val(', '.join(info['before']))}")

        # Display realization dependencies if any
        if info.get('requires_deps'):
            print(f"  {deco.key('Requires Deps')}: {deco.val(', '.join(info['requires_deps']))}")
        if info.get('requires_dockers'):
            print(f"  {deco.key('Requires Dockers')}: {deco.val(', '.join(info['requires_dockers']))}")
        if info.get('requires_pips'):
            print(f"  {deco.key('Requires Pips')}: {deco.val(', '.join(info['requires_pips']))}")
        if info.get('requires_tty') is not None:
            tty_num = info['requires_tty']
            print(f"  {deco.key('Requires TTY')}: {deco.val(f'tty{tty_num}')}")

    except RuntimeError as e:
        print(deco.err(str(e)))
        exit(1)

if __name__ == "__main__":
    main()
