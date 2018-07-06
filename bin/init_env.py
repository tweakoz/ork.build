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

print()

parser = argparse.ArgumentParser(description='ork.build environment launcher')
parser.add_argument('--create', metavar="stagedir", help='create staging folder' )
parser.add_argument('--launch', metavar="stagedir", help='launch from pre-existing folder' )
parser.add_argument("--command", metavar="command", help="execute in environ")
parser.add_argument('--novars', action="store_true", help='do not set env vars' )
parser.add_argument('--init' )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################

IsCommandSet = args["command"]!=None
print("IsCommandSet<%s>"%IsCommandSet)
###########################################

ORK_PROJECT_NAME = "ork.build"
if "ORK_PROJECT_NAME" in os.environ:
  ORK_PROJECT_NAME = os.environ["ORK_PROJECT_NAME"]
ORK_STAGING_FOLDER = curwd/".staging"
if "ORK_STAGING_FOLDER" in os.environ:
  ORK_STAGING_FOLDER = Path(os.environ["ORK_STAGING_FOLDER"])

###########################################

file_dir = os.path.realpath(__file__)
print(file_dir)
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
    ork.env.set("ORK_STAGING_FOLDER",ORK_STAGING_FOLDER)
    ork.env.set("ORKDOTBUILD_ROOT",root_dir)
    ork.env.prepend("PYTHONPATH",scripts_dir)
    ork.env.prepend("PATH",bin_dir)
    ork.env.prepend("PATH",ORK_STAGING_FOLDER/"bin")
    ork.env.prepend("LD_LIBRARY_PATH",ORK_STAGING_FOLDER/"lib")

###########################################
def lazyMakeDirs():
    (ork.path.prefix()/"lib").mkdir(parents=True,exist_ok=True)
    (ork.path.prefix()/"bin").mkdir(parents=True,exist_ok=True)
    ork.path.downloads().mkdir(parents=True,exist_ok=True)
    ork.path.builds().mkdir(parents=True,exist_ok=True)
    ork.path.manifests().mkdir(parents=True,exist_ok=True)
    ork.path.gitcache().mkdir(parents=True,exist_ok=True)
###########################################
if args["create"]!=None:
###########################################
    setenv()
    try_staging = Path(os.path.realpath(args["create"]))
    print(try_staging)
    ork.env.set("ORK_STAGING_FOLDER",try_staging)
    ork.path.prefix().mkdir(parents=True,exist_ok=False)
    lazyMakeDirs()
    #############
    bdeco = ork.deco.Deco(bash=True)
    BASHRC = 'parse_git_branch() { git branch 2> /dev/null | grep "*" | sed -e "s/*//";};\n'
    PROMPT = bdeco.red('[ %s ]'%ORK_PROJECT_NAME)
    PROMPT += bdeco.yellow("\w")
    PROMPT += bdeco.orange("[$(parse_git_branch) ]")
    PROMPT += bdeco.white("> ")
    BASHRC += "\nexport PS1='%s';\n" % PROMPT
    BASHRC += "alias ls='ls -G';\n"
    f = open(str(try_staging/'.bashrc'), 'w')
    f.write(BASHRC)
    f.close()

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
    try_staging = Path(args["launch"])
    print(try_staging)
    assert(try_staging.exists())
    try_staging_sh = try_staging/".launch_env"
    print(try_staging_sh)
    assert(try_staging_sh.exists())
    setenv()
    lazyMakeDirs()
    if args["command"]!=None:
        rval = os.system(args["command"]) # call shell with new vars (just "exit" to exit)
        sys.exit(rval>>8)
    else:
        Command([Path(file_dir),"--init",try_staging]).exec()
###########################################
elif args["init"]!=None:
###########################################
    try_staging = Path(args["init"])
    print(try_staging)
    assert(try_staging.exists())
    ORK_STAGING_FOLDER = Path(os.path.realpath(try_staging))
    setenv()

    lazyMakeDirs()
    shell = "bash"
    bashrc = try_staging/".bashrc"
    print(deco.inf("scanning for projects..."))
    import ork.utils as obt
    obt.check_for_projects(par3_dir)
    print(deco.inf("System is <"+os.name+">"))
    print("Launching env-shell<%s>" % deco.val(shell))
    print("ork.build eviron initialized ORKDOTBUILD_ROOT<%s>"%deco.path(root_dir))
    Command([shell,"--init-file",bashrc],environment={}).exec()
    pass
###########################################
else:
###########################################
    assert(False)
