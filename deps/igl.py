###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep

###############################################################################

class igl(dep.StdProvider):

  def __init__(self):
    name = "igl"
    super().__init__(name)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "http://github.com/libigl/libigl"
    self._fetcher._revision = "v2.2.0"

    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["cgal"])
    self._builder.requires(["lapack"])
