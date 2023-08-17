#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, site, pathlib, argparse

###############################################################################

Path = pathlib.Path
curwd = Path(os.getcwd())
homedir = Path(os.getenv("HOME"))
globaldir = homedir/".obt-global"

###############################################################################

parser = argparse.ArgumentParser(description='obt.build environment global dir management')
parser.add_argument('--tree', action="store_true", help='list globaldir directory tree' )
parser.add_argument('--du', action="store_true", help='list globaldir directory usage' )
args = vars(parser.parse_args())
if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###############################################################################

def ensure_exists():
  if not globaldir.exists():
    print("OBT global directory does not exist: %s" % globaldir)
    sys.exit(0)

###############################################################################

if args["tree"]==True:
    ensure_exists()
    os.system("tree %s" % str(globaldir))

###############################################################################

if args["du"]==True:
    ensure_exists()
    print( "######################################################")
    print( "## OBT global directory usage: (MiB)")
    print( "######################################################")
    os.system("du -s -m %s" % str(globaldir/"downloads"))
    os.system("du -s -m %s" % str(globaldir/"gitcache"))
