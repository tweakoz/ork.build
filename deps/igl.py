###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, host, path
###############################################################################
class igl(dep.StdProvider):
  def __init__(self):
    name = "igl"
    super().__init__(name)
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/libigl",
                                      revision="toz-obt",
                                      shallow=False,
                                      recursive=False,
                                      )
    cgal_path = path.libs()/"cmake"/"CGAL"
    eig3_path = path.stage()/"share"/"eigen3"/"cmake"
    embr_path = path.libs()/"cmake"/"embree-3.9.0"
    glfw_path = path.libs()/"cmake"/"glfw3"
    module_path = "%s:%s:%s:%s"%(
                   cgal_path,
                   eig3_path,
                   embr_path,
                   glfw_path)
    self._builder = dep.CMakeBuilder(name)
    self._builder.requires(["cgal","lapack","eigen"])
    self._builder.setCmVar("LIBIGL_WITH_CGAL","TRUE")
    self._builder.setCmVar("LIBIGL_USE_STATIC_LIBRARY","OFF")
    self._builder.setCmVar("LIBIGL_USE_STATIC_LIBRARY","OFF")
    #self._builder.setCmVar("CMAKE_MODULE_PATH",module_path)
    if host.IsOsx: # sadly mac igl-embree support is broken..
      # https://github.com/libigl/libigl/issues/1302
      self._builder.setCmVar("LIBIGL_WITH_EMBREE","OFF")
