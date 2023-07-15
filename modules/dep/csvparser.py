###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class csvparser(dep.StdProvider):
  name = "csvparser"
  def __init__(self):
    super().__init__(csvparser.name)
    src_root = self.source_root
    #################################################
    self._builder = dep.BinInstaller(csvparser.name)
    self._builder.install_item(self.source_root/"csv.h",path.includes()/"csv.h")
    #################################################
    self.declareDep("pkgconfig")
    self.declareDep("cmake")

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=csvparser.name,
                             repospec="ben-strasser/fast-cpp-csv-parser",
                             revision="master",
                             shallow=False,
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"csv.h").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"csv.h").exists()