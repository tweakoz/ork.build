###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path, env
from ork.path import Path
from ork.log import log
from ork.command import Command
from ork.deco import Deco
deco = Deco()

###############################################################################

class _ispc_from_source(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self.llvm = dep.instance("llvm")
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/ispc/ispc"
    self._fetcher._cache=False,
    self._fetcher._recursive=False
    self._fetcher._revision = "v1.12.0"
    self._builder = dep.CMakeBuilder(name)
    self._builder.requires([self.llvm])
    if host.IsOsx:
      self._builder.setCmVar("BISON_EXECUTABLE",path.osx_brewopt()/"bison"/"bin"/"bison")
      sysroot_cmd = Command(["xcrun","--show-sdk-path"])
      sysroot = sysroot_cmd.capture().replace("\n","")
      print(sysroot)
      self._builder.setCmVars({
        "CMAKE_OSX_ARCHITECTURES:STRING":"x86_64",
        "CMAKE_OSX_DEPLOYMENT_TARGET:STRING":"10.14",
        "CMAKE_OSX_SYSROOT:STRING":sysroot,
        "CMAKE_MACOSX_RPATH": "1",
        "CMAKE_INSTALL_RPATH": path.libs(),
        "CMAKE_SKIP_INSTALL_RPATH:BOOL":"NO",
        "CMAKE_SKIP_RPATH:BOOL":"NO",
        "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib"
      })

###############################################################################

class _ispc_from_wget(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self._fetcher = dep.WgetFetcher(name)
    #self._fetcher._url = "https://ci.appveyor.com/api/projects/ispc/ispc/artifacts/build%2Fispc-trunk-linux.tar.gz?job=Environment%3A%20APPVEYOR_BUILD_WORKER_IMAGE%3DUbuntu1604%2C%20LLVM_VERSION%3Dlatest"
    self._fetcher._url = "https://downloads.sourceforge.net/project/ispcmirror/v1.12.0/ispc-v1.12.0-linux.tar.gz?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fispcmirror%2Ffiles%2Fv1.12.0%2Fispc-v1.12.0-linux.tar.gz%2Fdownload&ts=1585039148"
    self._fetcher._fname = "ispc.tgz"
    self._fetcher._arctype = "tgz"
    self._fetcher._md5 = "7f0150e33a8f64a1942134b77f3c5046"
    self._builder = dep.BinInstaller(name)
    src_dir = path.builds()/"ispc"/"ispc-v1.12.0-linux"
    dst_dir = path.stage()
    self._builder.declare(src_dir/"bin"/"ispc",dst_dir/"bin"/"ispc")

###############################################################################

BASE = _ispc_from_wget
if host.IsOsx:
  BASE = _ispc_from_source

###############################################################################

class ispc(BASE):
  def __init__(self):
    super().__init__("ispc")
  def env_init(self):
    log(deco.white("BEGIN ispc-env_init"))
    env.set("ISPC",path.stage()/"bin"/"ispc")
    log(deco.white("END ispc-env_init"))
