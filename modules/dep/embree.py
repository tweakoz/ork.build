###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, host
###############################################################################
class _embree_from_source(dep.StdProvider):
  name = "embree"
  def __init__(self,name):
    super().__init__(_embree_from_source.name)
    self.declareDep("cmake")
    self._archlist = ["x86_64"]
    self.VERSION = "v3.9.0"
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("EMBREE_TUTORIALS","FALSE") # because they dont compile with ispc==1.13.0

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=_embree_from_source.name,
                             repospec="embree/embree",
                             revision=self.VERSION,
                             recursive=False)
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libembree3.so").exists()
###############################################################################
class _embree_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
    self.VERSION = "homebrew"
###############################################################################
class embree(dep.switch(linux=_embree_from_source, \
                        macos=_embree_from_homebrew)):
  def __init__(self):
    super().__init__("embree")
    if host.IsX86_64:
      self.requires(["ispc"])
  def env_init(self):
    log.marker("registering embree SDK(%s)"%self.VERSION)
