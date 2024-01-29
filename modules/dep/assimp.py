###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path, host, osrelease
###############################################################################
class assimp(dep.StdProvider):
  name = "assimp"
  VERSION ="obt-v5.2.5"
  def __init__(self):
    super().__init__(assimp.name)
    self.declareDep("cmake")    
    self._builder = dep.CMakeBuilder(assimp.name)
    self._builder.setCmVar("ASSIMP_BUILD_ASSIMP_TOOLS","TRUE")
    self._builder.setCmVar("ASSIMP_BUILD_ASSIMP_VIEW","TRUE")
    if host.IsDarwin:
      self._builder.setCmVar("CMAKE_CXX_FLAGS","-Wno-deprecated-declarations")
    else:
      desc = osrelease.descriptor()
      self._builder.setCmVar("CMAKE_CXX_FLAGS","-Wno-maybe-uninitialized")
      if desc.version_id == "23.10":
        self._builder.setCmVar("CMAKE_CXX_COMPILER","g++-11")
        self._builder.setCmVar("CMAKE_CMAKE_C_COMPILER","gcc-11")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=assimp.name,
                             repospec="tweakoz/assimp",
                             revision=assimp.VERSION,
                             recursive=False)

  #######################################################################
  ########
  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "ASSIMP",
                             environment = dict() )
  ########
  def linkenv(self): ##########################################################
    return {
        "LIBS": ["assimp"]
    }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libassimp.so").exists()
