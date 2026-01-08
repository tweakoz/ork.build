###############################################################################
# Orkid Build System
# Copyright 2010-2023, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, host, env, osrelease
from obt.command import Command
###############################################################################
NAME = "tbb"
VERSION = "v2022.0.0"
###############################################################################
class tbb(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME)

    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON",
      "TBB_TEST": "OFF",
      "TBB_STRICT": "OFF",
      "TBB_EXAMPLES": "OFF",
    }

    # On certain Ubuntu versions, use gcc-11
    if host.IsLinux:
      desc = osrelease.descriptor()
      use_gcc_11 = desc.version_id in ["23.10", "24.04"]
      if use_gcc_11:
        self._builder._cmakeenv["CMAKE_CXX_COMPILER"] = "g++-11"
        self._builder._cmakeenv["CMAKE_C_COMPILER"] = "gcc-11"

  def env_init(self):
    log.marker("registering TBB(%s) SDK" % VERSION)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=NAME,
                             repospec="uxlfoundation/oneTBB",
                             revision=VERSION,
                             recursive=False)

  ###############################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("tbb").exists()
###############################################################################

