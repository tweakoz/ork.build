###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log
###############################################################################
class _audiofile_from_source(dep.StdProvider):
  name = "audiofile"
  def __init__(self):
    super().__init__(_audiofile_from_source.name)
    self.VERSION = "master"
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    self._builder._needsautogendotsh = True
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=_audiofile_from_source.name,
                             repospec="wtay/audiofile",
                             revision=self.VERSION,
                             recursive=False)
  ########################################################################
###############################################################################
class _audiofile_from_homebrew(dep.HomebrewProvider):
  name = "audiofile"
  def __init__(self):
    super().__init__(_audiofile_from_homebrew.name,_audiofile_from_homebrew.name)
    self.VERSION = "audiofile"
###############################################################################
class audiofile(dep.switch(linux=_audiofile_from_source, \
                           macos=_audiofile_from_homebrew)):
  def __init__(self):
    super().__init__()
