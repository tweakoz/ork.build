###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class sse2neon(dep.StdProvider):
  name = "sse2neon"
  def __init__(self):
    super().__init__(sse2neon.name)
    #self._deps = ["pkgconfig"]
    src_root = self.source_root
    #################################################
    tgt_desc = self._target
    self._builder = self.createBuilder(dep.NopBuilder)

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=sse2neon.name,
                             repospec="tweakoz/sse2neon",
                             revision="master",
                             recursive=True)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"Makefile").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.source_root/"Makefile").exists()
