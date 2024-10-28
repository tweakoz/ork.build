###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class ftxui(dep.StdProvider):
  name = "ftxui"
  def __init__(self):
    super().__init__(ftxui.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def github_repo(self):
    return "ArthurSonzogni/FTXUI"
  ########################################################################
  @property
  def revision(self):
    return "v5.0.0"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=ftxui.name,
                             repospec=self.github_repo,
                             revision=self.revision,
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libftxui.so").exists()
