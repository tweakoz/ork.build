###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# torchvision — built from source against the OBT-built pytorch (v2.12.0).
# Pinned to upstream v0.27.0 (commit 78839c2b, 2026-05-13), the release
# paired with torch v2.12.0.
#
# Uses OBT-provided libjpeg-turbo / libpng / ffmpeg. NVJPEG and CUDA
# video-codec extensions stay off (macOS or CPU Linux).
###############################################################################

import os, glob
from obt import dep, host, path, log, command

NAME      = "torchvision"
VER       = "0.27.0"
GIT_SPEC  = "tweakoz/pytorch-vision"
GIT_REV   = "78839c2b06c83c6cfb5c4da692ffb331bbd4c4cc"  # upstream v0.27.0

###############################################################################
def _build_env():
  env = {
    "FORCE_CUDA":                  "0",
    "TORCHVISION_USE_NVJPEG":      "0",
    "TORCHVISION_USE_VIDEO_CODEC": "0",
    "TORCHVISION_USE_FFMPEG":      "1",
    # Wheel naming
    "BUILD_VERSION":               VER,
    # Header / lib discovery for jpegturbo, libpng, ffmpeg
    "CMAKE_PREFIX_PATH":           str(path.prefix()),
    "MAX_JOBS":                    str(max(1, (os.cpu_count() or 4)//2)),
  }
  return env

###############################################################################
def _build_wheel():
  PYTHON = dep.instance("python")
  src    = path.builds()/NAME
  retc = command.Command(
    [str(PYTHON.executable), "setup.py", "bdist_wheel"],
    environment=_build_env(),
    working_dir=src,
  ).exec()
  return retc == 0

###############################################################################
def _pip_install_wheel():
  src    = path.builds()/NAME
  wheels = sorted(glob.glob(str(src/"dist"/"torchvision-*.whl")))
  if not wheels:
    log.marker("no torchvision wheel under %s/dist/" % src)
    return False
  whl = wheels[-1]
  log.marker("installing torchvision wheel: %s" % whl)
  retc = command.Command(
    ["pip3","install","--no-deps","--force-reinstall",whl],
  ).exec()
  return retc == 0

###############################################################################
class torchvision(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = VER
    self.declareDep("python")
    self.declareDep("pytorch")
    self.declareDep("jpegturbo")
    self.declareDep("libpng")
    self.declareDep("ffmpeg")
    if path.has_deployment_marker:
      return
    self._builder = self.createBuilder(dep.CustomBuilder)
    self._builder._cleanbuildcommands += [ _build_wheel ]
    self._builder._incrbuildcommands  += [ _build_wheel ]
    self._builder._installcommands    += [ _pip_install_wheel ]
  ########################################################################
  @property
  def _fetcher(self):
    # recursive=False + GithubFetcher's default shallow=True enables the
    # tarball path (auto-generated /tarball/<sha> endpoint) — one HTTPS
    # stream instead of a full git clone. torchvision has no submodules
    # we depend on, so auto-tarball is sufficient.
    return dep.GithubFetcher(
      name=NAME,
      repospec=GIT_SPEC,
      revision=GIT_REV,
      md5val="e45298889651b43c4ee0af1d7f2a5734",
      recursive=False,
    )
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"setup.py").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    PYTHON = dep.instance("python")
    return (PYTHON.site_packages_dir/"torchvision"/"__init__.py").exists()
  ########################################################################
  def env_init(self):
    log.sdk_announce("registering torchvision SDK(%s)"%self.VERSION)
