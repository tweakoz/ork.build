###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path
###############################################################################
class cycles(dep.StdProvider):
  name = "cycles"
  def __init__(self):
    super().__init__(cycles.name)
    self.declareDep("boost")
    self.declareDep("pugixml")
    self.declareDep("openjpeg")
    self.declareDep("osl")
    self.declareDep("ocio")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("CMAKE_MODULE_PATH",path.stage()/"lib"/"cmake")
    self._builder.setCmVar("BOOST_ROOT",path.stage())
    self._builder.setCmVar("Boost_INCLUDE_DIR",path.includes()/"boost")
    self._builder.setCmVar("Boost_NO_SYSTEM_PATHS","ON")
    #self._builder.setCmVar("Boost_DEBUG","1")

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(cycles.name)
    fetcher._git_url = "https://git.blender.org/cycles.git"
    fetcher._cache=False,
    fetcher._recursive=False
    fetcher._revision = "master"
    return fetcher
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.stage()/"bin"/"llvm-cov").exists()
###############################################################################
