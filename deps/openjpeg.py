###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path
###############################################################################
class openjpeg(dep.StdProvider):
  def __init__(self):
    name = "openjpeg"
    super().__init__(name)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="uclouvain/openjpeg",
                                      revision="v2.4.0",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libopenjp2.a").exists()

###############################################################################
