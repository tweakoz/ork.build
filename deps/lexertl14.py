###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep

###############################################################################

class lexertl14(dep.StdProvider):
  def __init__(self):
    name = "lexertl14"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/lexertl14",
                                      revision="e3eef107f2881e39db028e0ded1252d335948a91",
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
