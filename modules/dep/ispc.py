###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path, env, log
from obt.path import Path
from obt.command import Command
from obt.deco import Deco
from yarl import URL
import re
import shutil
import subprocess
deco = Deco()

###############################################################################

class _ispc_from_source(dep.StdProvider):
  name = "ispc"
  def __init__(self):
    super().__init__(_ispc_from_source.name)
    self._archlist = ["x86_64"]
    self.llvm = dep.instance("llvm")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.requires([self.llvm])
    if host.IsOsx:
      self._builder.setCmVar("BISON_EXECUTABLE",path.macos_brew_opt/"bison"/"bin"/"bison")
  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GitFetcher(_ispc_from_source.name)
    fetcher._git_url = "https://github.com/ispc/ispc"
    fetcher._cache=False,
    fetcher._recursive=False
    fetcher._revision = "v1.13.0"
    return fetcher

###############################################################################

class _ispc_from_homebrew(dep.HomebrewProvider):
  name = "ispc"
  def __init__(self):
    super().__init__(_ispc_from_homebrew.name,_ispc_from_homebrew.name)
    self._archlist = ["x86_64"]
  def env_init(self):
    binary = self.brew_prefix()/"bin"/"ispc"
    version = ""
    log.sdk_announce("registering ispc SDK (%s)"%version)
    env.set("ISPC",binary)

###############################################################################
# prebuilt upstream release binaries.
#  keyed by (os,arch) -> (version, release-basename, md5-of-tarball)
#  the aarch64/macOS entry is what supplies the neon-* ispc targets
#   OIDN 2.5 needs ISPC >=1.30; both staged releases use 1.31.
###############################################################################

_ISPC_RELEASES = {
  ("linux","x86_64")  : ("v1.31.0", "ispc-v1.31.0-linux",       "72e6617e85e8d4f792b91efaf5715d4d"),
  ("macos","aarch64") : ("v1.31.0", "ispc-v1.31.0-macOS.arm64", "cd0083aa173d274d81f27f851263a7b2"),
}

class _ispc_from_wget(dep.StdProvider):
  name = "ispc"
  def __init__(self):
    super().__init__(_ispc_from_wget.name)
    oskey = "macos" if host.IsOsx else "linux"
    archkey = "aarch64" if host.IsAARCH64 else "x86_64"
    # only advertise the arches we actually have a pinned release for
    self._archlist = [a for (o,a) in _ISPC_RELEASES.keys() if o==oskey]
    entry = _ISPC_RELEASES.get((oskey,archkey),_ISPC_RELEASES[("linux","x86_64")])
    self._version, basename, self._md5 = entry
    self.filename = "%s.tar.gz" % basename
    self._builder = dep.BinInstaller(_ispc_from_wget.name)
    self.src_dir = path.builds()/"ispc"/basename
    dst_dir = path.stage()
    self._builder.install_item(source=self.src_dir/"bin"/"ispc", \
                               destination=dst_dir/"bin"/"ispc")
  ########################################################################
  @property
  def _fetcher(self):
    baseurl = URL("https://github.com/ispc/ispc/releases/download")
    fetcher = dep.WgetFetcher(_ispc_from_wget.name)
    fetcher._url = baseurl/self._version/self.filename
    fetcher._fname = self.filename
    fetcher._arctype = "tgz"
    fetcher._md5 = self._md5
    return fetcher

  ########################################################################
  def env_init(self):
    log.sdk_announce("registering ispc(%s) SDK"%self._version)
    env.set("ISPC",path.stage()/"bin"/"ispc")

  def install(self):
    if not self._builder.install(None):
      return False
    # ISPC resolves AMX and other standard-library headers relative to bin/.
    shutil.copytree(self.src_dir/"include", path.includes(), dirs_exist_ok=True)
    notices = path.stage()/"share"/"doc"/"ispc"
    notices.mkdir(parents=True, exist_ok=True)
    shutil.copy2(self.src_dir/"LICENSE.txt", notices/"LICENSE.txt")
    return True

  def areRequiredSourceFilesPresent(self):
    return (self.src_dir/"LICENSE.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    if not (path.stage()/"share"/"doc"/"ispc"/"LICENSE.txt").is_file():
      return False
    if not (path.includes()/"stdlib"/"amx.isph").exists():
      return False
    try:
      output = subprocess.check_output([str(path.bin()/"ispc"), "--version"],
                                       text=True, stderr=subprocess.STDOUT, timeout=10)
      match = re.search(r"\b(\d+\.\d+\.\d+)\b", output)
      return bool(match and tuple(map(int, match.group(1).split("."))) >=
                  tuple(map(int, self._version.lstrip("v").split("."))))
    except (OSError, subprocess.SubprocessError):
      return False

  @property
  def should_build(self):
    # An older binary plus an old manifest must not satisfy a bumped release.
    return super().should_build or not self.areRequiredBinaryFilesPresent()

###############################################################################
# homebrew's ispc is x86_64-only here and drags in llvm@22; on apple silicon
#  take the upstream prebuilt arm64 release instead (self-contained, no llvm dep)
###############################################################################

if host.IsOsx and host.IsAARCH64:
  BASE = _ispc_from_wget
else:
  BASE = dep.switch(linux=_ispc_from_wget,
                    macos=_ispc_from_homebrew)

class ispc(BASE):
  def __init__(self):
    super().__init__()

  @property
  def executable(self):
    if host.IsOsx and not host.IsAARCH64:
      return self.brew_prefix()/"bin"/"ispc"
    return path.bin()/"ispc"
