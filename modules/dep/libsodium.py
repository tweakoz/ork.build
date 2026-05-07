###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libsodium — replacement for /opt/homebrew/opt/libsodium. Used by ork.core
# (CMakeLists.txt:311–312, 409–410). Autoconf-based.
###############################################################################

VERSION  = "1.0.20"
BASENAME = "libsodium-%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://github.com/jedisct1/libsodium/releases/download/%s-RELEASE" % VERSION
MD5      = "597f2c7811f84e63e45e2277dfb5da46"

from yarl import URL
from obt import dep, path

class libsodium(dep.StdProvider):
    name = "libsodium"

    def __init__(self):
        super().__init__(libsodium.name)
        self.setSourceRoot(path.builds()/libsodium.name/BASENAME)
        self._builder = self.createBuilder(dep.AutoConfBuilder)
        self._builder._options = ["--disable-static"]

    def __str__(self):
        return "libsodium (jedisct1-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(libsodium.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"configure").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libsodium.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
