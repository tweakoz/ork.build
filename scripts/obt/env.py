###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os

import obt.deco
from obt import log

deco = obt.deco.Deco()

###########################################

def set(key,val):

  #log.output(deco.orange("set")+" var<" + deco.key(str(key))+"> to <" + deco.path(val) + ">")
  os.environ[str(key)] = str(val)

###########################################

def prepend(key,val):
  if False==(str(key) in os.environ):
    set(key,str(val))
  else:
    os.environ[str(key)] = str(val) + ":" + os.environ[key]
    #log.output(deco.magenta("prepend")+" var<" + deco.key(key) + "> to<" + deco.path(os.environ[key]) + ">")

###########################################

def append(key,val):
  val = os.path.normpath(str(val))
  if False==(str(key) in os.environ):
    set(key,val)
  else:
    os.environ[str(key)] = os.environ[str(key)]+":"+str(val)
    #log.output(deco.cyan("append")+" var<" + deco.key(key) + "> to<" + deco.path(os.environ[key]) + ">")

###########################################

def is_set(key):
  return str(key) in os.environ
