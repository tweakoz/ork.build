###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, host

###############################################################################

class cmake(dep.StdProvider):
  name = "cmake"
  def __init__(self):
    super().__init__(cmake.name)
    self.declareDep("pkgconfig")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv["CMAKE_USE_SYSTEM_CURL"]="YES"
    self._builder.requires(["pkgconfig"])
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=cmake.name,
                             repospec="kitware/cmake",
                             revision="v3.28.3",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"cmake").exists()
