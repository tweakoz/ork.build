###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path, host
from ork.command import Command
###############################################################################
class nextpnr(dep.StdProvider):
  def __init__(self):
    name = "nextpnr"
    super().__init__(name)
    self.declareDep("icestorm")
    self.VERSION = "67bd349e8f38d91a15f54340b29cc77ef156727f"
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="YosysHQ/nextpnr",
                                      revision=self.VERSION,
                                      recursive=False)
    ###########################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("ARCH","ice40")
