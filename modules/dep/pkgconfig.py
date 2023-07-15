import os, tarfile
from obt import dep, host, path, make, pathtools
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

VER = "0.29.2"
HASH = "f6e931e319531b736fadc017f470e68a"

class pkgconfig(dep.Provider):

  def __init__(self): ############################################
    super().__init__("pkgconfig")
    self.scope = dep.ProviderScope.INIT
    self.manifest = path.manifests()/"pkgconfig"
    self.extract_dir = path.builds()/"pkgconfig"
    self.source_dir = self.extract_dir/("pkg-config-%s" % VER)
    self.build_dir = self.source_dir/".build"
    self.url = "http://pkgconfig.freedesktop.org/releases/pkg-config-%s.tar.gz" % VER

    self.OK = self.manifest.exists()

  def build(self): ##########################################################
    self.arcpath = dep.downloadAndExtract([self.url],
                                          "pkg-config-%s" % VER,
                                          "gz",
                                          HASH,
                                          self.extract_dir)


    self.build_dir.mkdir()
    self.build_dir.chdir()

    conf_cmd = [
      "../configure",
      "--prefix=%s"%path.prefix(),
      "--with-internal-glib"
    ]
    if host.IsLinux and host.IsAARCH64:
      conf_cmd += ["--build=aarch64-linux-gnu"]

    self.OK = (Command(conf_cmd).exec()==0)

    #assert(False)

    if host.IsLinux and host.IsX86_64:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      os.system( "rm -f %s" % f2r)
    elif host.IsLinux and host.IsAARCH64:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      os.system( "rm -f %s" % f2r)

    pathtools.ensureDirectoryExists(path.pkgconfigdir())

    if self.OK:
      self.OK = (make.exec( "install" )==0)

    return self.OK
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_dir/"config.guess").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"pkg-config").exists()
