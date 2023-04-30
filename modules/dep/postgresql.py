
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "10.4"
HASH = "8e8770c289b3e0bdb779b5b171593479"

import os, tarfile
from yarl import URL
from ork import dep, host, path, cmake
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class postgresql(dep.Provider):

  def __init__(self): ############################################
    super().__init__("postgresql")
    #print(options)
    self.OK = self.manifest.exists()
    self.fname = "postgresql-%s.tar.bz2"%VERSION
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "Postgresql (%s-source)" % VERSION

  ########

  def download_and_extract(self): #############################################

    url = URL("https://ftp.postgresql.org/pub/source/v%s/postgresql-%s.tar.bz2"%(VERSION,VERSION))

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "bz2",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################
    self.download_and_extract()
    source_dir = self.build_dest/("postgresql-%s"%VERSION)
    build_temp = source_dir/".build"
    print(build_temp)
    if build_temp.exists():
      Command(["rm","-rf",build_temp]).exec()

    build_temp.mkdir(parents=True,exist_ok=True)
    os.chdir(str(build_temp))
    Command(["../configure","--prefix",path.prefix()]).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()
