###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# libsox — required by torchaudio's sox backend (decode mp3/flac/ogg/etc).
# Build from the chirlu/sox GitHub mirror of the canonical sox release.
# Optional external codecs (flac/vorbis/opus/mp3) are disabled by default
# because OBT does not ship those upstream deps; torchaudio uses libsox
# for its core audio I/O surfaces and we add codec deps later if needed.
###############################################################################
from obt import dep, host, path

###############################################################################
class sox(dep.StdProvider):
  name = "sox"
  def __init__(self):
    super().__init__(sox.name)
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    # sox-14.4.2 ships configure.ac + Makefile.am only; no autogen.sh, no
    # generated configure. Bootstrap with autoreconf -fi.
    self._builder._needsautoreconf = True
    self._builder.setOption("--disable-static")
    self._builder.setOption("--enable-shared")
    # Disable optional codecs OBT doesn't ship — keeps the configure step
    # from auto-detecting /opt/homebrew/opt/{flac,libvorbis,opus,lame}.
    for opt in ["--without-flac",
                "--without-oggvorbis",
                "--without-opus",
                "--without-amrnb","--without-amrwb",
                "--without-ao",
                "--without-id3tag",
                "--without-ladspa",
                "--without-lame",
                "--without-magic",
                "--without-mad",
                "--without-png",
                "--without-pulseaudio",
                "--without-sndio",
                "--without-twolame",
                "--without-wavpack"]:
      self._builder.setOption(opt)
    if host.IsDarwin:
      # autoconf 2.70+ + clang on apple silicon: tells configure to stop
      # treating implicit function decls as errors (sox 14.4.2 has stale
      # C declarations that newer clang rejects under -Werror).
      self._builder.setEnvVar("CFLAGS","-Wno-error=implicit-function-declaration")
      # sox's configure REQUIRES pkg-config even when every optional codec
      # is --without-*. Since we've disabled all codecs that would need
      # pkg-config detection, point at /usr/bin/true so the configure
      # probe succeeds and emits empty CFLAGS/LIBS for every PKG_CHECK_*.
      self._builder.setEnvVar("PKG_CONFIG","/usr/bin/true")
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=sox.name,
                             repospec="tweakoz/libsox",
                             revision="toz-2026-may18", # sox-14.4.2 + LP64 seek-typedef fixes
                             recursive=False,
                             shallow=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"configure.ac").exists()
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/("libsox.%s" % self.shlib_extension)).exists()
