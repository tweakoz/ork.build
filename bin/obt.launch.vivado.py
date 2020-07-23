#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import argparse, sys
from ork import vivado, deco

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

if _args["gui"]:
  vivado.run(args=[])
elif _args["batch"]:
  remargs = _args["remainderargs"][1:]
  vivado.run(dirmaps={},
             workingdir=None,
             args=["-mode","batch","-nojournal","-nolog"]+remargs)
else:
  assert(False)
