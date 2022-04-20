###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log, path
###############################################################################
class cycles(dep.StdProvider):
  def __init__(self):
    name = "cycles"
    super().__init__(name)
    self.declareDep("boost")
    self.declareDep("pugixml")
    self.declareDep("openjpeg")
    self.declareDep("osl")
    self.declareDep("ocio")
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://git.blender.org/cycles.git"
    self._fetcher._cache=False,
    self._fetcher._recursive=False
    self._fetcher._revision = "master"
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("CMAKE_MODULE_PATH",path.stage()/"lib"/"cmake")
    self._builder.setCmVar("BOOST_ROOT",path.stage())
    self._builder.setCmVar("Boost_INCLUDE_DIR",path.includes()/"boost")
    self._builder.setCmVar("Boost_NO_SYSTEM_PATHS","ON")
    #self._builder.setCmVar("Boost_DEBUG","1")

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"bin"/"llvm-cov").exists()
###############################################################################
