###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path, env, log
from obt.path import Path
from obt.command import Command
from obt.deco import Deco
from yarl import URL
deco = Deco()

###############################################################################

class _ispc_from_source(dep.StdProvider):
  name = "ispc"
  def __init__(self):
    super().__init__(_ispc_from_source.name)
    self._archlist = ["x86_64"]
    self.llvm = dep.instance("llvm")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires([self.llvm])
    if host.IsOsx:
      self._builder.setCmVar("BISON_EXECUTABLE",path.osx_brewopt()/"bison"/"bin"/"bison")
  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(_ispc_from_source.name)
    fetcher._git_url = "https://github.com/ispc/ispc"
    fetcher._cache=False,
    fetcher._recursive=False
    fetcher._revision = "v1.13.0"
    return fetcher

###############################################################################

class _ispc_from_homebrew(dep.HomebrewProvider):
  name = "ispc"
  def __init__(self):
    super().__init__(_ispc_from_homebrew.name,_ispc_from_homebrew.name)
    self._archlist = ["x86_64"]
  def env_init(self):
    binary = self.brew_prefix()/"bin"/"ispc"
    version = ""
    log.marker("registering ispc SDK (%s)"%version)
    env.set("ISPC",binary)

###############################################################################

class _ispc_from_wget(dep.StdProvider):
  name = "ispc"
  def __init__(self):
    super().__init__(_ispc_from_wget.name)
    self._archlist = ["x86_64"]
    self._version = "v1.13.0"
    basename = "ispc-%s-linux"%self._version
    self.filename = "%s.tar.gz" % basename
    self._builder = dep.BinInstaller(_ispc_from_wget.name)
    self.src_dir = path.builds()/"ispc"/basename
    dst_dir = path.stage()
    self._builder.install_item(source=self.src_dir/"bin"/"ispc", \
                               destination=dst_dir/"bin"/"ispc")
  ########################################################################
  @property
  def _fetcher(self):
    baseurl = URL("https://github.com/ispc/ispc/releases/download")
    fetcher = dep.WgetFetcher(_ispc_from_wget.name)
    fetcher._url = baseurl/self._version/self.filename
    fetcher._fname = self.filename
    fetcher._arctype = "tgz"
    fetcher._md5 = "98fe4a03ef0f39f5ebbae77a03c48e71"
    return fetcher

  ########################################################################
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
    super().__init__()
