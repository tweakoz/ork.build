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
from obt import dep, host, path, git, cmake
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class minetest(dep.Provider):

  def __init__(self): ############################################
    super().__init__("minetest")
    #print(options)
    build_dest = path.builds()/"minetest"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"minetest"
    self.OK = self.manifest.exists()
    self.fname = "minetest-%s.zip" % VERSION
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "Minetest (github-commit-%s-source)" % VERSION

  ########

  def download_and_extract(self): #############################################
    from yarl import URL
    url = URL("https://github.com/minetest/minetest/archive/%s.zip"%VERSION)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "zip",
                                          HASH,
                                          self.build_dest)


    source_dir = self.build_dest/("minetest-%s"%VERSION)
    os.chdir(str(source_dir/"games"))
    git.Clone("https://github.com/minetest/minetest_game","minetest_game")

    os.chdir(str(source_dir/"games"/"minetest_game"/"mods"))

    # install mods

    git.Clone("https://github.com/sofar/luscious","luscious")
    git.Clone("https://notabug.org/TenPlus1/mobs_redo","mobs_redo")
    git.Clone("https://notabug.org/TenPlus1/mobs_animal","mobs_animal")
    git.Clone("https://notabug.org/TenPlus1/mobs_monster","mobs_monster")
    git.Clone("https://notabug.org/TenPlus1/mobs_npc","mobs_npc")
    git.Clone("https://notabug.org/TenPlus1/mobs_horse","mobs_horse")
    git.Clone("https://github.com/blert2112/mobs_sky.git","mobs_sky")
    git.Clone("https://github.com/FreeLikeGNU/goblins","goblins")
    git.Clone("https://github.com/maikerumine/mobs_mc","mobs_mc")

    git.Clone("https://github.com/tweakoz/minetest_tozcmd","tozcmd")

    for item in "technic mesecons pipeworks moreores digtron lightning".split():
      git.Clone("https://github.com/minetest-mods/%s"%item,item)

  def build(self): ############################################################

    psql = dep.require("postgresql").instance
    irrl = dep.require("irrlicht").instance
    luaj = dep.require("luajit").instance

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

    cmake.context(root=source_dir,env=cmakeEnv).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()

  def provide(self): ##########################################################
    if False==self.OK:
      self.download_and_extract()
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    return self.OK
