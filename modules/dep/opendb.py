###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, env, path, host
###############################################################################
class opendb(dep.StdProvider):
  name = "opendb"
  def __init__(self):
    super().__init__(opendb.name)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    if host.IsOsx:
      self._builder.setCmVar("TCL_LIBRARY",path.osx_brewopt()/"tcl-tk"/"lib"/"libtcl8.6.dylib")
      self._builder.setCmVar("TK_LIBRARY",path.osx_brewopt()/"tcl-tk"/"lib"/"libk8.6.dylib")
    #self._builder.requires(["eigen","lemongraph"])
  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(opendb.name)
    fetcher._git_url = "https://github.com/tweakoz/OpenDB"
    fetcher._cache=False
    fetcher._recursive=True
    fetcher._revision = "develop"
    return fetcher
