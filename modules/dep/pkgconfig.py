import os, tarfile
from obt import dep, host, path, make, pathtools, log
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

VER = "0.29.2"
HASH = "f6e931e319531b736fadc017f470e68a"

class _pkgconfig_from_source(dep.Provider):

  def __init__(self,name): ############################################
    super().__init__(name,name)
    self.scope = dep.ProviderScope.INIT
    self.extract_dir = path.builds()/"pkgconfig"
    self.source_dir = self.extract_dir/("pkg-config-%s" % VER)
    self.build_dir = self.source_dir/".build"
    self.url = "http://pkgconfig.freedesktop.org/releases/pkg-config-%s.tar.gz" % VER
    self.VERSION = VER

  def build(self): ##########################################################
    self.arcpath = dep.downloadAndExtract([self.url],
                                          "pkg-config-%s.gz" % VER,
                                          "gz",
                                          HASH,
                                          self.extract_dir)


    self.build_dir.mkdir()
    self.build_dir.chdir()

    environ = dict()

    conf_cmd = [
      "../configure",
      "--prefix=%s"%path.prefix(),
      "--with-internal-glib"
    ]

    if host.IsDarwin and host.IsX86_64:
      environ["CC"] = "gcc-13"
      environ["CXX"] = "g++-13"

    if host.IsLinux and host.IsAARCH64:
      conf_cmd += ["--build=aarch64-linux-gnu"]

    OK = (Command(conf_cmd,environment=environ).exec()==0)

    #assert(False)

    if host.IsLinux and host.IsX86_64:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      os.system( "rm -f %s" % f2r)
    elif host.IsLinux and host.IsAARCH64:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      os.system( "rm -f %s" % f2r)

    pathtools.ensureDirectoryExists(path.pkgconfigdir())

    if OK:
      OK = (make.exec( "install" )==0)

    return OK
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_dir/"config.guess").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"pkg-config").exists()
###############################################################################
class _pkgconfig_from_homebrew(dep.HomebrewProvider):
  def __init__(self,name):
    super().__init__(name,name)
    self.VERSION = "homebrew"
###############################################################################
class pkgconfig(dep.switch(linux=_pkgconfig_from_source, \
                           macos=_pkgconfig_from_homebrew)):
  def __init__(self):
    super().__init__("pkgconfig")
  def env_init(self):
    log.marker("registering pkgconfig SDK(%s)"%self.VERSION)
