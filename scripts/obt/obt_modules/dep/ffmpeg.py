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
    #self._deps = ["pkgconfig"]
    src_root = self.source_root
    #################################################
    tgt_desc = self._target
    self._builder = self.createBuilder(dep.AutoConfBuilder)
    self._builder.setOption("--disable-vaapi")
    self._builder.setOption("--disable-vdpau")
    self._builder.setOption("--disable-static")
    self._builder.setOption("--enable-shared")
    if host.IsDarwin:
      self._builder.setEnvVar("LDFLAGS", '-Wl,-ld_classic')
      self._builder.setOption("--enable-videotoolbox")
    #elif host.IsLinux and host.IsX86_64:
    #  self._builder.setOption("--enable-nvenc")
    if tgt_desc.identifier == "x86_64-macos":
      self._builder.setOption("--disable-x86asm")

    #################################################
    self.declareDep("pkgconfig")
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
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"configure").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libffmpeg.so").exists()
