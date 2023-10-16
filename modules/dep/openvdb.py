###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class openvdb(dep.StdProvider):
  name = "openvdb"
  def __init__(self):
    super().__init__(openvdb.name)
    self.declareDep("cmake")
    self.declareDep("blosc")
    self.declareDep("boost")
    self.declareDep("tbb")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=openvdb.name,
                                repospec="AcademySoftwareFoundation/openvdb",
                                revision="v10.0.0",
                                recursive=False)
    return fetcher
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("openvdb").exists()
