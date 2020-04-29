###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log
###############################################################################
class _embree_from_source(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self.VERSION = "v3.9.0"
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="embree/embree",
                                      revision=self.VERSION,
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
    self._builder.setCmVar("EMBREE_TUTORIALS","FALSE") # because they dont compile with ispc==1.13.0
###############################################################################
class _embree_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
    self.VERSION = "homebrew"
###############################################################################
class embree(dep.switch(linux=_embree_from_source, \
                        macos=_embree_from_homebrew)):
  def __init__(self):
    super().__init__("embree")
    self.requires(["ispc"])
  def env_init(self):
    log.marker("registering embree SDK(%s)"%self.VERSION)
