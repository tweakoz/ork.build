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

VERSION = "4.1.0"
###############################################################################

class opencv(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(opencv,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"opencv"
    self.OK = self.manifest.exists()
    self.cv_source_dest = path.builds()/"opencv"
    self.cv_build_dest = self.cv_source_dest/".build"
    self.cvcontrib_source_dest = path.builds()/"opencv_contrib"

  ########

  def __str__(self):
    return "OpenCV (github-%s)" % VERSION

  ########

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.cv_source_dest)
    os.system("rm -rf %s"%self.cvcontrib_source_dest)

  ########

  def provide(self): ##########################################################

    dep.require(["pkgconfig","qt5","pybind11"])

    python_dep = dep.require("python")

    if not self.cv_source_dest.exists():
      git.Clone("https://github.com/opencv/opencv.git",
                self.cv_source_dest,
                VERSION)

    if not self.cvcontrib_source_dest.exists():
      git.Clone("https://github.com/opencv/opencv_contrib.git",
                self.cvcontrib_source_dest,
                VERSION)

    cmakeEnv = {
      "CMAKE_BUILD_TYPE": "RELEASE",
      "INSTALL_C_EXAMPLES": "ON",
      "INSTALL_PYTHON_EXAMPLES": "ON",
      "ENABLE_PRECOMPILED_HEADERS": "OFF",
      "WITH_TBB": "OFF",
      "WITH_QT": "ON",
      "WITH_OPENGL": "OFF",
      "OPENCV_EXTRA_MODULES_PATH": "../../opencv_contrib/modules",
      "PYTHON_DEFAULT_EXECUTABLE": python_dep.executable(),
      # todo get internal python3 working
      # todo get internal openexr working
      "PYTHON3_EXECUTABLE": python_dep.executable(),
      "PYTHON3_LIBRARY": python_dep.lib(),
      "PYTHON_INCLUDE_DIR": python_dep.include_dir(),
      "PYTHON3_PACKAGES_PATH": python_dep.site_packages_dir(),
      "BUILD_EXAMPLES": "ON"
    }
    if host.IsLinux:
      cmakeEnv["WITH_V4L"]="ON"

    self.OK = self._std_cmake_build(self.cv_source_dest,self.cv_build_dest,cmakeEnv)
    return self.OK
