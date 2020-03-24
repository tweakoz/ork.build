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
parser.add_argument('--create', metavar="createdir", help='create staging folder and enter session' )
parser.add_argument('--createonly', metavar="createdir", help='create staging folder and exit' )
parser.add_argument('--launch', metavar="launchdir", help='launch from pre-existing folder' )
parser.add_argument('--chdir', metavar="chdir", help='working directory of command' )
parser.add_argument('--wipe', action="store_true", help='wipe old staging folder' )
parser.add_argument('--stack', metavar="stackdir", help='stack env' )
parser.add_argument('--prompt', metavar="prompt", help='prompt suffix' )
parser.add_argument("--command", metavar="command", help="execute in environ")
parser.add_argument("--numcores", metavar="numcores", help="numcores for environment")
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

###########################################

os.environ["OBT_SEARCH_EXTLIST"] = ".cpp:.c:.cc:.h:.hpp:.inl:.qml:.m:.mm:.py:.txt:.glfx"

###########################################


###########################################

ORK_PROJECT_NAME = "obt"
if "ORK_PROJECT_NAME" in os.environ:
  ORK_PROJECT_NAME = os.environ["ORK_PROJECT_NAME"]
OBT_STAGE = curwd/".staging"
if "OBT_STAGE" in os.environ:
  OBT_STAGE = Path(os.environ["OBT_STAGE"])
if args["launch"]!=None:
  try_staging = Path(args["launch"]).resolve()
elif args["create"]!=None:
  try_staging = Path(args["create"]).resolve()
  if args["wipe"] and try_staging.exists():
    os.system( "rm -rf %s"%try_staging)
elif args["createonly"]!=None:
  try_staging = Path(args["createonly"]).resolve()
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

import ork.deco
import ork.env
import ork.path
import ork.host
import ork.dep
import ork._globals as _glob
from ork.command import Command

deco = ork.deco.Deco()
bin_dir = root_dir/"bin"

print( _glob.yo )

##########################################

def setenv():
  if args["novars"]==False:
    ork.env.set("color_prompt","yes")
    ork.env.set("OBT_STAGE",OBT_STAGE)
    ork.env.set("OBT_BUILDS",OBT_STAGE/"builds")
    ork.env.set("OBT_ROOT",root_dir)
    ork.env.prepend("PYTHONPATH",scripts_dir)
    ork.env.prepend("PKG_CONFIG",OBT_STAGE/"bin"/"pkg-config")
    ork.env.prepend("PKG_CONFIG_PATH",OBT_STAGE/"lib"/"pkgconfig")
    ork.env.prepend("PKG_CONFIG_PATH",OBT_STAGE/"lib64"/"pkgconfig")
    ork.env.prepend("PATH",bin_dir)
    ork.env.prepend("PATH",OBT_STAGE/"bin")
    ork.env.prepend("LD_LIBRARY_PATH",OBT_STAGE/"lib")
    ork.env.prepend("LD_LIBRARY_PATH",OBT_STAGE/"lib64")
    subenv = root_dir/".."/"obt.project"/"scripts"/"init_env.py"
    if subenv.exists():
      import importlib
      modulename = importlib.machinery.SourceFileLoader('modulename',str(subenv)).load_module()
      #print(modulename)
      modulename.setup()
      #modul.setup()
    if ork.host.IsLinux:
      pkgcfgdir = ork.path.Path("/usr/lib/x86_64-linux-gnu/pkgconfig")
      if pkgcfgdir.exists():
        ork.env.append("PKG_CONFIG_PATH",pkgcfgdir)
      pkgcfgdir = ork.path.Path("/usr/share/pkgconfig")
      if pkgcfgdir.exists():
        ork.env.append("PKG_CONFIG_PATH",pkgcfgdir)

###########################################
# per dep dynamic env init
###########################################

def dynamicInit():
  depitems = ork.dep.enumerate_with_method("env_init")
  for depitemk in depitems:
    depitem = depitems[depitemk]
    depitem.env_init()

###########################################
def lazyMakeDirs():
    my_log(deco.white("Making required directories"))
    (ork.path.prefix()/"lib").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"bin").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"include").mkdir(parents=True,exist_ok=True)
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

    #########################################
    # statically defined goto and push methods
    #########################################

    dirs = {
        "root": "${OBT_ROOT}",
        "deps": "${OBT_ROOT}/deps",
        "stage": "${OBT_STAGE}",
        "builds": "${OBT_STAGE}/builds",
        "litex": "${OBT_STAGE}/builds/litex_env", # todo convert obt.litex.env.py to litex dep
    }

    #########################################
    # dynamic goto and pushd methods
    #  generated from individual deps
    #########################################

    depitems = ork.dep.enumerate_with_method("env_goto")
    for depitemk in depitems:
      depitem = depitems[depitemk]
      gotos = depitem.env_goto()
      dirs.update(gotos)

    #########################################

    for k in dirs:
        v = dirs[k]
        BASHRC += "obt.goto.%s() { cd %s; };" % (k,v)
        BASHRC += "obt.push.%s() { pushd %s; };" % (k,v)

    f = open(str(try_staging/'.bashrc'), 'w')
    f.write(BASHRC)
    f.close()
###########################################
if args["create"] or args["createonly"]!=None:
###########################################
    createOnly = args["createonly"]!=None
    setenv() # sets OBT_STAGE env var (which prefix() uses)
    ork.path.prefix().mkdir(parents=True,exist_ok=False)
    #############
    lazyMakeDirs()
    genBashRc(try_staging)
    #############
    LAUNCHER = "%s/bin/init_env.py --numcores %d --launch %s;\n" % (root_dir,NumCores,try_staging)
    f = open(str(try_staging/'.launch_env'), 'w')
    f.write(LAUNCHER)
    f.close()
    try_staging_sh = try_staging/".launch_env"
    os.system("chmod ugo+x %s"%str(try_staging/'.launch_env'))
    if createOnly:
        sys.exit(0)
    elif IsCommandSet:
        rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        sys.exit(rval>>8)
    else:
        Command([Path(file_path),"--novars", "--init", "--launch", try_staging]).exec()
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
    dynamicInit()
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
else:
###########################################
    assert(False)
