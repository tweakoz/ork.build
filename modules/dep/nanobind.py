###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class nanobind(dep.StdProvider):
  name = "nanobind"
  def __init__(self):
    super().__init__(nanobind.name)
    self.declareDep("python")
    self.declareDep("cmake")
    PYTHON = dep.instance("python")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #self._builder.setCmVar("Python3_FIND_STRATEGY","LOCATION")
    #self._builder.setCmVar("Python3_ROOT_DIR",PYTHON.home_dir)
    self._builder.setCmVar("PYTHON_EXECUTABLE",PYTHON.executable)
    self._builder.requires(["python"])
    self._debug = True
    self._fetcher._debug = True
    self._builder._debug = True
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=nanobind.name,
                             repospec="wjakob/nanobind",
                             revision="v2.2.0",
                             recursive=True)
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"nanobind"/"attr.h").exists()
