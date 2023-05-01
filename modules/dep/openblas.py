###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, command, pathtools, path, subspace
###############################################################################
class openblas(dep.StdProvider):
  VERSION ="v0.3.23"
  NAME = "openblas"
  def __init__(self):
    super().__init__(openblas.NAME)
    self.declareDep("cmake")    
    self.setAllowedSubspaces(["host","ios"])
    self._builder = dep.CMakeBuilder(openblas.NAME)

    if subspace.current()=="ios":
      self._builder.setCmVars({
        "BUILD_TESTING": "OFF",
      })
      # TODO: 
      # Linking C executable xzcblat3.app/xzcblat3
      #       # "_cblas_ztrsv", referenced from:
      #        _cztrsv_ in c_zblas2.c.o
      #        _cz2chke_ in c_z2chke.c.o
    else:
      self._builder.setCmVars({
       "BUILD_EXAMPLES": "ON"
      })

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openblas.NAME,
                             repospec="tweakoz/OpenBLAS",
                             revision=openblas.VERSION,
                             recursive=True)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"openblas"/"lapacke.h").exists()

