###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log
###############################################################################
class _cgal_from_source(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="CGAL/cgal",
                                      revision="releases/CGAL-5.0.2",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires(["lapack"])
###############################################################################
class _cgal_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
###############################################################################
class cgal(dep.switch(linux=_cgal_from_source,macos=_cgal_from_homebrew)):
  def __init__(self):
    super().__init__("cgal")
  def env_init(self):
    log.marker("registering cgal SDK")
###############################################################################
