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

###########################################

Path = pathlib.Path
curwd = Path(os.getcwd())
file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
par2_dir = os.path.dirname(file_dir)
root_dir = Path(par2_dir)

###########################################

parser = argparse.ArgumentParser(description='obt.build environment launcher')
parser.add_argument('--stagedir', metavar="stagedir", help='launch from pre-existing folder' )
parser.add_argument('--project', metavar="project", help='override project directory' )
parser.add_argument('--inplace', action="store_true" )
parser.add_argument('--prompt', metavar="prompt", help='prompt suffix' )
parser.add_argument("--numcores", metavar="numcores", help="numcores for environment")
parser.add_argument("--quiet", action="store_true", help="no output")
parser.add_argument('--novars', action="store_true", help='do not set env vars' )
parser.add_argument('--obttrace',action="store_true",help='enable OBT buildtrace logging')

parser.add_argument('--subspace', metavar="subspace", help='subspace to launch' )
parser.add_argument('--chdir', metavar="chdir", help='working directory of command' )
parser.add_argument("--command", metavar="command", help="execute in environ")
parser.add_argument('--stack', metavar="stackdir", help='stack env' )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################

from _obt_config import configFromCommandLine, initializeDependencyEnvironments, importProject
obt_config = configFromCommandLine(args)
###########################################

if args["obttrace"]==True:
  import obt._globals as _glob
  _glob.enableBuildTracing()

###########################################

import obt._envutils 
envsetup = obt._envutils.EnvSetup(obt_config)

###########################################

import obt._globals as _glob
import obt.command
import obt.deco
deco = obt.deco.Deco()

stage_dir = obt_config.stage_dir

###########################################

obt_config.dump()
print(sys.path)
initializeDependencyEnvironments(envsetup)
obt_config.dump()
#importProject(obt_config)

###########################################
if args["stagedir"]!=None:
###########################################
    envsetup.lazyMakeDirs()
    envsetup.genBashRc(stage_dir/".bashrc")
    stage_dir_sh = stage_dir/"obt-launch-env"
    envsetup.log(stage_dir_sh)
    assert(stage_dir_sh.exists())
    #############
    shell = "bash"
    bashrc = stage_dir/".bashrc"
    if args["project"]!=None:
      #envsetup.importProject(Path(item)/"obt.project")
      pass
    #############
    if args["subspace"]!=None:
        if args["chdir"]!=None:
            os.chdir(args["chdir"])
        #rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        subspacemodulename = args["subspace"]
        obt._globals.setOption("subspacemodulename",subspacemodulename)

        subspacemodule = obt.subspace.requires(subspacemodulename)

        if args["command"]!=None:
          if args["chdir"]!=None:
            os.chdir(args["chdir"])
          rval = subspacemodule.launch(obt.command.procargs(args["command"]))
        else:
          rval = subspacemodule.shell()
  
        sys.exit(rval>>8)
    #############
    elif args["command"]!=None:
        if args["chdir"]!=None:
            os.chdir(args["chdir"])
        rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        sys.exit(rval>>8)
    #############
    else:
        obt.command.Command([shell,"--init-file",bashrc],environment={}).exec()
###########################################
elif args["stack"]!=None:
###########################################
    envsetup.lazyMakeDirs()
    envsetup.genBashRc(stage_dir/".bashrc-stack")
    #############
    if args["chdir"]!=None:
      os.chdir(args["chdir"])
    #############
    shell = "bash"
    bashrc = stage_dir/".bashrc-stack"
    envsetup.log(deco.inf("System is <"+os.name+">"))
    print("Stacking env<%s>" % deco.val(stage_dir))
    envsetup.log("obt.build eviron initialized OBT_ROOT<%s>"%deco.path(root_dir))
    if args["command"]!=None:
        obt.command.Command([shell,"--init-file",bashrc,"-c",args["command"]],environment={}).exec()
    else:
        obt.command.Command([shell,"--init-file",bashrc],environment={}).exec()
    pass
###########################################
else:
###########################################
    assert(False)
