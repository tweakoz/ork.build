###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class klein(dep.StdProvider):
  name = "klein"
  def __init__(self):
    super().__init__(klein.name)
    if host.IsAARCH64:
      self.declareDep("sse2neon")
    src_root = self.source_root
    #################################################
    tgt_desc = self._target
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("KLEIN_ENABLE_PERF","OFF")
    if host.IsAARCH64:
      self._builder.setCmVar("KLEIN_ARCHITECTURE_ARM","1")
      self._builder.setCmVar("KLEIN_BUILD_SYM","OFF")
      self._builder.setCmVar("KLEIN_SSE2NEON_DIR", path.builds()/"sse2neon")
    else:
      self._builder.setCmVar("KLEIN_ENABLE_TESTS","ON")

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=klein.name,
                             repospec="tweakoz/klein",
                             revision="master",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libklein.so").exists()
