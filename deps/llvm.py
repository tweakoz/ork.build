###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path
from ork.command import Command
from ork import log
from ork.deco import Deco
deco = Deco()

class _llvm_from_source(dep.StdProvider):

  def __init__(self,name):
    super().__init__(name)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/llvm/llvm-project"
    self._fetcher._revision = "llvmorg-9.0.1"
    self._builder = dep.CMakeBuilder(name)
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


###############################################################################

class _llvm_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)

###############################################################################

BASE = _llvm_from_source
if host.IsOsx:
  BASE = _llvm_from_homebrew

###############################################################################

class llvm(BASE):
  def __init__(self):
    super().__init__("llvm")
  def env_init(self):
    log.marker("BEGIN llvm-env_init")
    log.marker("END llvm-env_init")
