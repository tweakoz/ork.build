#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################


import os, sys, pathlib, argparse

as_main = (__name__ == '__main__')

Path = pathlib.Path

curwd = Path(os.getcwd())

parser = argparse.ArgumentParser(description='ork.build environment launcher')
parser.add_argument('--create', metavar="createdir", help='create staging folder' )
parser.add_argument('--launch', metavar="launchdir", help='launch from pre-existing folder' )
parser.add_argument('--stack', metavar="stackdir", help='stack env' )
parser.add_argument('--prompt', metavar="prompt", help='prompt suffix' )
parser.add_argument("--command", metavar="command", help="execute in environ")
parser.add_argument("--quiet", action="store_true", help="no output")
parser.add_argument('--novars', action="store_true", help='do not set env vars' )
parser.add_argument('--init', action="store_true" )

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

def my_log(x):
    if False==IsQuiet:
       print(x)

###########################################

my_log("IsCommandSet<%s>"%IsCommandSet)
#print(args)
###########################################

ORK_PROJECT_NAME = "obt"
if "ORK_PROJECT_NAME" in os.environ:
  ORK_PROJECT_NAME = os.environ["ORK_PROJECT_NAME"]
OBT_STAGE = curwd/".staging"
if "OBT_STAGE" in os.environ:
  OBT_STAGE = Path(os.environ["OBT_STAGE"])
if args["launch"]!=None:
  try_staging = Path(args["launch"])
elif args["create"]!=None:
  try_staging = Path(args["create"])
elif args["stack"]!=None:
  try_staging = Path(args["stack"])

if try_staging!=None:
  OBT_STAGE = try_staging

###########################################

file_dir = os.path.realpath(__file__)
my_log(file_dir)
par1_dir = os.path.dirname(file_dir)
par2_dir = os.path.dirname(par1_dir)
par3_dir = os.path.dirname(par2_dir)
par4_dir = os.path.dirname(par3_dir)
par5_dir = os.path.dirname(par4_dir)

root_dir = Path(par2_dir)
scripts_dir = root_dir/"scripts"
sys.path.append(str(scripts_dir))

import ork.deco
import ork.env
import ork.path
from ork.command import Command

deco = ork.deco.Deco()
bin_dir = root_dir/"bin"

###########################################

def setenv():
  if args["novars"]==False:
    ork.env.set("color_prompt","yes")
    ork.env.set("OBT_STAGE",OBT_STAGE)
    ork.env.set("OBT_ROOT",root_dir)
    ork.env.set("OBT_PYLIB",ork.path.python_lib())
    ork.env.set("OBT_PYPKG",ork.path.python_pkg())
    ork.env.prepend("PYTHONPATH",scripts_dir)
    ork.env.prepend("PATH",bin_dir)
    ork.env.prepend("PATH",OBT_STAGE/"bin")
    ork.env.prepend("LD_LIBRARY_PATH",OBT_STAGE/"lib")

###########################################
def lazyMakeDirs():
    my_log(deco.white("Making required directories"))
    (ork.path.prefix()/"lib").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"bin").mkdir(parents=True,exist_ok=True)
    ork.path.downloads().mkdir(parents=True,exist_ok=True)
    ork.path.builds().mkdir(parents=True,exist_ok=True)
    ork.path.manifests().mkdir(parents=True,exist_ok=True)
    ork.path.gitcache().mkdir(parents=True,exist_ok=True)
###########################################
def genBashRc(staging):
    my_log(deco.white("Generating bashrc"))
    bdeco = ork.deco.Deco(bash=True)
    BASHRC = 'parse_git_branch() { git branch 2> /dev/null | grep "*" | sed -e "s/*//";};\n'
    PROMPT = bdeco.red('[ %s ]'%ORK_PROJECT_NAME)
    PROMPT += bdeco.yellow("\w")
    PROMPT += bdeco.orange("[$(parse_git_branch) ]")
    PROMPT += bdeco.white("> ")
    BASHRC += "\nexport PS1='%s';\n" % PROMPT
    BASHRC += "alias ls='ls -G';\n"

    dirs = {
        "root": "${OBT_ROOT}",
        "deps": "${OBT_ROOT}/deps",

        "stage": "${OBT_STAGE}",
        "builds": "${OBT_STAGE}/builds",
        "pylib": str(ork.path.python_lib()),
        "pypkg": str(ork.path.python_pkg())
    }

    for k in dirs:
        v = dirs[k]
        BASHRC += "obt_goto_%s() { cd %s; };" % (k,v)
        BASHRC += "obt_push_%s() { pushd %s; };" % (k,v)

    f = open(str(try_staging/'.bashrc'), 'w')
    f.write(BASHRC)
    f.close()
###########################################
if args["create"]!=None:
###########################################
    setenv() # sets OBT_STAGE env var (which prefix() uses)
    ork.path.prefix().mkdir(parents=True,exist_ok=False)
    #############
    lazyMakeDirs()
    genBashRc(try_staging)
    #############
    LAUNCHER = "%s/bin/init_env.py --launch %s;\n" % (root_dir,try_staging)
    f = open(str(try_staging/'.launch_env'), 'w')
    f.write(LAUNCHER)
    f.close()
    try_staging_sh = try_staging/".launch_env"
    os.system("chmod ugo+x %s"%str(try_staging/'.launch_env'))
    if args["command"]!=None:
        rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        sys.exit(rval>>8)
    else:
        Command([Path(file_dir),"--novars", "--init",try_staging]).exec()
###########################################
elif args["launch"]!=None:
###########################################
    try_staging_sh = try_staging/".launch_env"
    my_log(try_staging_sh)
    assert(try_staging_sh.exists())
    setenv()
    #############
    lazyMakeDirs()
    genBashRc(try_staging)
    #############
    shell = "bash"
    bashrc = try_staging/".bashrc"
    #############
    if args["command"]!=None:
        rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        sys.exit(rval>>8)
    else:
        Command([shell,"--init-file",bashrc],environment={}).exec()
###########################################
elif args["stack"]!=None:
###########################################
    setenv()
    #############
    lazyMakeDirs()
    genBashRc(try_staging)
    #############
    shell = "bash"
    bashrc = try_staging/".bashrc"
    my_log(deco.inf("System is <"+os.name+">"))
    print("Stacking env<%s>" % deco.val(try_staging))
    my_log("ork.build eviron initialized OBT_ROOT<%s>"%deco.path(root_dir))
    if args["command"]!=None:
        Command([shell,"--init-file",bashrc,"-c",args["command"]],environment={}).exec()
    else:
        Command([shell,"--init-file",bashrc],environment={}).exec()
    pass
###########################################
elif args["init"]!=None:
###########################################
    try_staging = Path(args["init"])
    my_log(try_staging)
    assert(try_staging.exists())
    OBT_STAGE = Path(os.path.realpath(try_staging))
    setenv()
    #############
    lazyMakeDirs()
    genBashRc(try_staging)
    #############
    shell = "bash"
    bashrc = try_staging/".bashrc"
    my_log(deco.inf("scanning for projects..."))
    import ork.utils as obt
    obt.check_for_projects(par3_dir)
    my_log(deco.inf("System is <"+os.name+">"))
    my_log("Launching env-shell<%s>" % deco.val(shell))
    my_log("ork.build eviron initialized OBT_ROOT<%s>"%deco.path(root_dir))
    Command([shell,"--init-file",bashrc],environment={}).exec()
    pass
###########################################
else:
###########################################
    assert(False)