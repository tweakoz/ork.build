###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# freetype — replacement for /opt/homebrew/opt/freetype. Used by oiio.
# Built against OBT libpng + system zlib (in macOS SDK).
###############################################################################

VERSION  = "2.13.3"
BASENAME = "freetype-VER-%s" % VERSION.replace(".", "-")
FILENAME = "VER-%s.tar.gz" % VERSION.replace(".", "-")
URL_BASE = "https://github.com/freetype/freetype/archive/refs/tags"
MD5      = "4425315beb50f913ae12d643e4e121e1"

from yarl import URL
from obt import dep, path

class freetype(dep.StdProvider):
    name = "freetype"

    def __init__(self):
        super().__init__(freetype.name)
        # Tarball extracts as freetype-VER-X-Y-Z/
        self.setSourceRoot(path.builds()/freetype.name/BASENAME)
        self.declareDep("cmake")
        self.declareDep("libpng")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "BUILD_SHARED_LIBS":              "ON",
            "FT_DISABLE_HARFBUZZ":            "ON",   # avoid /opt/homebrew/opt/harfbuzz
            "FT_DISABLE_BROTLI":              "ON",   # no OBT brotli — disable
            "FT_DISABLE_BZIP2":               "ON",
            "FT_REQUIRE_PNG":                 "ON",   # use OBT libpng
            "FT_REQUIRE_ZLIB":                "ON",   # system zlib in SDK
        })

    def __str__(self):
        return "freetype (savannah-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(freetype.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libfreetype.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
