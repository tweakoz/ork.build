###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path, host

###############################################################################

class _nnsvs(dep.StdProvider):
  name = "_nnsvs"
  def __init__(self):
    super().__init__(_nnsvs.name)
    self._builder = self.createBuilder(dep.NopBuilder)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=_nnsvs.name,
                             repospec="tweakoz/nnsvs",
                             revision="master",
                             recursive=True)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()
