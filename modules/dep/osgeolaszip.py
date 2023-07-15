###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class osgeolaszip(dep.StdProvider):
  name = "osgeolaszip"
  def __init__(self):
    super().__init__(osgeolaszip.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=osgeolaszip.name,
                             repospec="LASzip/LASzip",
                             revision="v2.2.0", # 2.2.0 is last version liblas is compatibile with!
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"liblaszip.so").exists()
