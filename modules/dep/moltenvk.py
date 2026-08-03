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
# SPIRV-CROSS SOURCE: MoltenVK fetches SPIRV-Cross from the tweakoz/SPIRV-Cross
# FORK (branch toz-2026-aug02-spvc-meshview), pinned by the MoltenVK tree's own
# ExternalRevisions/SPIRV-Cross_repo_revision. The mesh-stage view-index and
# vertex-amplification work are REAL COMMITS on that branch, which is why this
# recipe no longer carries a patch-application step.
#
# The older arrangement pinned upstream KhronosGroup at af71ba0bbfcc — a commit
# reachable only through unmerged SPIRV-Cross PR #2650 — and hand-applied the
# fork's patches on top. Both the PR pin and the patches are retired; a MoltenVK
# tree at or after the fork-repointing commit needs neither.
#
# FOLLOWUP: when PR #2777 merges upstream, repin to the upstream release tag
# and retire the fork pin.
#
#
# PIN NOTE: VERSION is the head of tweakoz/MoltenVK branch toz-2026-taskmesh,
# recorded as a SHA rather than the branch name — see the comment at VERSION for
# why a moving ref is not usable through the tarball fetcher.
#
# NOTE: bumping this pin moves MoltenVK's bundled External/Vulkan-Headers,
# which vulkan.py `git describe`s to pick its Vulkan-Loader tag + md5 — see
# the fetch there before/after any change to VERSION.
#
# WIPE REQUIRED on repin OR config change: build() only fetches when
# source_root is absent, so a VERSION change alone leaves the old tree in
# place. --wipe alone is a no-op once the dep is provisioned (should_build
# short-circuits on the existing $OBT_STAGE/manifests/moltenvk), so both
# flags are needed —
#   obt.dep.build.py moltenvk --wipe --force
#
# NO PATCH STEP. Earlier revisions of this recipe hand-applied the fork's
# ExternalRevisions/SPIRV-Cross_*.patch files to the fetched External/SPIRV-Cross.
# Those patches are retired: their content is now real commits on the SPIRV-Cross
# fork branch, so the fetch alone produces patched source. (The old step also only
# ever applied ONE of the two patch files, so the mesh view-index change was never
# applied by this recipe at all — another reason the fork is the correct home.)
#
# STAMP + FORCE-CLEAN LAW (guards a field-proven SILENT MISCOMPILE): the law
# survives the patches, because the hazard was never really about patching — it
# is that External/build caches a libSPIRVCross.a compiled against ONE
# SPIRV-Cross source while the tree now holds ANOTHER. That build links GREEN and
# emits WRONG shaders: every CompilerMSL::Options member past the point of
# divergence shifts, and multiview reads false. So the guard is now keyed on the
# SPIRV-Cross PIN itself (ExternalRevisions/SPIRV-Cross_repo_revision) — any
# change to it force-cleans External/build before the rebuild.
#
# This matters beyond a repin: fetchDependencies runs on EVERY build and does
# `git checkout --force <rev>` inside an existing External/SPIRV-Cross, so the
# source can move under a cached External/build without the tree being refetched.
#
# VERIFY LINE (for the gate that owns this): the built dylib's shader dump for
# a 2-view multiview vertex shader must contain "[[amplification_id]]" — the
# fork's Tests/multiview-amplification runner prints it (categorical, cheap).
#
# ARCH NOTE: the package step keeps whatever arch set the fleet ships today
# (universal); the SPIRV-Cross source change affects no arch behavior.
#
# BUILD CONFIG: OBT_MOLTENVK_CONFIG selects the xcodebuild -configuration.
# Default is Release (owner decision 2026-07-25 — the Debug default's
# validation overhead tainted every mac graphics perf number). Set to Debug
# only when debugging MoltenVK itself. A config switch reuses the same
# fetched source tree but produces a different xcodebuild product, so the
# same --wipe --force is required to force a rebuild — the Package/Latest
# symlink follows the built config.
###############################################################################

import os
from obt import dep, path, command, log

# Head of tweakoz/MoltenVK branch toz-2026-taskmesh, as a SHA — the branch name
# itself is not usable here: GithubFetcher's tarball path caches by output name
# ("tweakoz_MoltenVK-<revision>.tar.gz"), so a moving ref would reuse a stale
# tarball, and md5val would have to be rewritten every time the branch advanced.
# Bump both lines together when the branch moves.
VERSION      = "bf9c132a1499055535ee9556189db8e7d575cfb8"
MOLTENVK_MD5 = "6891e5a819a55f29443b141014600e52"  # tweakoz/MoltenVK @ bf9c132a tarball

# SPIRV-Cross pin identity, stamped into the fetched tree (see header). This is
# NOT a patch: it is the revision fetchDependencies checked out, used only to
# decide whether a cached External/build is still valid.
SPVX_REV_RELPATH = ("ExternalRevisions", "SPIRV-Cross_repo_revision")
SPVX_STAMP_NAME  = ".obt-spirv-cross-pin.stamp"

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

  def _spirvCrossPin(self): ###################################################
    # The SPIRV-Cross revision fetchDependencies just checked out, read from the
    # MoltenVK tree itself. "absent" is a first-class value: a tree with no pin
    # file must still invalidate a build compiled against one.
    p = self.source_root
    for item in SPVX_REV_RELPATH:
      p = p/item
    if not p.exists():
      return "absent"
    with open(str(p), "r") as f:
      return f.read().strip() or "absent"

  def guardSpirvCrossPin(self): ###############################################
    # MISCOMPILE-TRAP GUARD (see header). Runs after ./fetchDependencies has
    # populated External/SPIRV-Cross and before xcodebuild. Always returns True:
    # this step only ever invalidates stale output, it cannot fail the build.
    import shutil
    stamp_path = self.source_root/SPVX_STAMP_NAME
    ext_build  = self.source_root/"External"/"build"

    cur_pin  = self._spirvCrossPin()
    prev_pin = None
    if stamp_path.exists():
      with open(str(stamp_path), "r") as f:
        prev_pin = f.read().strip()

    # A never-stamped tree is treated as unchanged so that adopting this recipe
    # does not gratuitously invalidate an existing, correctly-built tree.
    if prev_pin is not None and prev_pin != cur_pin:
      log.marker("MoltenVK: SPIRV-Cross pin changed (%s -> %s) — force-cleaning External/build"
                 % (prev_pin[:12], cur_pin[:12]))
      if ext_build.exists():
        shutil.rmtree(str(ext_build), ignore_errors=True)

    with open(str(stamp_path), "w") as f:
      f.write(cur_pin + "\n")
    return True

  def build(self): ############################################################
    # Build configuration: Release (default) or Debug. OBT_MOLTENVK_CONFIG=
    # Debug is the opt-out for debugging MoltenVK itself.
    config = os.environ.get("OBT_MOLTENVK_CONFIG", "Release")
    if config not in ("Debug", "Release"):
      log.marker("MoltenVK: OBT_MOLTENVK_CONFIG=%r invalid (must be Debug or Release)" % config)
      return False
    log.marker("MoltenVK build configuration: %s  (OBT_MOLTENVK_CONFIG, default Release)" % config)

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
      # SPIRV-Cross pin guard: after fetchDependencies populated
      # External/SPIRV-Cross, before xcodebuild. Only invalidates stale output.
      ok = self.guardSpirvCrossPin()
    if ok:
      ok = (0 == command.run(["xcodebuild", "build",
                              "-project", "MoltenVKPackaging.xcodeproj",
                              "-scheme", "MoltenVK Package (macOS only)",
                              "-configuration", config],
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
