###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt.dependency_artifacts import cmake_version
from obt import dep, path, pathtools
from pathlib import Path
import subprocess


class igl(dep.StdProvider):
  name = "igl"
  VERSION = "2.6.0"

  def __init__(self):
    super().__init__(igl.name)
    self.setSourceRoot(path.builds()/("igl-"+self.VERSION))
    self.declareDep("cmake")
    self.declareDep("eigen")
    embree = self.declareDep("embree")
    boost = self.declareDep("boost")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "LIBIGL_COPYLEFT_CGAL": "OFF",
      "LIBIGL_USE_STATIC_LIBRARY": "OFF",
      "LIBIGL_BUILD_TESTS": "OFF",
      "LIBIGL_BUILD_TUTORIALS": "OFF",
      "LIBIGL_EMBREE": "ON",
      "LIBIGL_INSTALL": "ON",
      "embree_DIR": str(path.libs()/"cmake"/("embree-"+embree.VERSION)),
      "Eigen3_DIR": str(path.stage()/"share"/"eigen3"/"cmake"),
      "CMAKE_PREFIX_PATH": str(path.stage()),
    })
    self._builder.setCmVars(boost.cmake_additional_flags())
    self._builder._parallelism = 0.5
    self._builder.useMold()

    def post_install():
      pathtools.copyfile(self.build_dest/"lib"/"libtriangle.a", path.libs()/"libtriangle.a")
      pathtools.copyfile(self.build_dest/"_deps"/"triangle-src"/"triangle.h", path.includes()/"triangle.h")
    self._builder._onPostInstall = post_install

  def build(self):
    # The old fork only redirected Embree to two obsolete diagnostic fixes.
    # Embree 4 includes those fixes; this patch replaces the private FetchContent
    # copy with OBT's shared dependency and retains the existing Eigen 3.4 ABI.
    patch = Path(__file__).parent/"patches"/"igl-2.6.0-staged-deps.patch"
    if subprocess.run(["git", "apply", "--check", "--reverse", str(patch)],
                      cwd=str(self.source_root), capture_output=True).returncode:
      subprocess.run(["git", "apply", "--check", str(patch)], cwd=str(self.source_root), check=True)
      subprocess.run(["git", "apply", str(patch)], cwd=str(self.source_root), check=True)
    return super().build()

  @property
  def github_repo(self):
    return "libigl/libigl"

  @property
  def revision(self):
    return "v"+self.VERSION

  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=self.name, repospec=self.github_repo,
                             revision=self.revision, recursive=False)

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return ((path.includes()/"igl"/"embree"/"EmbreeIntersector.h").is_file()
            and (path.libs()/"libtriangle.a").is_file()
            and cmake_version(path.libs()/"cmake"/"igl"/"libigl-config-version.cmake", self.VERSION))

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()
