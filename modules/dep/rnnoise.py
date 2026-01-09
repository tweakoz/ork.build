###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep,path
###############################################################################
class rnnoise(dep.StdProvider):
  name = "rnnoise"
  def __init__(self):
    super().__init__(rnnoise.name)
    self.VERSION = "70f1d256acd4b34a572f999a05c87bf00b67730d"
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    self._builder._needsautogendotsh = True
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=rnnoise.name,
                             repospec="xiph/rnnoise",
                             revision=self.VERSION,
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"configure.ac").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"librnnoise.a").exists()
###############################################################################
