#!/usr/bin/env python3

import argparse
from obt import macos, path

parser = argparse.ArgumentParser(description='show librarys referenced by macho binary')
parser.add_argument('--machobin', help='macho file to show libs on' )

_args = vars(parser.parse_args())

if _args["machobin"]!=None:
	machobin = _args["machobin"]
	macos.macho_dump(machobin)
