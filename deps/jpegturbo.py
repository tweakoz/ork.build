###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path
###############################################################################
class jpegturbo(dep.StdProvider):
  def __init__(self):
    name = "jpegturbo"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="libjpeg-turbo/libjpeg-turbo",
                                      revision="2.1.2",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libopenjp2.a").exists()

###############################################################################
