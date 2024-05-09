###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v2.50.0-obt"

import os
from obt import dep, host, path, cmake, git, make, pathtools, log
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()
class _realsense_from_source(dep.StdProvider):
  name = "realsense2"
  def __init__(self): ############################################
    super().__init__(_realsense_from_source.name)
    self.fullver = VERSION
    self.declareDep("cmake")
    self.declareDep("glfw")
    self.createBuilder(dep.CMakeBuilder)

    CMAKE_VARS = {
      "CMAKE_CXX_FLAGS": "-Wno-error=deprecated",
      "FORCE_RSUSB_BACKEND": "true"
    }

    if self._target.identifier=="aarch64-macos":
      _vars = {
        "TBB_ROOT": "/opt/homebrew/Cellar/tbb/2021.5.0_1/",
        "CMAKE_THREAD_LIBS_INIT": "-lpthread",
        "CMAKE_HAVE_THREADS_LIBRARY": "1",
        "CMAKE_USE_WIN32_THREADS_INIT": "0",
        "CMAKE_USE_PTHREADS_INIT": "1",
        "THREADS_PREFER_PTHREAD_FLAG": "ON"
      }
      CMAKE_VARS.update(_vars)

    self._builder.setCmVars(CMAKE_VARS)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=_realsense_from_source.name,
                             repospec="tweakoz/librealsense",
                             revision=VERSION,
                             recursive=False)

  #######################################################################
  def linkenv(self): 
    LIBS = ["librealsense2"]
    return {
        "LIBS": LIBS,
        "LFLAGS": ["-l%s"%item for item in LIBS]
    }
  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  #######################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"librealsense2.so").exists()

###############################################################################

class _realsense_from_homebrew(dep.HomebrewProvider):
  def __init__(self):
    super().__init__("librealsense","librealsense")
    self.fullver = "5.15.1"
  #def install_dir(self):
  #  return path.Path("/usr/local/opt/qt5")

###############################################################################

BASE = _realsense_from_source
#if host.IsOsx:
#  BASE = _realsense_from_homebrew

###############################################################################

class realsense2(BASE):
  def __init__(self):
    super().__init__()
  ########
  def __str__(self):
    return "realsense2"
  ########
  def env_init(self):
    log.marker("registering realsense2(%s) SDK"%self.fullver)
    #if host.IsOsx:
    #  qtdir = Path("/")/"usr"/"local"/"opt"/"qt5"
    #else:
    #  qtdir = path.stage()/"qt5"
    #env.set("QTDIR",qtdir)
    #env.prepend("PATH",qtdir/"bin")
    #env.prepend("LD_LIBRARY_PATH",qtdir/"lib")
    #env.append("PKG_CONFIG_PATH",qtdir/"lib"/"pkgconfig")
    #env.prepend("PKG_CONFIG_PATH",qtdir/"lib"/"pkgconfig")
    #env.set("QTVER",self.fullver)
  ########
  #@property
  #def include_dir(self):
  #  return path.qt5dir()/"include"
