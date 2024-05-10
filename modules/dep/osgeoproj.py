
###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path
from obt.command import *

###############################################################################

class osgeoproj(dep.StdProvider):
  name = "osgeoproj"
  def __init__(self):
    super().__init__(osgeoproj.name)
    self.declareDep("cmake")
    ###########################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=osgeoproj.name,
                             repospec="OSGeo/PROJ",
                             revision="a892e23d9a444e86b35fc67d0fb84e4acca05c2f",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libproj.so").exists()
