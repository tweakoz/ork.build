###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# xz / liblzma — replacement for /opt/homebrew/opt/xz on macOS.
#
# Pinned to 5.8.3 (released 2026-03-31), well past the CVE-2024-3094 backdoor
# in 5.6.0/5.6.1. Release tarball ships a pre-generated configure script, so
# AutoConfBuilder is sufficient — no autotools dance needed at build time.
###############################################################################

VERSION  = "5.8.3"
BASENAME = "xz-%s" % VERSION
FILENAME = "%s.tar.xz" % BASENAME
URL_BASE = "https://github.com/tukaani-project/xz/releases/download/v%s" % VERSION
MD5      = "a02753f34e5546d20213b87f876a0933"

from yarl import URL
from obt import dep, path

###############################################################################

class xz(dep.StdProvider):
    name = "xz"

    def __init__(self):
        super().__init__(xz.name)
        self.setSourceRoot(path.builds()/xz.name/BASENAME)
        self._builder = self.createBuilder(dep.AutoConfBuilder)
        self._builder._options = [
            "--disable-doc",
            "--disable-static",
            "--disable-nls",
        ]

    def __str__(self):
        return "xz (tukaani-source-%s)" % VERSION

    # _fetcher is a property: must be built fully in the getter, since
    # writes to a property's return value are discarded.
    @property
    def _fetcher(self):
        f = dep.WgetFetcher(xz.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"   # downloadAndExtract calls `tar xvf` which auto-detects xz
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"configure").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("liblzma.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        """Install prefix exposed to consumers (e.g. python.py)."""
        return path.prefix()

    @property
    def include_dir(self):
        return path.includes()

    @property
    def lib_dir(self):
        return path.libs()
