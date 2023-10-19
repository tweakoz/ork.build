###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class portaudio(dep.StdProvider):
  name = "portaudio"
  def __init__(self):
    super().__init__(portaudio.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("CMAKE_INSTALL_INCLUDEDIR",path.includes()/"portaudio")

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=portaudio.name,
                                repospec="PortAudio/portaudio",
                                revision="v19.7.0",
                                recursive=False)
    return fetcher
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libportaudio.so").exists()