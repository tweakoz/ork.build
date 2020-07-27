###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep
###############################################################################
class lemongraph(dep.StdProvider):
  def __init__(self):
    name = "lemongraph"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/lemon-mirror",
                                      revision="master",
                                      recursive=True)
    self._builder = dep.CMakeBuilder(name)
    #self._builder.requires(["eigen"])
