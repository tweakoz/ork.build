###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, host
from obt.command import Command
###############################################################################
class nextpnr(dep.StdProvider):
  name = "nextpnr"
  VERSION = "67bd349e8f38d91a15f54340b29cc77ef156727f"
  def __init__(self):
    super().__init__(nextpnr.name)
    self.declareDep("icestorm")
    ###########################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("ARCH","ice40")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=nextpnr.name,
                             repospec="YosysHQ/nextpnr",
                             revision=nextpnr.VERSION,
                             recursive=False)

  #######################################################################
