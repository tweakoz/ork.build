###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "2.0.5"
HASH = "48353202cbcacab84ee41a5a70ea0a2c"

import os, tarfile
from yarl import URL
from ork import dep, host, path
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
import fileinput

deco = Deco()
    
###############################################################################

class luajit(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(luajit,self)
    parclass.__init__(options=options)
    #print(options)
    build_dest = path.builds()/"luajit"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"luajit"
    self.OK = self.manifest.exists()
    self.fname = "luajit-stable-%s.tar.gz"%VERSION
    self.source_dir = self.build_dest/("LuaJIT-%s"%VERSION)

  ########

  def __str__(self):
    return "LuaJit (%s-source)" % VERSION

  ########

  def download_and_extract(self): #############################################

    url = URL("http://luajit.org/download/LuaJIT-%s.tar.gz"%VERSION)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "gz",
                                          HASH,
                                          self.build_dest)


    with fileinput.FileInput(str(self.source_dir/"Makefile"), inplace=True, backup='.bak') as file:
      for line in file:
        print(line.replace("export PREFIX= /usr/local", "export PREFIX=%s"%path.prefix()), end='')

  def build(self): ############################################################

    os.chdir(str(self.source_dir))
    return 0 == Command(["make","-j",host.NumCores,"install"]).exec()

  def provide(self): ##########################################################
    if False==self.OK:
      self.download_and_extract()
      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    return self.OK

