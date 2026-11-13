###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# Published under the GPL 2.0 license
###############################################################################
"""Shader Slang compiler from the user's pinned fork (not the S-Lang library).

Builds the compiler SDK, slangc, language server and shader-source backends.
DXIL/DXC and optional LLVM JIT are disabled; native SPIR-V emission is enabled.
"""
import subprocess
import sys
import os
from obt import dep, host, path, log, git_auth

VERSION = "2026.18"
REVISION = "c8ba6929456b8e9c1a097970d929f5bc003250f8"
MODULES = ["glslang", "spirv-tools", "spirv-headers", "miniz", "lz4",
           "unordered_dense", "vulkan", "cmark", "fast_float", "metal-cpp",
           "lua", "replxx", "nlohmann-json"]


class _Fetcher(dep.GithubFetcher):
  def __init__(self):
    super().__init__(name="slang", repospec="tweakoz/slang", revision="v" + VERSION,
                     recursive=False, disable_tarball=True)

  def fetch(self, dest):
    if not (dest/".git").exists() and not super().fetch(dest):
      return False
    try:
      actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dest, text=True).strip()
      if actual != REVISION:
        raise RuntimeError("Slang checkout differs from the pinned fork revision: " + actual)
      # OBT's shallow fetch checks out the commit but omits its annotated tag.
      # Slang derives ABI filenames and serialized-module compatibility from it.
      tag = "refs/tags/v" + VERSION
      environment = git_auth.environment(os.environ)
      subprocess.run(["git", "fetch", "--depth", "1", "origin", tag + ":" + tag],
                     cwd=dest, check=True, env=environment)
      tagged = subprocess.check_output(["git", "rev-parse", tag + "^{}"], cwd=dest, text=True).strip()
      if tagged != REVISION:
        raise RuntimeError("Slang release tag does not match the pinned revision")
      subprocess.run(["git", "submodule", "update", "--init", "--recursive", "--depth", "1", "--"] +
                     ["external/" + name for name in MODULES], cwd=dest, check=True, env=environment)
      return True
    except (subprocess.CalledProcessError, RuntimeError) as error:
      print("Slang fetch failed:", error)
      return False


class _Builder(dep.CMakeBuilder):
  def install(self, blddir):
    if not super().install(blddir):
      return False
    # Slang's license/notices component is EXCLUDE_FROM_ALL upstream.
    # Keep its complete metadata together instead of polluting the stage root.
    subprocess.run(["cmake", "--install", str(blddir), "--component", "metadata",
                    "--prefix", str(path.prefix()/"share"/"doc"/"Slang")], check=True)
    return True


class slang(dep.StdProvider):
  name = "slang"

  def __init__(self):
    super().__init__(self.name)
    self.setSourceRoot(path.builds()/self.name/("slang-" + VERSION))
    self.declareDep("cmake")
    self._builder = self.createBuilder(_Builder)
    self._builder.setCmVars({
      "SLANG_VERSION_FULL": VERSION,
      "SLANG_VERSION_NUMERIC": VERSION,
      "SLANG_LIB_TYPE": "SHARED",
      # Bundled helper libraries are private/static; only the Slang SDK is shared.
      "BUILD_SHARED_LIBS": "OFF",
      "SLANG_ENABLE_SLANGC": "ON",
      "SLANG_ENABLE_SLANGD": "ON",
      "SLANG_ENABLE_SLANGRT": "ON",
      "SLANG_ENABLE_SLANGI": "OFF",
      "SLANG_ENABLE_SLANG_GLSLANG": "ON",
      "SLANG_ENABLE_GFX": "OFF",
      "SLANG_ENABLE_SLANG_RHI": "OFF",
      "SLANG_ENABLE_TESTS": "OFF",
      "SLANG_ENABLE_EXAMPLES": "OFF",
      "SLANG_ENABLE_REPLAYER": "OFF",
      "SLANG_ENABLE_DXIL": "OFF",
      "SLANG_ENABLE_CUDA": "OFF",
      "SLANG_ENABLE_OPTIX": "OFF",
      "SLANG_ENABLE_NVAPI": "OFF",
      "SLANG_ENABLE_AFTERMATH": "OFF",
      "SLANG_ENABLE_XLIB": "OFF",
      "SLANG_SLANG_LLVM_FLAVOR": "DISABLE",
      "SLANG_EXCLUDE_DAWN": "ON",
      "SLANG_EXCLUDE_TINT": "ON",
      "SLANG_ENABLE_RELEASE_DEBUG_INFO": "OFF",
      "SLANG_ENABLE_SPLIT_DEBUG_INFO": "OFF",
      "SLANG_STANDARD_MODULE_DEVELOP_BUILD": "OFF",
      "Python_EXECUTABLE": sys.executable,
      "Python3_EXECUTABLE": sys.executable,
      "CMAKE_INSTALL_BINDIR": "bin",
      "CMAKE_INSTALL_LIBDIR": "lib",
      "CMAKE_POLICY_VERSION_MINIMUM": "3.5",
    })

  @property
  def _fetcher(self):
    return _Fetcher()

  def areRequiredSourceFilesPresent(self):
    if not ((self.source_root/"CMakeLists.txt").exists() and
            all((self.source_root/"external"/name/".git").exists() for name in MODULES)):
      return False
    try:
      tagged = subprocess.check_output(["git", "rev-parse", "refs/tags/v" + VERSION + "^{}"],
                                       cwd=self.source_root, text=True, stderr=subprocess.DEVNULL).strip()
      head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     cwd=self.source_root, text=True, stderr=subprocess.DEVNULL).strip()
      return tagged == REVISION and head == REVISION
    except subprocess.CalledProcessError:
      return False

  def areRequiredBinaryFilesPresent(self):
    notices = path.prefix()/"share"/"doc"/"Slang"
    required_notices = ["LICENSE", "LICENSES/Apache-2.0.txt", "LICENSES/LLVM-exception.txt",
                        "third-party-notices/cmark-COPYING", "third-party-notices/lz4-LICENSE",
                        "third-party-notices/glslang-LICENSE.txt", "third-party-notices/miniz-LICENSE",
                        "third-party-notices/unordered_dense-LICENSE", "third-party-notices/spirv-tools-LICENSE"]
    if not all((notices/name).exists() for name in required_notices):
      return False
    suffix = ".0." + VERSION + ".dylib" if host.IsOsx else ".so.0." + VERSION
    if not ((path.libs()/("libslang-compiler" + suffix)).exists() and
            (path.includes()/"slang.h").exists() and
            (path.libs()/"cmake"/"slang"/"slangConfig.cmake").exists()):
      return False
    try:
      version = subprocess.check_output([str(path.bin()/"slangc"), "-version"],
                                        text=True, stderr=subprocess.STDOUT, timeout=15)
      return VERSION in version
    except (OSError, subprocess.SubprocessError):
      return False

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()

  def env_init(self):
    log.sdk_announce("registering Slang shader compiler SDK(%s)" % VERSION)
