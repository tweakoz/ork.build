###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libdeflate — replacement for /opt/homebrew/opt/libdeflate. Used by OpenEXR's
# OpenEXRCore for fast deflate compression (faster than zlib).
###############################################################################

VERSION  = "1.25"
BASENAME = "libdeflate-%s" % VERSION
FILENAME = "v%s.tar.gz" % VERSION
URL_BASE = "https://github.com/ebiggers/libdeflate/archive/refs/tags"
MD5      = "d64c5bb82c3757dd588972b30c3a97b6"

from yarl import URL
from obt import dep, path

###############################################################################

class libdeflate(dep.StdProvider):
    name = "libdeflate"

    def __init__(self):
        super().__init__(libdeflate.name)
        # Tarball extracts as libdeflate-<VERSION>/.
        self.setSourceRoot(path.builds()/libdeflate.name/BASENAME)
        self.declareDep("cmake")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "LIBDEFLATE_BUILD_SHARED_LIB": "ON",
            "LIBDEFLATE_BUILD_STATIC_LIB": "ON",
            "LIBDEFLATE_BUILD_GZIP":       "OFF",   # skip the gzip CLI tool
            "LIBDEFLATE_BUILD_TESTS":      "OFF",
        })

    def __str__(self):
        return "libdeflate (ebiggers-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(libdeflate.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libdeflate.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
