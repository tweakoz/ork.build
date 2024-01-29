###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path, host, osrelease
###############################################################################
class rapidjson(dep.StdProvider):
  VERSION ="toz-master"
  NAME = "rapidjson"
  def __init__(self):
    super().__init__(rapidjson.NAME)
    self.declareDep("cmake")
    self._builder = dep.CMakeBuilder(rapidjson.NAME)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
    })
    if host.IsDarwin:
      osxname = host.description().codename
      self._builder.setCmVars({
        "RAPIDJSON_BUILD_THIRDPARTY_GTEST": "OFF",
        "RAPIDJSON_BUILD_TESTS": "OFF",
      })
      if osxname=="monterey" or osxname=="ventura" or osxname=="sonoma":
        self._builder.setCmVars({
          "CMAKE_CXX_FLAGS": "-Wno-deprecated-declarations -Wno-deprecated-copy-with-user-provided-copy"
        })
    else:
      desc = osrelease.descriptor()
      if desc.version_id == "23.10":
        self._builder.setCmVar("CMAKE_CXX_COMPILER","g++-10")
        self._builder.setCmVar("CMAKE_CMAKE_C_COMPILER","gcc-10")
        self._builder.setCmVar("RAPIDJSON_BUILD_CXX17","ON")
        self._builder.setCmVar("RAPIDJSON_BUILD_CXX11","OFF")
      self._builder.setCmVars({
        "CMAKE_CXX_FLAGS": "-Wno-stringop-overflow -Wno-array-bounds -std=c++17",
        "BUILD_EXAMPLES": "ON",
      })
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=rapidjson.NAME,
                             repospec="tweakoz/rapidjson",
                             revision=rapidjson.VERSION,
                             recursive=True)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"rapidjson"/"rapidjson.h").exists()
