#!/usr/bin/env python3

import os, sys, pathlib, argparse, shlex, subprocess, pprint
import obt.deco
import obt.path
import obt.pathtools
import obt.git
from obt.command import run
import json

lxdir = obt.path.builds()/"litex"

parser = argparse.ArgumentParser(description='obt.build environment creator')
parser.add_argument('--create', action="store_true", help='create litex environment' )
parser.add_argument('--enter', action="store_true", help='enter litex environment' )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

if args["create"]:
  obt.pathtools.mkdir(lxdir,clean=True)
  lxdir.chdir()
  cmd1 = ["wget","https://raw.githubusercontent.com/enjoy-digital/litex/e0e9311cebcfa7334b867041850f5aca2dc50f05/litex_setup.py"]
  cmd2 = ["chmod","+x","litex_setup.py"]
  cmd3 = ["./litex_setup.py","init","install","--user"]
  run(cmd1)
  run(cmd2)
  run(cmd3)

elif args["enter"]:
  #lxdir.chdir()
  run(["bash"])
