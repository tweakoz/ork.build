###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libwebp — replacement for /opt/homebrew/opt/webp. Provides libwebp,
# libwebpdemux, libsharpyuv. Used by oiio.
###############################################################################

VERSION  = "1.5.0"
BASENAME = "libwebp-%s" % VERSION
FILENAME = "v%s.tar.gz" % VERSION
URL_BASE = "https://github.com/webmproject/libwebp/archive/refs/tags"
MD5      = "4d1324c93788a4333aacc6238e0ef251"

from yarl import URL
from obt import dep, path

class libwebp(dep.StdProvider):
    name = "libwebp"

    def __init__(self):
        super().__init__(libwebp.name)
        self.setSourceRoot(path.builds()/libwebp.name/BASENAME)
        self.declareDep("cmake")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "BUILD_SHARED_LIBS":         "ON",
            "WEBP_BUILD_ANIM_UTILS":     "OFF",
            "WEBP_BUILD_CWEBP":          "OFF",
            "WEBP_BUILD_DWEBP":          "OFF",
            "WEBP_BUILD_GIF2WEBP":       "OFF",
            "WEBP_BUILD_IMG2WEBP":       "OFF",
            "WEBP_BUILD_VWEBP":          "OFF",
            "WEBP_BUILD_WEBPINFO":       "OFF",
            "WEBP_BUILD_WEBPMUX":        "OFF",
            "WEBP_BUILD_EXTRAS":         "OFF",
            "WEBP_BUILD_LIBWEBPMUX":     "ON",
        })

    def __str__(self):
        return "libwebp (webmproject-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(libwebp.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libwebp.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
