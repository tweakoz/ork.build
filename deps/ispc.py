###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path
from ork.path import Path
from ork.command import Command

###############################################################################

class ispc(dep.StdProvider):
  def __init__(self,miscoptions=None):
    name = "ispc"
    parclass = super(ispc,self)
    parclass.__init__(name=name,miscoptions=miscoptions)
    self.llvm = dep.require("llvm")
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/ispc/ispc"
    self._fetcher._cache=False,
    self._fetcher._recursive=False
    self._fetcher._revision = "v1.12.0"
    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["llvm"])
    if host.IsOsx:
      self._builder.setCmVar("BISON_EXECUTABLE",path.osx_brewcellar()/"bison"/"3.5.2"/"bin"/"bison")
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
