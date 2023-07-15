#!/usr/bin/env python3

import os, argparse, subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description='obt.otbuild test buildscript')
parser.add_argument('--stage', metavar="stagedir", help='staging directory' )
args = vars(parser.parse_args())
assert(args["stage"]!=None)
STAGEDIR = Path(args["stage"])
SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))
os.chdir(SCRIPTDIR)

cmdlist = ["./bin/init_env.py",
           "--create",STAGEDIR,
           "--command","obt.dep.build.py pkgconfig"]

proc = subprocess.Popen(cmdlist)
proc.wait()
