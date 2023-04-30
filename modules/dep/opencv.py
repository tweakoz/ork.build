###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, pathtools, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

VERSION = "4.7.0"
###############################################################################

class opencv(dep.StdProvider):
  name = "opencv"
  def __init__(self): ############################################
    super().__init__(opencv.name)

    self.misc_deps = [self.declareDep(x) for x in ["pkgconfig","pybind11","opencv_contrib"]]
    self.EXR = self.declareDep("openexr")
    self.python_dep = self.declareDep("python")

    if self.python_dep == None:
      return False 

    self._builder = self.createBuilder(dep.CMakeBuilder)

    cmakeEnv = {
      "CMAKE_BUILD_TYPE": "RELEASE",
      "INSTALL_C_EXAMPLES": "ON",
      "INSTALL_PYTHON_EXAMPLES": "ON",
      "ENABLE_PRECOMPILED_HEADERS": "OFF",
      "WITH_TBB": "OFF",
      "WITH_GDAL": "OFF",
      "WITH_QT": "OFF",
      "WITH_GTk": "ON",
      "WITH_GTK_2_X": "OFF",
      "WITH_OPENGL": "OFF",
      "WITH_CAROTENE": "OFF",
      "WITH_FFMPEG": "OFF",
      "WITH_GSTREAMER": "OFF",
      "OPENCV_EXTRA_MODULES_PATH": "../../opencv_contrib/modules",
      "WITH_OPENEXR": "OFF",
      "BUILD_opencv_gapi":"OFF", # fails to build on ub22-aarch64
      "BUILD_opencv_python2":"OFF", # fails to build on ub22-aarch64
      "BUILD_EXAMPLES": "OFF",
      #"OPENEXR_ROOT": path.stage(),
      # todo get internal python3 working
      # todo get internal openexr working
      "PYTHON_DEFAULT_EXECUTABLE": self.python_dep.executable,
      "PYTHON3_EXECUTABLE": self.python_dep.executable,
      "PYTHON3_LIBRARY": self.python_dep.library_file,
      "PYTHON3_INCLUDE_PATH": self.python_dep.include_dir,
      "PYTHON3_PACKAGES_PATH": self.python_dep.site_packages_dir,
    }
    if host.IsLinux:
      cmakeEnv["WITH_V4L"]="ON"
    self._builder.setCmVars(cmakeEnv)

    ######################################################

  ########################################################################

  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=opencv.name,
                             repospec="tweakoz/opencv",
                             revision=VERSION,
                             recursive=False)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"opencv4"/"opencv2"/"core.hpp").exists()
