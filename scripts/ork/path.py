###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, sys, pathlib
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

def deps():
  return root()/"deps"

###############################################################################

def buildlogs():
  return stage()/"buildlogs"

###############################################################################

def dockers():
  return root()/"dockers"

###############################################################################

def apps():
    return stage()/"apps"

###############################################################################

def patches():
  return root()/"deps"/"patches"

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

def pkgconfigdir():
  return libs()/"pkgconfig"

###############################################################################

def manifests():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"manifests"

###############################################################################

def litex_env_dir():
    return builds()/"litex-buildenv"

###############################################################################

def temp():
  staging = Path(os.environ["OBT_STAGE"])
  return staging/"tempdir"

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


def orkid():
  orkroot = Path(os.environ["ORKID_WORKSPACE_DIR"])
  return orkroot

###############################################################################

def project_root():
  return root()/".."

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
  return Path("/usr/local")


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
