###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, env, path, host
###############################################################################
class openroad(dep.StdProvider):
  def __init__(self):
    name = "openroad"
    super().__init__(name)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/tweakoz/OpenROAD"
    self._fetcher._cache=False
    self._fetcher._recursive=True
    self._fetcher._revision = "toztest"

    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["eigen","lemongraph"])
    if host.IsOsx:
      self._builder.setCmVar("TCL_LIBRARY",path.osx_brewopt()/"tcl-tk"/"lib"/"libtcl8.6.dylib")
