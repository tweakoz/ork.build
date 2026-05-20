###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# torchaudio — built from source against the OBT-built pytorch (v2.12.0).
# Pinned to upstream v2.11.0 (commit 34c52a67, 2026-03-23). torchaudio
# trails the main torch release cadence; 2.11.0 is the latest tagged
# release as of 2026-05-18 and is backwards-compatible with torch 2.12.0.
#
# Uses OBT-provided ffmpeg + sox. BUILD_SOX=0 prevents torchaudio's setup
# from trying to download/build its own bundled sox; USE_SOX=1 enables
# the sox backend, finding OBT's libsox via CMAKE_PREFIX_PATH.
###############################################################################

import os, glob
from obt import dep, host, path, log, command

NAME      = "torchaudio"
VER       = "2.11.0"
GIT_SPEC  = "tweakoz/pytorch-audio"
GIT_REV   = "34c52a67e8941bbd8e6adaca0eb0b9eabec11d78"  # upstream v2.11.0

###############################################################################
def _build_env():
  env = {
    "USE_CUDA":          "0",
    "USE_ROCM":          "0",
    "USE_FFMPEG":        "1",
    "USE_SOX":           "1",
    # Do NOT download a bundled sox; use OBT's libsox already on
    # CMAKE_PREFIX_PATH. Same for kaldi-formatted feature extractors.
    "BUILD_SOX":         "0",
    "BUILD_KALDI":       "0",
    "BUILD_RNNT":        "1",
    "BUILD_CTC_DECODER": "0",
    # Wheel naming
    "BUILD_VERSION":     VER,
    "CMAKE_PREFIX_PATH": str(path.prefix()),
    "MAX_JOBS":          str(max(1, (os.cpu_count() or 4)//2)),
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
  wheels = sorted(glob.glob(str(src/"dist"/"torchaudio-*.whl")))
  if not wheels:
    log.marker("no torchaudio wheel under %s/dist/" % src)
    return False
  whl = wheels[-1]
  log.marker("installing torchaudio wheel: %s" % whl)
  retc = command.Command(
    ["pip3","install","--no-deps","--force-reinstall",whl],
  ).exec()
  return retc == 0

###############################################################################
class torchaudio(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = VER
    self.declareDep("python")
    self.declareDep("pytorch")
    self.declareDep("ffmpeg")
    self.declareDep("sox")
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
    # stream instead of a full git clone. torchaudio has no submodules
    # we depend on, so auto-tarball is sufficient.
    return dep.GithubFetcher(
      name=NAME,
      repospec=GIT_SPEC,
      revision=GIT_REV,
      md5val="c036e27f61347b69bbb6c76d00897716",
      recursive=False,
    )
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"setup.py").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    PYTHON = dep.instance("python")
    return (PYTHON.site_packages_dir/"torchaudio"/"__init__.py").exists()
  ########################################################################
  def env_init(self):
    log.marker("registering torchaudio SDK(%s)"%self.VERSION)
