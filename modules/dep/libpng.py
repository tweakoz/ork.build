###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libpng — replacement for /opt/homebrew/opt/libpng. Used by oiio, freetype.
###############################################################################

VERSION  = "1.6.49"
BASENAME = "libpng-%s" % VERSION
FILENAME = "v%s.tar.gz" % VERSION
URL_BASE = "https://github.com/pnggroup/libpng/archive/refs/tags"
MD5      = "e9490d9038120e1111cff514e0b08fac"

from yarl import URL
from obt import dep, path

class libpng(dep.StdProvider):
    name = "libpng"

    def __init__(self):
        super().__init__(libpng.name)
        self.setSourceRoot(path.builds()/libpng.name/BASENAME)
        self.declareDep("cmake")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "PNG_TESTS":   "OFF",
            "PNG_TOOLS":   "ON",
            "PNG_SHARED":  "ON",
            "PNG_STATIC":  "ON",
        })

    def __str__(self):
        return "libpng (pnggroup-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(libpng.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libpng16.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
