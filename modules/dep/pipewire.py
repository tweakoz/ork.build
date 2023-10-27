###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, template
from obt.command import Command
###############################################################################
class pipewire(dep.StdProvider):
  name = "pipewire"
  def __init__(self):
    super().__init__(pipewire.name)
    self._builder = self.createBuilder(dep.CustomBuilder)
    def cmd(cmd_l):
      return Command(
      cmd_l,
      do_log=True,
      working_dir=self.source_root)
    def mcmd(cmd_l):
        return cmd(["meson"]+cmd_l)
    self._builder._cleanbuildcommands = [mcmd(["setup",".build"])]
    self._builder._incrbuildcommands = [mcmd(["configure",".build",("-Dprefix=%s"%path.stage())])]
    self._builder._incrbuildcommands = [mcmd(["configure",".build"])]
    self._builder._installcommands = []

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=pipewire.name,
                             repospec="PipeWire/pipewire",
                             revision="0.3.83",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"LICENSE").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libPtex.so").exists()
###############################################################################




