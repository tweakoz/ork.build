###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, command, path

###############################################################################

class libpqpp(dep.StdProvider):
  def __init__(self):
    name = "libpqpp"
    super().__init__(name)
    #self._deps = ["pkgconfig"]

    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="jtv/libpqxx",
                                      revision="7.4.1",
                                      recursive=False)

    src_root = self.source_root
    #################################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #################################################
    self.declareDep("pkgconfig")
    self.declareDep("cmake")
    self.declareDep("postgresql")

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libpqxx.so").exists()