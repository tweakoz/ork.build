###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, path

###############################################################################

class libsocket(dep.StdProvider):
  def __init__(self):
    name = "libsocket"
    super().__init__(name)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/libsocket",
                                      revision="master",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires(["cmake"])
    self._debug = True
    self._fetcher._debug = True
    self._builder._debug = True
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"package.xml").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"libsocket"/"epoll.hpp").exists()
