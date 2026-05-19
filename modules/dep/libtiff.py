###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libtiff — replacement for /opt/homebrew/opt/libtiff. Used by oiio.
# Builds against OBT-built libjpeg-turbo (jpegturbo dep) and zlib (system SDK).
###############################################################################

VERSION  = "4.7.0"
BASENAME = "libtiff-v%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://gitlab.com/libtiff/libtiff/-/archive/v%s" % VERSION
MD5      = "b7703bcd976e5f20348832587fdfe71a"

from yarl import URL
from obt import dep, path

class libtiff(dep.StdProvider):
    name = "libtiff"

    def __init__(self):
        super().__init__(libtiff.name)
        # Tarball extracts as libtiff-v<VERSION>/
        self.setSourceRoot(path.builds()/libtiff.name/BASENAME)
        self.declareDep("cmake")
        self.declareDep("jpegturbo")
        self.declareDep("zstd")
        self.declareDep("libdeflate")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "BUILD_SHARED_LIBS": "ON",
            "tiff-tests":  "OFF",
            "tiff-docs":   "OFF",
            "tiff-tools":  "ON",
            "tiff-contrib":"OFF",
            # libtiff's cmake uses bare find_path/find_library which on
            # macOS prefers /opt/homebrew. Force it to look in OBT staging
            # first, and explicitly blacklist /opt/homebrew.
            "CMAKE_PREFIX_PATH": str(path.prefix()),
            "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
        })

    def __str__(self):
        return "libtiff (gitlab-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(libtiff.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libtiff.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
