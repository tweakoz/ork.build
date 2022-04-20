###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path, template
###############################################################################
class opensubdiv(dep.StdProvider):
  def __init__(self):
    name = "opensubdiv"
    super().__init__(name)
    #self.declareDep("llvm")
    self.declareDep("cmake")
    cuda = self.declareDep("cuda")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="PixarAnimationStudios/OpenSubdiv",
                                      revision="release",
                                      recursive=True)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "CMAKE_CXX_COMPILER": cuda.cxx_compiler,
      "CMAKE_C_COMPILER": cuda.c_compiler,
      "CMAKE_CXX_STANDARD": "17",
      "PXR_ENABLE_PYTHON_SUPPORT": "OFF",
      "BOOST_ROOT": path.stage(),
      "Boost_NO_SYSTEM_PATHS": "ON",
      "OSD_CUDA_NVCC_FLAGS": "--gpu-architecture compute_30"
      #"Boost_DEBUG":"ON"
    }

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libosdGPU.so").exists()
###############################################################################


