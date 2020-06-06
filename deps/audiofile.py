###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, log
###############################################################################
class _audiofile_from_source(dep.StdProvider):
  def __init__(self,name):
    super().__init__(name)
    self.VERSION = "master"
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="wtay/audiofile",
                                      revision=self.VERSION,
                                      recursive=False)
    self._builder = dep.CMakeBuilder(name)
###############################################################################
class _audiofile_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
    self.VERSION = "audiofile"
###############################################################################
class audiofile(dep.switch(linux=_audiofile_from_source, \
                        macos=_audiofile_from_homebrew)):
  def __init__(self):
    super().__init__("audiofile")
