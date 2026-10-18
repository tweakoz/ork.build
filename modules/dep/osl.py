###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt.dependency_artifacts import defines_version
from obt import dep, path
###############################################################################
class osl(dep.StdProvider):
  name = "osl"
  def __init__(self):
    super().__init__(osl.name)
    self.setSourceRoot(path.builds()/"osl-1.15.7.0")
    self.declareDep("llvm")
    clang = self.declareDep("clang")
    self.declareDep("oiio")
    self.declareDep("pugixml")
    self.declareDep("cmake")
    self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "CMAKE_CXX_STANDARD": "17",
      "LLVM_DIRECTORY": str(path.stage()),
      "LLVM_BC_GENERATOR": str(clang.bitcode_compiler),
      "CMAKE_PREFIX_PATH": str(path.stage()),
      "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
      "USE_PYTHON": "OFF",
      "USE_QT": "OFF",
      "USE_PARTIO": "OFF",
      "OSL_BUILD_TESTS": "ON",
      "OSL_BUILD_SHADERS": "ON",
      "OSL_BUILD_BATCHED": "OFF",
      "OSL_USE_OPTIX": "OFF",
    })
    self._builder.useMold()

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=osl.name,
                             repospec="AcademySoftwareFoundation/OpenShadingLanguage",
                             revision="v1.15.7.0",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return ((path.bin()/"oslc").is_file()
            and all((path.libs()/("lib" + lib + "." + self.shlib_extension)).is_file()
                    for lib in ("oslexec", "oslcomp", "oslquery"))
            and defines_version(path.includes()/"OSL"/"oslversion.h", "OSL_LIBRARY_VERSION_", "1.15.7.0"))

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()
###############################################################################
