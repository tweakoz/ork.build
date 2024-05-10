###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################

class curlpp(dep.StdProvider):
  name = "curlpp"
  def __init__(self):
    super().__init__(curlpp.name)
    #self._deps = ["pkgconfig"]
    src_root = self.source_root
    #################################################
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #if host.IsOsx:
    #  import obt.macos_homebrew
    #  sslroot = obt.macos_homebrew.prefix_for_package("openssl")
    #  print(sslroot)
    #  self._builder.setCmVar("OPENSSL_ROOT_DIR",sslroot)
    #################################################
    self.declareDep("pkgconfig")
    self.declareDep("cmake")
    self.declareDep("libcurl")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=curlpp.name,
                             repospec="tweakoz/curlpp",
                             revision="v0.8.1",
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libcurlpp.so").exists()