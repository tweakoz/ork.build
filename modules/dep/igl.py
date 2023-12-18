###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, host, path, pathtools
###############################################################################
class igl(dep.StdProvider):
  name = "igl"
  def __init__(self):
    super().__init__(igl.name)
    #self._archlist = ["x86_64"]
    self.declareDep("cmake")
    #self.declareDep("lapack")
    self.declareDep("eigen")
    BOOST = self.declareDep("boost")
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
    self._builder.requires(["eigen","tbb"])
    self._builder.setCmVar("LIBIGL_WITH_CGAL","TRUE")
    self._builder.setCmVar("LIBIGL_USE_STATIC_LIBRARY","OFF")

    boost_cmake = BOOST.cmake_additional_flags()
    for key in boost_cmake.keys():
      val = boost_cmake[key]
      self._builder.setCmVar(key,val)

    #self._builder.setCmVar("CMAKE_MODULE_PATH",module_path)
    if host.IsAppleSilicon: # sadly mac igl-embree support is broken..
      # https://github.com/libigl/libigl/issues/1302
      self._builder.setCmVar("LIBIGL_WITH_EMBREE","OFF")
      self._builder.setCmVar("CMAKE_EXE_LINKER_FLAGS","-ld_classic")

    self._builder._parallelism = 0.5 # prevent out of memory..

    #####################################
    # install triangle
    #####################################

    def post_install():
      print("post installing IGL!!")
      igl_builddir = path.builds()/"igl"/".build"
      pathtools.copyfile(igl_builddir/"lib"/"libtriangle.a",path.libs()/"libtriangle.a")
      pathtools.copyfile(igl_builddir/"_deps"/"triangle-src"/"triangle.h",path.includes()/"triangle.h")

    self._builder._onPostInstall = post_install

    #####################################

  ########################################################################
  @property
  def github_repo(self):
    return "tweakoz/libigl"
  ########################################################################
  @property
  def revision(self):
    return "toz-v2.5.0"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=igl.name,
                             repospec=self.github_repo,
                             revision=self.revision,
                             shallow=False,
                             recursive=False)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"igl"/"igl_inline.h").exists()
