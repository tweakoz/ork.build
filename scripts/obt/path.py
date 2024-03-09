###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, sys, pathlib
from pathlib import Path as _Path_, PosixPath as _PosixPath_, WindowsPath  as _WindowsPath_
from functools import lru_cache

###############################################################################

class Path(_Path_) :
 def __new__(cls, *args, **kvps):
  return super().__new__(WindowsPath if os.name == 'nt' else PosixPath, *args, **kvps)

 @property
 def norm(self):
   return Path(os.path.normpath(str(self)))
    
class WindowsPath(_WindowsPath_, Path) :
 pass

class PosixPath(_PosixPath_, Path) :
  if "OBT_STAGE" in os.environ:
    def chdir(self):
      from obt import buildtrace
      buildtrace.buildTrace({"op":"path.chdir(%s)"%str(self)})
      os.chdir(str(self))
  else:
    def chdir(self):
      os.chdir(str(self))
  pass


###############################################################################

def fileOfInvokingModule():
  frame = inspect.stack()[1]
  module = inspect.getmodule(frame[0])
  if module:
    this_path = os.path.realpath(module.__file__)
    return Path(this_path)
  else:
      assert(False)

def directoryOfInvokingModule(the_file=None):
  if(the_file==None):
    import inspect
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    if module:
      this_path = os.path.realpath(module.__file__)
      return Path(os.path.dirname(this_path))
    else:
      assert(False)
  else:
    this_path = os.path.realpath(the_file)
    return Path(os.path.dirname(this_path))

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

def subspace_builds():
  return subspace_dir()/"builds"

###############################################################################

def conan_prefix():
  return subspace_dir()/"conan"

##########################################

@lru_cache(maxsize=None)
def obt_data_base():
  mpath = obt_module_path()
  keep_going = True
  counter = 0
  while keep_going:
    p1 = mpath/"modules"/"dep"
    p2 = mpath/"obt"/"modules"/"dep"
    if p1.exists():
      return mpath
    elif p2.exists():
      return mpath/"obt"
    else:
      mpath = mpath.parent
      counter+=1
    keep_going = (counter<10)
  assert(False)
  return None

##########################################

@lru_cache(maxsize=None)
def obt_in_tree():
  return (obt_data_base()/".git").exists()

##########################################

@lru_cache(maxsize=None)
def pip_obt_data_path(filename):
  return obt_data_base()/filename

##########################################

@lru_cache(maxsize=None)
def obt_module_path():
   import obt 
   return Path(obt.__path__[0])

##########################################

@lru_cache(maxsize=None)
def obt_modules_base():
  return obt_data_base()/"modules"

##########################################

@lru_cache(maxsize=None)
def obt_bin_priv_base():
  return obt_data_base()/"bin_priv"

##########################################

@lru_cache(maxsize=None)
def running_from_pip():
  if "OBT_INPLACE" in os.environ:
    return False
  else:
    return True

###############################################################################

def modules(provider=None):
  if provider==None:
    if running_from_pip():
      return obt_modules_base()
    else:
      return root()/"modules"
  else:
    depnode = provider._node
    name = provider._name
    return depnode.modules_base

###############################################################################

#def dockers():
 # return modules()/"docker"

###############################################################################

@lru_cache(maxsize=None)
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

def pysite():
  return scripts()/"obt"

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

def subspace_includes():
  return subspace_dir()/"include"

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

def manifests():
  return subspace_dir()/"manifests"

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
  import obt.command
  result = obt.command.capture([
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
