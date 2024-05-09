###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep
###############################################################################
class lemongraph(dep.StdProvider):
  name = "lemongraph"
  def __init__(self):
    super().__init__(lemongraph.name)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #self._builder.requires(["eigen"])
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=lemongraph.name,
                             repospec="tweakoz/lemon-mirror",
                             revision="master",
                             recursive=True)
  ########################################################################
