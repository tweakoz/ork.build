###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path

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
    self._builder.requires(["llvm","clang"])
