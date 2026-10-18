###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt.dependency_artifacts import defines_version
from obt import dep, path, log, host


class embree(dep.StdProvider):
  name = "embree"
  VERSION = "4.4.1"

  def __init__(self):
    super().__init__(embree.name)
    self.setSourceRoot(path.builds()/("embree-"+self.VERSION))
    self.declareDep("cmake")
    self.declareDep("tbb")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "EMBREE_STATIC_LIB": "OFF",
      "EMBREE_TUTORIALS": "OFF",
      "EMBREE_ISPC_SUPPORT": "OFF",
      "EMBREE_SYCL_SUPPORT": "OFF",
      "EMBREE_TASKING_SYSTEM": "TBB",
      # Build optimized variants and let Embree dispatch at runtime. DEFAULT
      # only detects the compiler's default ISA (often plain SSE2 on x86).
      "EMBREE_MAX_ISA": "NEON2X" if host.IsAARCH64 else "AVX512",
      "TBB_DIR": str(path.libs()/"cmake"/"TBB"),
      "CMAKE_PREFIX_PATH": str(path.stage()),
      "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
    })
    self._builder.useMold()

  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=self.name,
                             repospec="RenderKit/embree",
                             revision="v"+self.VERSION,
                             recursive=False)

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return ((path.libs()/("libembree4." + self.shlib_extension)).is_file()
            and defines_version(path.includes()/"embree4"/"rtcore_config.h", "RTC_VERSION_", self.VERSION))

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()

  def env_init(self):
    log.sdk_announce("registering embree SDK(%s)" % self.VERSION)
