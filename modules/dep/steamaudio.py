###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# Steam Audio (libphonon) — Valve's spatial audio SDK, Apache-2.0.
#
# Built MINIMAL and proprietary-free: no Intel IPP, no Embree, no
# RadeonRays/TrueAudioNext. That leaves the built-in ray tracer and the PFFFT
# FFT path, and the three permissively-licensed libraries Steam Audio actually
# requires:
#
#   pffft       (BSD-like)  — FFT
#   libmysofa   (BSD-3)     — SOFA/HRTF dataset reader   (needs zlib)
#   zlib        (zlib)      — for libmysofa
#   flatbuffers (Apache-2.0) — HOST tool (flatc) + headers, schema compiler
#
# Those four are fetched by upstream's own dependency fetcher
# (core/build/get_dependencies.py) at the revisions pinned in
# core/build/dependencies.json. That is deliberate: Steam Audio pins its own
# dependency SHAs and its Find*.cmake modules only look in core/deps/, so the
# staging's own embree/zlib are NOT reused. We call the fetcher once per
# required dep by name (--dependency) rather than letting it walk the whole
# manifest — the unfiltered run would also clone the optional/proprietary
# entries (embree, ispc, radeonrays, trueaudionext, glfw, imgui, portaudio,
# doxygen) and then exit(1) because they failed.
#
# Two upstream quirks worth knowing:
#  - get_dependencies.py does os.chdir('..') on startup, so it MUST be invoked
#    with cwd = core/build, not core/.
#  - core/CMakeLists.txt does a plain (non-CACHE) set(CMAKE_OSX_ARCHITECTURES
#    "x86_64;arm64"), which shadows anything passed with -D. The macOS build is
#    therefore always universal; that matches the deps, which upstream's
#    fetcher also builds universal. arm64 slice is what this box consumes.
#  - the pinned flatbuffers (v2.0.0-era) trips GCC 13's -Wstringop-overflow in
#    reflection.cpp AddFlatBuffer (the well-known false positive on
#    std::vector::insert after a reserve), and flatbuffers compiles with
#    -Werror, so that warning is fatal. On Linux we demote EXACTLY that
#    diagnostic for the vendored dep builds via CXXFLAGS — see
#    LINUX_DEP_CXXFLAGS below. CXXFLAGS only seeds CMAKE_CXX_FLAGS on a build
#    dir's FIRST configure, and upstream's fetcher reconfigures in place, so
#    changed build settings invalidate both the upstream output stamps and
#    CMake caches rather than trusting the env to take.
#  - upstream's Linux AVX path compiles with -fabi-version=6, which also turns
#    off P0136 inheriting constructors and thereby breaks libstdc++ 13's own
#    headers. LINUX_CORE_CXXFLAGS puts that one ABI bit back.
#
# Install: upstream installs to <prefix>/lib/<platform-subdir>/ plus a macOS
# phonon.bundle. We install into a private prefix under builds/ and then place
# just the flat artifacts into the staging: libphonon.<ext> in lib/, and
# phonon.h + phonon_version.h + phonon_interfaces.h in include/.
#
# macOS install name is forced ABSOLUTE (same call hdf5.py makes, same reason):
# the consumers include the pyvenv interpreter at <staging>/pyvenv/bin/python
# via ctypes, for which the usual @executable_path/../lib would resolve to
# <staging>/pyvenv/lib — the wrong place.
###############################################################################

import os, sys, json, shutil
from yarl import URL
from obt import dep, host, path, log, pathtools
from obt.command import Command

NAME     = "steamaudio"
VERSION  = "4.8.1"
BASENAME = "steam-audio-%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://github.com/ValveSoftware/steam-audio/archive/refs/tags"
MD5      = "633a1d52d4350d3ce8aa4c199c22b7c4"

# fetched by upstream's fetcher, in dependency order (mysofa needs zlib)
REQUIRED_DEPS = ["zlib", "mysofa", "pffft", "flatbuffers"]

# GCC-13-only concession for the vendored deps build (Linux). Scoped to the one
# diagnostic; everything else stays warning-as-error exactly as upstream wants.
LINUX_DEP_CXXFLAGS = "-Wno-error=stringop-overflow"

