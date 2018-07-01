###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "0.4"
HASH = "e754d6ca543d943ab1364e55d48b2840"

import os, tarfile
from yarl import URL
from ork import dep, host, path
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import CMakeContext

deco = Deco()
psql = dep.require("postgresql").instance
irrl = dep.require("irrlicht").instance
    
###############################################################################

class minetest(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(minetest,self)
    parclass.__init__(options=options)
    #print(options)
    build_dest = path.builds()/"minetest"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"minetest"
    self.OK = self.manifest.exists()
    self.fname = "minetest-stable-%s.zip"%VERSION
    if False==self.OK:
      self.download_and_extract()
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

  def download_and_extract(self): #############################################

    url = URL("https://github.com/minetest/minetest/archive/stable-%s.zip"%VERSION)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "zip",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################

    source_dir = self.build_dest/("minetest-stable-%s"%VERSION)
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

    CMakeContext(root=source_dir,env=cmakeEnv).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()

  def provide(self): ##########################################################

      return self.OK

