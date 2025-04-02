import os, tarfile
from obt import dep, host, path, make, pathtools, log
from obt.deco import Deco
from obt.wget import wget
from obt import command

VER = "0.29.2"
NAME = "pkgconfig"

class _pkgconfig_from_source(dep.StdProvider):

  def __init__(self): ############################################
    super().__init__(NAME,NAME)
    self._builder = self.createBuilder(dep.CustomBuilder)

    environ = dict()
    if host.IsDarwin and host.IsX86_64:
      environ["CC"] = "gcc-13"
      environ["CXX"] = "g++-13"

    self.scope = dep.ProviderScope.INIT
    cmd_factory_sdir = command.factory(environ={"NOCONFIGURE":1},wdir=self.source_root)
    cmd_factory_bdir = command.factory(environ=environ,wdir=self.build_dest)

    autogen = cmd_factory_sdir.cmd("./autogen.sh")
    mkdir = cmd_factory_sdir.cmd("mkdir",".build")
    configure = cmd_factory_bdir.cmd("../configure","--prefix=%s"%path.prefix(),"--with-internal-glib")
    if host.IsLinux and host.IsAARCH64:
      configure.append_args(["--build=aarch64-linux-gnu"])

    self._builder._cleanbuildcommands = [autogen,mkdir,configure]
    self.VERSION = VER

    if host.IsLinux and host.IsX86_64:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      os.system( "rm -f %s" % f2r)
    elif host.IsLinux and host.IsAARCH64:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      os.system( "rm -f %s" % f2r)

    pathtools.ensureDirectoryExists(path.pkgconfigdir())

    self._builder._incrbuildcommands += [cmd_factory_bdir.cmd("make")]
    self._builder._installcommands  = [cmd_factory_bdir.cmd("make","install")]


  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=NAME,
                             repospec="tweakoz/pkg-config",
                             revision="obt-pkg-config-%s"%VER,
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"pkg-config-guide.html").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"pkg-config").exists()
###############################################################################
class _pkgconfig_from_homebrew(dep.HomebrewProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = "homebrew"
###############################################################################
class pkgconfig(dep.switch(linux=_pkgconfig_from_source, \
                           macos=_pkgconfig_from_homebrew)):
  def __init__(self):
    super().__init__()
  def env_init(self):
    log.marker("registering pkgconfig SDK(%s)"%self.VERSION)
