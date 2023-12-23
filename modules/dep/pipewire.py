###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, log, path, template
from obt import command 
###############################################################################
class pipewire(dep.StdProvider):
  name = "pipewire"
  def __init__(self):
    super().__init__(pipewire.name)
    self._builder = self.createBuilder(dep.CustomBuilder)

    def configure_pw(key,val):
      f2 = command.factory(prefix=["meson","configure",".build"],wdir=self.source_root)
      self._builder._incrbuildcommands += [f2.cmd("-D%s=%s"%(key,str(val)))]

    pw_meson = command.factory(prefix=["meson"],wdir=self.source_root)
    self._builder._cleanbuildcommands = [pw_meson.cmd("setup",".build")]
    configure_pw("prefix",path.stage())
    configure_pw("systemd-user-service","disabled")
    configure_pw("session-managers","['wireplumber']")
    configure_pw("udevrulesdir",path.stage()/"udevrules")
    configure_pw("includedir",path.stage()/"include")
    configure_pw("dbus","disabled")
    configure_pw("alsa","enabled")
    #configure_pw("pipewire-alsa","enabled")
    configure_pw("libdir",path.stage()/"lib")
    
    
    # systemd-system-unit-dir : /usr/lib/systemd/system
    # systemd-user-unit-dir   : /usr/lib/systemd/user
    # udevrulesdir : /lib/udev/rules.d

    self._builder._incrbuildcommands += [pw_meson.cmd("configure",".build")]
    if True:
      self._builder._incrbuildcommands += [pw_meson.cmd("compile","-C",".build")]
      self._builder._installcommands  = [pw_meson.cmd("install","-C",".build")]

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




