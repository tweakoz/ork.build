###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path

class llvm(dep.StdProvider):

  def __init__(self,miscoptions):
    name = "llvm"
    parclass = super(llvm,self)
    parclass.__init__(name=name,miscoptions=miscoptions)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/llvm/llvm-project"
    self._fetcher._revision = "llvmorg-8.0.1"
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
        "LLVM_ENABLE_DUMP": "ON"
    })
    if host.IsOsx:
      self._builder.setCmVars({
        "CMAKE_OSX_ARCHITECTURES:STRING":"x86_64",
        "CMAKE_OSX_DEPLOYMENT_TARGET:STRING":"10.14",
        "CMAKE_OSX_SYSROOT:STRING":"$(xcrun --show-sdk-path)",
        "CMAKE_SKIP_INSTALL_RPATH:BOOL":"NO",
        "CMAKE_SKIP_RPATH:BOOL":"NO",
      })
