###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# {fmt} — replacement for /opt/homebrew/opt/fmt. Used by oiio for
# compile-time format strings.
###############################################################################

VERSION  = "12.1.0"
BASENAME = "fmt-%s" % VERSION
FILENAME = "%s.tar.gz" % VERSION
URL_BASE = "https://github.com/fmtlib/fmt/archive/refs/tags"
MD5      = "92eb6f492e4838e5f024ce5207beafc7"

from yarl import URL
from obt import dep, path

class fmt(dep.StdProvider):
    name = "fmt"

    def __init__(self):
        super().__init__(fmt.name)
        self.setSourceRoot(path.builds()/fmt.name/BASENAME)
        self.declareDep("cmake")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "FMT_TEST":  "OFF",
            "FMT_DOC":   "OFF",
            "BUILD_SHARED_LIBS": "ON",
        })

    def __str__(self):
        return "fmt (fmtlib-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(fmt.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libfmt.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
