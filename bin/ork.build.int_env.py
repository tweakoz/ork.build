#! /usr/bin/env python

import os
import sys

as_main = (__name__ == '__main__')

###########################################

curwd = os.getcwd()

file_dir = os.path.realpath(__file__)
par1_dir = os.path.dirname(file_dir)
par2_dir = os.path.dirname(par1_dir)
par3_dir = os.path.dirname(par2_dir)
par4_dir = os.path.dirname(par3_dir)
par5_dir = os.path.dirname(par4_dir)

root_dir = par2_dir
scripts_dir = "%s/scripts" % root_dir
sys.path.append(scripts_dir)

import ork.build.common
deco = ork.build.common.deco()

print "%s<%s>" % (deco.key("CURWD"),deco.path(curwd))

bin_dir = "%s/bin" % root_dir
print "%s<%s>" % (deco.key("ROOTDIR"),deco.path(root_dir))

stg_dir = "%s/stage"%curwd
os.system( "mkdir -p %s" % stg_dir)


if os.path.exists(stg_dir):
	print "%s<%s>" % (deco.key("ORKDOTBUILD_STAGE_DIR"),deco.path(stg_dir))
	os.environ["ORKDOTBUILD_STAGE_DIR"]=stg_dir

###########################################

def set_env(key,val):
  print deco.orange("set")+" var<" + deco.key(key)+"> to <" + deco.path(val) + ">"
  os.environ[key] = val

def prepend_env(key,val):
  if False==(key in os.environ):
    set_env(key,val)
  else:
    os.environ[key] = val + ":" + os.environ[key]
    print deco.magenta("prepend")+" var<" + deco.key(key) + "> to<" + deco.path(os.environ[key]) + ">"

def append_env(key,val):
  if False==(key in os.environ):
    set_env(key,val)
  else:
    os.environ[key] = os.environ[key] + ":" + val 
    print deco.cyan("prepend")+" var<" + deco.key(key) + "> to<" + deco.val(os.environ[key]) + ">"

###########################################

set_env("color_prompt","yes")
set_env("ORKDOTBUILD_SLN_ROOT",par3_dir)
set_env("ORKDOTBUILD_ROOT",root_dir)
prepend_env("PYTHONPATH",scripts_dir)
prepend_env("PATH",bin_dir)
prepend_env("PATH","%s/bin"%stg_dir)
prepend_env("LD_LIBRARY_PATH","%s/lib"%stg_dir)
prepend_env("SITE_SCONS","%s/site_scons"%scripts_dir)
import ork.build.utils as obt

###########################################

print
print "ork.build eviron initialized ORKDOTBUILD_ROOT<%s>"%deco.path(root_dir)
print "scanning for projects..."
obt.check_for_projects(par3_dir)
print

###########################################

if as_main:
    shell = os.environ["SHELL"] # get previous shell
    print "SHELL<%s>" % deco.val(shell)
    bdeco = ork.build.common.deco(bash=True)
    BASHRC = 'parse_git_branch() { git branch 2> /dev/null | grep "*" | sed -e "s/*//";}; '
    PROMPT = bdeco.red('[ uORK ]')
    PROMPT += bdeco.yellow("\w")
    PROMPT += bdeco.orange("[$(parse_git_branch) ]")
    PROMPT += bdeco.white("> ")
    BASHRC += "\nexport PS1='%s';" % PROMPT
    BASHRC += "alias ls='ls -G';"
    bashrc = os.path.expandvars('$ORKDOTBUILD_STAGE_DIR/.bashrc')
    f = open(bashrc, 'w')
    f.write(BASHRC)
    f.close()
    print deco.inf("System is <"+os.name+">")
    #os.system(shell) # call shell with new vars (just "exit" to exit)
    os.system("%s --init-file '%s'" %(shell,bashrc)) # call shell with new vars (just "exit" to exit)

