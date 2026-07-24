###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path

###############################################################################
class ffmpeg(dep.StdProvider):
  name = "ffmpeg"
  def __init__(self):
    super().__init__(ffmpeg.name)
    src_root = self.source_root
    #################################################
    tgt_desc = self._target
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    self._builder.setOption("--disable-vdpau")
    self._builder.setOption("--disable-static")
    self._builder.setOption("--enable-shared")
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
      self._builder.setOption("--enable-nvenc")
      self._builder.setOption("--enable-nonfree")
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
    return (path.libs()/("libavcodec.%s" % self.shlib_extension)).exists()
