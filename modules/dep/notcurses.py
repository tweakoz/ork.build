###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path
###############################################################################
class notcurses(dep.StdProvider):
  VERSION ="master"
  NAME = "notcurses"
  def __init__(self):
    super().__init__(notcurses.NAME)
    self.declareDep("cmake")    
    self._builder = dep.CMakeBuilder(notcurses.NAME)
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

