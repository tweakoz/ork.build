###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, os, pathlib,sys
import obt.module

###############################################################################

file_path = os.path.realpath(__file__)
this_dir = pathlib.Path(os.path.dirname(file_path))

###############################################################################

def descriptor(architecture,osname):
  import obt.module
  import obt.path
  identifier = "%s-%s" % (architecture,osname)
  hi_name = obt.path.modules()/"sdk"
  hi_name = hi_name / ("%s.py"%identifier)
  the_module = obt.module.instance(identifier,hi_name)
  if the_module != None:
    hostident = obt.host.description().identifier
    if hasattr(the_module,"sdkinfo"):
      sdkinfo = the_module.sdkinfo()
      if hostident in sdkinfo.supports_host:
        return sdkinfo
  return None

###############################################################################

class enuminterface:
  def __init__(self):
    self.subdir = "sdk"
  def tryAsModule(self,hostidentifier,item,pth):
    identifier = item.replace(".py","")
    m = obt.module.instance(identifier,pth)
    if hasattr(m,"sdkinfo"):
      sdki = m.sdkinfo()
      if hostidentifier in sdki.supports_host:
        return m
    else:
      return None

###############################################################################

def enumerate():
  iface = enuminterface()
  return obt.module.enumerate_simple(iface)
