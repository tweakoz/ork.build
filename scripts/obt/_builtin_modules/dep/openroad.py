###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, env, path, host
###############################################################################
class openroad(dep.StdProvider):
  name = "openroad"
  def __init__(self):
    super().__init__(openroad.name)
    self.declareDep("cmake")
    self._archlist = ["x86_64"]

    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires(["eigen","lemongraph"])
    if host.IsOsx:
      self._builder.setCmVar("TCL_LIBRARY",path.osx_brewopt()/"tcl-tk"/"lib"/"libtcl8.6.dylib")
  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(openroad.name)
    fetcher._git_url = "https://github.com/tweakoz/OpenROAD"
    fetcher._cache=False
    fetcher._recursive=True
    fetcher._revision = "toztest"
    return fetcher
  ########################################################################
