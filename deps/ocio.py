###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path

###############################################################################

class ocio(dep.StdProvider):
  def __init__(self): ############################################
    name = "ocio"
    super().__init__(name)
    self.declareDep("cmake")
    self.declareDep("pkgconfig")
    self.declareDep("oiio")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="AcademySoftwareFoundation/OpenColorIO",
                                      revision="v2.0.1",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "CMAKE_CXX_FLAGS": "-Wno-error=deprecated",
      "USE_NUKE": "OFF",
      "USE_PYTHON": "OFF",
      "OIIO_BUILD_TOOLS": "ON",
      "OIIO_BUILD_TESTS": "ON"
    })
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"ocioconvert").exists()
