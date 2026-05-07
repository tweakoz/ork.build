###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# xxhash — replacement for /opt/homebrew/opt/xxhash. Used by ork.core
# (CMakeLists.txt:82). Has Makefile + cmake — using cmake (under cmake_unofficial).
###############################################################################

VERSION  = "0.8.3"
BASENAME = "xxHash-%s" % VERSION
FILENAME = "v%s.tar.gz" % VERSION
URL_BASE = "https://github.com/Cyan4973/xxHash/archive/refs/tags"
MD5      = "599804eb9555e51c05f1b821f9212a07"

from yarl import URL
from obt import dep, path

class xxhash(dep.StdProvider):
    name = "xxhash"

    def __init__(self):
        super().__init__(xxhash.name)
        self.setSourceRoot(path.builds()/xxhash.name/BASENAME)
        # xxHash's cmake project lives in cmake_unofficial/, not the repo root.
        self.build_src = self.source_root/"cmake_unofficial"
        self.declareDep("cmake")
        self._builder = self.createBuilder(
            dep.CMakeBuilder,
            src_dir_override=self.build_src,
        )
        self._builder.setCmVars({
            "BUILD_SHARED_LIBS":   "ON",
            "XXHASH_BUILD_XXHSUM": "ON",
            "XXHASH_BUILD_TESTS":  "OFF",
        })

    def __str__(self):
        return "xxhash (Cyan4973-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(xxhash.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"cmake_unofficial"/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libxxhash.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
