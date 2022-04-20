
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION_MAJOR = "3.9"
VERSION_MINOR = "4"
VERSION = "%s.%s" % (VERSION_MAJOR,VERSION_MINOR)
HASH = "cc8507b3799ed4d8baa7534cd8d5b35f"

import os, tarfile
from ork import dep, host, path, cmake, env, pip
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork import log, osx

deco = Deco()


###############################################################################

class python(dep.Provider):

  def __init__(self): ############################################
    super().__init__("python")
    #print(options)
    build_dest = path.builds()/"python"
    self.build_dest = build_dest
    self.manifest = path.manifests()/"python"
    self.OK = self.manifest.exists()
    self.fname = "Python-%s.tgz"%VERSION
    self.source_dir = self.build_dest/("Python-%s"%VERSION)

  ########  

  def __str__(self):
    return "Python3 (%s-source)" % VERSION

  ########

  def env_init(self):
    log.marker("registering Python(%s) SDK"%VERSION)
    env.set("OBT_PYLIB",self.library_dir)
    env.set("OBT_PYPKG",self.site_packages_dir)
    env.set("OBT_PYTHON_HEADER_PATH",self.include_dir)
    env.set("OBT_PYTHON_LIB_PATH",self.home_dir/"lib")
    env.set("OBT_PYTHON_PYLIB_PATH",self.pylib_dir)
    env.set("OBT_PYTHON_LIB_FILE",self.library_file)
    env.set("OBT_PYTHON_LIB_NAME",self.library_name)
    env.set("OBT_PYTHON_DECO_NAME",self._deconame)
    env.set("OBT_PYTHON_DECOD_NAME",self._deconame_d)
    env.prepend("PATH",self.virtualenv_dir/"bin" )
    env.set("VIRTUAL_ENV",self.virtualenv_dir)
    env.prepend("LD_LIBRARY_PATH",self.home_dir/"lib")
    
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
    return self.home_dir/"lib"
  ########
  @property
  def venvlibrary_dir(self):
    # todo - use pkgconfig ?
    return self.virtualenv_dir/"lib64"
  ########
  @property
  def pylib_dir(self):
    # todo - use pkgconfig ?
    return self.library_dir/self._deconame
  ########
  @property
  def library_file(self):
    # todo - use pkgconfig ?
    return ("lib%s.%s"%(self._deconame_d,self.shlib_extension))
  ########
  @property
  def library_name(self):
    # todo - use pkgconfig ?
    return ("lib%s"%self._deconame_d)
  ########
  @property
  def site_packages_dir(self):
    # todo - use pkgconfig ?
    return self.venvlibrary_dir/self._deconame/"site-packages"
  ########
  @property
  def virtualenv_dir(self):
    return path.stage()/"pyvenv"
  ########
  @property
  def home_dir(self):
    return path.stage()/("python-%s"%VERSION)
  ########
  @property
  def include_dir(self):
    return self.home_dir/"include"/self._deconame_d
  ########
  @property
  def executable(self):
    return self.virtualenv_dir/"bin"/"python3"
  ########

  def download_and_extract(self): #############################################

    url = "https://www.python.org/ftp/python/%s/%s"%(VERSION,self.fname)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "gz",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################
    pkgconfig = dep.require("pkgconfig")
    if pkgconfig == None:
      return False
      
    self.download_and_extract()
    build_temp = self.source_dir/".build"
    print(build_temp)
    if build_temp.exists():
      Command(["rm","-rf",build_temp]).exec()

    build_temp.mkdir(parents=True,exist_ok=True)
    os.chdir(str(build_temp))
    options = [
        "--prefix",self.home_dir,
        "--with-pydebug",
        "--with-system-ffi",
        "--enable-shared",
        "--enable-loadable-sqlite-extensions",
        "--with-ensurepip=install" # atomically build pip
    ]
    if host.IsOsx:
       sdkdir = path.osx_sdkdir()
       print(sdkdir)
       options += ["--with-openssl=/usr/local/opt/openssl@1.1"]
       options += ["--enable-universalsdk=%s"%sdkdir]
       options += ["--with-universal-archs=intel-64"]
    else:
       options += ["--with-openssl=/usr"]


    env.set("CCFLAGS","-march=x86_64")

    Command(["../configure"]+options).exec()
    OK = (0==Command(["make",
                      "-j", host.NumCores,
                      "install"]).exec())
    ################################
    # install default packages
    ################################
    if OK:
      env.prepend("LD_LIBRARY_PATH",self.home_dir/"lib")
      os.chdir(str(build_temp))
      obt_python = self.home_dir/"bin"/"python3"
      venv_python = self.virtualenv_dir/"bin"/"python3"
      Command([obt_python,"-m","pip","install","--upgrade","pip"]).exec()
      Command([obt_python,"-m","pip","install","virtualenv"]).exec()
      Command([obt_python,"-m","venv", self.virtualenv_dir]).exec()
      Command([venv_python,"-m","pip","install","--upgrade","pip"]).exec()
      Command([venv_python,"-m","pip","install","yarl"]).exec()
      Command([venv_python,"-m","pip","install","toposort"]).exec()
      Command([venv_python,"-m","pip","install","pytest"]).exec()
    ################################
    return OK

  def areRequiredSourceFilesPresent(self):
    return (self.source_dir/"LICENSE").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.executable).exists()
