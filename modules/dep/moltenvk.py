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
#
# PIN: MoltenVK PR #2777 ("taskless Vulkan mesh shader support"), commit
# 4fc3f6c1 (authored on dttdrv/MoltenVK branch macgaming/mesh-shader), fetched
# from the tweakoz/MoltenVK fork where tag v1.4.2-taskless-mesh-pr2777 anchors
# that exact sha — the PR branch head moves and an untagged sha on someone
# else's fork is GC-eligible; the tag on our own fork is the permanence
# guarantee. No released MoltenVK (through 1.4.2) implements
# VK_EXT_mesh_shader; orkid's vulkan backend requires it for its mesh pass.
# The PR exposes the extension taskless (meshShader=true, taskShader=false).
#
# The PR also pins SPIRV-Cross to af71ba0bbfcc (a commit that exists only in
# unmerged SPIRV-Cross PR #2650). That resolves without help from us: the PR's
# fetchDependencies fetches the exact revision (`git fetch origin <sha>`)
# instead of `git fetch --all`, which cannot see an unmerged PR commit.
#
# FOLLOWUP: when PR #2777 merges upstream, repin to the upstream release tag
# and retire the fork pin.
#
# NOTE: bumping this pin moves MoltenVK's bundled External/Vulkan-Headers,
# which vulkan.py `git describe`s to pick its Vulkan-Loader tag + md5 — see
# the fetch there before/after any change to VERSION.
#
# WIPE REQUIRED on repin: build() only fetches when source_root is absent, so
# a VERSION change alone leaves the old tree in place. --wipe alone is a no-op
# once the dep is provisioned (should_build short-circuits on the existing
# $OBT_STAGE/manifests/moltenvk), so both flags are needed —
#   obt.dep.build.py moltenvk --wipe --force
###############################################################################

from obt import dep, path, command, log

VERSION      = "4fc3f6c1f97c7579aa6bbffa791b7a9b35b7fcd4"
MOLTENVK_MD5 = "b27e7a2837fc6aa2046ccb6eefc56a9f"  # tweakoz/MoltenVK @ 4fc3f6c tarball

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
