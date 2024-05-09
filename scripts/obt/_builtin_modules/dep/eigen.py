###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, host
###############################################################################
class eigen(dep.StdProvider):
  name = "eigen"
  def __init__(self):
    super().__init__(eigen.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)

    #self._builder.requires(["lapack"])

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(eigen.name)
    fetcher._git_url = "git@github.com:tweakoz/eigen.git"
    fetcher._cache=False,
    fetcher._recursive=False
    fetcher._revision = "3.4.0"
    return fetcher
  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"share"/"pkgconfig"/"eigen3.pc").exists()

  def compileenv(self): ##########################################################
    return {
        "INCLUDE_PATH": path.includes()/"eigen3"
    }
