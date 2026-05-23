###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
# pytorch — from-source build for python 3.14t (free-threaded).
#
# Pinned to upstream v2.12.0 (commit 0d62256a, 2026-05-13). 2.12.0 is the
# first release whose macOS wheels ship cp314t; we mirror that toolchain
# from source so we get a binary matched to OBT's exact pybind11 v3.0.4
# install instead of importing a pip wheel that drags in its own pybind11.
###############################################################################

import os, glob, shutil, subprocess
from yarl import URL
from obt import dep, host, path, log, command

NAME      = "pytorch"
VER       = "2.12.0"
# Official source tarball ships with all submodules bundled — one ~411 MB
# HTTPS stream instead of a recursive git clone with ~30 submodule chases.
# Drops fetch time from ~5–10 min to ~30 s on a typical residential link.
BASENAME  = "pytorch-v%s" % VER
FILENAME  = "%s.tar.gz" % BASENAME
SRC_URL   = "https://github.com/pytorch/pytorch/releases/download/v%s/%s" % (VER, FILENAME)
MD5       = "b372b5d6d201814e7be2071d1d5e8f42"

###############################################################################
# NOTE: the former `_cherrypick_torch_assets()` — which copied torch's
# headers to $OBT_STAGE/include/obt.torch and copied+RENAMED the dylibs to
# libobt.torch.* — has been removed. The rename created a SECOND libtorch
# instance: a process that both `import torch` (loads torch/lib/libtorch_*)
# and uses orkid's C++ torch integration (linked libobt.torch.*) ended up
# with two copies of libtorch's global c10 type registry → custom-class
# lookups (e.g. ConvPackedParamsBase) failed with "could not be converted
# to any of the known types". The rename's original justification — torch
# bundling a conflicting pybind11 — is moot: pytorch 2.12 builds with
# USE_SYSTEM_PYBIND11=ON against OBT's pybind11 v3.0.4. orkid now links the
# real libtorch_* at $OBT_PYPKG/torch/lib (see orkid.cmake ork_torch_opts),
# so there is exactly one libtorch per process.
###############################################################################
def _build_env():
  """Env vars consumed by pytorch's setup.py / cmake. Caller merges with
  the parent environment; Command's environment= kwarg already overlays
  on os.environ so we only return the deltas."""
  PYTHON = dep.instance("python")
  env = {
    # Feature flags
    "USE_NCCL":              "OFF",
    "USE_DISTRIBUTED":       "OFF",
    "USE_GLOO":              "OFF",
    "USE_TENSORPIPE":        "OFF",
    "USE_KINETO":            "OFF",
    "USE_OPENMP":            "ON",
    "USE_XNNPACK":           "ON",
    "USE_QNNPACK":           "OFF",
    "USE_SYSTEM_PYBIND11":   "ON",
    # Disable bundled flash-attention. pytorch 2.12's vendored flash-
    # attention still uses implicit __half→unsigned short conversions
    # which CUDA 12.8 made explicit; nvcc rejects the conversion at
    # third_party/flash-attention/csrc/flash_attn/src/*.cu. Flash-attn
    # is a perf optimization for transformer attention; not needed for
    # orkid's integration. Same applies to bundled mem-efficient attn
    # kernels (USE_MEM_EFF_ATTENTION) which share the type-conversion
    # surface.
    "USE_FLASH_ATTENTION":   "OFF",
    "USE_MEM_EFF_ATTENTION": "OFF",
    "BUILD_TEST":            "0",
    # Versioning — wheel name + torch.__version__
    "PYTORCH_BUILD_VERSION": VER,
    "PYTORCH_BUILD_NUMBER":  "1",
    # cmake discovery
    "CMAKE_PREFIX_PATH":     str(path.prefix()),
    # Throttle MAX_JOBS to avoid OOM during compile of large units (e.g.
    # ATen_cpu). pytorch's setup.py respects this when invoking ninja.
    "MAX_JOBS":              str(max(1, (os.cpu_count() or 4)//2)),
  }
  if host.IsOsx:
    env["USE_CUDA"]   = "OFF"
    env["USE_MPS"]    = "ON"
    # pytorch's cmake/Dependencies.cmake names the Apple Accelerate
    # framework "vecLib" (not "Accelerate") — anything else fails its
    # if/elseif validator with FATAL_ERROR "Unrecognized BLAS option".
    env["BLAS"]       = "vecLib"
    # FBGEMM has x86-only SIMD paths; off for Apple Silicon.
    env["USE_FBGEMM"] = "OFF"
  else:
    env["USE_MPS"]    = "OFF"
    env["BLAS"]       = "OpenBLAS"
    env["USE_FBGEMM"] = "ON"
    # CUDA — pick up an explicit CUDA_HOME from the parent env if present,
    # else probe in preference order: 12.8 → 12.6 → 12.4. The earlier
    # 12.8 attempt blew up with __half conversion errors, but that turned
    # out to be a mismatch: the Ubuntu-distro `nvidia-cuda-toolkit`
    # wrapper at /usr/bin/nvcc (12.0) was being preferred by cmake over
    # /usr/local/cuda-12.8/bin/nvcc, so we got 12.0 nvcc + 12.8 headers.
    # With nvidia-cuda-toolkit removed, a coherent 12.8 install should
    # work. Falls back to 12.6 / 12.4 if 12.8 isn't installed.
    cuda_home = os.environ.get("CUDA_HOME")
    if not cuda_home:
      for cand in ("/usr/local/cuda-12.8",
                   "/usr/local/cuda-12.6",
                   "/usr/local/cuda-12.4"):
        if os.path.exists(cand):
          cuda_home = cand
          break
      if not cuda_home:
        cuda_home = "/usr/local/cuda-12.8"  # nominal target if nothing found
    env["USE_CUDA"]   = "ON"
    env["CUDA_HOME"]  = cuda_home
    env["PATH"]       = "%s/bin:%s" % (cuda_home, os.environ.get("PATH",""))
    # Pin host C++/C compiler to gcc-12 for CUDA. On Ubuntu 24.04 the
    # default gcc-13 + glibc 2.39 combo trips nvcc's preprocessor:
    # /usr/include/x86_64-linux-gnu/bits/mathcalls.h's _Float32 /
    # _Float64x / _Float128 type uses aren't visible to nvcc's
    # compiler-id test, failing CMAKE_DETERMINE_COMPILER_ID for CUDA.
    # gcc-12 is NVIDIA's blessed pair for CUDA 12.x and avoids this.
    if os.path.exists("/usr/bin/g++-12"):
      env["CC"]          = "/usr/bin/gcc-12"
      env["CXX"]         = "/usr/bin/g++-12"
      env["CUDAHOSTCXX"] = "/usr/bin/g++-12"
    # mold linker — pytorch's build has a long serial link tail
    # (libtorch_cpu / libtorch_cuda / libtorch_python and downstream
    # exes); mold cuts that sharply.
    #
    # Must use the LDFLAGS env var, NOT CMAKE_*_LINKER_FLAGS:
    # CMAKE_{EXE,SHARED,MODULE}_LINKER_FLAGS are standard cmake variables
    # that project() defines (empty) at CMakeLists.txt:28. pytorch's
    # cmake/EnvVarForwarding.cmake runs later (line 39) and only forwards
    # env vars `if(NOT DEFINED ...)` — so it SKIPS the already-defined
    # linker-flags vars and our value is lost. cmake instead natively
    # seeds all three linker-flags vars from $ENV{LDFLAGS} during
    # project(), before EnvVarForwarding — so LDFLAGS reaches the link
    # steps. (Linux only — this is the else branch.)
    env["LDFLAGS"] = "-fuse-ld=mold"

  # Point pybind11_DIR at OBT's pybind11 v3.0.4 cmake config so
  # find_package(pybind11) under USE_SYSTEM_PYBIND11 finds ours, not
  # the system / homebrew one.
  pyb_cmake = path.prefix()/"share"/"cmake"/"pybind11"
  if pyb_cmake.exists():
    env["pybind11_DIR"] = str(pyb_cmake)

  return env

###############################################################################
def _wipe_pytorch_build_dir():
  """Run only on the clean-build path. pytorch's setup.py uses build/
  (not .build/), outside OBT's builder dir, so a stale CMakeCache.txt
  from a prior failed run silently overrides env vars like BLAS. Always
  wipe it before a clean build so env changes take effect."""
  import shutil
  src = path.builds()/NAME/BASENAME
  bdir = src/"build"
  if bdir.exists():
    log.marker("wiping stale pytorch build/ at %s" % bdir)
    shutil.rmtree(str(bdir))
  return True

###############################################################################
def _build_pytorch_wheel():
  """Run setup.py bdist_wheel in pytorch source tree, producing
  dist/torch-<VER>-cp314t-*.whl. Command() passes working_dir= via cwd=
  so this is safe under the parallel pipeline."""
  PYTHON = dep.instance("python")
  src    = path.builds()/NAME/BASENAME
  retc = command.Command(
    [str(PYTHON.executable), "setup.py", "bdist_wheel"],
    environment=_build_env(),
    working_dir=src,
  ).exec()
  return retc == 0

###############################################################################
def _pip_install_torch_wheel():
  """Find dist/torch-*.whl and pip install --no-deps. --force-reinstall
  guards against a half-completed install in site-packages from a
  previous failed run."""
  src    = path.builds()/NAME/BASENAME
  wheels = sorted(glob.glob(str(src/"dist"/"torch-*.whl")))
  if not wheels:
    log.marker("no torch wheel under %s/dist/" % src)
    return False
  whl = wheels[-1]
  log.marker("installing torch wheel: %s" % whl)
  retc = command.Command(
    ["pip3","install","--no-deps","--force-reinstall",whl],
  ).exec()
  return retc == 0

###############################################################################
class _pytorch_from_source(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = VER
    # Long-pole build (~50 min, large serial sections). Front-load it:
    # the pipeline scheduler dispatches highest build_priority first, so
    # pytorch grabs a build slot the instant its prereqs finish.
    self.build_priority = 100
    # WgetFetcher extracts the tarball into path.builds()/NAME/. The
    # archive's top-level dir is BASENAME ("pytorch-v2.12.0/"), so the
    # actual source root is one level deeper than the default.
    self.setSourceRoot(path.builds()/NAME/BASENAME)
    self.declareDep("python")
    self.declareDep("pybind11")
    self.declareDep("cmake")
    if path.has_deployment_marker:
      return
    self._builder = self.createBuilder(dep.CustomBuilder)
    # bdist_wheel produces dist/torch-*.whl in the source tree; pip
    # install --no-deps writes it into $OBT_PYPKG/torch/. orkid links the
    # real libtorch_* there directly (orkid.cmake ork_torch_opts) — no
    # cherrypick/rename step (see the NOTE above _build_env).
    self._builder._cleanbuildcommands += [ _wipe_pytorch_build_dir,
                                           _build_pytorch_wheel ]
    self._builder._incrbuildcommands  += [ _build_pytorch_wheel ]
    self._builder._installcommands    += [
      _pip_install_torch_wheel,
    ]
  ########################################################################
  @property
  def _fetcher(self):
    # Official release tarball with bundled submodules — see SRC_URL/MD5
    # constants up top. Avoids the ~5–10 min recursive git clone.
    f = dep.WgetFetcher(NAME)
    f._url     = URL(SRC_URL)
    f._fname   = FILENAME
    f._arctype = "tgz"
    f._md5     = MD5
    return f
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"setup.py").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    PYTHON = dep.instance("python")
    torch_dir = PYTHON.site_packages_dir/"torch"
    shext = "dylib" if host.IsOsx else "so"
    return (torch_dir/"__init__.py").exists() \
       and (torch_dir/"lib"/("libtorch_cpu.%s" % shext)).exists()

###############################################################################
class pytorch(dep.switch(linux=_pytorch_from_source,
                         macos=_pytorch_from_source)):
  def __init__(self):
    super().__init__()
  def env_init(self):
    log.marker("registering pytorch SDK(%s)"%self.VERSION)
