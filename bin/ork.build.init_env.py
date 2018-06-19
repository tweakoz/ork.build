#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################


import os, sys, pathlib

as_main = (__name__ == '__main__')

Path = pathlib.Path

curwd = Path(os.getcwd())

print()

###########################################

ORK_PROJECT_NAME = "ork.build"
if "ORK_PROJECT_NAME" in os.environ:
  ORK_PROJECT_NAME = os.environ["ORK_PROJECT_NAME"]
ORK_STAGING_FOLDER = curwd/".staging"
if "ORK_STAGING_FOLDER" in os.environ:
  ORK_STAGING_FOLDER = Path(os.environ["ORK_STAGING_FOLDER"])

###########################################

file_dir = os.path.realpath(__file__)
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

os.system( "mkdir -p %s" % ORK_STAGING_FOLDER)

###########################################

ork.env.set("color_prompt","yes")
ork.env.set("ORK_STAGING_FOLDER",ORK_STAGING_FOLDER)
ork.env.set("ORKDOTBUILD_ROOT",root_dir)
ork.env.prepend("PYTHONPATH",scripts_dir)
ork.env.prepend("PATH",bin_dir)
ork.env.prepend("PATH",ORK_STAGING_FOLDER/"bin")
ork.env.prepend("LD_LIBRARY_PATH",ORK_STAGING_FOLDER/"lib")

###########################################

print()
print("ork.build eviron initialized ORKDOTBUILD_ROOT<%s>"%deco.path(root_dir))

###########################################

print()
print(deco.inf("scanning for projects..."))
import ork.utils as obt
obt.check_for_projects(par3_dir)

###########################################
# create DL dir
###########################################

ork.path.prefix().mkdir(parents=True,exist_ok=True)
ork.path.downloads().mkdir(parents=True,exist_ok=True)
ork.path.builds().mkdir(parents=True,exist_ok=True)
ork.path.manifests().mkdir(parents=True,exist_ok=True)

###########################################

print()

if as_main:
    shell = os.environ["SHELL"] # get previous shell
    bdeco = ork.deco.Deco(bash=True)
    BASHRC = 'parse_git_branch() { git branch 2> /dev/null | grep "*" | sed -e "s/*//";}; '
    PROMPT = bdeco.red('[ %s ]'%ORK_PROJECT_NAME)
    PROMPT += bdeco.yellow("\w")
    PROMPT += bdeco.orange("[$(parse_git_branch) ]")
    PROMPT += bdeco.white("> ")
    BASHRC += "\nexport PS1='%s';" % PROMPT
    BASHRC += "alias ls='ls -G';"
    bashrc = os.path.expandvars('$ORK_STAGING_FOLDER/.bashrc')
    f = open(bashrc, 'w')
    f.write(BASHRC)
    f.close()
    print(deco.inf("System is <"+os.name+">"))
    print("Launching env-shell<%s>" % deco.val(shell))
    Command([shell,"--init-file",bashrc],environment={}).exec()

