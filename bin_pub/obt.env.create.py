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

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################
IsQuiet = (args["quiet"]==True)
###########################################

if IsQuiet:
    os.environ["OBT_QUIET"]="1"
#else:
#    os.environ["OBT_QUIET"]=IsQuiet

def my_log(x):
    if False==IsQuiet:
       print(x)

###########################################

file_path = os.path.realpath(__file__)
my_log(file_path)
file_dir = os.path.dirname(file_path)
par2_dir = os.path.dirname(file_dir)
par3_dir = os.path.dirname(par2_dir)
par4_dir = os.path.dirname(par3_dir)
par5_dir = os.path.dirname(par4_dir)

root_dir = Path(par2_dir)
scripts_dir = root_dir/"scripts"
sys.path.append(str(scripts_dir))
project_dir = root_dir

###########################################
# are we standalone or attached to a project ?
###########################################

explicitprojectdir = None
if args["projectdir"]!=None:
  explicitprojectdir = Path(args["projectdir"])

####################
# first try implicit projectdir (curwd)
####################

try_project_manifest = curwd/"obt.project"/"obt.manifest"
if try_project_manifest.exists():
  project_dir = curwd
else:

  project_dir = root_dir/".." # default is parent of OBT 

  if (explicitprojectdir!=None) and explicitprojectdir.exists(): # explicit passed in...
    try_project_manifest = explicitprojectdir/"obt.project"/"obt.manifest"
    if try_project_manifest.exists():
      project_dir = explicitprojectdir
    else:
      assert(False) # explicit does not exist
      
###########################################

ORK_PROJECT_NAME = "obt"
if "ORK_PROJECT_NAME" in os.environ:
  ORK_PROJECT_NAME = os.environ["ORK_PROJECT_NAME"]
OBT_STAGE = curwd/".staging"
if "OBT_STAGE" in os.environ:
  OBT_STAGE = Path(os.environ["OBT_STAGE"])
if args["stagedir"]!=None:
  try_staging = Path(args["stagedir"]).resolve()
  if try_staging.exists() and args["wipe"]==False:
    print("Not going to wipe your staging folder<%s> unless you ask... use --wipe"%try_staging)
    sys.exit(0)
  if args["wipe"] and try_staging.exists():
    os.system( "rm -rf %s"%try_staging)
else:
  assert(False)

NumCores = multiprocessing.cpu_count()
if args["numcores"]!=None:
  NumCores = int(args["numcores"])
if "OBT_NUM_CORES" not in os.environ:
  os.environ["OBT_NUM_CORES"]=str(NumCores)

if args["prompt"]!=None:
  os.environ["OBT_USE_PROMPT_PREFIX"] = args["prompt"]
if try_staging!=None:
  OBT_STAGE = try_staging

GIT_SSH_COMMAND = None
if args["sshkey"]!=None:
  GIT_SSH_COMMAND="ssh -i %s" % args["sshkey"]

###########################################

import obt.deco
import obt.env
import obt.path
import obt.host
import obt.dep
import obt._globals as _glob
from obt.command import Command

deco = obt.deco.Deco()
bin_dir = root_dir/"bin"

if args["obttrace"]==True:
  _glob.enableBuildTracing()

##########################################

import obt._envutils 

envsetup = obt._envutils.EnvSetup(stagedir=OBT_STAGE,
                                  projectdir=project_dir,
                                  rootdir=root_dir,
                                  bindir=bin_dir,
                                  scriptsdir=scripts_dir,
                                  is_quiet=IsQuiet,
                                  git_ssh_command = GIT_SSH_COMMAND)

###########################################

if args["compose"] != None:
  for item in args["compose"]:
    envsetup.importProject(Path(item))


###########################################
if args["novars"]==False:
  envsetup.install() # sets OBT_STAGE env var (which prefix() uses)
###########################################
obt.path.prefix().mkdir(parents=True,exist_ok=False)
#############
# Create base scripts
#############
envsetup.lazyMakeDirs()
envsetup.genBashRc(try_staging/".bashrc")
envsetup.genLaunchScript(out_path=try_staging/"obt-launch-env")
#############

#if not obt.host.IsAARCH64:
PYTHON = obt.dep.instance("python")
PYTHON.provide()
PYTHONDEFS = obt.dep.instance("pydefaults")
PYTHONDEFS.provide()
