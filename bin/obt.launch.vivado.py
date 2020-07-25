#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import argparse, sys, os
from ork import deco, path
from ork.eda.xilinx import vivado

deco = deco.Deco()

epilog = deco.orange("Example (vivado help): %s --batch -- -help"%sys.argv[0])

parser = argparse.ArgumentParser(description='Launch command in EDA Docker Containers',
                                 epilog=epilog)
parser.add_argument('--gui', action="store_true", help=deco.yellow('Launch Vivado GUI'))
parser.add_argument('--batch', action="store_true", help=deco.yellow('Launch Vivado in batch mode, seperate vivado arguments using -- arg break'))
parser.add_argument('remainderargs', nargs=argparse.REMAINDER)

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

cwd = path.Path(os.getcwd())
vctx = vivado.Context(hostdir=cwd)

if _args["gui"]:
  vctx.run(args=[])
elif _args["batch"]:
  remargs = _args["remainderargs"][1:]
  vctx.run_batch(args=remargs)
else:
  assert(False)
