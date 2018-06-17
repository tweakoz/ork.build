###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os

import ork.deco
deco = ork.deco.Deco()

###########################################

def set(key,val):
  print(deco.orange("set")+" var<" + deco.key(str(key))+"> to <" + deco.path(val) + ">")
  os.environ[str(key)] = str(val)

###########################################

def prepend(key,val):
  if False==(str(key) in os.environ):
    set(key,val)
  else:
    os.environ[str(key)] = str(val) + ":" + os.environ[key]
    print(deco.magenta("prepend")+" var<" + deco.key(key) + "> to<" + deco.path(os.environ[key]) + ">")
	
###########################################

def append(key,val):
  if False==(str(key) in os.environ):
    set(key,val)
  else:
    os.environ[str(key)] = os.environ[str(key)]+":"+str(val) 
    print(deco.cyan("append")+" var<" + deco.key(key) + "> to<" + deco.val(os.environ[key]) + ">")
	