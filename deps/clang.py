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
  def __init__(self):
    name = "clang"
    super().__init__(name=name)
    self.llvm = dep.instance("llvm")
    if hasattr(self.llvm,"_fetcher"):
      self._fetcher = dep.NopFetcher(name)
      self._fetcher._revision = self.llvm._fetcher._revision
      self._builder = dep.CMakeBuilder(name)
      self._builder.requires([self.llvm])
      ##########################################
      # llvm cmake file is 1 subdir deeper than usual
      ##########################################
      self.source_root = path.builds()/"llvm"
      self.build_src = self.source_root/"clang"
      self.build_dest = self.source_root/".build"
