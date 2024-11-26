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
    self._archlist = ["x86_64","aarch64"]
    ##########################################
    # llvm cmake file is 1 subdir deeper than usual
    ##########################################
    self.build_src = self.source_root/"llvm"
    self.build_dest = self.source_root/".build"
    ##########################################
    self._builder = self.createBuilder(
      dep.CMakeBuilder,
      src_dir_override=self.build_src)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
        "LLVM_INSTALL_UTILS": "ON",
        "LLVM_ENABLE_DUMP": "ON",
        #"LLVM_ENABLE_PROJECTS": "clang;libcxx;libcxxabi"
    })
    # arm64-apple-darwin24.1.0
    if host.IsAARCH64:
      self._builder.setCmVar("LLVM_TARGETS_TO_BUILD","AArch64")
    else:
      self._builder.setCmVar("LLVM_TARGETS_TO_BUILD","X86")

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=_llvm_from_source.name,
                                repospec="llvm/llvm-project",
                                revision="llvmorg-15.0.7",
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

###############################################################################

class llvm(BASE):
  def __init__(self):
    super().__init__("llvm")
  def env_init(self):
    log.marker("registering LLVM SDK")
