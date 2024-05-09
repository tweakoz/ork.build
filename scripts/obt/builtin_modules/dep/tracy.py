###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class tracy(dep.StdProvider):
  name = "tracy"
  def __init__(self):
    super().__init__(tracy.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #self._builder.setCmVar("CMAKE_INSTALL_INCLUDEDIR",path.includes()/"tracy")
    #self._builder.requires(["eigen"])

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=tracy.name,
                             repospec="wolfpld/tracy",
                             revision="v0.9.1",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"readme.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libtracy.so").exists()
  
