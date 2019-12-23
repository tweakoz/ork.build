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

  def provide(self): ##########################################################
    if False==self.OK:

        os.system("rm -rf %s"%self.cv_source_dest)
        os.system("rm -rf %s"%self.cvcontrib_source_dest)

        git.Clone("https://github.com/opencv/opencv.git",
                  self.cv_source_dest,
                  VERSION)

        git.Clone("https://github.com/opencv/opencv_contrib.git",
                  self.cvcontrib_source_dest,
                  VERSION)

        pathtools.mkdir(self.cv_build_dest,clean=True)
        pathtools.chdir(self.cv_build_dest)

        cmakeEnv = {
            "CMAKE_BUILD_TYPE": "RELEASE",
            "INSTALL_C_EXAMPLES": "ON",
            "INSTALL_PYTHON_EXAMPLES": "ON",
            "ENABLE_PRECOMPILED_HEADERS": "OFF",
            "WITH_TBB": "OFF",
            "WITH_V4L": "ON",
            "WITH_QT": "OFF",
            "WITH_OPENGL": "OFF",
            "OPENCV_EXTRA_MODULES_PATH": "../../opencv_contrib/modules",
            "BUILD_EXAMPLES": "ON"
        }

        cmake_ctx = cmake.context(root="..",env=cmakeEnv)
        if cmake_ctx.exec()==0:
            if make.exec("install")==0:
                self.manifest.touch()
                self.OK = True

    return self.OK
