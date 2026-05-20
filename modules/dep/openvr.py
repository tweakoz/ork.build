###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path
###############################################################################
class openvr(dep.StdProvider):
  name = "openvr"
  def __init__(self):
    super().__init__(openvr.name)
    self._archlist = ["x86_64"]
    self._oslist = ["Linux"]
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON"
    }
    # mold linker — Linux-only opt-in (no-op elsewhere). Called AFTER the
    # _cmakeenv reassignment above so the -fuse-ld=mold flags survive.
    self._builder.useMold()

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openvr.name,
                             repospec="ValveSoftware/openvr",
                             revision="v1.11.11",
                             md5val="344c31fa7c7787826b95e97e4d55405e",
                             recursive=False)
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libopenvr_api.a").exists()
