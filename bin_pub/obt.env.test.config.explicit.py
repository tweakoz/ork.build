#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, multiprocessing, json

as_main = (__name__ == '__main__')

Path = pathlib.Path
curwd = Path(os.getcwd())
###########################################

file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
par2_dir = os.path.dirname(file_dir)

root_dir = Path(par2_dir)
scripts_dir = root_dir/"scripts"
project_dir = root_dir

sys.path.append(str(file_dir))

###########################################

parser = argparse.ArgumentParser(description='obt.build environment explicit tester')
parser.add_argument('--stagedir', metavar="stagedir", help='staging folder for session' )
parser.add_argument('--projectdir',metavar="projectdir",help='sidechain project directory(with obt manifest)')
parser.add_argument('--inplace', action="store_true" )
parser.add_argument("--quiet", action="store_true", help="no output")
parser.add_argument("--command", metavar="command", help="execute in environ")
parser.add_argument("--numcores", metavar="numcores", help="numcores for environment")

###########################################

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################

from _obt_config import configFromCommandLine
config = configFromCommandLine(args)
config.dump()

