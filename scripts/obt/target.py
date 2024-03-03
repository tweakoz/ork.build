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

target_arch = None 
target_os = None

if "OBT_TARGET" not in os.environ:
  SYSTEM = platform.system()
  ##############
  IsOsx = (SYSTEM=="Darwin")
  IsDarwin = (SYSTEM=="Darwin")
  IsIrix = (SYSTEM=="IRIX64")
  IsLinux = (SYSTEM=="Linux")
  ##############
  IsX86_64 = platform.machine()=="x86_64"
  IsAARCH64 = (platform.machine()=="aarch64") or (platform.machine()=="arm64")
  IsX86_32 = platform.machine()=="i686"
  IsAppleSilicon = IsAARCH64 and IsDarwin
  ##############
  if IsX86_32:
    machine = "x86_32"
  elif IsAARCH64:
    machine = "aarch64"
  else:
    machine = "x86_64"
  target_arch = machine
  if IsOsx:
    target_os = "macos"
  elif IsLinux:
    target_os = "linux"
            
else:
  TARGET_STR = os.environ.get("OBT_TARGET")
  target_arch = TARGET_STR.split("-")[0]
  target_os = TARGET_STR.split("-")[1]

is_linux = (target_os=="linux")
is_macos = (target_os=="macos")
is_windows = (target_os=="windows")
is_android = (target_os=="android")
is_ios = (target_os=="ios")

###############################################################################

def descriptor(architecture,osname):
  import obt.module
  import obt.path
  identifier = "%s-%s" % (architecture,osname)
  hi_name = obt.path.modules()/"target"
  hi_name = hi_name / ("%s.py"%identifier)
  the_module = obt.module.instance(identifier,hi_name)
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
  return obt.module.enumerate_simple(iface)
