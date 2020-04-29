###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep
###############################################################################
class assimp(dep.StdProvider):
  def __init__(self):
    VERSION ="v5.0.0"
    NAME = "assimp"
    super().__init__(NAME)
    self._fetcher = dep.GithubFetcher(name=NAME,
                                      repospec="assimp/assimp",
                                      revision=VERSION,
                                      recursive=False)
    self._builder = dep.CMakeBuilder(NAME)
  def linkenv(self): ##########################################################
    return {
        "LIBS": ["assimp"]
    }
