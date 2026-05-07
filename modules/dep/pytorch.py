import os, tarfile, shutil, glob
from obt import dep, host, path, make, pathtools, log
from obt.deco import Deco
from obt.wget import wget
from obt import command, patch, dep

VER = "X"
NAME = "pytorch"

###############################################################################
def _cherrypick_torch_assets():
  """Copy torch's include + lib assets into orkid-owned, explicitly-named
  locations under $OBT_STAGE so orkid never references $OBT_PYPKG/torch
  directly. Two purposes:

  1. The include copy EXCLUDES torch's bundled pybind11/ — that's the one
     that, if shadowed onto orkid's compile path, gives _lev2.so a different
     pybind11 ABI than _core.so (v11 vs v5) and breaks cross-module type
     sharing for fvec4 etc.
  2. The libs are RENAMED to libobt.torch.<component>.{dylib,so} with their
     install-names / sonames + cross-references rewritten via
     install_name_tool / patchelf, so orkid links to a hermetically-sealed
     torch instance that cannot collide with the regular torch (still in
     $OBT_PYPKG/torch/lib) used by torchvision / torchaudio / user scripts.

  Layout result:
    $OBT_PYPKG/torch/include/<X>   -> $OBT_STAGE/include/obt.torch/<X>   (X != pybind11)
    $OBT_PYPKG/torch/lib/libtorch.{ext}        -> $OBT_STAGE/lib/libobt.torch.{ext}
    $OBT_PYPKG/torch/lib/libtorch_cpu.{ext}    -> $OBT_STAGE/lib/libobt.torch.cpu.{ext}
    $OBT_PYPKG/torch/lib/libtorch_python.{ext} -> $OBT_STAGE/lib/libobt.torch.python.{ext}
    $OBT_PYPKG/torch/lib/libc10.{ext}          -> $OBT_STAGE/lib/libobt.torch.c10.{ext}
    $OBT_PYPKG/torch/lib/libshm.{ext}          -> $OBT_STAGE/lib/libobt.torch.shm.{ext}
    $OBT_PYPKG/torch/lib/libomp.{ext}          -> $OBT_STAGE/lib/libobt.torch.omp.{ext}
    (Linux only) libtorch_cuda.so              -> libobt.torch.cuda.so
    libtorch_global_deps.{ext}                  -> libobt.torch.global_deps.{ext}
  """
  import subprocess
  PYTHON = dep.instance("python")
  src_torch  = PYTHON.site_packages_dir/"torch"
  src_inc    = src_torch/"include"
  src_lib    = src_torch/"lib"
  dst_inc    = path.includes()/"obt.torch"
  dst_lib    = path.libs()

  ##########################################################################
  # 1) Headers — copy everything except pybind11/
  ##########################################################################
  log.marker("cherrypicking torch headers (sans pybind11) -> $OBT_STAGE/include/obt.torch")
  if dst_inc.exists():
    shutil.rmtree(str(dst_inc))
  dst_inc.mkdir(parents=True)
  for entry in sorted(os.listdir(str(src_inc))):
    if entry == "pybind11":
      continue  # do NOT copy torch's bundled pybind11 — orkid uses obt.pybind11
    s = src_inc/entry
    d = dst_inc/entry
    if s.is_dir():
      shutil.copytree(str(s), str(d), symlinks=False)
    else:
      shutil.copy2(str(s), str(d))

  ##########################################################################
  # 2) Libs — copy + rename + fixup install_names / sonames + cross-refs
  ##########################################################################
  log.marker("cherrypicking torch libs -> $OBT_STAGE/lib (renamed to libobt.torch.*)")
  shext = "dylib" if host.IsOsx else "so"
  rename_map = {
    "libtorch.%s"             % shext: "libobt.torch.%s"             % shext,
    "libtorch_cpu.%s"         % shext: "libobt.torch.cpu.%s"         % shext,
    "libtorch_python.%s"      % shext: "libobt.torch.python.%s"      % shext,
    "libc10.%s"               % shext: "libobt.torch.c10.%s"         % shext,
    "libshm.%s"               % shext: "libobt.torch.shm.%s"         % shext,
    "libomp.%s"               % shext: "libobt.torch.omp.%s"         % shext,
    "libtorch_global_deps.%s" % shext: "libobt.torch.global_deps.%s" % shext,
  }
  if not host.IsOsx:
    rename_map["libtorch_cuda.so"] = "libobt.torch.cuda.so"

  for src_name, dst_name in rename_map.items():
    src_path = src_lib/src_name
    if not src_path.exists() or src_path.is_symlink():
      continue  # skip symlinks / missing files
    dst_path = dst_lib/dst_name
    if dst_path.exists() or os.path.islink(str(dst_path)):
      os.unlink(str(dst_path))
    shutil.copy2(str(src_path), str(dst_path))

    if host.IsOsx:
      # Set new install-name (LC_ID_DYLIB) and fix LC_LOAD_DYLIB cross-refs
      # for siblings in the rename set, then re-sign (Apple Silicon enforces
      # valid signatures even for unsigned dev binaries).
      subprocess.run(["install_name_tool", "-id",
                      "@rpath/" + dst_name, str(dst_path)],
                     check=False, capture_output=True)
      for ref_src, ref_dst in rename_map.items():
        subprocess.run(["install_name_tool", "-change",
                        "@rpath/" + ref_src, "@rpath/" + ref_dst, str(dst_path)],
                       check=False, capture_output=True)
      subprocess.run(["codesign", "--force", "--sign", "-", str(dst_path)],
                     check=False, capture_output=True)
    else:
      # Linux: patchelf for soname + DT_NEEDED rewrite.
      subprocess.run(["patchelf", "--set-soname", dst_name, str(dst_path)],
                     check=False, capture_output=True)
      for ref_src, ref_dst in rename_map.items():
        subprocess.run(["patchelf", "--replace-needed", ref_src, ref_dst, str(dst_path)],
                       check=False, capture_output=True)
  return True
###############################################################################

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
    self._builder._cleanbuildcommands += [_cherrypick_torch_assets]
    self._builder._incrbuildcommands  += [_cherrypick_torch_assets]
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
    if path.has_deployment_marker:
      return
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
      # cherrypick torch headers (sans pybind11) + libs into orkid-owned
      # staging locations — see _cherrypick_torch_assets() docstring.
      _cherrypick_torch_assets,
    ]
  ########################################################################
  @property
  def _fetcher(self):
    return dep.NopFetcher(name="pytorch_for_mps")
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return True
  ########################################################################
  def areRequiredBinaryFilesPresent(self):
    PYTHON = dep.instance("python")
    TORCHDIR = PYTHON.site_packages_dir/"torch"
    return TORCHDIR.exists()

###############################################################################
class pytorch(dep.switch(linux=_pytorch_from_source, \
                         macos=_pytorch_for_mps)):
  def __init__(self):
    super().__init__()
  def env_init(self):
    log.marker("registering pytorch SDK(%s)"%self.VERSION)
