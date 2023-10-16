###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path, command

###############################################################################

class oiio(dep.StdProvider):
  name = "oiio"
  def __init__(self): ############################################
    super().__init__(oiio.name)
    self.declareDep("cmake")
    self.declareDep("pkgconfig")
    self.declareDep("jpegturbo")
    self.declareDep("openexr")
    self.declareDep("giflib")
    self.declareDep("ffmpeg")
    BOOST = self.declareDep("boost")
    self.createBuilder(dep.CMakeBuilder)

    CMAKE_VARS = {
      "CMAKE_CXX_FLAGS": "-Wno-error=deprecated -Wno-error=ignored-attributes",
      "USE_NUKE": "OFF",
      "USE_PYTHON": "OFF",
      #"OIIO_PYTHON_VERSION": "3.8.1",
      #"pybind11_ROOT": path.stage(),
      "OIIO_BUILD_TOOLS": "ON",
      "OIIO_BUILD_TESTS": "ON",
      "JPEG_INCLUDE_DIR": path.includes(),
      "OpenCV_INCLUDE_DIR": "/dev/null", 
      "GIF_INCLUDE_DIR": path.includes(),
    }
    #if host.IsLinux:
    #  self._builder.setCmVar("CMAKE_CXX_COMPILER","g++")
    #  self._builder.setCmVar("CMAKE_C_COMPILER","gcc")



    CMAKE_VARS.update(BOOST.cmake_additional_flags())

    self._builder.setCmVars(CMAKE_VARS)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=oiio.name,
                             repospec="OpenImageIO/oiio",
                             revision="v2.5.4.0",
                             recursive=False)

  #######################################################################
  def on_build_shell(self):
    env = {
      "CMAKE_ENVFLAGS" : self._builder.cmakeEnvAsString
    }
    print("use cmake $(echo $CMAKE_ENVFLAGS) -B . -S ..")
    return command.subshell( directory=self.build_dest,
                             prompt = "OIIO",
                             environment = env )
  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  #######################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libIlmImf.so").exists()
