###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, sys, pathlib
from pathlib import Path as _Path_, PosixPath as _PosixPath_, WindowsPath  as _WindowsPath_

###############################################################################

class Path(_Path_) :
 def __new__(cls, *args, **kvps):
  return super().__new__(WindowsPath if os.name == 'nt' else PosixPath, *args, **kvps)

class WindowsPath(_WindowsPath_, Path) :
 pass

class PosixPath(_PosixPath_, Path) :
 def chdir(self):
   os.chdir(str(self))
 pass

###############################################################################

def wrap(a):
    return Path(str(a))

###############################################################################

def root():
  root = Path(os.environ["OBT_ROOT"])
  return root

###############################################################################

def zephyr_base():
  return Path(os.environ["ZEPHYR_BASE"])

###############################################################################

def deps():
  return root()/"deps"

###############################################################################

def patches():
  return root()/"deps"/"patches"

###############################################################################

def pysite():
  return root()/"scripts"/"ork"

###############################################################################

def python_lib():
  pfx = Path(sys.prefix)
  ver = sys.version_info
  epfx = "python%d.%d" % (ver.major,ver.minor)
  #print(pfx,epfx)
  return pfx/"lib"/epfx

###############################################################################

def python_pkg():
  return python_lib()/"site-packages"

###############################################################################

def stage():
  staging = Path(os.environ["OBT_STAGE"])
  return staging

###############################################################################

def qt5dir():
  return stage()/"qt5"

###############################################################################

def prefix():
  return stage()

###############################################################################

def includes():
  return prefix()/"include"

###############################################################################

def libs():
  return prefix()/"lib"

###############################################################################

def manifests():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"manifests"

###############################################################################

def litex_env_dir():
    return builds()/"litex-buildenv"

###############################################################################

def downloads():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"downloads"

###############################################################################

def gitcache():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"gitcache"

###############################################################################

def builds():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"builds"

###############################################################################

def project_root():
  root = Path(os.environ["ORKID_WORKSPACE_DIR"])
  return root

###############################################################################

def vivado_base():
  return Path("/opt/Xilinx/Vivado/2018.3")
