
###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep

###############################################################################

class lapack(dep.StdProvider):
  name = "lapack"
  def __init__(self):
    super().__init__(lapack.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=lapack.name,
                                repospec="Reference-LAPACK/lapack",
                                revision="v3.9.0",
                                recursive=False)
    return fetcher
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"liblapack.so").exists()