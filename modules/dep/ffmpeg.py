###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import subprocess

from obt import dep, host, command, path

###############################################################################
# nvenc is OPTIONAL - probed, never assumed (2026-08-18)
#
# ffmpeg's configure HARD-FAILS (it does not warn and continue) when
# --enable-nvenc is passed and the ffnvcodec headers are absent or too old,
# and that failure takes the whole obt dep phase down with it - which then
# surfaces confusingly downstream as "Could NOT find ObtOpenBlas" from cmake,
# because the deps after ffmpeg never got staged.
#
# Two real linux/x86_64 cases prove that assuming nvenc is wrong:
#   A LinuxCNC box (Debian 12 bookworm): the archive's libffmpeg-nvenc-dev is
#     11.1.5.2 and n6.1.1 requires >= 11.1.5.3 in that band - short by ONE
#     patch version, so no distro package can ever satisfy it there.
#   An AMD Strix Halo box: NVIDIA encode hardware it will never have.
#
# So probe with ffmpeg's OWN acceptance test and enable nvenc only when that
# passes. --enable-nonfree rides with nvenc and ONLY with it: nonfree is what
# makes the result non-redistributable, and a box that gets no nvenc should
# not pay that cost for nothing.
###############################################################################

# Copied verbatim from ffmpeg n6.1.1's configure (the ffnvcodec block, ~line
# 6578): a disjunction of accepted version bands, not a single floor. Re-copy
# it whenever `revision` below moves - a stale list silently mis-detects.
_FFNVCODEC_CONSTRAINTS = [
  "ffnvcodec >= 12.1.14.0",
  "ffnvcodec >= 12.0.16.1 ffnvcodec < 12.1",
  "ffnvcodec >= 11.1.5.3 ffnvcodec < 12.0",
  "ffnvcodec >= 11.0.10.3 ffnvcodec < 11.1",
  "ffnvcodec >= 8.1.24.15 ffnvcodec < 8.2",
]

