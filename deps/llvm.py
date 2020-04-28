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
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="llvm/llvm-project",
                                      revision="llvmorg-9.0.1",
                                      recursive=False)
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
  def install_dir(self):
    return path.stage()

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
