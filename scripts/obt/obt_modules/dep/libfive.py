###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class libfive(dep.StdProvider):
  name = "libfive"
  def __init__(self):
    super().__init__(libfive.name)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.build_dest = self.build_dest
    ###########################################
    self._builder.requires(["eigen"])
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON",
    }
    ############################################
    # because, cuda 10 requires it - todo - make dynamic
    ############################################
    if host.IsLinux:
        self._builder.setCmVars({
          "CMAKE_CXX_COMPILER": "g++-8",
          "CMAKE_C_COMPILER": "gcc-8" })
    elif host.IsOsx:
        self._builder.setCmVars({
          "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib/",
          "CMAKE_BUILD_WITH_INSTALL_RPATH": "ON"})
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=libfive.name,
                             repospec="tweakoz/libfive",
                             revision="master",
                             recursive=False)

  ########################################################################
