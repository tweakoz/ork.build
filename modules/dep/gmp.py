###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# GMP — GNU Multiple Precision Arithmetic. Replacement for
# /opt/homebrew/opt/gmp. Used by ork.lev2 (CMakeLists.txt:130). Autoconf.
###############################################################################

VERSION  = "6.3.0"
BASENAME = "gmp-%s" % VERSION
FILENAME = "%s.tar.xz" % BASENAME
URL_BASE = "https://gmplib.org/download/gmp"
MD5      = "956dc04e864001a9c22429f761f2c283"

from yarl import URL
from obt import dep, host, path

class gmp(dep.StdProvider):
    name = "gmp"

    def __init__(self):
        super().__init__(gmp.name)
        self.setSourceRoot(path.builds()/gmp.name/BASENAME)
        self._builder = self.createBuilder(dep.AutoConfBuilder)
        self._builder._options = ["--enable-cxx", "--disable-static"]
        # gmp-6.3.0's configure probes (e.g. the "long long reliability"
        # test in tests/mpn/t-iord_u.c) use pre-C23 unprototyped function
        # calls. gcc-15 defaults to -std=gnu23 where those are hard errors
        # ("too many arguments to function"), so the probe misfires and
        # configure aborts with "could not find a working compiler". Pin
        # the C dialect to gnu17 via CC so gmp still does its own per-CPU
        # CFLAGS tuning (setting CFLAGS would disable that).
        if host.IsLinux:
            self._builder.setEnvVar("CC", "gcc -std=gnu17")

    def __str__(self):
        return "gmp (gmplib-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(gmp.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"   # `tar xvf` auto-detects xz
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"configure").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libgmp.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
