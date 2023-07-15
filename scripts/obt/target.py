###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, os, pathlib,sys

###############################################################################

file_path = os.path.realpath(__file__)
this_dir = pathlib.Path(os.path.dirname(file_path))

###############################################################################

def descriptor(architecture,osname):
  import ork.module
  identifier = "%s-%s" % (architecture,osname)
  hi_name = this_dir/".."/".."/"modules"/"target"
  hi_name = hi_name / ("%s.py"%identifier)
  the_module = ork.module.instance(identifier,hi_name)
  if the_module != None:
    return the_module.targetinfo()

###############################################################################

class enuminterface:
  def __init__(self):
    self.subdir = "target"
  def tryAsModule(self,item,pth):
    return None

###############################################################################

def enumerate():
  iface = enuminterface()
  return ork.module.enumerate_simple(iface)
