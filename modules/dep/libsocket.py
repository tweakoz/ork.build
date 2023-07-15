###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class libsocket(dep.StdProvider):
  name = "libsocket"
  def __init__(self):
    super().__init__(libsocket.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires(["cmake"])
    self._debug = True
    self._builder._debug = True
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=libsocket.name,
                             repospec="tweakoz/libsocket",
                             revision="master",
                             recursive=False,
                             #debug=True,
                             )
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"package.xml").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"libsocket"/"epoll.hpp").exists()
