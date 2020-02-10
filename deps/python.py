
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "3.8.1"
HASH = "f215fa2f55a78de739c1787ec56b2bcd"

import os, tarfile
from ork import dep, host, path, cmake
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()


###############################################################################

class python(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(python,self)
    parclass.__init__(options=options)
    #print(options)
    build_dest = path.builds()/"python"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"python"
    self.OK = self.manifest.exists()
    self.fname = "Python-%s.tgz"%VERSION

  ########

  def __str__(self):
    return "Python3 (%s-source)" % VERSION

  ########

  def download_and_extract(self): #############################################

    url = "https://www.python.org/ftp/python/%s/%s"%(VERSION,self.fname)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "gz",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################
    self.download_and_extract()
    source_dir = self.build_dest/("Python-%s"%VERSION)
    build_temp = source_dir/".build"
    print(build_temp)
    if build_temp.exists():
      Command(["rm","-rf",build_temp]).exec()

    build_temp.mkdir(parents=True,exist_ok=True)
    os.chdir(str(build_temp))
    options = [
        "--prefix",path.prefix(),
        "--with-pydebug",
        "--enable-shared"
    ]
    if host.IsOsx:
       options += ["--with-openssl=/usr/local/Cellar/openssl@1.1/1.1.1d/"]

    Command(["../configure"]+options).exec()
    return 0==Command(["make","-j",host.NumCores,"install"]).exec()
