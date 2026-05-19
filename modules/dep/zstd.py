###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# Zstandard — replacement for /opt/homebrew/opt/zstd on macOS.
#
# Pinned to 1.5.7 (released 2025-02-19). zstd ships a top-level CMakeLists.txt
# under build/cmake/, so we use CMakeBuilder with src_dir_override.
###############################################################################

VERSION  = "1.5.7"
BASENAME = "zstd-%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://github.com/facebook/zstd/releases/download/v%s" % VERSION
MD5      = "780fc1896922b1bc52a4e90980cdda48"

from yarl import URL
from obt import dep, path

###############################################################################

class zstd(dep.StdProvider):
    name = "zstd"

    def __init__(self):
        super().__init__(zstd.name)
        # Tarball extracts to builds/zstd/zstd-X.Y.Z/, not builds/zstd/.
        self.setSourceRoot(path.builds()/zstd.name/BASENAME)
        # zstd's top-level CMakeLists.txt lives in build/cmake/, not the repo root.
        # Both build_src and src_dir_override must point to the same dir or
        # obt.cmake.context emits a conflicting positional source-dir arg.
        self.build_src = self.source_root/"build"/"cmake"
        self._builder = self.createBuilder(
            dep.CMakeBuilder,
            src_dir_override=self.build_src,
        )
        self._builder.setCmVars({
            "ZSTD_BUILD_PROGRAMS":   "ON",
            "ZSTD_BUILD_SHARED":     "ON",
            "ZSTD_BUILD_STATIC":     "ON",
            "ZSTD_BUILD_TESTS":      "OFF",
            "ZSTD_LEGACY_SUPPORT":   "OFF",
            "ZSTD_MULTITHREAD_SUPPORT": "ON",
            # Override CMakeBuilder's macos default of
            # @executable_path/../lib so consumer build trees (e.g. llvm's
            # .build/bin/llvm-tblgen running mid-build) find libzstd via
            # rpath instead of a path hardcoded relative to their own bin.
            "CMAKE_INSTALL_NAME_DIR": "@rpath",
        })

    def __str__(self):
        return "zstd (facebook-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(zstd.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"build"/"cmake"/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libzstd.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()

    @property
    def include_dir(self):
        return path.includes()

    @property
    def lib_dir(self):
        return path.libs()
