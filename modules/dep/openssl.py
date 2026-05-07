###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# OpenSSL — replacement for /opt/homebrew/opt/openssl@3 on macOS.
#
# Pinned to 3.5.6 (LTS, supported until 2030-04-08).
# OpenSSL uses a Perl-based ./Configure (capital C), so AutoConfBuilder
# does not apply — drives ./Configure / make / make install_sw via
# CustomBuilder, mirroring the luajit.py / lz4.py pattern.
###############################################################################

VERSION  = "3.5.6"
BASENAME = "openssl-%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://github.com/openssl/openssl/releases/download/openssl-%s" % VERSION
MD5      = "1bb3506c580865a0a464e09288ac157e"

from yarl import URL
from obt import dep, host, path
from obt.command import Command
import obt.host

###############################################################################

def _configure_target():
    if obt.host.IsOsx and obt.host.IsAARCH64:
        return "darwin64-arm64-cc"
    if obt.host.IsOsx and obt.host.IsX86_64:
        return "darwin64-x86_64-cc"
    if obt.host.IsLinux and obt.host.IsAARCH64:
        return "linux-aarch64"
    if obt.host.IsLinux and obt.host.IsX86_64:
        return "linux-x86_64"
    raise RuntimeError("openssl dep: unsupported host")


class openssl(dep.StdProvider):
    name = "openssl"

    def __init__(self):
        super().__init__(openssl.name)
        self.setSourceRoot(path.builds()/openssl.name/BASENAME)

        bdir = self.source_root
        target = _configure_target()

        configure_cmd = Command([
            "perl", "./Configure", target,
            "--prefix=%s" % path.prefix(),
            "--openssldir=%s" % (path.prefix()/"etc/ssl"),
            "--libdir=lib",                  # avoid lib64 on linux
            "no-tests",
            "no-docs",
            "shared",
        ], working_dir=bdir)

        make_cmd    = Command(["make", "-j", host.NumCores], working_dir=bdir)
        # install_sw skips man pages and HTML; install_ssldirs creates the cert/etc tree.
        install_cmd = Command(["make", "install_sw", "install_ssldirs"], working_dir=bdir)

        self._builder = dep.CustomBuilder(openssl.name)
        self._builder._cleanbuildcommands = [configure_cmd, make_cmd, install_cmd]
        self._builder._incrbuildcommands  = [make_cmd, install_cmd]
        self._builder._builddir = bdir

    def __str__(self):
        return "OpenSSL (openssl.org-source-%s)" % VERSION

    # _fetcher is a property: must be built fully in the getter, since
    # writes to a property's return value are discarded.
    @property
    def _fetcher(self):
        f = dep.WgetFetcher(openssl.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"Configure").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libssl.%s" % self.shlib_extension)).exists() \
           and (path.libs()/("libcrypto.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        """Install prefix exposed to consumers (python.py uses --with-openssl=<root>)."""
        return path.prefix()

    @property
    def include_dir(self):
        return path.includes()

    @property
    def lib_dir(self):
        return path.libs()
