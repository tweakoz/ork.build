import os, tarfile
from obt import dep, host, path, make, pathtools, log
from obt.deco import Deco
from obt.wget import wget
from obt import command, patch, dep

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
class _pytorch_from_pip(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = "pip"
###############################################################################
class _pytorch_for_mps(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME,NAME)
    self.VERSION = "MPS"
    self._builder = self.createBuilder(dep.CustomBuilder)
    #################
    # create patch file
    #################
    DIFF = """\
--- serialization.py
+++ serialization.py
@@ -2077,1 +2077,2 @@
-            nbytes = numel * torch._utils._element_size(dtype)
+            nbytes = numel * torch._utils._element_size(dtype)
+            location = "mps"
 """
    diff_file = path.temp()/"pytorch_mps.diff"
    with open(str(diff_file),"w") as f:
      f.write(DIFF)

    #################

    PYTHON = dep.instance("python")
    serpy_file = PYTHON.site_packages_dir/"torch"/"serialization.py"

    self._builder._installcommands += [
      command.Command(
        [ "pip3","install",
          "--pre","torch",
          "torchvision","torchaudio",
          "--extra-index-url","https://download.pytorch.org/whl/nightly/cpu"
        ]
      ),
      # command to patch the file
      command.Command(
        [ "patch", "-p0", "-i", str(diff_file), str(serpy_file) ]
      ),
    ]
  @property
  def _fetcher(self):
    return dep.NopFetcher(name="pytorch_for_mps")

###############################################################################
class pytorch(dep.switch(linux=_pytorch_from_source, \
                         macos=_pytorch_for_mps)):
  def __init__(self):
    super().__init__()
  def env_init(self):
    log.marker("registering pytorch SDK(%s)"%self.VERSION)
