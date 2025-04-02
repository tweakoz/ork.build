import os, tarfile
from obt import dep, host, path, make, pathtools, log
from obt.deco import Deco
from obt.wget import wget
from obt import command

VER = "X"
NAME = "pytorch"

class _pytorch_from_source(dep.StdProvider):

  def __init__(self): ############################################
    super().__init__(NAME,NAME)
    self._builder = self.createBuilder(dep.CustomBuilder)
    self.VERSION = VER
    cmd_list = ["pip3","install","--pre",
                "torch","torchvision","torchaudio",
                "--index-url",
                "https://download.pytorch.org/whl/nightly/cu128"]
    self._builder._cleanbuildcommands += [command.Command(cmd_list)]
  ########################################################################
  @property
  def _fetcher(self):
    return dep.NopFetcher(name=NAME)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return True
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    return (path.bin()/"pkg-config").exists()
###############################################################################
class _pytorch_from_homebrew(dep.HomebrewProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = "homebrew"
###############################################################################
class pytorch(dep.switch(linux=_pytorch_from_source, \
                           macos=_pytorch_from_homebrew)):
  def __init__(self):
    super().__init__()
  def env_init(self):
    log.marker("registering pytorch SDK(%s)"%self.VERSION)
