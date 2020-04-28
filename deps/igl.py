###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host

###############################################################################

class igl(dep.StdProvider):

  def __init__(self):
    name = "igl"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="libigl/libigl",
                                      revision="v2.2.0",
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["cgal","lapack","eigen"])
    self._builder.setCmVar("LIBIGL_WITH_CGAL","TRUE")
    self._builder.setCmVar("LIBIGL_USE_STATIC_LIBRARY","OFF")
    if host.IsOsx: # sadly mac igl-embree support is broken..
      # https://github.com/libigl/libigl/issues/1302
      self._builder.setCmVar("LIBIGL_WITH_EMBREE","OFF")
