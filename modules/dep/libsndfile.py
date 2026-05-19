###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libsndfile — replacement for /opt/homebrew/opt/libsndfile. Used by
# ork.lev2 (CMakeLists.txt:142, "sndfile"). Disable optional codec deps
# (ogg/vorbis/flac/opus) — orkid only needs WAV/AIFF/etc. core formats.
###############################################################################

VERSION  = "1.2.2"
BASENAME = "libsndfile-%s" % VERSION
FILENAME = "%s.tar.xz" % BASENAME
URL_BASE = "https://github.com/libsndfile/libsndfile/releases/download/%s" % VERSION
MD5      = "04e2e6f726da7c5dc87f8cf72f250d04"

from yarl import URL
from obt import dep, path

class libsndfile(dep.StdProvider):
    name = "libsndfile"

    def __init__(self):
        super().__init__(libsndfile.name)
        self.setSourceRoot(path.builds()/libsndfile.name/BASENAME)
        self.declareDep("cmake")
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            "BUILD_SHARED_LIBS":              "ON",
            "BUILD_TESTING":                  "OFF",
            "BUILD_EXAMPLES":                 "OFF",
            "BUILD_PROGRAMS":                 "OFF",
            # No OBT ogg/vorbis/flac/opus deps — disable so cmake doesn't
            # auto-pick them up from /opt/homebrew. Core formats (WAV, AIFF,
            # AU, RAW) still work without these codecs.
            "ENABLE_EXTERNAL_LIBS":           "OFF",
            "ENABLE_MPEG":                    "OFF",
            "CMAKE_PREFIX_PATH":              str(path.prefix()),
            "CMAKE_IGNORE_PATH":              "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
        })

    def __str__(self):
        return "libsndfile (github-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(libsndfile.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libsndfile.%s" % self.shlib_extension)).exists()

    @property
    def root(self):
        return path.prefix()