# core/CMakeLists.txt adds -fabi-version=6 on Linux whenever AVX is enabled (it
# is, by default) to keep the pre-GCC-4.9 __m256 argument passing ABI. ABI v6
# also predates P0136, so it turns OFF -fnew-inheriting-ctors — and libstdc++ 13
# REQUIRES the P0136 semantics: <future>, <memory> et al fail to compile with
# "no matching function for call to __uniq_ptr_data()" because the inherited
# default constructor of std::__uniq_ptr_impl goes missing. Re-enable just that
# one ABI bit; the vector-argument ABI upstream cares about is untouched. Order
# on the command line does not matter (gcc resolves an explicit
# -fnew-inheriting-ctors after all -fabi-version handling), which is what lets
# this ride in CMAKE_CXX_FLAGS ahead of upstream's add_compile_options.
LINUX_CORE_CXXFLAGS = "-fnew-inheriting-ctors"

###############################################################################

def _src_root():
    return path.builds()/NAME/BASENAME

def _core_dir():
    return _src_root()/"core"

# build + private install prefix live INSIDE the extracted source root, so a
# source wipe (or a re-fetch, which clears builds/steamaudio entirely) cannot
# leave a stale cmake cache pointing at a deleted source tree
def _build_dir():
    return _src_root()/".build"

def _priv_prefix():
    return _src_root()/".install"

###############################################################################
# upstream platform naming (core/build/get_dependencies.py and
# SteamAudioHelpers.cmake get_bin_subdir agree on these)
###############################################################################

def _platform_args():
    if host.IsOsx:
        return ["-p", "osx"]
    return ["-p", "linux", "-a", "arm64" if host.IsAARCH64 else "x64"]

def _bin_subdir():
    if host.IsOsx:
        return "osx"
    return "linux-arm64" if host.IsAARCH64 else "linux-x64"

###############################################################################

def _dep_cxxflags():
    """CXXFLAGS handed to upstream's dep builder (env, inherited by its cmakes)."""
    if not host.IsLinux:
        return None
    inherited = os.environ.get("CXXFLAGS", "").strip()
    return ("%s %s" % (inherited, LINUX_DEP_CXXFLAGS)).strip()

def _dependency_driver():
    """Adapt the upstream cross-build driver only for native Linux ARM64.

    Keep the downloaded source untouched. The generated driver still uses
    upstream's pinned dependency recipes, but host tools and target libraries
    both belong to linux-arm64 and use the native compiler/SDK search paths.
    """
    original = _core_dir()/"build"/"get_dependencies.py"
    if not (host.IsLinux and host.IsAARCH64):
        return original
    text = original.read_text()
    changes = {
        "host_platform = 'linux-x64'": "host_platform = 'linux-arm64'",
        "toolchain('linux_arm64')": "toolchain('obt_native_linux_arm64')",
    }
    for before, after in changes.items():
        if text.count(before) != 1:
            raise RuntimeError("Steam Audio native ARM adaptation: upstream driver changed: " + before)
        text = text.replace(before, after)
    native = _core_dir()/"build"/"toolchain_obt_native_linux_arm64.cmake"
    native.write_text("# OBT native ARM64: use host compilers; no cross sysroot.\n")
    generated = original.with_name("_obt_get_dependencies.py")
    generated.write_text("# Generated by OBT from Valve's Apache-2.0 dependency driver.\n"
                         "# Changes: native Linux ARM64 host identity and toolchain.\n" + text)
    return generated


def _dependency_settings(env):
    keys = ("CC", "CXX", "CFLAGS", "CXXFLAGS", "LDFLAGS", "SDKROOT",
            "MACOSX_DEPLOYMENT_TARGET")
    return {"platform": _bin_subdir(), "native_arm_driver": bool(host.IsLinux and host.IsAARCH64),
            "environment": {key: env.get(key, os.environ.get(key)) for key in keys}}


