###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep

###############################################################################

class openvr(dep.StdProvider):

  def __init__(self):
    name = "openvr"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="ValveSoftware/openvr",
                                      revision="v1.10.20",
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }
