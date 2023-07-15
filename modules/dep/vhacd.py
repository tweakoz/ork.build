###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class vhacd(dep.StdProvider):
  name = "vhacd"
  def __init__(self):
    super().__init__(vhacd.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self.build_src = self.build_src/"app"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=vhacd.name,
                             repospec="kmammou/v-hacd",
                             revision="v4.1.0",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"app"/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libBulletDynamics.so").exists()


