###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class openexr(dep.StdProvider):
  name = "openexr"
  def __init__(self):
    super().__init__(openexr.name)
    self.declareDep("cmake")
    #self.declareDep("fltk")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("OPENEXR_VIEWERS_ENABLE","OFF")
    self._builder.setCmVar("CMAKE_MODULE_PATH",self.source_root)
    self._builder.setCmVar("PYILMBASE_ENABLE","OFF")
    #self._builder.requires(["fltk"])
    
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openexr.name,
                             repospec="AcademySoftwareFoundation/openexr",
                             #revision="v2.5.8",
                             revision="v3.2.1",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libIlmImf.so").exists()
