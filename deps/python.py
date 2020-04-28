
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION_MAJOR = "3.8"
VERSION_MINOR = "1"
VERSION = "%s.%s" % (VERSION_MAJOR,VERSION_MINOR)
HASH = "f215fa2f55a78de739c1787ec56b2bcd"

import os, tarfile
from ork import dep, host, path, cmake, env, pip
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork import log

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
    log.marker("registering Python(%s) SDK"%VERSION)
    env.set("OBT_PYLIB",self.library_dir)
    env.set("OBT_PYPKG",self.site_packages_dir)

  ########

  def env_goto(self):
    return {
      "pylib": str(self.library_dir),
      "pypkg": str(self.site_packages_dir)
    }

  ########

  def env_properties(self):
    return {
      "pylib": self.library_dir,
      "pypkg": self.site_packages_dir
    }

  ########

  @property
  def version(self):
    return VERSION
  ########
  @property
  def version_major(self):
    return VERSION_MAJOR
  ########
  @property
  def executable(self):
    return path.bin()/"python3"
  ########
  @property
  def _deconame(self):
    return "python%s"%VERSION_MAJOR
  ########
  @property
  def _deconame_d(self):
    return "python%sd"%VERSION_MAJOR
  ########
  @property
  def library_dir(self):
    # todo - use pkgconfig ?
    return path.libs()/self._deconame
  ########
  @property
  def library_file(self):
    # todo - use pkgconfig ?
    return path.libs()/("lib%s.%s"%(\
                        self._deconame_d,\
                        self.shlib_extension))
  ########
  @property
  def site_packages_dir(self):
    # todo - use pkgconfig ?
    return self.library_dir/"site-packages"
  ########
  @property
  def include_dir(self):
    return path.includes()/self._deconame
  ########

  def download_and_extract(self): #############################################

    url = "https://www.python.org/ftp/python/%s/%s"%(VERSION,self.fname)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "gz",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################
    dep.require("pkgconfig")
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
       options += ["--with-openssl=/usr/local/opt/openssl@1.1"]
    else:
       options += ["--with-openssl=/usr"]

    Command(["../configure"]+options).exec()
    OK = (0==Command(["make","-j",host.NumCores,"install"]).exec())
    ################################
    # install default packages
    ################################
    if OK:
      Command(["pip3","install","--upgrade","pip"]).exec()
      pip.install(["virtualenv"])
      pip.install(["yarl","pytest",
                   "numpy","scipy",
                   "matplotlib",
                   "zmq"])
      Command(["pip3","install","--upgrade",
               "Pillow","pysqlite3","jupyter","plotly","trimesh"]).exec()
    ################################
    return OK
