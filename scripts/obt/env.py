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

  log.output(deco.orange("set")+" var<" + deco.key(str(key))+"> to <" + deco.path(val) + ">")
  os.environ[str(key)] = str(val)

###########################################

def prepend(key,val,dedupe=True):
  val = os.path.normpath(str(val))
  if False==(str(key) in os.environ):
    set(key,str(val))
  else:
    if dedupe:
      prev = os.environ[key]
      if str(val) in prev:
        return
    prev = os.environ[key]
    newv = str(val) + ":" + prev
    os.environ[str(key)] = newv
    log_str = deco.magenta("prepend")+" var<" + deco.key(key) 
    log_str += "> -> <" + deco.val(str(val)) + ":" + deco.path(prev) + ">"
    log.output(log_str)

###########################################

def append(key,val,dedupe=True):
  val = os.path.normpath(str(val))
  if(str(val)==""):
    return
  prev_val_has_length = True
  key_present = str(key) in os.environ
  if key_present:
    prev = os.environ[str(key)]
    prev_val_has_length = len(str(prev))>0
  if (not key_present) or (not prev_val_has_length):
    set(key,val)
    return
  else:
    if dedupe:
      prev = os.environ[key]
      if str(val) in prev:
        return
    #CHK = (str(key) in os.environ.keys())
    prev = os.environ[str(key)]
    newv = prev + ":" + str(val)
    os.environ[str(key)] = newv
    #print("prev<%s:%d:%s>"%(CHK,len(prev),prev))
    #print(os.environ)
    log_str = deco.cyan("append")+" var<" + deco.key(key) 
    log_str += "> -> <" + deco.path(prev) + ":" + deco.val(str(val)) + ">"
    log.output(log_str)

###########################################

def is_set(key):
  return str(key) in os.environ
