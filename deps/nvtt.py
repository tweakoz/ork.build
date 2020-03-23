###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host

###############################################################################

class nvtt(dep.StdProvider):

  def __init__(self,miscoptions):
    name = "nvtt"
    parclass = super(nvtt,self)
    parclass.__init__(name=name,miscoptions=miscoptions)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/castano/nvidia-texture-tools"
    self._fetcher._revision = "b45560cfc4684fec8a79d812a20780e5d79df9b3"
    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["openexr"])
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }
    ############################################
    # because, cuda 10 requires it - todo - make dynamic
    ############################################
    if host.IsLinux:
        self._builder.setCmVars({
          "CMAKE_CXX_COMPILER": "g++-8",
          "CMAKE_C_COMPILER": "gcc-8" })
