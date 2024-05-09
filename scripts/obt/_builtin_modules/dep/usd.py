###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, template
###############################################################################
class usd(dep.StdProvider):
  name = "usd"
  def __init__(self):
    super().__init__(usd.name)
    python = self.declareDep("python")
    self.declareDep("boost")
    self.declareDep("llvm")
    self.declareDep("opensubdiv")
    self.declareDep("oiio")
    self.declareDep("osl")
    self.declareDep("ptex")
    self.declareDep("pyside2")
    self.declareDep("pyopengl")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "CMAKE_CXX_STANDARD": "17",
      "PXR_ENABLE_PYTHON_SUPPORT": "ON",
      "PXR_USE_PYTHON_3": "ON",
      "PXR_ENABLE_GL_SUPPORT": "ON",
      #"PXR_ENABLE_VULKAN_SUPPORT": "ON",
      "PXR_ENABLE_OSL_SUPPORT": "ON",
      "BOOST_ROOT": path.stage(),
      "Boost_NO_SYSTEM_PATHS": "ON",
      "CMAKE_LIBRARY_PATH": python.library_dir,
      "CMAKE_SHARED_LINKER_FLAGS": "-L"+str(python.library_dir),
      "CMAKE_MODULE_LINKER_FLAGS": "-L"+str(python.library_dir),
      "CMAKE_EXE_LINKER_FLAGS": "-L"+str(python.library_dir),
      "PYTHON_INCLUDE_DIR": python.include_dir,
      "PYTHON_LIBRARY": python.library_dir/python.library_file,
      "PYTHON_LIBRARY_DEBUG": python.library_dir/python.library_file,
      #"Boost_DEBUG":"ON"
    }

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=usd.name,
                             repospec="PixarAnimationStudios/USD",
                             revision="release",
                             recursive=True)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libusd_arch.so").exists()
###############################################################################


