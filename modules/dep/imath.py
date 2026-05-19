###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# Imath — replacement for /opt/homebrew/opt/imath. Required by OpenEXR 3.x
# (which had Imath split out into its own project at the 3.0 boundary).
###############################################################################

VERSION  = "3.2.2"
BASENAME = "Imath-%s" % VERSION
FILENAME = "v%s.tar.gz" % VERSION
URL_BASE = "https://github.com/AcademySoftwareFoundation/Imath/archive/refs/tags"
MD5      = "e29f25ce926ac53d8e0a52197299f61b"

from yarl import URL
from obt import dep, path

###############################################################################

class imath(dep.StdProvider):
    name = "imath"

    def __init__(self):
        super().__init__(imath.name)
        # Tarball extracts as Imath-<VERSION>/.
        self.setSourceRoot(path.builds()/imath.name/BASENAME)
        self.declareDep("cmake")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "BUILD_TESTING":      "OFF",
            "IMATH_INSTALL_PKG_CONFIG": "ON",
        })

    def __str__(self):
        return "Imath (academysoftwarefoundation-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(imath.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libImath.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
