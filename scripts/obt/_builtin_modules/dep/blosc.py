###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class blosc(dep.StdProvider):
  name = "blosc"
  def __init__(self):
    super().__init__(blosc.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=blosc.name,
                             repospec="Blosc/c-blosc",
                             revision="v1.21.1",
                             recursive=False)
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("blosc").exists()
