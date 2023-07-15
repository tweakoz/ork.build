###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class libcurl(dep.StdProvider):
  name = "libcurl"
  def __init__(self):
    super().__init__(libcurl.name)
    src_root = self.source_root
    #################################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    if host.IsOsx:
      import obt.macos_homebrew
      sslroot = obt.macos_homebrew.prefix_for_package("openssl")
      print(sslroot)
      self._builder.setCmVar("OPENSSL_ROOT_DIR",sslroot)
      self._builder.setCmVar("USE_ZLIB","ON")
    #################################################
    self.declareDep("pkgconfig")
    self.declareDep("cmake")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=libcurl.name,
                             repospec="tweakoz/curl",
                             revision="obt-7.84",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libcurl.so").exists()