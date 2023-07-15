###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path
from obt.command import Command
from obt import log
from obt.deco import Deco
deco = Deco()

class _llvm_from_source(dep.StdProvider):
  name = "llvm"
  def __init__(self,name):
    super().__init__(_llvm_from_source.name)
    self._archlist = ["x86_64"]
    self._builder = self.createBuilder(dep.CMakeBuilder)
    ##########################################
    # llvm cmake file is 1 subdir deeper than usual
    ##########################################
    self.build_src = self.source_root/"llvm"
    self.build_dest = self.source_root/".build"
    ##########################################
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
        "LLVM_INSTALL_UTILS": "ON",
        "LLVM_ENABLE_DUMP": "ON",
        "LLVM_ENABLE_PROJECTS": "clang;libcxx;libcxxabi"
    })

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=_llvm_from_source.name,
                                repospec="llvm/llvm-project",
                                revision="llvmorg-12.0.1",
                                recursive=False)
    return fetcher
  ########################################################################

  def install_dir(self):
    return path.stage()

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"bin"/"llvm-cov").exists()

###############################################################################

class _llvm_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
  def install_dir(self):
    return path.Path("/usr/local/opt/llvm")

###############################################################################

BASE = _llvm_from_source
if host.IsOsx:
  BASE = _llvm_from_homebrew

###############################################################################

class llvm(BASE):
  def __init__(self):
    super().__init__("llvm")
  def env_init(self):
    log.marker("registering LLVM SDK")
