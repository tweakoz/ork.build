
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION_MAJOR = "3"
VERSION_MINOR = "11"
VERSION_MICRO = "6"
VERSION = "%s.%s.%s" % (VERSION_MAJOR,VERSION_MINOR,VERSION_MICRO)
HASH = "ed23dadb9f1b9fd2e4e7d78619685c79"

import os, tarfile, sys
from obt import dep, host, path, cmake, env, pip
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt import log

deco = Deco()


###############################################################################

class python_from_source(dep.Provider):

  def __init__(self,target=None): ############################################
    super().__init__("python")
    self._debug_build = False
    ##########################################
    if target==None:
      # target implied is host => INIT scope
      self.scope = dep.ProviderScope.INIT
    else:
      assert(False) # not supported yet
    ##########################################
    # TODO - remove recursion...
    #self.declareDep("pkgconfig")
    ##########################################
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
    env.set("OBT_PYTHON_SUBSPACE_BUILD_DIR",path.builds())
    env.set("OBT_PYLIB",self.library_dir)
    env.set("OBT_PYPKG",self.site_packages_dir)
    env.set("OBT_PYTHON_HEADER_PATH",self.include_dir)
    env.set("OBT_PYTHON_LIB_PATH",self.home_dir/"lib")
    env.set("OBT_PYTHON_PYLIB_PATH",self.pylib_dir)
    env.set("OBT_PYTHON_LIB_FILE",self.library_file)
    env.set("OBT_PYTHON_LIB_NAME",self.library_name)
    env.set("OBT_PYTHON_DECO_NAME",self._deconame)
    env.set("OBT_PYTHON_DECOD_NAME",self._deconame_d)
    env.set("OBT_PYTHONHOME",self.virtualenv_dir)
    if True: # WIP
      env.prepend("PATH",self.virtualenv_dir/"bin" )
    #env.set("VIRTUAL_ENV",self.virtualenv_dir)
    env.prepend("LD_LIBRARY_PATH",self.home_dir/"lib")
    env.prepend("PKG_CONFIG_PATH",self.library_dir/"pkgconfig")
    
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
    va = VERSION_MAJOR
    vb = VERSION_MINOR
    vc = VERSION_MICRO
    return "%s.%s.%s" % (va,vb,vc)
  ########
  @property
  def version_major(self):
    va = VERSION_MAJOR
    vb = VERSION_MINOR
    return "%s.%s" % (va,vb)
  ########
  @property
  def _deconame(self):
    return "python%s"%(self.version_major)
  ########
  @property
  def _deconame_d(self):
    a = self._deconame
    if self._debug_build:
      a+= "d"
    return a
  ########
  @property
  def library_dir(self):
    # todo - use pkgconfig ?
    return self.home_dir/"lib"
  ########
  @property
  def venvlibrary_dir(self):
    # todo - use pkgconfig ?
    return self.virtualenv_dir/"lib"
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
    return self.home_dir
  ########
  @property
  def home_dir(self):
    return path.Path(os.environ["OBT_PYTHONHOME"])
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
        #"--enable-loadable-sqlite-extensions",
        "--with-ensurepip=install" # atomically build pip
    ]

    if self._debug_build:
      options += ["--with-pydebug"]

    env.set("CCFLAGS","-march=%s"%self._target.architecture)

    if host.IsOsx:
       from obt import macos, macos_homebrew
       sdkdir = path.osx_sdkdir()
       print(sdkdir)
       #options += ["--enable-universalsdk=%s"%sdkdir]

       sslpath = macos_homebrew.prefix_for_package("openssl@3")
       print(sslpath)
 
       xzpath = macos_homebrew.prefix_for_package("xz")
       print(xzpath)
 
       options += ["--with-openssl=%s"%sslpath]
       #options += ["--enable-framework"]
       options += ["--enable-shared"]
        #export LDFLAGS="-L$(brew --prefix xz)/lib $LDFLAGS";  export CPPFLAGS="-I$(brew --prefix xz)/include $CPPFLAGS";  export PKG_CONFIG_PATH="$(brew --prefix xz)/lib/pkgconfig:$PKG_CONFIG_PATH"
      
    else:
       options += ["--with-system-ffi"]
       options += ["--with-openssl=/usr"]
       options += ["--enable-shared"]

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

      modules =  ["yarl","toposort","pytest","os_release","pyyaml", "conan"]

      Command([venv_python,"-m","pip","install"]+modules).exec()

    ################################
    return OK

  def areRequiredSourceFilesPresent(self):
    return (self.source_dir/"LICENSE").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.executable).exists()


python = python_from_source

