###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host

###############################################################################

class oiio(dep.StdProvider):

  def __init__(self,miscoptions=None): ############################################
    name = "oiio"
    parclass = super(oiio,self)
    parclass.__init__(name=name,miscoptions=miscoptions)

    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/OpenImageIO/oiio"
    self._fetcher._revision = "spi-spcomp2-release-49.4"

    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["pkgconfig","openexr","pybind11"])
    self._builder.setCmVars({
      "CMAKE_CXX_FLAGS": "-Wno-error=deprecated",
      "USE_NUKE": "OFF",
      "USE_PYTHON": "ON",
      "OIIO_BUILD_TOOLS": "ON",
      "OIIO_BUILD_TESTS": "ON"
    })
    if host.IsLinux:
      self._builder.requires(["qt5"])
      self._builder.setCmVar("CMAKE_CXX_COMPILER","g++-9")
      self._builder.setCmVar("CMAKE_C_COMPILER","gcc-9")
