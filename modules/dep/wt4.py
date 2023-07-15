###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "4.1.2"
HASH = "3a4621dd15a774658008e43203f49137"

import os, tarfile
from yarl import URL
from obt import dep, host, path, cmake
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class wt4(dep.Provider):

  def __init__(self): ############################################
    super().__init__("wt4")
    #print(options)
    build_dest = path.builds()/"wt4"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"wt4"
    self.OK = self.manifest.exists()
    self.fname = "wt-%s.tar.gz"%VERSION
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "WT4 (github-%s)" % VERSION

  ########

  def download_and_extract(self): #############################################

    url = URL("https://github.com/emweb/wt/archive/%s/.tar.gz"%VERSION)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "gz",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################

    #psql = dep.require("postgresql").instance

    source_dir = self.build_dest/("wt-%s"%VERSION)
    build_temp = source_dir/".build"
    print(build_temp)
    if build_temp.exists():
      Command(["rm","-rf",build_temp]).exec()

    build_temp.mkdir(parents=True,exist_ok=True)
    os.chdir(str(build_temp))
    cmakeEnv = {
      "BOOST_ALL_DYN_LINK": None,
      "WT_BOOST_DISCOVERY": 1,
      #"BOOST_COMPILER": "clang++",
      #"BOOST_PREFIX": path.prefix(),
      #"BOOST_VERSION": boost.version,
      "ENABLE_MYSQL": False,
      #"ENABLE_POSTGRES": True,
      "ENABLE_QT4": False,
      "ENABLE_SQLITE": False,
      "WT_CPP_11_MODE": "-std=c++11",
    }
    if host.IsOsx:
      cmakeEnv["CMAKE_MACOSX_RPATH"]=1
      cmakeEnv["CMAKE_INSTALL_RPATH"]=path.prefix()/"lib"

    cmake.context(root=source_dir,env=cmakeEnv).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()

  def provide(self): ##########################################################

    if False==self.OK:
      self.download_and_extract()
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()
    return self.OK
