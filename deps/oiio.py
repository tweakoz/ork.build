###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path

###############################################################################

class oiio(dep.StdProvider):
  def __init__(self): ############################################
    name = "oiio"
    super().__init__(name)
    self.declareDep("cmake")
    self.declareDep("pkgconfig")
    self.declareDep("jpegturbo")
    self.declareDep("openexr")
    self.declareDep("pybind11")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="OpenImageIO/oiio",
                                      revision="release",
                                      recursive=False)
    self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "CMAKE_CXX_FLAGS": "-Wno-error=deprecated",
      "USE_NUKE": "OFF",
      "USE_PYTHON": "OFF",
      #"OIIO_PYTHON_VERSION": "3.8.1",
      #"pybind11_ROOT": path.stage(),
      "OIIO_BUILD_TOOLS": "ON",
      "OIIO_BUILD_TESTS": "ON",
      "JPEG_INCLUDE_DIR": path.includes(),
      "OpenCV_INCLUDE_DIR": "/dev/null"
    })
    #if host.IsLinux:
    #  self._builder.setCmVar("CMAKE_CXX_COMPILER","g++")
    #  self._builder.setCmVar("CMAKE_C_COMPILER","gcc")
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libIlmImf.so").exists()
