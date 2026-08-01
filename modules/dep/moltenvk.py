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
# WIPE REQUIRED on repin OR config change: build() only fetches when
# source_root is absent, so a VERSION change alone leaves the old tree in
# place. --wipe alone is a no-op once the dep is provisioned (should_build
# short-circuits on the existing $OBT_STAGE/manifests/moltenvk), so both
# flags are needed —
#   obt.dep.build.py moltenvk --wipe --force
#
# SPIRV-CROSS PATCH STEP: after ./fetchDependencies populates
# External/SPIRV-Cross and before the xcodebuild package step, this recipe
# applies the fork's ExternalRevisions/SPIRV-Cross_vertex_amplification.patch
# (vertex amplification / multiview support in CompilerMSL) when that file is
# present in the fetched tree. When the fork state carries no such patch the
# step is a logged NO-OP, so unpatched forks still build.
#
# STAMP + FORCE-CLEAN LAW (guards a field-proven SILENT MISCOMPILE): the patch
# content hash is stamped into the fetched tree, and any change of that hash
# force-cleans External/build (and restores the pristine SPIRV-Cross pin)
# before the rebuild. A cached External/build libSPIRVCross.a compiled against
# the pre-patch CompilerMSL::Options struct builds GREEN but produces WRONG
# shaders — every option past the insertion point shifts, multiview reads
# false. Never ship the patch step without the clean.
#
# VERIFY LINE (for the gate that owns this): the built dylib's shader dump for
# a 2-view multiview vertex shader must contain "[[amplification_id]]" — the
# fork's Tests/multiview-amplification runner prints it (categorical, cheap).
#
# ARCH NOTE: the package step keeps whatever arch set the fleet ships today
# (universal); the patch changes no arch behavior.
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

VERSION      = "4fc3f6c1f97c7579aa6bbffa791b7a9b35b7fcd4"
MOLTENVK_MD5 = "b27e7a2837fc6aa2046ccb6eefc56a9f"  # tweakoz/MoltenVK @ 4fc3f6c tarball

# fork-carried SPIRV-Cross patch (optional; see header) + its build stamp
SPVR_PATCH_RELPATH = ("ExternalRevisions", "SPIRV-Cross_vertex_amplification.patch")
SPVR_STAMP_NAME    = ".obt-spirv-cross-patch.stamp"

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

  def _spvrPatchPath(self): ###################################################
    p = self.source_root
    for item in SPVR_PATCH_RELPATH:
      p = p/item
    return p

  def _spvrPatchHash(self): ###################################################
    # "absent" is a first-class stamp value: a fork state that drops the patch
    # must also invalidate a build tree that was compiled with it.
    import hashlib
    patch_path = self._spvrPatchPath()
    if not patch_path.exists():
      return "absent"
    with open(str(patch_path), "rb") as f:
      return hashlib.sha256(f.read()).hexdigest()

  def applySpirvCrossPatch(self): #############################################
    # Applies the fork's SPIRV-Cross vertex-amplification patch to the fetched
    # External/SPIRV-Cross, enforcing the stamp + force-clean law (see header).
    # Returns True on success, INCLUDING the no-op case where the fork state
    # carries no patch file.
    import shutil
    patch_path = self._spvrPatchPath()
    stamp_path = self.source_root/SPVR_STAMP_NAME
    spvx_root  = self.source_root/"External"/"SPIRV-Cross"
    ext_build  = self.source_root/"External"/"build"

    cur_hash  = self._spvrPatchHash()
    prev_hash = None
    if stamp_path.exists():
      with open(str(stamp_path), "r") as f:
        prev_hash = f.read().strip()

    # MISCOMPILE-TRAP GUARD: a cached External/build built against the other
    # patch state links green and emits wrong shaders. Any hash change wipes
    # it. (A never-stamped tree with no patch is treated as unchanged, so
    # adopting this recipe does not gratuitously invalidate existing trees.)
    changed = (prev_hash != cur_hash) and not (prev_hash is None and cur_hash == "absent")
    if changed:
      log.marker("MoltenVK: SPIRV-Cross patch stamp changed (%s -> %s) — force-cleaning External/build"
                 % (prev_hash if prev_hash else "none", cur_hash[:12]))
      if ext_build.exists():
        shutil.rmtree(str(ext_build), ignore_errors=True)
      # restore the pristine SPIRV-Cross pin, so the new patch state is applied
      # to unpatched source rather than on top of the previous patch
      if (spvx_root/".git").exists():
        command.run(["git", "checkout", "--", "."], working_dir=spvx_root)

    if not patch_path.exists():
      log.marker("MoltenVK: no ExternalRevisions/%s in this fork state — SPIRV-Cross patch step is a NO-OP"
                 % SPVR_PATCH_RELPATH[-1])
      self._writeSpvrStamp(stamp_path, cur_hash)
      return True

    if not spvx_root.exists():
      log.marker("MoltenVK: SPIRV-Cross patch present but External/SPIRV-Cross missing (fetchDependencies did not populate it)")
      return False

    # idempotent application: clean apply / already applied / neither (fail loud)
    ok = False
    if 0 == command.run(["git", "apply", "--check", "-p1", str(patch_path)], working_dir=spvx_root):
      ok = (0 == command.run(["git", "apply", "-p1", str(patch_path)], working_dir=spvx_root))
      if ok:
        log.marker("MoltenVK: applied SPIRV-Cross patch %s (sha256 %s)" % (SPVR_PATCH_RELPATH[-1], cur_hash[:12]))
    elif 0 == command.run(["git", "apply", "--reverse", "--check", "-p1", str(patch_path)], working_dir=spvx_root):
      ok = True
      log.marker("MoltenVK: SPIRV-Cross patch %s already applied to External/SPIRV-Cross — skipping" % SPVR_PATCH_RELPATH[-1])

    if not ok:
      log.marker("MoltenVK: SPIRV-Cross patch %s FAILED to apply to External/SPIRV-Cross (wrong SPIRV-Cross pin, or partially patched tree)"
                 % SPVR_PATCH_RELPATH[-1])
      return False

    log.marker("MoltenVK: VERIFY after build — a 2-view multiview vertex shader dump must contain [[amplification_id]] (Tests/multiview-amplification)")
    self._writeSpvrStamp(stamp_path, cur_hash)
    return True

  def _writeSpvrStamp(self, stamp_path, value): ###############################
    with open(str(stamp_path), "w") as f:
      f.write(value + "\n")

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
      # fork-carried SPIRV-Cross patch: after fetchDependencies populated
      # External/SPIRV-Cross, before xcodebuild. No-op when absent.
      ok = self.applySpirvCrossPatch()
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
