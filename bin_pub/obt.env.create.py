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

###########################################

Path = pathlib.Path
curwd = Path(os.getcwd())
file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
sys.path.append(str(file_dir))

###########################################

parser = argparse.ArgumentParser(description='obt.build environment creator')
parser.add_argument('--stagedir', metavar="createdir", help='create staging folder and enter session' )
parser.add_argument('--wipe', action="store_true", help='wipe old staging folder' )
parser.add_argument('--prompt', metavar="prompt", help='prompt suffix' )
parser.add_argument("--numcores", metavar="numcores", help="numcores for environment")
parser.add_argument("--quiet", action="store_true", help="no output")
parser.add_argument('--novars', action="store_true", help='do not set env vars' )
parser.add_argument('--compose',action='append',help='compose obt project into container')
parser.add_argument('--obttrace',action="store_true",help='enable OBT buildtrace logging')
parser.add_argument('--sshkey',metavar="sshkey",help='ssh key to use with OBT/GIT')
parser.add_argument('--projectdir',metavar="projectdir",help='sidechain project directory(with obt manifest)')
parser.add_argument('--inplace', action="store_true" )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################
# parse args and generate config / core environment vars
###########################################

from _obt_config import configFromCommandLine
obt_config = configFromCommandLine(args)
      
###########################################
# wipe old staging folder ?
###########################################

try_staging = obt_config._stage_dir
if try_staging.exists() and args["wipe"]==False:
  print("Not going to wipe your staging folder<%s> unless you ask... use --wipe"%try_staging)
  sys.exit(0)
if args["wipe"] and try_staging.exists():
  os.system( "rm -rf %s"%try_staging)

###########################################

if args["obttrace"]==True:
  import obt._globals as _glob
  _glob.enableBuildTracing()

##########################################

import obt._envutils 
envsetup = obt._envutils.EnvSetup(obt_config)

###########################################

if args["compose"] != None:
  for item in args["compose"]:
    envsetup.importProject(Path(item))

###########################################
# Create staging folder, scripts
###########################################

import obt.path

obt.path.prefix().mkdir(parents=True,exist_ok=False)
envsetup.lazyMakeDirs()
envsetup.genBashRc(try_staging/".bashrc")
envsetup.genLaunchScript(out_path=try_staging/"obt-launch-env")

###########################################
# build mandatory dependencies
###########################################

MANDATORY_DEPS = ["cmake","python","pydefaults"]

import obt.dep
for item in MANDATORY_DEPS:
  dep = obt.dep.instance(item)
  dep.provide()
