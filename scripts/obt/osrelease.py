###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, multiprocessing 
from obt import target, host

###############################################################################

class OsDescriptor:
  def __init__(self):
    self.id = ""
    self.version_id = ""
    self.version_codename = ""

###############################################################################

def descriptorLinux():
  try:
    import distro
    INFO = distro.name(), distro.version()
    #print(INFO)
    #print(dir(distro))
    osd = OsDescriptor()
    osd.id = distro.name()
    osd.version_id = distro.version()
    osd.version_codename = distro.codename()
    #print(osd)
    #assert(False)
    return osd
  except ModuleNotFoundError:
    try:
      import os_release
      INFO = os_release.current_release()
      #print(INFO)
      osd = OsDescriptor()
      #print(osd)
      osd.id = INFO.id
      osd.version_id = INFO.version_id
      osd.version_codename = INFO.version_codename
      return osd
    except ModuleNotFoundError:
      try:
        import lsb_release
        INFO = lsb_release.get_os_release()
        #print(INFO)
        osd = OsDescriptor()
        osd.id = INFO["ID"]
        osd.version_id = INFO["RELEASE"]
        osd.version_codename = INFO["CODENAME"]
        print(osd)
        return osd
      except ModuleNotFoundError:
        print("python module 'lsb_release' or 'os_release' is not installed")
        return {}
      
###############################################################################

def descriptorMacos():
  try:
    import os_release
    #print(dir(os_release))
    #INFO = os_release.current_release()
    #print(INFO)
    osd = OsDescriptor()
    #print(osd)
    #osd.id = INFO.id
    #osd.version_id = INFO.version_id
    #osd.version_codename = INFO.version_codename
    return osd
  except ModuleNotFoundError:
    try:
      import lsb_release
      INFO = lsb_release.get_os_release()
      #print(INFO)
      osd = OsDescriptor()
      osd.id = INFO["ID"]
      osd.version_id = INFO["RELEASE"]
      osd.version_codename = INFO["CODENAME"]
      #print(osd)
      return osd
    except ModuleNotFoundError:
      print("python module 'lsb_release' or 'os_release' is not installed")
      return {}
    
###############################################################################

def descriptor():
  if host.IsLinux:
    return descriptorLinux()
  elif host.IsOsx:
    return descriptorMacos()
  print("UHOH")
  return {}
  
  
