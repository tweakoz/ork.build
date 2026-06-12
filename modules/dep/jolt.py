###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class jolt(dep.StdProvider):
  name = "jolt"
  def __init__(self):
    super().__init__(jolt.name)
    self.declareDep("cmake")
    # Jolt's CMakeLists.txt lives in Build/, not the repo root.
    # build_src and src_dir_override must point to the same dir or
    # obt.cmake.context emits a conflicting positional source-dir arg.
    self.build_src = self.source_root/"Build"
    self._builder = self.createBuilder(dep.CMakeBuilder,
                                       src_dir_override=self.build_src)
    self._builder.setCmVars({
      # library only — tests/samples/viewer default ON upstream
      "TARGET_UNIT_TESTS": "OFF",
      "TARGET_HELLO_WORLD": "OFF",
      "TARGET_PERFORMANCE_TEST": "OFF",
      "TARGET_SAMPLES": "OFF",
      "TARGET_VIEWER": "OFF",
      # jolt defaults these OFF; orkid hosts exception/RTTI-enabled code
      "CPP_EXCEPTIONS_ENABLED": "ON",
      "CPP_RTTI_ENABLED": "ON",
      # upstream treats warnings as errors — too fragile across compilers
      "ENABLE_ALL_WARNINGS": "OFF",
    })
  ########################################################################
  @property
  def github_repo(self):
    return "tweakoz/jolt"
  ########################################################################
  @property
  def revision(self):
    return "v5.5.0"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=jolt.name,
                             repospec=self.github_repo,
                             revision=self.revision,
                             md5val="5c8b6d4210e6867601cb0896f3d662a6", # v5.5.0
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.build_src/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/("libJolt.%s"%self.shlib_extension)).exists()
