###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path

###############################################################################

class libarchive(dep.StdProvider):
  name = "libarchive"
  def __init__(self):
    super().__init__(libarchive.name)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("ENABLE_TEST", "OFF")
    self._builder.setCmVar("ENABLE_TAR", "OFF")
    self._builder.setCmVar("ENABLE_CPIO", "OFF")
    self._builder.setCmVar("ENABLE_CAT", "OFF")

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=libarchive.name,
                             repospec="libarchive/libarchive",
                             revision="v3.8.4",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    if host.IsOsx:
      return (path.libs()/"libarchive.dylib").exists()
    else:
      return (path.libs()/"libarchive.so").exists()
