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

    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/embree/embree"
    self._fetcher._revision = self.VERSION

    self._builder = dep.CMakeBuilder(name)
  def env_init(self):
    log.marker("registering embree(%s) SDK"%self.VERSION)

###############################################################################

class _embree_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
  def env_init(self):
    log.marker("registering embree SDK")

###############################################################################

BASE = dep.switch(linux=_embree_from_source,
                  macos=_embree_from_homebrew)

class embree(BASE):
  def __init__(self):
    super().__init__("embree")
    self.requires(["ispc"])
