###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class apitrace(dep.StdProvider):
  name = "apitrace"
  def __init__(self):
    super().__init__(apitrace.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def github_repo(self):
    return "apitrace/apitrace"
  ########################################################################
  @property
  def revision(self):
    return "11.1"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=apitrace.name,
                             repospec=self.github_repo,
                             revision=self.revision,
                             recursive=True)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"apitrace").exists()
