###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
import os
from obt import dep, command, pathtools, path, host
###############################################################################
class _notcurses_from_source(dep.StdProvider):
  VERSION ="toz-2025-jul08"
  NAME = "notcurses"
  def __init__(self):
    super().__init__(notcurses.NAME)
    self.declareDep("cmake")    
    pre_pkg_config = os.environ.get("PKG_CONFIG_PATH", "")
    os_env = {}
    self._builder = dep.CMakeBuilder(notcurses.NAME,os_env=os_env)
    self._builder.setCmVars({
      "CMAKE_BUILD_TYPE": "RELEASE",
    })
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=notcurses.NAME,
                             repospec="tweakoz/notcurses",
                             revision=notcurses.VERSION,
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"notcurses"/"version.h").exists()

###############################################################################
class _notcurses_from_homebrew(dep.HomebrewProvider):
  def __init__(self):
    super().__init__("notcurses","notcurses")
###############################################################################
source = dep.switch(linux=_notcurses_from_source,macos=_notcurses_from_homebrew)
###############################################################################
class notcurses(source):
  def __init__(self):
    super().__init__()
