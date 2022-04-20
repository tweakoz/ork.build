###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path, env, log
from ork.path import Path
from ork.command import Command
from ork.deco import Deco
from yarl import URL
deco = Deco()

###############################################################################

class _ispc_from_source(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self._archlist = ["x86_64"]
    self.llvm = dep.instance("llvm")
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/ispc/ispc"
    self._fetcher._cache=False,
    self._fetcher._recursive=False
    self._fetcher._revision = "v1.13.0"
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires([self.llvm])
    if host.IsOsx:
      self._builder.setCmVar("BISON_EXECUTABLE",path.osx_brewopt()/"bison"/"bin"/"bison")

###############################################################################

class _ispc_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
    self._archlist = ["x86_64"]
  def env_init(self):
    binary = self.brew_prefix()/"bin"/"ispc"
    version = ""
    log.marker("registering ispc SDK (%s)"%version)
    env.set("ISPC",binary)

###############################################################################

class _ispc_from_wget(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self._archlist = ["x86_64"]
    self._version = "v1.13.0"
    self._fetcher = dep.WgetFetcher(name)
    baseurl = URL("https://github.com/ispc/ispc/releases/download")
    basename = "ispc-%s-linux"%self._version
    filename = "%s.tar.gz" % basename
    self._fetcher._url = baseurl/self._version/filename
    self._fetcher._fname = filename
    self._fetcher._arctype = "tgz"
    self._fetcher._md5 = "98fe4a03ef0f39f5ebbae77a03c48e71"
    self._builder = dep.BinInstaller(name)
    self.src_dir = path.builds()/"ispc"/basename
    dst_dir = path.stage()
    self._builder.install_item(source=self.src_dir/"bin"/"ispc", \
                               destination=dst_dir/"bin"/"ispc")
  def env_init(self):
    log.marker("registering ispc(%s) SDK"%self._version)
    env.set("ISPC",path.stage()/"bin"/"ispc")

  def install(self):
    return self._builder.install(None)

  def areRequiredSourceFilesPresent(self):
    return (self.src_dir/"LICENSE.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"ispc").exists()

###############################################################################

BASE = dep.switch(linux=_ispc_from_wget,
                  macos=_ispc_from_homebrew)

class ispc(BASE):
  def __init__(self):
    super().__init__("ispc")
