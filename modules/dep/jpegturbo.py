###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path
###############################################################################
class jpegturbo(dep.StdProvider):
  name = "jpegturbo"
  def __init__(self):
    super().__init__(jpegturbo.name)
    self._builder = self.createBuilder(dep.CMakeBuilder)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=jpegturbo.name,
                             repospec="libjpeg-turbo/libjpeg-turbo",
                             revision="2.1.2",
                             recursive=False)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libopenjp2.a").exists()

###############################################################################
