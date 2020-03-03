###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path
from ork.command import Command

###############################################################################

class clang(dep.StdProvider):
  def __init__(self,miscoptions=None):
    name = "clang"
    parclass = super(clang,self)
    parclass.__init__(name=name,miscoptions=miscoptions)
    self.llvm = dep.require("llvm")
    self._fetcher = dep.NopFetcher(name)
    self._fetcher._revision = self.llvm._fetcher._revision
    self._builder = dep.CMakeBuilder(name)
    ##########################################
    # llvm cmake file is 1 subdir deeper than usual
    ##########################################
    self.source_root = path.builds()/"llvm"
    self.build_src = self.source_root/"clang"
    self.build_dest = self.source_root/".build"
    if host.IsOsx:
      sysroot_cmd = Command(["xcrun","--show-sdk-path"])
      sysroot = sysroot_cmd.capture().replace("\n","")
      print(sysroot)
      self._builder.setCmVars({
        "CMAKE_OSX_ARCHITECTURES:STRING":"x86_64",
        "CMAKE_OSX_DEPLOYMENT_TARGET:STRING":"10.14",
        "CMAKE_OSX_SYSROOT:STRING":sysroot,
        "CMAKE_SKIP_INSTALL_RPATH:BOOL":"NO",
        "CMAKE_SKIP_RPATH:BOOL":"NO",
        "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib"
      })
