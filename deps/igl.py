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
    #self._archlist = ["x86_64"]
    self.declareDep("cmake")
    #self.declareDep("lapack")
    self.declareDep("eigen")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/libigl",
                                      revision="master",
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
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires(["eigen"])
    self._builder.setCmVar("LIBIGL_WITH_CGAL","FALSE")
    self._builder.setCmVar("LIBIGL_USE_STATIC_LIBRARY","OFF")
    #self._builder.setCmVar("CMAKE_MODULE_PATH",module_path)
    if host.IsOsx or host.IsAARCH64: # sadly mac igl-embree support is broken..
      # https://github.com/libigl/libigl/issues/1302
      self._builder.setCmVar("LIBIGL_WITH_EMBREE","OFF")

    self._builder._parallelism = 0.5 # prevent out of memory..

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"igl"/"igl_inline.h").exists()
