###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path
###############################################################################
class openjpeg(dep.StdProvider):
  name = "openjpeg"
  def __init__(self):
    super().__init__(openjpeg.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openjpeg.name,
                             repospec="uclouvain/openjpeg",
                             revision="v2.4.0",
                             recursive=False)
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libopenjp2.a").exists()

###############################################################################
