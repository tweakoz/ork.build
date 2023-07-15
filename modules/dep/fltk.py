###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, command, path, host


###############################################################################

class fltk(dep.StdProvider):
  #############################################
  name = "fltk"
  def __init__(self):
    super().__init__(fltk.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVar("OPTION_BUILD_SHARED_LIBS","ON")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=fltk.name,
                             repospec="fltk/fltk",
                             revision="release-1.3.5",
                             recursive=False)
  ########################################################################
  def install(self):
    ok = self._builder.install(self.build_dest)
    if ok:
      if host.IsGentoo:
        ok = (0==command.system(["rm",path.stage()/"lib64"/"libfltk*.a"]))
      else:
        ok = (0==command.system(["rm",path.libs()/"libfltk*.a"]))
    return ok
  #############################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libfltk_SHARED.so").exists()
