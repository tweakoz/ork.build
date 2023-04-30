###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, sys, pathlib, tempfile
from pathlib import Path as _Path_, PosixPath as _PosixPath_, WindowsPath  as _WindowsPath_
import ork.command
from ork import buildtrace

###############################################################################

class Path(_Path_) :
 def __new__(cls, *args, **kvps):
  return super().__new__(WindowsPath if os.name == 'nt' else PosixPath, *args, **kvps)

class WindowsPath(_WindowsPath_, Path) :
 pass

class PosixPath(_PosixPath_, Path) :
 def chdir(self):
   buildtrace.buildTrace({"op":"path.chdir(%s)"%str(self)})
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

def buildlogs():
  return stage()/"buildlogs"

###############################################################################

def apps():
    return stage()/"apps"

###############################################################################

def sdks():
    return stage()/"sdks"

###############################################################################

def subspace_root():
    return stage()/"subspaces"

###############################################################################

def quarantine():
  return subspace_root()/"quarantine"

###############################################################################

def subspace():
  subspace = "host"
  if "OBT_SUBSPACE" in os.environ:
    subspace = os.environ["OBT_SUBSPACE"]
  return subspace

###############################################################################

def subspace_dir():
  return Path(os.environ["OBT_SUBSPACE_DIR"])

###############################################################################

def modules(provider=None):
  if provider==None:
    return root()/"modules"
  else:
    depnode = provider._node
    name = provider._name
    return depnode.modules_base

###############################################################################

#def dockers():
 # return modules()/"docker"

###############################################################################

def deps(provider=None):
 return modules(provider)/"dep"

###############################################################################

#def hosts():
#    return modules()/"host"

###############################################################################

#def targets():
#    return modules()/"target"

###############################################################################

#def sdk_modules():
#    return modules()/"sdk"

###############################################################################

def patches(provider=None):
  return deps(provider)/"patches"

###############################################################################

def scripts():
  return root()/"scripts"

###############################################################################

def obt_bin():
  return root()/"bin"

###############################################################################

def pysite():
  return scripts()/"ork"

###############################################################################

def stage():
  staging = Path(os.environ["OBT_STAGE"])
  return staging

###############################################################################

def dblockcache():
    return stage()/"dblockcache"

###############################################################################

def qt5dir():
  return stage()/"qt5"

###############################################################################

def prefix():
  return stage()

###############################################################################

def bin():
  return prefix()/"bin"

###############################################################################

def includes():
  return prefix()/"include"

###############################################################################

def libs():
  return prefix()/"lib"

###############################################################################

def share():
  return prefix()/"share"

###############################################################################

def pkgconfigdir():
  return libs()/"pkgconfig"

###############################################################################

def litex_env_dir():
    return builds()/"litex-buildenv"

###############################################################################

def temp():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"tempdir"

###############################################################################

def home():
  return Path(os.environ["HOME"])

###############################################################################

def user_global():
  return home()/".obt-global"

###############################################################################

def gitcache():
  return user_global()/"gitcache"

###############################################################################

def downloads():
  return user_global()/"downloads"

###############################################################################

def builds():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"builds"


def orkid():
  orkroot = Path(os.environ["ORKID_WORKSPACE_DIR"])
  return orkroot

###############################################################################

def project_root():
  return Path(os.environ["OBT_PROJECT_DIR"])

###############################################################################
def osx_sdkdir():
  result = ork.command.capture([
                    "xcodebuild",
                    "-version",
                    "-sdk", "macosx",
                    "Path"],do_log=False).splitlines()
  return result[0]

###############################################################################

def osx_brewdir():
  result = "/usr/local"
  if "HOMEBREW_PREFIX" in os.environ:
    result = os.environ["HOMEBREW_PREFIX"]
  return Path(result)

###############################################################################

def osx_brewopt():
  return osx_brewdir()/"opt"

###############################################################################

def osx_brewcellar():
  return osx_brewdir()/"Cellar"

###############################################################################

def vivado_base():
  return Path("/opt/Xilinx/Vivado")

###############################################################################

def decorate_obt_lib(named):
  return libs()/("lib%s.so"%named)

###############################################################################
# module properties
###############################################################################

def __getattr__(name):
  if name == "subspace_python_build_dir":
    build_dir = builds()
    if "OBT_PYTHON_SUBSPACE_BUILD_DIR" in os.environ:
      build_dir = Path(os.environ["OBT_PYTHON_SUBSPACE_BUILD_DIR"])
    return build_dir
  if name == "subspace_build_dir":
    subs_dir = Path(os.environ["OBT_SUBSPACE_DIR"])
    return subs_dir/"builds"
  if name == "subspace_lib_dir":
    lib_dir = libs()
    if "OBT_SUBSPACE_LIB_DIR" in os.environ:
      lib_dir = Path(os.environ["OBT_SUBSPACE_LIB_DIR"])
    return lib_dir
  if name == "subspace_bin_dir":
    bin_dir = bin()
    if "OBT_SUBSPACE_BIN_DIR" in os.environ:
      bin_dir = Path(os.environ["OBT_SUBSPACE_BIN_DIR"])
    return bin_dir
  else:
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
  return None
