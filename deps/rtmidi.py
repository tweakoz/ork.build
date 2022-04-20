###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path
###############################################################################
class rtmidi(dep.StdProvider):
  def __init__(self):
    name = "rtmidi"
    super().__init__(name)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="thestk/rtmidi",
                                      revision="4.0.0",
                                      recursive=True)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("CMAKE_INSTALL_INCLUDEDIR",path.includes()/"rtmidi")
    #self._builder.requires(["eigen"])

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"librtmidi.so").exists()