#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
# TODO: convert to global dependency when OBT has them
#  (since Docker images are practically speaking system global)
###############################################################################

import argparse, sys
from obt import dep, host, path, pathtools, git, command, deco, _dep_fetch

deco = deco.Deco()

parser = argparse.ArgumentParser(description='Install EDA Docker Containers')
parser.add_argument('xdpath', metavar='X', type=str, help='Xilinx installer binary folder')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

xdpath = path.Path(_args["xdpath"])

xuname = "Xilinx_Unified_2020.1_0602_1208_Lin64.bin"
plname = "petalinux-v2020.1-final-installer.run"
xuinst = xdpath/xuname
plinst = xdpath/plname

if not (xuinst.exists() and plinst.exists()):
  print(deco.yellow("You must point to a directory containing:"))
  print("1. "+deco.orange(xuname))
  print("2. "+deco.orange(plname))
  print(deco.red("They must be downloaded manually due to Xilinx licensing restrictions"))
  assert(False)

fetcher = _dep_fetch.GithubFetcher(name="tozeda1",
                                   repospec="tweakoz/petalinux-docker",
                                   revision="2020.1")

builddir = path.builds()/"petalinux-docker"
fetcher.fetch(dest=builddir)

pathtools.copyfile(xuinst,builddir/xuname)
pathtools.copyfile(plinst,builddir/plname)

builddir.chdir()
command.run(["./build.py"])
