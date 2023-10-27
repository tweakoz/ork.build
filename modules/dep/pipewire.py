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
    def ccmd(key,val):
        c_str = "-D%s=%s"%(key,str(val))
        return mcmd(["configure",".build",c_str])
    self._builder._cleanbuildcommands = [mcmd(["setup",".build"])]
    self._builder._incrbuildcommands += [ccmd("prefix",path.stage())]
    self._builder._incrbuildcommands += [ccmd("systemd-user-service","disabled")]
    self._builder._incrbuildcommands += [ccmd("session-managers","[]")]
    self._builder._incrbuildcommands += [ccmd("udevrulesdir",path.stage()/"udevrules")]
    self._builder._incrbuildcommands += [ccmd("dbus","disabled")]
    self._builder._incrbuildcommands += [ccmd("alsa","enabled")]
    self._builder._incrbuildcommands += [ccmd("libdir","lib")]
    
    
    # systemd-system-unit-dir : /usr/lib/systemd/system
    # systemd-user-unit-dir   : /usr/lib/systemd/user
    # udevrulesdir : /lib/udev/rules.d

    self._builder._incrbuildcommands += [mcmd(["configure",".build"])]
    self._builder._incrbuildcommands += [mcmd(["compile","-C",".build"])]
    self._builder._installcommands  = [mcmd(["install","-C",".build"])]
    self._builder._installcommands += [cmd(["cp",
                                            path.modules()/"misc"/"pipewire.conf",
                                            path.stage()/"etc"/"pipewire.conf"])]

    # PIPEWIRE_CONFIG_DIR=${OBT_STAGE}/etc pipewire

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




