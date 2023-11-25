###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, os, pathlib,sys
import multiprocessing

SYSTEM = platform.system()
IsOsx = (SYSTEM=="Darwin")
IsDarwin = (SYSTEM=="Darwin")
IsIrix = (SYSTEM=="IRIX64")
IsLinux = (SYSTEM=="Linux")
IsIx = IsLinux or IsOsx or IsIrix
IsX86_64 = platform.machine()=="x86_64"
IsAARCH64 = (platform.machine()=="aarch64") or (platform.machine()=="arm64")
IsX86_32 = platform.machine()=="i686"
IsAppleSilicon = IsAARCH64 and IsDarwin
file_path = os.path.realpath(__file__)
this_dir = pathlib.Path(os.path.dirname(file_path))

###############################################################################

def description():
  import obt.module
  import obt.path
  hostinfo_dir = obt.path.modules()/"host"
  the_module = None
  if IsOsx:
    machine = platform.machine()
    if machine == "arm64":
       machine = "aarch64"
    identifier = machine+"-"+"macos"
    hi_name = hostinfo_dir/("%s.py"%identifier)
    the_module = obt.module.instance(identifier,hi_name)
  elif IsLinux:
    identifier = platform.machine()+"-"+"linux"
    hi_name = hostinfo_dir/("%s.py"%identifier)
    the_module = obt.module.instance(identifier,hi_name)
  if the_module != None:
    return the_module.hostinfo()

###############################################################################

class enuminterface:
  def __init__(self):
    self.subdir = "host"
  def tryAsModule(self,item,pth):
    identifier = item.replace(".py","")
    m = obt.module.instance(identifier,pth)
    if hasattr(m,"hostinfo"):
      return m
    else:
      return None

###############################################################################

def enumerate():
  iface = enuminterface()
  return obt.module.enumerate_simple(iface)

###############################################################################

def _TryGentoo():
	portage_exists = os.path.exists("/etc/portage")
	return portage_exists

###############################################################################

def _TryDebian():
	apt_exists = os.path.exists("/etc/apt")
	return apt_exists

###############################################################################

IsGentoo = _TryGentoo()
IsDebian = _TryDebian()

###############################################################################

if "OBT_NUM_CORES" in os.environ:
  NumCores = int(os.environ["OBT_NUM_CORES"])
else:
  NumCores = multiprocessing.cpu_count()

if IsLinux:
    PlatformId = "ix"
elif IsOsx:
    PlatformId = "osx"
else:
    PlatformId = "unknown"

###############################################################################
