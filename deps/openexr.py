###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep

###############################################################################

class openexr(dep.StdProvider):

  def __init__(self):
    name = "openexr"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="openexr/openexr",
                                      revision="v2.4.1",
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
    self._builder.setCmVar("OPENEXR_VIEWERS_ENABLE","OFF")
    self._builder.setCmVar("CMAKE_MODULE_PATH",self.source_root)
    self._builder.requires(["fltk"])
