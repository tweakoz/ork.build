###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class pangolin(dep.StdProvider):
  name = "pangolin"
  def __init__(self):
    super().__init__(pangolin.name)
    #self._deps = ["pkgconfig"]
    src_root = self.source_root
    #################################################
    self.declareDep("pkgconfig")
    self.declareDep("cmake")
    self.declareDep("libcurl")
    self.declareDep("pybind11")
    #################################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("BUILD_PANGOLIN_LIBUVC","OFF")
    self._builder.setCmVar("BUILD_PANGOLIN_FFMPEG","OFF")
    #################################################
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=pangolin.name,
                             repospec="stevenlovegrove/pangolin",
                             revision="v0.8",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libpangolin.so").exists()