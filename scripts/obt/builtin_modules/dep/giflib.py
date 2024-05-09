###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, host, patch
from obt.command import Command
###############################################################################
class giflib(dep.StdProvider):
  name = "giflib"
  def __init__(self):
    super().__init__(giflib.name)
    self.declareDep("cmake")
    ###########################################
    toolset = "darwin" if self._target.os=="macos" else "gcc"
    ###########################################
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanOnClean = False
    build_dir = path.builds()/giflib.name

    env = {
      "PREFIX": path.stage()
    }
    ###############################
    def patch_makefile():
      if toolset == "darwin":
        p = patch.patcher(self)
        p.patch(self.source_root,"Makefile")
      return True
    ###############################
    make_clean_command = Command([
      "make","-e",
      "all", "install"
      ],
      working_dir=build_dir,
      environment=env)

    make_incr_command = Command([
      "make","-e","install"],
      working_dir=build_dir,
      environment=env)

    self._builder._cleanbuildcommands += [patch_makefile,make_clean_command]
    self._builder._incrbuildcommands += [make_incr_command]
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=giflib.name,
                             repospec="tweakoz/giflib",
                             revision="5.2.1",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"Makefile").exists()

  def areRequiredBinaryFilesPresent(self):
    return None
