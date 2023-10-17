###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class bullet(dep.StdProvider):
  name = "bullet"
  def __init__(self):
    super().__init__(bullet.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def github_repo(self):
    return "bulletphysics/bullet3"
  ########################################################################
  @property
  def revision(self):
    return "3.25"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=bullet.name,
                             repospec=self.github_repo,
                             revision=self.revision,
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libBulletDynamics.so").exists()
