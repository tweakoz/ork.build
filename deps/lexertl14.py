###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, path

###############################################################################

class lexertl14(dep.StdProvider):
  def __init__(self):
    name = "lexertl14"
    super().__init__(name)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/lexertl14",
                                      revision="e9fd6c95b530f3a3840c65e74e79627732cfd4a7",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
  #############################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"lexertl"/"char_traits.hpp").exists()
