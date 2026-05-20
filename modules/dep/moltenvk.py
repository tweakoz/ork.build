###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
# MoltenVK — Vulkan-on-Metal. Split out from vulkan.py so its long build
# (./fetchDependencies + xcodebuild, ~5-10 min) can run in parallel with
# cmake and python in the pipeline.
#
# This dep uses NO cmake: `./fetchDependencies --macos` only invokes cmake
# under its `--build-spirv-tools` path, which we do not pass — without that
# flag fetchDependencies extracts pre-generated SPIRV-Tools headers from a
# bundled template zip. MoltenVK proper builds via xcodebuild. So moltenvk
# declares no cmake dependency and is free to schedule alongside cmake.
#
# The cmake-dependent Vulkan-Loader build lives in vulkan.py, which declares
# both `moltenvk` and `cmake`.
###############################################################################

from obt import dep, path, command, log

VERSION      = "v1.4.1"
MOLTENVK_MD5 = "ba3285b89dfb4a633185f29e4d4cd30e"  # tweakoz/MoltenVK v1.4.1 tarball

###############################################################################

class moltenvk(dep.Provider):

  def __init__(self): ##########################################################
    super().__init__("moltenvk")
    self._oslist       = ["Darwin"]
    self.VERSION       = VERSION
    self.source_root   = path.builds()/"moltenvk"
    self.build_dest    = path.builds()/"moltenvk"/".build"
    self.sdk_dir       = self.source_root/"Package"/"Latest"/"MoltenVK"
    self.build_lib_dir = self.sdk_dir/"dylib"/"macOS"

  def __str__(self): ###########################################################
    return "MoltenVK (github-%s)" % self.VERSION

  def wipe(self): ##############################################################
    # shutil.rmtree instead of os.system("rm -rf ...") — os.system inherits
    # the process's fd 1/2 directly, bypassing the per-thread log redirect
    # set up by obt.pipeline_io, and would leak output through the TUI.
    import shutil
    if self.source_root.exists():
      shutil.rmtree(str(self.source_root), ignore_errors=True)
    if self.build_dest.exists():
      shutil.rmtree(str(self.build_dest), ignore_errors=True)

  def build(self): ############################################################
    if not self.source_root.exists():
      # GithubFetcher tarball mode — md5-cached + validated. The guard
      # stays because the followup ./fetchDependencies + xcodebuild are
      # expensive; we only refetch when source_root is absent.
      dep.GithubFetcher(name="moltenvk",
                        repospec="tweakoz/MoltenVK",
                        revision=self.VERSION,
                        md5val=MOLTENVK_MD5,
                        recursive=False).fetch(self.source_root)

    # No os.chdir(self.source_root) — racy under the parallel pipeline.
    # Each command.run() below sets working_dir explicitly.
    ok = (0 == command.run(["./fetchDependencies", "--macos"],
                            working_dir=self.source_root))
    if ok:
      ok = (0 == command.run(["xcodebuild", "build",
                              "-project", "MoltenVKPackaging.xcodeproj",
                              "-scheme", "MoltenVK Package (macOS only)",
                              "-configuration", "Debug"],
                              working_dir=self.source_root))
    if ok:
      ok = (0 == command.run(["cp",
                              str(self.build_lib_dir/"libMoltenVk.dylib"),
                              str(path.libs()/"libMoltenVk.dylib")]))
    if ok:
      # Copy MoltenVK's public headers into $OBT_STAGE/include. cp -r with
      # a glob needs shell expansion; iterate with a real glob instead.
      import shutil as _sh
      src_dir = self.source_root/"Package"/"Latest"/"MoltenVK"/"include"
      ok = src_dir.exists()
      if ok:
        for entry in src_dir.iterdir():
          tgt = path.includes()/entry.name
          try:
            if entry.is_dir():
              _sh.copytree(str(entry), str(tgt), dirs_exist_ok=True)
            else:
              _sh.copy2(str(entry), str(tgt))
          except Exception as e:
            print("copy %s -> %s failed: %s" % (entry, tgt, e))
            ok = False
            break
    return ok

  def areRequiredBinaryFilesPresent(self): ####################################
    return (path.libs()/"libMoltenVk.dylib").exists()
