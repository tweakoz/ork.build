###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path
###############################################################################
class opuscodec(dep.StdProvider):
  name = "opuscodec"
  def __init__(self):
    super().__init__(opuscodec.name)
    self.declareDep("cmake")
    self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "CMAKE_CXX_STANDARD": "17",
      "OPUS_BUILD_SHARED_LIBRARY": "ON"
    }

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=opuscodec.name,
                             repospec="xiph/opus",
                             revision="v1.4",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"oslc").exists()
###############################################################################