###############################################################################
def _have_ffnvcodec():
  """True when pkg-config finds an ffnvcodec ffmpeg would actually accept.

  Mirrors configure's own check (whitespace-split, as its unquoted shell
  expansion does), so a pass here means configure will pass too."""
  for constraint in _FFNVCODEC_CONSTRAINTS:
    try:
      rval = subprocess.run(["pkg-config", "--exists"] + constraint.split(),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    except OSError:
      return False  # no pkg-config on the host - nothing to detect with
    if rval.returncode == 0:
      return True
  return False

###############################################################################
class ffmpeg(dep.StdProvider):
  name = "ffmpeg"
  def __init__(self):
    super().__init__(ffmpeg.name)
    self.declareDep("lame")
    src_root = self.source_root
    #################################################
    tgt_desc = self._target
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    self._builder.setOption("--disable-vdpau")
    self._builder.setOption("--disable-static")
    self._builder.setOption("--enable-shared")
    # Explicit staged LAME dependency: do not silently ship an FFmpeg binary
    # that cannot perform the DAW's MP3 export, or link a Homebrew-only codec.
    self._builder.setOption("--enable-libmp3lame")
    self._builder.setOption("--extra-cflags=-I%s" % path.includes())
    self._builder.setOption("--extra-ldflags=-L%s" % path.libs())
    # ffmpeg-n6.1.1's Vulkan AV1 decoder (libavcodec/vulkan_av1.c) targets
    # the pre-standardization MESA vendor types (VkVideoDecodeAV1ProfileInfoMESA,
    # StdVideoAV1MESATile*). Current Vulkan headers ship only the ratified
    # KHR AV1 decode types, so configure auto-enables Vulkan whenever the
    # staging include prefix exposes vulkan/vulkan.h — Linux Vulkan SDK OR
    # macOS MoltenVK (the second-staging bringup hit this on mac 2026-07-24,
    # where MoltenVK landed on the prefix before ffmpeg built) — and the build
    # then fails to compile that file. orkid does not use ffmpeg's Vulkan
    # hwaccel on any platform, so disable it on every host.
    self._builder.setOption("--disable-vulkan")
    if host.IsLinux:
      # n6.1.1's doc/t2h.pm HTML converter calls Texinfo::Convert::HTML->gdt,
      # a method dropped in the Texinfo perl shipped on newer distros
      # (Ubuntu 26.04), so `make install` fails building the HTML manuals
      # after the libraries are already built. orkid consumes only the
      # libav* shared libs — skip doc generation entirely.
      self._builder.setOption("--disable-doc")
    if host.IsDarwin:
      self._builder.setOption("--disable-vaapi")
      self._builder.setEnvVar("LDFLAGS", '-Wl,-ld_classic')
      self._builder.setOption("--enable-videotoolbox")
      # On macOS we don't need X11 video input. videotoolbox is the
      # native capture/render path. Disabling these stops ffmpeg's
      # configure from auto-detecting /opt/homebrew/opt/{libx11,libxcb}
      # which would otherwise leak into libav* dylibs.
      self._builder.setOption("--disable-xlib")
      self._builder.setOption("--disable-libxcb")
      self._builder.setOption("--disable-libxcb-shm")
      self._builder.setOption("--disable-libxcb-xfixes")
      self._builder.setOption("--disable-libxcb-shape")
    elif host.IsLinux and host.IsX86_64:
      if _have_ffnvcodec():
        self._builder.setOption("--enable-nvenc")
        self._builder.setOption("--enable-nonfree")
      else:
        # explicit, not merely left to autodetect, so the configure line in the
        # build log states the decision instead of hiding it in a default
        print("[ffmpeg] no ffmpeg-acceptable ffnvcodec found - building without nvenc")
        self._builder.setOption("--disable-nvenc")
    if tgt_desc.identifier == "x86_64-macos":
      self._builder.setOption("--disable-x86asm")
  ########################################################################
  @property
  def github_repo(self):
    return "FFmpeg/FFmpeg"
  ########################################################################
  @property
  def revision(self):
    return "n6.1.1"
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=ffmpeg.name,
                             repospec=self.github_repo,
                             revision=self.revision,
                             md5val="6aeda1ecb4a33c18e98ba722168be88b", # n6.1.1
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"configure").exists()

  def areRequiredBinaryFilesPresent(self):
    # ffmpeg produces the split libav* / libsw* shared libs, never a
    # combined "libffmpeg.so" (which existed on no platform). Probe the
    # primary codec lib with the host's shared-lib extension.
    if not (path.libs()/("libavcodec.%s" % self.shlib_extension)).is_file():
      return False
    encoder = path.bin()/"ffmpeg"
    if not encoder.is_file():
      return False
    try:
      result = subprocess.run([str(encoder), "-hide_banner", "-encoders"],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              text=True, timeout=10)
      return result.returncode == 0 and any("libmp3lame" in line.split()
                                           for line in result.stdout.splitlines())
    except (OSError, subprocess.SubprocessError):
      return False

  @property
  def should_build(self):
    # Old manifests only checked libavcodec; upgrade them when the actual
    # staged command lacks the newly required encoder.
    return super().should_build or not self.areRequiredBinaryFilesPresent()

  def onPostInstall(self):
    import json, shutil
    target = path.prefix()/"share"/"ffmpeg"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("LICENSE.md", "COPYING.LGPLv2.1", "COPYING.LGPLv3", "COPYING.GPLv2", "COPYING.GPLv3"):
      shutil.copy2(self.source_root/name, target/name)
    (target/"source.json").write_text(json.dumps(dict(
        name="FFmpeg", version=self.revision, source_url="https://github.com/FFmpeg/FFmpeg",
        source_archive_md5="6aeda1ecb4a33c18e98ba722168be88b",
        enabled_mp3_encoder="libmp3lame",
        configuration=next(line.split("=",1)[1] for line in (self.build_dest/"ffbuild"/"config.mak").read_text().splitlines() if line.startswith("FFMPEG_CONFIGURATION="))), indent=2)+"\n")
    return True
