###############################################################################
# Orkid Build System
# Copyright 2010-2024, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class oscar64(dep.StdProvider):
  name = "oscar64"
  VERSION = "v1.32.268"
  def __init__(self):
    super().__init__(oscar64.name)
    self._builder = dep.CMakeBuilder(oscar64.name)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=oscar64.name,
                             repospec="drmortalwombat/oscar64",
                             revision=oscar64.VERSION,
                             recursive=False,
                             disable_tarball=True)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"oscar64").exists()
