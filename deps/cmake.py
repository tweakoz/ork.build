###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="v3.16.4"

import os, tarfile
import ork.cmake
from ork import dep, host, path, git, make, pathtools
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class cmake(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(cmake,self)
    parclass.__init__(options=options)

    self.source_dest = path.builds()/"cmake"
    self.build_dest = path.builds()/"cmake"/".build"
    self.manifest = path.manifests()/"cmake"

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "CMAKE (latest)"

  def wipe(self): ##########################################################
    os.system("rm -rf %s"%self.source_dest)

  def build(self): ##########################################################

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
        git.Clone("https://github.com/kitware/cmake",self.source_dest,VERSION,cache=False)

    #########################################
    # prep for build
    #########################################

    if self.incremental():
        os.chdir(self.build_dest)
    else:
        pathtools.mkdir(self.build_dest, clean=True)
        os.chdir(self.build_dest)
        cmake_ctx = ork.cmake.context("..")
        cmake_ctx.exec()

    #########################################
    # build
    #########################################

    return (make.exec("install")==0)
