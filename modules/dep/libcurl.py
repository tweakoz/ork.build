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
    self.declareDep("cmake")
    self.declareDep("openssl")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    if host.IsOsx:
      # Use OBT-built openssl (3.5.6 LTS), not /opt/homebrew/opt/openssl@3.
      self._builder.setCmVar("OPENSSL_ROOT_DIR", str(path.prefix()))
      self._builder.setCmVar("USE_ZLIB","ON")
    # No OBT libssh2 dep — disable SCP/SFTP support so curl doesn't pull
    # /opt/homebrew/opt/libssh2. orkid only uses HTTP(S).
    self._builder.setCmVar("CURL_USE_LIBSSH2", "OFF")
    self._builder.setCmVar("CURL_USE_LIBSSH",  "OFF")
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