def _invalidate_dependency_settings(settings):
    """Invalidate upstream output stamps as well as CMake's cached flags.

    Upstream skips a completed dependency using core/deps/*/stamp, without
    looking at its build cache or inherited environment. Record settings only
    after every dependency succeeds, so a failed attempt is safely retried.
    """
    marker = _core_dir()/".obt-dependency-settings.json"
    try:
        if json.loads(marker.read_text()) == settings:
            return marker
    except (FileNotFoundError, ValueError):
        pass
    for item in REQUIRED_DEPS:
        cache = _core_dir()/"deps-build"/item/"build"/_bin_subdir()/"CMakeCache.txt"
        stamp = _core_dir()/"deps"/item/"stamp"/_bin_subdir()/".configureinfo"
        # Compiler/toolchain detection also lives here; a previous cross-build
        # must not seed the next native configure after its cache is removed.
        generated = cache.parent/"CMakeFiles"
        if generated.exists():
            shutil.rmtree(generated)
        for stale in (cache, stamp):
            if stale.exists():
                stale.unlink()
    return marker

def _macos_build_env():
    # Upstream uses the Xcode generator: select an SDK bundled with Xcode,
    # not the external CLT SDK used by our CPython build. Xcode 27 requires
    # a deployment target of at least macOS 12.
    sdk = Command(["xcrun", "--sdk", "macosx", "--show-sdk-path"],
                  do_log=False).capture().strip()
    if not sdk:
        raise RuntimeError("Steam Audio: cannot resolve the Xcode macOS SDK")
    return {"SDKROOT": sdk, "MACOSX_DEPLOYMENT_TARGET": "12.0"}

def _fetch_sa_deps():
    """Fetch + build the four required third-party libs into core/deps."""
    env = _macos_build_env() if host.IsOsx else {}
    cxxflags = _dep_cxxflags()
    if cxxflags is not None:
        env["CXXFLAGS"] = cxxflags
    driver = _dependency_driver()
    settings = _dependency_settings(env)
    marker = _invalidate_dependency_settings(settings)
    for item in REQUIRED_DEPS:
        log.marker("steamaudio: fetching upstream dep <%s>" % item)
        rc = Command([sys.executable, str(driver)]
                     + _platform_args()
                     + ["--dependency", item],
                     environment=env,
                     working_dir=_core_dir()/"build").exec()
        if rc != 0:
            log.marker("steamaudio: upstream dep <%s> FAILED" % item)
            return False
    marker.write_text(json.dumps(settings, sort_keys=True) + "\n")
    return True

###############################################################################

def _cmake_vars():
    vars = {
        "CMAKE_BUILD_TYPE":                "Release",
        "BUILD_SHARED_LIBS":               "ON",
        "CMAKE_INSTALL_PREFIX":            str(_priv_prefix()),
        # minimal: no unit tests, benchmarks, samples, docs
        "STEAMAUDIO_BUILD_TESTS":          "OFF",
        "STEAMAUDIO_BUILD_BENCHMARKS":     "OFF",
        "STEAMAUDIO_BUILD_SAMPLES":        "OFF",
        "STEAMAUDIO_BUILD_DOCS":           "OFF",
        # proprietary-free: no IPP, no Embree, no RadeonRays, no TrueAudioNext
        "STEAMAUDIO_ENABLE_IPP":           "OFF",
        "STEAMAUDIO_ENABLE_MKL":           "OFF",
        "STEAMAUDIO_ENABLE_EMBREE":        "OFF",
        "STEAMAUDIO_ENABLE_RADEONRAYS":    "OFF",
        "STEAMAUDIO_ENABLE_TRUEAUDIONEXT": "OFF",
    }
    if host.IsLinux:
        vars["CMAKE_CXX_FLAGS"] = LINUX_CORE_CXXFLAGS
        if host.IsAARCH64:
            # Upstream get_host_bin_subdir assumes every Linux host is x64.
            vars["FlatBuffers_EXECUTABLE"] = str(_core_dir()/"deps"/"flatbuffers"/
                                                "bin"/"linux-arm64"/"flatc")
    elif host.IsOsx:
        build_env = _macos_build_env()
        vars["CMAKE_OSX_SYSROOT"] = build_env["SDKROOT"]
        vars["CMAKE_OSX_DEPLOYMENT_TARGET"] = build_env["MACOSX_DEPLOYMENT_TARGET"]
    return vars

