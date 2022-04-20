###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path
###############################################################################
class eigen(dep.StdProvider):
  def __init__(self):
    name = "eigen"
    super().__init__(name)
    self.declareDep("cmake")
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "git@github.com:tweakoz/eigen.git"
    self._fetcher._cache=False,
    self._fetcher._recursive=False
    self._fetcher._revision = "3.4.0"
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #self._builder.requires(["lapack"])

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"share"/"pkgconfig"/"eigen3.pc").exists()

  def compileenv(self): ##########################################################
    return {
        "INCLUDE_PATH": path.includes()/"eigen3"
    }
