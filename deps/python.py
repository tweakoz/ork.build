
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
from ork import dep, host, path, cmake, env, pip
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.log import log

deco = Deco()


###############################################################################

class python(dep.Provider):

  def __init__(self): ############################################
    super().__init__()
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

  def env_init(self):
    log(deco.white("BEGIN python-env_init"))
    env.set("OBT_PYLIB",self.libdir())
    env.set("OBT_PYPKG",self.site_packages_dir())
    log(deco.white("END python-env_init"))

  ########

  def env_goto(self):
    return {
      "pylib": str(self.libdir()),
      "pypkg": str(self.site_packages_dir())
    }

  ########

  def version(self):
    return VERSION
  def executable(self):
    return path.bin()/"python3"
  def lib(self):
    # todo - use pkgconfig ?
    return path.libs()/"libpython3.8d.so"
  def libdir(self):
    # todo - use pkgconfig ?
    return path.libs()/"python3.8"
  def site_packages_dir(self):
    # todo - use pkgconfig ?
    return self.libdir()/"site-packages"
  def include_dir(self):
    return path.includes()/(VERSION+"d")

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
        "--enable-shared",
        "--enable-loadable-sqlite-extensions"
    ]
    if host.IsOsx:
       options += ["--with-openssl=/usr/local/Cellar/openssl@1.1/1.1.1d/"]
    else:
       options += ["--with-openssl=/usr"]

    Command(["../configure"]+options).exec()
    OK = (0==Command(["make","-j",host.NumCores,"install"]).exec())
    ################################
    # install default packages
    ################################
    if OK:
      Command(["pip3","install","--upgrade","pip"]).exec()
      pip.install(["pytest","yarl","numpy","zmq"])
      Command(["pip3","install","--upgrade",
               "Pillow","pysqlite3","jupyter","plotly"]).exec()
    ################################
    return OK
