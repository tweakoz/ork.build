###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep

###############################################################################

class cmake(dep.StdProvider):

  def __init__(self):
    name = "cmake"
    super().__init__(name)

    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/kitware/cmake"
    self._fetcher._revision = "v3.16.4"

    self._builder = dep.CMakeBuilder(name)
    self._builder._cmakeenv["CMAKE_USE_SYSTEM_CURL"]="YES"
    self._builder.requires(["pkgconfig"])
