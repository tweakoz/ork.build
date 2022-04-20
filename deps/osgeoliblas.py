
###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, path

###############################################################################

class osgeoliblas(dep.StdProvider):
  def __init__(self):
    name = "osgeoliblas"
    super().__init__(name)
    self.declareDep("cmake")
    self.declareDep("osgeolaszip")
    self.declareDep("osgeoproj")
    self.declareDep("osgeotiff")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="libLAS/libLAS",
                                      revision="e6a1aaed412d638687b8aec44f7b12df7ca2bbbb",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "WITH_LASZIP" : "TRUE",
      "OSGEO4W_ROOT_DIR": path.stage()
    })
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"liblas_c.so").exists()
