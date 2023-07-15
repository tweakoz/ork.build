
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

class osgeotiff(dep.StdProvider):
  name = "osgeotiff"
  def __init__(self):
    super().__init__(osgeotiff.name)
    self.declareDep("osgeoproj")
    self.declareDep("cmake")
    ###########################################
    self.build_src = path.builds()/"osgeotiff"/"libgeotiff"
    self.build_dest = self.source_root/".build"
    ###########################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=osgeotiff.name,
                             repospec="OSGeo/libgeotiff",
                             revision="3467bd7b49cca8df29efd606a554b5caf910a3d4",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libgeotiff.so").exists()
