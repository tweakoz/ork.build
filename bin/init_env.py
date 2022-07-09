#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################


import os, sys, pathlib, argparse, multiprocessing

as_main = (__name__ == '__main__')

Path = pathlib.Path

curwd = Path(os.getcwd())

parser = argparse.ArgumentParser(description='ork.build environment launcher')
parser.add_argument('--launch', metavar="launchdir", help='launch from pre-existing folder' )
parser.add_argument('--prjdir', metavar="prjdir", help='override project directory' )
parser.add_argument('--chdir', metavar="chdir", help='working directory of command' )
parser.add_argument('--stack', metavar="stackdir", help='stack env' )
parser.add_argument('--prompt', metavar="prompt", help='prompt suffix' )
parser.add_argument("--command", metavar="command", help="execute in environ")
parser.add_argument("--numcores", metavar="numcores", help="numcores for environment")
parser.add_argument("--quiet", action="store_true", help="no output")
parser.add_argument('--novars', action="store_true", help='do not set env vars' )
parser.add_argument('--init', action="store_true" )
parser.add_argument('--compose',action='append',help='compose obt project into container')

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################
IsQuiet = (args["quiet"]==True)
IsCommandSet = args["command"]!=None
###########################################

if IsQuiet:
    os.environ["OBT_QUIET"]="1"
#else:
#    os.environ["OBT_QUIET"]=IsQuiet

if args["prompt"]!=None:
  os.environ["OBT_USE_PROMPT_PREFIX"] = args["prompt"]

###########################################

file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
par2_dir = os.path.dirname(file_dir)
par3_dir = os.path.dirname(par2_dir)
par4_dir = os.path.dirname(par3_dir)
par5_dir = os.path.dirname(par4_dir)

root_dir = Path(par2_dir)
scripts_dir = root_dir/"scripts"
sys.path.append(str(scripts_dir))

###########################################

project_dir = root_dir
if args["prjdir"]!=None:
  project_dir = Path(args["prjdir"])

###########################################

ORK_PROJECT_NAME = "obt"
if "ORK_PROJECT_NAME" in os.environ:
  ORK_PROJECT_NAME = os.environ["ORK_PROJECT_NAME"]
OBT_STAGE = curwd/".staging"
if "OBT_STAGE" in os.environ:
  OBT_STAGE = Path(os.environ["OBT_STAGE"])
if args["launch"]!=None:
  try_staging = Path(args["launch"]).resolve()
elif args["stack"]!=None:
  try_staging = Path(args["stack"]).resolve()

NumCores = multiprocessing.cpu_count()
if args["numcores"]!=None:
  NumCores = int(args["numcores"])
if "OBT_NUM_CORES" not in os.environ:
  os.environ["OBT_NUM_CORES"]=str(NumCores)

if try_staging!=None:
  OBT_STAGE = try_staging

###########################################

os.environ["OBT_SEARCH_EXTLIST"] = ".cpp:.c:.cc:.h:.hpp:.inl:.qml:.m:.mm:.py:.txt:.glfx"

###########################################

import ork.deco
import ork.env
import ork.path
import ork.host
import ork.dep
import ork.subspace
import ork.sdk
import ork._globals as _glob
from ork.command import Command

deco = ork.deco.Deco()
bin_dir = root_dir/"bin"

##########################################

import _envutils 
envsetup = _envutils.EnvSetup(stagedir=OBT_STAGE,
                              rootdir=root_dir,
                              projectdir=project_dir,
                              bindir=bin_dir,
                              scriptsdir=scripts_dir,
                              disable_syspypath=True,
                              is_quiet=IsQuiet,
                              project_name = ORK_PROJECT_NAME)

###########################################

if args["compose"] != None:
  for item in args["compose"]:
    envsetup.importProject(Path(item))

###########################################
# per dep dynamic env init
###########################################

def dynamicInit():
  ####################################
  hostinfo = ork.host.description()
  if hasattr(hostinfo,"env_init"):
    hostinfo.env_init()
  ####################################
  sdkitems = ork.sdk.enumerate()
  print(sdkitems)
  for sdk_module_key in sdkitems.keys():
    sdk_module_item = sdkitems[sdk_module_key]
    print(sdk_module_item)
    sdk_module = sdk_module_item._module
    print(sdk_module)
    sdkinfo = sdk_module.sdkinfo()
    if hasattr(sdkinfo,"env_init"):
      sdkinfo.env_init()
  ####################################
  depitems = ork.dep.DepNode.FindWithMethod("env_init")
  for depitemk in depitems:
    depitem = depitems[depitemk]
    depitem.env_init()
  ####################################
  subspaceitems = ork.subspace.findWithMethod("env_init")
  for subitemk in subspaceitems:
    subitem = subspaceitems[subitemk]
    subitem._module.env_init()
  ####################################

###########################################
if args["launch"]!=None:
###########################################
    if args["novars"]==False:
      envsetup.install()
    #############
    envsetup.lazyMakeDirs()
    envsetup.genBashRc(try_staging/".bashrc")
    dynamicInit()
    try_staging_sh = try_staging/".launch_env"
    envsetup.log(try_staging_sh)
    assert(try_staging_sh.exists())
    #############
    shell = "bash"
    bashrc = try_staging/".bashrc"
    #############
    if args["command"]!=None:
        if args["chdir"]!=None:
            os.chdir(args["chdir"])
        rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        sys.exit(rval>>8)
    else:
        Command([shell,"--init-file",bashrc],environment={}).exec()
###########################################
elif args["stack"]!=None:
###########################################
    ork.env.append("OBT_STACK","<")
    if args["novars"]==False:
      envsetup.install()
    #############
    envsetup.lazyMakeDirs()
    envsetup.genBashRc(try_staging/".bashrc-stack")
    dynamicInit()
    #############
    if args["compose"]!=None:
      for item in args["compose"]:
        envsetup.importProject(Path(item)/"obt.project")
    #############
    if args["chdir"]!=None:
      os.chdir(args["chdir"])
    #############
    shell = "bash"
    bashrc = try_staging/".bashrc-stack"
    envsetup.log(deco.inf("System is <"+os.name+">"))
    print("Stacking env<%s>" % deco.val(try_staging))
    envsetup.log("ork.build eviron initialized OBT_ROOT<%s>"%deco.path(root_dir))
    if args["command"]!=None:
        Command([shell,"--init-file",bashrc,"-c",args["command"]],environment={}).exec()
    else:
        Command([shell,"--init-file",bashrc],environment={}).exec()
    pass
###########################################
else:
###########################################
    assert(False)
