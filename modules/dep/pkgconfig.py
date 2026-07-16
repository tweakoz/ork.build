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

    if host.IsLinux:
      f2r = path.stage()/"bin"/"x86_64-unknown-linux-gnu-pkg-config"
      try:
        f2r.unlink(missing_ok=True)
      except OSError:
        # Read-only deployed stage (e.g. a Flatpak /app): this INIT-scope
        # cleanup is a build-time concern; nothing to remove at runtime.
        pass

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
# macOS: pkgconfig is being severed from the macOS build. Its only macOS
# provider used to be a HomebrewProvider (`brew install pkg-config`) — a
# homebrew touch we're eliminating. On macOS, cmake's find_package config
# files + system frameworks cover what pkg-config did; the rare autotools
# dep that genuinely needs it sets PKG_CONFIG=/usr/bin/true (see sox.py).
#
# This guard provider asserts if any dep still pulls pkgconfig into a
# macOS build — a deliberate tripwire while we remove the last
# declareDep("pkgconfig") / requires(["pkgconfig"]) call sites.
###############################################################################
class _pkgconfig_macos_forbidden(dep.Provider):
  def __init__(self):
    super().__init__(NAME)
    self.VERSION = "macos-forbidden"
  def build(self):
    assert False, (
      "pkgconfig must not be used on macOS — a dependency still declares "
      "it as a prereq. Find the offending declareDep('pkgconfig') / "
      "requires(['pkgconfig']) and remove it. cmake find_package config "
      "files cover macOS; autotools deps that truly need pkg-config set "
      "PKG_CONFIG=/usr/bin/true (see sox.py). See pkgconfig.py.")
  def areRequiredSourceFilesPresent(self):
    return True
  def areRequiredBinaryFilesPresent(self):
    return True
###############################################################################
class pkgconfig(dep.switch(linux=_pkgconfig_from_source, \
                           macos=_pkgconfig_macos_forbidden)):
  def __init__(self):
    super().__init__()
  def env_init(self):
    log.sdk_announce("registering pkgconfig SDK(%s)"%self.VERSION)
