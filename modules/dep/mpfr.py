###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# MPFR — Multi-Precision Floating-Point Reliable. Replacement for
# /opt/homebrew/opt/mpfr. Used by ork.lev2 (CMakeLists.txt:130). Depends
# on GMP. Autoconf.
###############################################################################

VERSION  = "4.2.2"
BASENAME = "mpfr-%s" % VERSION
FILENAME = "%s.tar.xz" % BASENAME
URL_BASE = "https://www.mpfr.org/mpfr-current"
MD5      = "7c32c39b8b6e3ae85f25156228156061"

from yarl import URL
from obt import dep, path

class mpfr(dep.StdProvider):
    name = "mpfr"

    def __init__(self):
        super().__init__(mpfr.name)
        self.setSourceRoot(path.builds()/mpfr.name/BASENAME)
        self.declareDep("gmp")
        self._builder = self.createBuilder(dep.AutoConfBuilder)
        self._builder._options = [
            "--with-gmp=%s" % path.prefix(),
            "--disable-static",
        ]

    def __str__(self):
        return "mpfr (mpfr.org-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(mpfr.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"configure").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libmpfr.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
