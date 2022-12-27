###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, command, path

###############################################################################

class klein(dep.StdProvider):
  name = "klein"
  def __init__(self):
    super().__init__(klein.name)
    #self._deps = ["pkgconfig"]
    src_root = self.source_root
    #################################################
    tgt_desc = self._target
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("KLEIN_ENABLE_PERF","OFF")
    self._builder.setCmVar("KLEIN_ENABLE_TESTS","ON")
    #self._builder.setOption("--disable-vaapi")

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=klein.name,
                             repospec="jeremyong/klein",
                             revision="master",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libklein.so").exists()
