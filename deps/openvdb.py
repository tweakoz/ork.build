###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path
###############################################################################
class openvdb(dep.StdProvider):
  def __init__(self):
    name = "openvdb"
    super().__init__(name)
    self.declareDep("cmake")
    self.declareDep("blosc")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="AcademySoftwareFoundation/openvdb",
                                      revision="v9.0.0",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("openvdb").exists()
