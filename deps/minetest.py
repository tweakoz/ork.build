###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "03edcafdda550e55e29bf48a682097028ae01306"
HASH = "1453e79e663ea3bd8b528ef20a17109b"

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
    self.fname = "minetest-%s.zip" % VERSION
    if False==self.OK:
      self.download_and_extract()
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

  def download_and_extract(self): #############################################

    url = URL("https://github.com/minetest/minetest/archive/%s.zip"%VERSION)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "zip",
                                          HASH,
                                          self.build_dest)


    source_dir = self.build_dest/("minetest-%s"%VERSION)
    os.chdir(str(source_dir/"games"))
    Command(["git","clone","https://github.com/minetest/minetest_game"]).exec()

    os.chdir(str(source_dir/"games"/"minetest_game"/"mods"))

    # install mods
    for item in "technic mesecons pipeworks moreores digtron lightning".split():
      Command(["git","clone","https://github.com/minetest-mods/%s"%item]).exec()

  def build(self): ############################################################

    source_dir = self.build_dest/("minetest-%s"%VERSION)
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
      cmakeEnv["GETTEXT_INCLUDE_DIR"]="/usr/local/opt/gettext/include"
      cmakeEnv["GETTEXT_LIBRARY"]="/usr/local/opt/gettext/lib"

    CMakeContext(root=source_dir,env=cmakeEnv).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()

  def provide(self): ##########################################################

      return self.OK

