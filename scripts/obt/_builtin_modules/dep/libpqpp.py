###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class libpqpp(dep.StdProvider):
  name = "libpqpp"
  def __init__(self):
    super().__init__(libpqpp.name)
    #self._deps = ["pkgconfig"]
    src_root = self.source_root
    #################################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #################################################
    self.declareDep("pkgconfig")
    self.declareDep("cmake")
    self.declareDep("postgresql")

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=libpqpp.name,
                             repospec="jtv/libpqxx",
                             revision="7.4.1",
                             recursive="7.4.1")

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libpqxx.so").exists()