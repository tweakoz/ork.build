###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# Published under the GPL 2.0 license
###############################################################################
"""Pixar OpenSubdiv: shared osdCPU/osdGPU libs, TBB CPU backend.

GPU backend: Metal on macOS; OpenGL (internal GL loader, no GLEW/GLFW) on Linux.
CUDA/OpenCL/DX/OpenMP/Ptex, examples, tutorials, regression, docs, tests: off.
"""
from obt.dependency_artifacts import defines_version
from obt import dep, path, log, host

VERSION = "3.6.1"
TAG = "v" + VERSION.replace(".", "_")


class opensubdiv(dep.StdProvider):
  name = "opensubdiv"
  VERSION = VERSION

  def __init__(self):
    super().__init__(opensubdiv.name)
    self.setSourceRoot(path.builds()/self.name/("opensubdiv-" + VERSION))
    self.declareDep("cmake")
    self.declareDep("tbb")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "CMAKE_CXX_STANDARD": "17",
      "BUILD_SHARED_LIBS": "ON",
      "NO_EXAMPLES": "ON",
      "NO_TUTORIALS": "ON",
      "NO_REGRESSION": "ON",
      "NO_DOC": "ON",
      "NO_TESTS": "ON",
      "NO_GLTESTS": "ON",
      "NO_PTEX": "ON",    # ptex is not staged
      "NO_OMP": "ON",
      "NO_TBB": "OFF",
      "NO_CUDA": "ON",
      "NO_OPENCL": "ON",
      "NO_CLEW": "ON",
      "NO_DX": "ON",
      "NO_GLEW": "ON",
      "NO_GLFW": "ON",    # GLFW only feeds examples
      "NO_METAL": "OFF" if host.IsOsx else "ON",
      "NO_OPENGL": "ON" if host.IsOsx else "OFF",
      # plain dylibs in lib/, not OpenSubdiv.framework
      "NO_MACOS_FRAMEWORK": "ON",
      # oneTBB 2022 via its CMake config (OSD 3.6 has no FindTBB module)
      "TBB_DIR": str(path.libs()/"cmake"/"TBB"),
      "CMAKE_PREFIX_PATH": str(path.stage()),
      "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
    })
    self._builder.useMold()

  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=self.name,
                             repospec="PixarAnimationStudios/OpenSubdiv",
                             revision=TAG,
                             recursive=False)

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    ext = self.shlib_extension
    return ((path.libs()/("libosdCPU." + ext)).is_file()
            and (path.libs()/("libosdGPU." + ext)).is_file()
            and defines_version(path.includes()/"opensubdiv"/"version.h",
                                "OPENSUBDIV_VERSION_", VERSION))

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()

  def env_init(self):
    log.sdk_announce("registering opensubdiv SDK(%s)" % VERSION)
