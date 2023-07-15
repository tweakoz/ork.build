###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, git, make, pathtools, env, command
from obt.deco import Deco
from obt.wget import wget
from obt.cmake import context as cmake_context
from obt import log
from yarl import URL
from pathlib import Path

deco = Deco()
cmd = command.Command 

###############################################################################

class _qt5_from_source(dep.Provider):


  def __init__(self): ############################################
    super().__init__("qt5")
    #print(options)
    self.MAJOR_VERSION = "5.15"
    self.MINOR_VERSION = "2"
    self.HASH = "e1447db4f06c841d8947f0a6ce83a7b5"
    self.manifest = path.manifests()/"qt5"
    self.OK = self.manifest.exists()
    self.baseurl = URL("https://mirrors.ukfast.co.uk/sites/qt.io/official_releases/qt")
    self.fullver = "%s.%s" % (self.MAJOR_VERSION,self.MINOR_VERSION)
    self.name = "qt-everywhere-src-%s" % self.fullver
    self.xzname = "%s.tar.xz" % self.name
    self.url = self.baseurl/self.MAJOR_VERSION/self.fullver/"single"/self.xzname
    self.source_base = path.builds()/"qt5"
    self.source_root = self.source_base/self.name
    self.build_dest = path.builds()/"qt5"/"qt5-build"
    self._archlist = ["x86_64"]
    self.declareDep("assimp")
  ########
  def env_goto(self):
    return {
      "qt5-src": self.source_root,
      "qt5-build": self.build_dest
    }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.qt5dir()/"bin"/"qmlscene").exists()
  ########
  def on_build_shell(self):
    return command.subshell( directory=self.build_dest,
                             prompt = "QT5",
                             environment = dict() )
  ########
  def download_and_extract(self): #############################################
    self.arcpath = dep.downloadAndExtract([self.url],
                                           self.xzname,
                                           "xz",
                                           self.HASH,
                                           self.source_base)
  ########
  def wipe(self):
    os.system("rm -rf %s"%self.source_root)
    os.system("rm -rf %s"%self.build_dest)
  ########
  def build(self): ############################################################
    if dep.require(["assimp"])==None:
      return False
    self.OK = True
    #########################################
    # fetch source
    #########################################
    if not self.source_root.exists():
        self.download_and_extract()
    #########################################
    # prep for build
    #########################################
    if self.should_incremental_build:
        os.chdir(self.build_dest)
    else:
        pathtools.mkdir(self.build_dest,clean=True)
        os.chdir(self.build_dest)

        options =  ["-prefix", path.qt5dir()]
        options += ["-release"]
        options += ["-opensource", "-confirm-license"]
        #options += ["-c++std", "c++14", "-shared"]
        #options += ["-nomake", "tests"]
        #options += ["-nomake", "examples"]
        #options += ["-opengl","desktop"]

        if host.IsOsx:
          print("yo")
          #options += ["-qt-libpng","-qt-zlib","-no-framework.]
          #options += [,"-qt-libjpeg","-qt-pcre","-qt-freetype"]
          #options += ["-no-feature-sql"] # xcode11 + sql-tds (long long / uint64_t typedef compile errors)
          #options += ["-no-feature-location"]
        else:
          options += ["-system-zlib"]
          options += ["-xcb"]
        options += ["-skip","qtwebengine"]
        options += ["-system-assimp"]
        #options += ["-no-rpath"]
        #options += ["-pkg-config"]
        #options += ["-proprietary-codecs"]

        b = cmd(["sh", self.source_root/"configure"]+options)
        self.OK = (b.exec()==0)
    #########################################
    # build
    #########################################
    if self.OK:
      self.OK = (make.exec(parallelism=self.default_parallelism)==0)
    if self.OK:
      self.OK = (make.exec(parallelism=self.default_parallelism)==0)
    # uhhuh - https://bugreports.qt.io/browse/QTBUG-60496
    if self.OK:
      self.OK = (0==make.exec(target="install", parallelism=0.0))
    return self.OK

###############################################################################

class _qt5_from_homebrew(dep.HomebrewProvider):
  def __init__(self):
    super().__init__("qt5","qt5")
    self.fullver = "5.15.1"
  def install_dir(self):
    return path.Path("/usr/local/opt/qt5")

###############################################################################

BASE = _qt5_from_source
if host.IsOsx:
  BASE = _qt5_from_homebrew

###############################################################################

class qt5(BASE):
  def __init__(self):
    super().__init__()
  ########
  def __str__(self):
    return "QT5"
  ########
  def env_init(self):
    log.marker("registering QT5(%s) SDK"%self.fullver)
    if host.IsOsx:
      qtdir = Path("/")/"usr"/"local"/"opt"/"qt5"
    else:
      qtdir = path.stage()/"qt5"
    env.set("QTDIR",qtdir)
    env.prepend("PATH",qtdir/"bin")
    env.prepend("LD_LIBRARY_PATH",qtdir/"lib")
    #env.append("PKG_CONFIG_PATH",qtdir/"lib"/"pkgconfig")
    env.prepend("PKG_CONFIG_PATH",qtdir/"lib"/"pkgconfig")
    env.set("QTVER",self.fullver)
  ########
  @property
  def include_dir(self):
    return path.qt5dir()/"include"
