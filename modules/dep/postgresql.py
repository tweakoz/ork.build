###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# PostgreSQL — server + client libs (libpq) + tools (initdb, pg_ctl, psql, ...).
# Autoconf, installed into the staging prefix. Used by libpqpp, and by stacks
# that run a private database inside an OBT stage (e.g. LiteLLM's key store).
# readline and zlib come from the host (libreadline-dev, zlib1g-dev on Ubuntu).
# Built without ICU: the stage's pkg-config doesn't see the host's icu-uc.pc, and
# libc collations are enough for an embedded/service database.
###############################################################################

VERSION  = "18.6"
BASENAME = "postgresql-%s" % VERSION
FILENAME = "%s.tar.bz2" % BASENAME
URL_BASE = "https://ftp.postgresql.org/pub/source/v%s" % VERSION
MD5      = "6143c18ab91bdfcaa056a61861814cde"   # matches the upstream .md5

from yarl import URL
from obt import dep, path

class postgresql(dep.StdProvider):
    name = "postgresql"

    def __init__(self):
        super().__init__(postgresql.name)
        self.setSourceRoot(path.builds()/postgresql.name/BASENAME)
        self._builder = self.createBuilder(dep.AutoConfBuilder)
        self._builder._options = ["--without-icu", "--without-llvm", "--without-systemd", "--disable-rpath"]

    def __str__(self):
        return "PostgreSQL (source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(postgresql.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"   # `tar xvf` auto-detects bz2
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"configure").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.bin()/"postgres").exists() and (path.bin()/"initdb").exists()

    @property
    def root(self):
        return path.prefix()
