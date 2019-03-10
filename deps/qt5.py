###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v5.11.1"
HASH = "32eee8f17a24305ddf33e9ca5821f4cdaa1483cd"

import os, tarfile
from ork import dep, host, path, git
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context as cmake_context

deco = Deco()

###############################################################################

class qt5(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(qt5,self)
    parclass.__init__(options=options)
    #print(options)
    build_dest = path.builds()/"qt5"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"qt5"
    self.OK = self.manifest.exists()
    self.fname = "qt5-%s.zip"%VERSION

  ########

  def __str__(self):
    return "QT5 (%s-source)" % VERSION

  ########

  def download_and_extract(self): #############################################
    git.Clone("https://github.com/qt/qt5",self.build_dest,"v5.11")
    os.chdir(str(self.build_dest))
    Command(["./init-repository"]).exec()

  def build(self): ############################################################

    source_dir = self.build_dest/("qt5-%s"%VERSION)
    build_temp = source_dir/".build"
    print(build_temp)
    if build_temp.exists():
      Command(["rm","-rf",build_temp]).exec()

    build_temp.mkdir(parents=True,exist_ok=True)
    os.chdir(str(build_temp))
    cmakeEnv = {
    }
    if host.IsOsx:
      cmakeEnv["CMAKE_MACOSX_RPATH"]=1
      cmakeEnv["CMAKE_INSTALL_RPATH"]=path.prefix()/"lib"
    
    cmake_context(root=source_dir,env=cmakeEnv).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()

  def provide(self): ##########################################################
    if False==self.OK:
      self.download_and_extract()
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    return self.OK