def _configure():
    # plain makefiles, not Ninja: ninja is not a staging dep, and upstream's
    # own dep fetcher already uses the stock generator per platform
    args = ["cmake", "-S", str(_core_dir()), "-B", str(_build_dir()),
            "-G", "Unix Makefiles"]
    for k, v in _cmake_vars().items():
        args += ["-D%s=%s" % (k, v)]
    return 0 == Command(args, working_dir=_src_root()).exec()

def _compile():
    return 0 == Command(["cmake", "--build", str(_build_dir()),
                         "--parallel", str(host.NumCores)],
                        working_dir=_src_root()).exec()

###############################################################################

def _license_sources():
    sources = {"LICENSE.md": _src_root()/"LICENSE.md",
               "THIRDPARTY.md": _core_dir()/"THIRDPARTY.md"}
    for item, filename in (("zlib", "LICENSE"), ("mysofa", "LICENSE"),
                           ("pffft", "LICENSE.txt"), ("flatbuffers", "LICENSE.txt")):
        sources[item + "-" + filename] = _core_dir()/"deps-build"/item/"src"/item/filename
    return sources


def _install_notices():
    destination = path.prefix()/"share"/"doc"/"steamaudio"
    destination.mkdir(parents=True, exist_ok=True)
    for name, source in _license_sources().items():
        shutil.copy2(source, destination/name)


def _install():
    rc = Command(["cmake", "--install", str(_build_dir())],
                 working_dir=_src_root()).exec()
    if rc != 0:
        return False

    shlib = "libphonon.%s" % ("dylib" if host.IsOsx else "so")
    src_lib = _priv_prefix()/"lib"/_bin_subdir()/shlib
    if not src_lib.exists():
        log.marker("steamaudio: expected library missing: %s" % src_lib)
        return False

    dst_lib = path.libs()/shlib
    pathtools.mkdir(path.libs(), clean=False, parents=True)
    pathtools.mkdir(path.includes(), clean=False, parents=True)
    if 0 != Command(["cp", "-f", str(src_lib), str(dst_lib)]).exec():
        return False

    for header in ["phonon.h", "phonon_version.h", "phonon_interfaces.h"]:
        src_hdr = _priv_prefix()/"include"/header
        if not src_hdr.exists():
            log.marker("steamaudio: expected header missing: %s" % src_hdr)
            return False
        if 0 != Command(["cp", "-f", str(src_hdr), str(path.includes()/header)]).exec():
            return False

    if host.IsOsx:
        # absolute install name — see header comment
        if 0 != Command(["install_name_tool", "-id", str(dst_lib), str(dst_lib)]).exec():
            return False

    _install_notices()
    log.marker("steamaudio: installed %s" % dst_lib)
    return True

###############################################################################

class steamaudio(dep.StdProvider):
    name = NAME

    def __init__(self):
        super().__init__(NAME)
        self.VERSION = VERSION
        self.declareDep("cmake")
        if path.has_deployment_marker:
            return
        # tarball extracts to builds/steamaudio/steam-audio-X.Y.Z/
        self.setSourceRoot(_src_root())
        self._builder = self.createBuilder(dep.CustomBuilder)
        self._builder._cleanbuildcommands += [_fetch_sa_deps, _configure, _compile]
        self._builder._incrbuildcommands  += [_fetch_sa_deps, _configure, _compile]
        self._builder._installcommands    += [_install]

    def __str__(self):
        return "steamaudio (valve-source-%s)" % VERSION

    ###########################################################################
    # _fetcher is a property: must be built fully in the getter, since
    # writes to a property's return value are discarded.
    ###########################################################################

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(NAME)
        f._url     = URL(URL_BASE)/("v%s.tar.gz" % VERSION)
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"core"/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        notices = path.prefix()/"share"/"doc"/"steamaudio"
        return ((path.libs()/("libphonon.%s" % self.shlib_extension)).exists()
                and all((notices/name).is_file() for name in _license_sources()))

    @property
    def should_build(self):
        return super().should_build or not self.areRequiredBinaryFilesPresent()

    ###########################################################################
    # consumer-facing properties
    ###########################################################################

    @property
    def root(self):
        return path.prefix()

    @property
    def include_dir(self):
        return path.includes()

    @property
    def lib_dir(self):
        return path.libs()
