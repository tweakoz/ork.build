###############################################################################
# Orkid Build System
# Copyright 2010-2023, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, host, env
from obt.command import Command
###############################################################################
SRC_VERSION = "v2021.8.0"
NAME = "tbb"
class _tbb_from_source(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME)

    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }

    #self._builder = self.createBuilder(dep.CustomBuilder)
    #build_dir = path.subspace_build_dir/"tbb"
    #env = {
     # "PREFIX": path.stage()
    #}

    #make_clean_command = Command([
    #  "make",
    #  "-j",host.NumCores
    #  ],
    #  working_dir=build_dir,
    #  environment=env)

    #make_incr_command = Command([
    #  "make",
    #  "-j",host.NumCores],
    #  working_dir=build_dir,
    #  environment=env)

    #self._builder._cleanbuildcommands += [make_clean_command]
    #self._builder._incrbuildcommands += [make_incr_command]
    #self._tbb_dir = build_dir

  def env_init(self):
    log.marker("registering TBB(%s) SDK"%SRC_VERSION)
    #env.set("TBB_ROOT",self._tbb_dir)
    #env.set("TBB_INCLUDE",self._tbb_dir/"include")
    #env.set("TBB_LIBRARY_RELEASE" = $TBB_INSTALL_DIR/build/RELEASE_FOLDER
    #env.set("TBB_LIBRARY_DEBUG" = $TBB_INSTALL_DIR/build/DEBUG_FOLDER

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=NAME,
                             repospec="oneapi-src/oneTBB",
                             revision=SRC_VERSION,
                             recursive=False)
###############################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("openvdb").exists()
###############################################################################
class _tbb_from_homebrew(dep.HomebrewProvider):
  def __init__(self):
    super().__init__("tbb","tbb")
  def env_init(self):
    log.marker("registering TBB(homebrew) SDK")
###############################################################################
source = dep.switch(linux=_tbb_from_source,macos=_tbb_from_homebrew)
###############################################################################
class tbb(source):
  def __init__(self):
    super().__init__()
  def env_init(self):
    super().env_init()
###############################################################################

