###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path
###############################################################################
class osl(dep.StdProvider):
  name = "osl"
  def __init__(self):
    super().__init__(osl.name)
    self.declareDep("llvm")
    self.declareDep("pugixml")
    self.declareDep("cmake")
    self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "CMAKE_CXX_STANDARD": "17"
    }

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=osl.name,
                             repospec="AcademySoftwareFoundation/OpenShadingLanguage",
                             revision="v1.11.16.0",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"oslc").exists()
###############################################################################
