###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path
###############################################################################
class openvr(dep.StdProvider):
  def __init__(self):
    name = "openvr"
    super().__init__(name)
    self._archlist = ["x86_64"]
    self._oslist = ["Linux"]
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="ValveSoftware/openvr",
                                      revision="v1.11.11",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libopenvr_api.a").exists()
