###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path
from obt.command import Command

###############################################################################

class clang(dep.StdProvider):
  def __init__(self):
    name = "clang"
    super().__init__(name=name)
    #self._archlist = ["x86_64"]
    self.llvm = dep.instance("llvm")
    self.hostdesc = host.description()
    if hasattr(self.llvm,"_fetcher"):
      self._builder = self.createBuilder(dep.CMakeBuilder)
      self._builder.requires([self.llvm])
      ##########################################
      # llvm cmake file is 1 subdir deeper than usual
      ##########################################
      self.source_root = path.builds()/"llvm"
      self.build_src = self.source_root/"clang"
      self.build_dest = self.source_root/".build"
  ##########################################
  def __str__(self):
    return "Clang(From LLVM)"
  ##########################################
  @property
  def _fetcher(self):
    fetcher = dep.NopFetcher(clang.name)
    fetcher._revision = self.llvm._fetcher._revision
    return fetcher
  ##########################################
  @property
  def linux_bindir(self):
    if host.IsLinux:
      if host.IsGentoo:
        return path.Path("/usr/lib/llvm/11/bin")
      elif host.IsDebian:
        return path.Path("/usr/bin")
    return path.Path("")
  ##########################################
  @property
  def bin_clangpp(self):
   ub_release = {
      "bionic": "clang++-10",
      "buster": "clang++-13",
      "focal": "clang++-10",
      "jammy": "clang++-12",
      "mantic": "clang++-17",
   }
   if host.IsLinux:
      return self.linux_bindir/ub_release[self.hostdesc.codename]
   return path.Path("clang++")
  ##########################################
  @property
  def bin_clang(self):
   ub_release = {
      "bionic": "clang-10",
      "buster": "clang-11",
      "focal": "clang-10",
      "jammy": "clang-12",
      "mantic": "clang-17",
   }   
   if host.IsLinux:
     return self.linux_bindir/ub_release[self.hostdesc.codename]
   return path.Path("clang")
  ##########################################
