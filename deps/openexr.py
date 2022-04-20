###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, path

###############################################################################

class openexr(dep.StdProvider):

  def __init__(self):
    name = "openexr"
    super().__init__(name)
    self.declareDep("cmake")
    self.declareDep("fltk")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="openexr/openexr",
                                      revision="v2.4.1",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("OPENEXR_VIEWERS_ENABLE","OFF")
    self._builder.setCmVar("CMAKE_MODULE_PATH",self.source_root)
    self._builder.setCmVar("PYILMBASE_ENABLE","OFF")
    
    self._builder.requires(["fltk"])

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libIlmImf.so").exists()
