###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path, log, env, host
from ork.command import Command
###############################################################################
class ue5(dep.StdProvider):
  name = "ue5"
  def __init__(self):
    super().__init__(ue5.name)
    self._archlist = ["x86_64","aarch64"]
    self._oslist = ["Linux","Darwin"]
    self._builder = dep.CustomBuilder(ue5.name)

    bdir = self.source_root

    setupcmd = Command(["./Setup.sh"],working_dir=bdir,do_log=False)
    genprjcmd = Command(["./GenerateProjectFiles.sh"],working_dir=bdir,do_log=False)

    if host.IsOsx:
      buildcmd = Command(["xcodebuild","-workspace","UE5.xcworkspace","-scheme","UE5"],
                          working_dir=bdir,
                          do_log=False)

    self._builder._cleanbuildcommands += [setupcmd,genprjcmd,buildcmd]
    self._builder._incrbuildcommands = [buildcmd]

    self._builder._builddir = bdir/".fake_build"
    #print("unrealdep<%s>"%self)

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=ue5.name,
                                repospec="EpicGames/UnrealEngine",
                                revision="5.0.2-release",
                                recursive=True,
                                shallow=False)
    return fetcher
  ########################################################################

  def find_paths(self):
    return [self.source_root/"Engine"/"Plugins"] + \
           [self.source_root/"Engine"/"Source"/"Runtime"]    

  def env_init(self):
    log.marker("registering Unreal SDK")
    env.append("PATH",path.builds()/"unreal"/"Engine"/"Binaries"/"Linux")

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"GenerateProjectFiles.sh").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.source_root/"Engine"/"Binaries"/"Linux"/"UE4Editor-Linux-Debug").exists()
