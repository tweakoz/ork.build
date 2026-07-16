#!/usr/bin/env python3
###############################################################################
# obt.linux  —  ELF relocation toolkit (the Linux analog of obt.macos)
#
# Mirrors the API surface of obt.macos that ork's deploy_phases consumes, but
# targets ELF / patchelf instead of Mach-O / install_name_tool+codesign.
#
#   obt.macos                         obt.linux
#   ------------------------------    ------------------------------------------
#   is_macho_binary                   is_elf_binary
#   macho_enumerate_dylibs            elf_enumerate_needed   (bare SONAMEs)
#   macho_enumerate_rpaths            elf_enumerate_rpaths   (DT_RUNPATH/DT_RPATH)
#   macho_change_id                   elf_set_soname         (usually a NO-OP)
#   discover_macho_files              discover_elf_files
#   MachoDependencyWalker             ElfDependencyWalker
#   MachoRelocator                    ElfRelocator
#   MachoVerifier                     ElfVerifier
#
# Key semantic differences vs Mach-O (why the Linux path is *simpler*):
#   * ELF NEEDED entries are bare SONAMEs resolved at load time via RPATH, so
#     there is NO per-dependency string rewrite (the bulk of MachoRelocator
#     vanishes). We only rewrite RPATH to be $ORIGIN-relative.
#   * $ORIGIN is the exact analog of @loader_path / @executable_path.
#   * There is NO codesigning — editing an ELF with patchelf needs no re-sign.
#   * There is NO framework / .app / minos concept.
#
# Requires the `patchelf` tool (>=0.14 for --print-soname/--add-rpath) and the
# standard binutils (`readelf`), plus `ldd` from glibc for closure resolution.
###############################################################################
import os, re, shutil, subprocess
from obt import host, path, pathtools
from obt.command import capture, run
from obt.command import Deco
deco = Deco()

###############################################################################
# tool discovery
###############################################################################

def _tool(name):
  p = shutil.which(name)
  if p is None:
    raise RuntimeError(
      f"obt.linux: required tool '{name}' not found on PATH "
      f"(apt install patchelf binutils)")
  return p

def have_patchelf():
  return shutil.which("patchelf") is not None

###############################################################################
# ELF identification
###############################################################################

_ELF_MAGIC = b"\x7fELF"

def is_elf_binary(file_path):
  """True if file_path is an ELF object (checks the 4-byte magic — cheap)."""
  try:
    with open(str(file_path), "rb") as fh:
      return fh.read(4) == _ELF_MAGIC
  except (OSError, IOError):
    return False

# File extensions that hint at an ELF shared object (checked before the magic
# read, mirroring _MACHO_EXTENSIONS). '' (no extension) and '.N' (versioned
# .so.1.2.3) are also considered — resolved by the magic check.
_ELF_EXTENSIONS = {'.so'}

###############################################################################
# low-level ELF queries (patchelf / readelf)
###############################################################################

def elf_enumerate_needed(elf_path):
  """Return the list of DT_NEEDED SONAMEs of an ELF object (bare names)."""
  assert host.IsLinux
  out = capture([_tool("patchelf"), "--print-needed", str(elf_path)],
                do_log=False)
  return [ln.strip() for ln in out.splitlines() if ln.strip()]

def elf_enumerate_rpaths(elf_path):
  """Return the RPATH/RUNPATH entries of an ELF object as a list.

  patchelf prints a single ':'-joined string for whichever of DT_RPATH /
  DT_RUNPATH is present (RUNPATH preferred). Mirrors macho_enumerate_rpaths.
  """
  assert host.IsLinux
  out = capture([_tool("patchelf"), "--print-rpath", str(elf_path)],
                do_log=False).strip()
  if not out:
    return []
  return [seg for seg in out.split(":") if seg]

def elf_get_soname(elf_path):
  """Return the DT_SONAME of a shared object, or '' if none."""
  assert host.IsLinux
  try:
    return capture([_tool("patchelf"), "--print-soname", str(elf_path)],
                   do_log=False).strip()
  except Exception:
    return ""

def elf_set_soname(elf_path, soname):
  """Set an ELF's DT_SONAME. NOTE: rarely needed — SONAMEs are baked correctly
  at build time and changing one breaks every NEEDED reference to the old name.
  Provided only as the macho_change_id analog. Callers should almost always
  leave the SONAME alone."""
  assert host.IsLinux
  run([_tool("patchelf"), "--set-soname", str(soname), str(elf_path)],
      do_log=False)

def elf_set_rpath(elf_path, rpaths, force_rpath=True):
  """Set the RPATH of an ELF object.

  Args:
    rpaths:      list of entries (e.g. ['$ORIGIN', '$ORIGIN/../lib']) or a
                 pre-joined ':' string.
    force_rpath: True  -> write legacy DT_RPATH (applies transitively to the
                          whole dependency chain — simplest for a self-contained
                          bundle, matches Mach-O @rpath propagation).
                 False -> write modern DT_RUNPATH (non-transitive; every object
                          must then carry its own $ORIGIN rpath).
  """
  assert host.IsLinux
  joined = rpaths if isinstance(rpaths, str) else ":".join(rpaths)
  # Idempotency guard: skip if the rpath is already exactly what we want. A
  # repeated patchelf --set-rpath can GROW the file each call and eventually
  # corrupt it ("data region extends past file end"), which is easy to trigger
  # when the same physical inode is reached via multiple hardlink names (e.g.
  # pythonX.Yt hardlinked to pythonX.Y) or across phases.
  try:
    if capture([_tool("patchelf"), "--print-rpath", str(elf_path)],
               do_log=False).strip() == joined:
      return
  except Exception:
    pass
  cmd = [_tool("patchelf")]
  if force_rpath:
    cmd.append("--force-rpath")
  cmd += ["--set-rpath", joined, str(elf_path)]
  run(cmd, do_log=False)

def elf_replace_needed(elf_path, old, new):
  """Replace a single DT_NEEDED entry (the ELF analog of an install_name_tool
  -change). Only used for the rare case of a NEEDED entry that carries a path
  separator or absolute path instead of a bare SONAME."""
  assert host.IsLinux
  run([_tool("patchelf"), "--replace-needed", str(old), str(new),
       str(elf_path)], do_log=False)

###############################################################################
# ldd-based closure resolution
###############################################################################

# `libfoo.so.1 => /abs/path/libfoo.so.1 (0x...)`  |  `libfoo.so.1 => not found`
# `/lib64/ld-linux-x86-64.so.2 (0x...)`           |  `linux-vdso.so.1 (0x...)`
# NOTE: "not found" MUST precede \S+ in the alternation, else \S+ greedily
# captures just "not" and a missing lib is mis-read as resolved-to-"not".
_LDD_ARROW = re.compile(r"^\s*(\S+)\s*=>\s*(not found|\S+)")
_LDD_BARE  = re.compile(r"^\s*(/\S+)\s*\(0x")

def ldd_resolve(elf_path, extra_ld_library_path=None):
  """Resolve an ELF object's *full transitive* dependency closure via ldd.

  Returns a dict {soname: resolved_path_or_None}. ldd runs the real dynamic
  loader, so it honors the object's own RPATH/RUNPATH ($ORIGIN expanded) — this
  gives the exact soname->file mapping including transitive deps in one call.

  `not found` entries map to None. The vDSO and the loader itself are omitted.
  """
  assert host.IsLinux
  env = dict(os.environ)
  # For build-time closure discovery we honor the object's own rpath; callers
  # (the verifier) pass extra_ld_library_path="" to force a clean resolution.
  if extra_ld_library_path is not None:
    env["LD_LIBRARY_PATH"] = extra_ld_library_path
  try:
    proc = subprocess.run(["ldd", str(elf_path)], capture_output=True,
                          text=True, env=env)
    lines = proc.stdout.splitlines()
  except Exception:
    return {}
  result = {}
  for ln in lines:
    if "linux-vdso" in ln or "ld-linux" in ln or "/ld-" in ln:
      continue
    m = _LDD_ARROW.match(ln)
    if m:
      soname, tgt = m.group(1), m.group(2)
      result[soname] = None if tgt == "not found" else tgt
      continue
    # bare absolute (e.g. the loader) — skip; already filtered above
  return result

###############################################################################
# discovery
###############################################################################

# Directories to skip when scanning a staging tree (mirrors macos.DEPLOY_SKIP_DIRS)
DEPLOY_SKIP_DIRS = {'builds', 'include', 'manifests', 'buildlogs',
                    'nanobind', 'sdks', 'subspaces', 'tempdir',
                    'doc', 'apps'}

def _looks_like_elf_name(fname):
  base, ext = os.path.splitext(fname)
  if ext in _ELF_EXTENSIONS:          # .so
    return True
  if ext == '':                        # bare executable
    return True
  if ext and ext[1:].isdigit():        # versioned .so.1 / .so.1.2.3
    return True
  return False

def discover_elf_files(root_dir, skip_dirs=None):
  """Find all ELF objects under root_dir (real files only, symlinks skipped).

  Dynamic discovery — no hardcoded lists. Mirrors discover_macho_files.
  """
  if skip_dirs is None:
    skip_dirs = set()
  root_dir = path.Path(root_dir)
  result = []
  seen_inodes = set()   # dedup hardlinks: one physical file -> patch once
  for dirpath, dirnames, filenames in os.walk(str(root_dir), followlinks=False):
    dirnames[:] = [d for d in dirnames if d not in skip_dirs]
    for fname in filenames:
      fpath = os.path.join(dirpath, fname)
      if os.path.islink(fpath) or not os.path.isfile(fpath):
        continue
      if _looks_like_elf_name(fname) and is_elf_binary(fpath):
        try:
          st = os.stat(fpath)
          key = (st.st_dev, st.st_ino)
          if key in seen_inodes:
            continue           # already returned via another hardlink name
          seen_inodes.add(key)
        except OSError:
          pass
        result.append(path.Path(fpath))
  return result

###############################################################################
# system-vs-bundle policy
###############################################################################

# SONAMEs that must ALWAYS be provided by the host, never internalized. Two
# groups:
#   (1) glibc core + loader + toolchain runtime — ABI-tied to the host kernel
#       and dynamic loader; bundling them across distros is fragile.
#   (2) GPU / display / driver / audio userspace — must match the host kernel
#       driver + (under Flatpak) arrive via org.freedesktop.Platform.GL.* .
# This is the Linux analog of macOS's "/usr/lib + /System are system" rule and
# is the ONE real policy knob of the port — tune via keep_on_host_extra /
# bundle_anyway on the walker.
KEEP_ON_HOST_EXACT = {
  "libc.so.6", "libm.so.6", "libdl.so.2", "libpthread.so.0", "librt.so.1",
  "libresolv.so.2", "libutil.so.1", "libnsl.so.1", "libanl.so.1",
  "libgcc_s.so.1", "libstdc++.so.6", "libmvec.so.1",
  # driver ICD loaders — must be host (kernel-driver ABI)
  "libGL.so.1", "libGLX.so.0", "libGLdispatch.so.0", "libOpenGL.so.0",
  "libEGL.so.1", "libGLESv2.so.2", "libGLU.so.1",
  "libvulkan.so.1", "libOpenCL.so.1",
  "libgbm.so.1", "libdrm.so.2",
}
# prefix patterns (soname.startswith) that are always host-provided
KEEP_ON_HOST_PREFIXES = (
  "ld-linux", "linux-vdso", "libc.so", "libm.so", "libpthread",
  "libX",            # libX11, libXext, libXrandr, libXi, ...
  "libxcb",          # xcb stack
  "libwayland-", "libxkbcommon", "libdecor",
  "libasound", "libpulse", "libpipewire", "libjack",
  "libdbus-", "libsystemd", "libudev",
  "libnvidia-", "libcuda",   # proprietary NVIDIA userspace — never bundle
)

def is_keep_on_host(soname, keep_extra=(), bundle_anyway=()):
  base = os.path.basename(soname)
  if base in bundle_anyway:
    return False
  if base in KEEP_ON_HOST_EXACT or base in set(keep_extra):
    return True
  return any(base.startswith(p) for p in KEEP_ON_HOST_PREFIXES)

def internalize_lib(src_lib, lib_dir):
  """Copy an external .so into lib_dir as a self-contained, SONAME-linked entry.

  ELF consumers reference a dependency by its SONAME (e.g. `libavcodec.so.60`),
  which on disk is usually a symlink to the real versioned file
  (`libavcodec.so.60.31.102`). To keep the bundle self-contained we copy the
  REAL file and recreate the SONAME (and the ldd-referenced basename) as
  symlinks pointing at it, so the loader resolves by SONAME within lib/.

  This is the ELF analog of the macOS "copy homebrew dylib into lib/" step
  (Mach-O needs no symlink because it references by full basename).

  Returns the destination real-file path, or None if the source is missing.
  """
  lib_dir = path.Path(lib_dir)
  lib_dir.mkdir(parents=True, exist_ok=True)
  real = os.path.realpath(str(src_lib))
  if not os.path.isfile(real):
    return None
  realbase = os.path.basename(real)
  dest = lib_dir / realbase
  if not dest.exists():
    shutil.copy2(real, str(dest))
  # Recreate the SONAME + the referenced basename as symlinks -> realbase.
  linknames = set()
  soname = elf_get_soname(real)
  if soname:
    linknames.add(os.path.basename(soname))
  linknames.add(os.path.basename(str(src_lib)))
  for ln in linknames:
    if ln and ln != realbase:
      lp = lib_dir / ln
      if not lp.exists():
        try:
          os.symlink(realbase, str(lp))
        except FileExistsError:
          pass
  return str(dest)

###############################################################################

class ElfDependencyWalker:
  """Recursively resolves the ELF dependency closure of a staging tree and
  partitions it into (STAGING / SYSTEM / BUNDLE / MISSING).

  Analog of MachoDependencyWalker. The 'BUNDLE' set is the ELF analog of the
  macOS 'homebrew closure' — the third-party libs that must be internalized
  into the bundle's lib/. Uses ldd for transitive resolution (one ldd call
  yields the full recursive closure of a seed).
  """

  SYSTEM  = "SYSTEM"     # keep-on-host (glibc/toolchain/driver)
  STAGING = "STAGING"    # already inside the staging tree
  BUNDLE  = "BUNDLE"     # third-party lib to internalize (homebrew analog)
  MISSING = "MISSING"    # ldd reported 'not found'

  def __init__(self, root_dir, keep_on_host_extra=(), bundle_anyway=()):
    self.root_dir = path.Path(root_dir)
    self.keep_extra = set(keep_on_host_extra)
    self.bundle_anyway = set(bundle_anyway)
    self.seed_files = []
    # soname -> resolved path (as seen from any seed)
    self.resolved = {}
    self.by_category = {self.SYSTEM: set(), self.STAGING: set(),
                        self.BUNDLE: set(), self.MISSING: set()}
    self._walked = False

  def discover_seeds(self, skip_dirs=None):
    if skip_dirs is None:
      skip_dirs = DEPLOY_SKIP_DIRS
    self.seed_files = discover_elf_files(self.root_dir, skip_dirs=skip_dirs)
    return self.seed_files

  def classify(self, soname, resolved_path):
    if resolved_path is None:
      return self.MISSING
    rp = os.path.realpath(resolved_path)
    if rp.startswith(os.path.realpath(str(self.root_dir)) + os.sep):
      return self.STAGING
    if is_keep_on_host(soname, self.keep_extra, self.bundle_anyway):
      return self.SYSTEM
    return self.BUNDLE

  def walk(self):
    if not self.seed_files:
      self.discover_seeds()
    print(deco.val(f"Walking {len(self.seed_files)} ELF binaries (ldd)..."))
    for i, seed in enumerate(self.seed_files):
      for soname, tgt in ldd_resolve(seed).items():
        # keep the first non-None resolution we see for a soname
        if soname not in self.resolved or self.resolved[soname] is None:
          self.resolved[soname] = tgt
      if (i + 1) % 100 == 0:
        print(deco.val(f"  Processed {i+1}/{len(self.seed_files)}..."))
    for soname, tgt in self.resolved.items():
      cat = self.classify(soname, tgt)
      self.by_category[cat].add(soname if cat == self.MISSING else (tgt or soname))
    self._walked = True
    print(deco.val(f"  STAGING={len(self.by_category[self.STAGING])} "
                   f"SYSTEM={len(self.by_category[self.SYSTEM])} "
                   f"BUNDLE={len(self.by_category[self.BUNDLE])} "
                   f"MISSING={len(self.by_category[self.MISSING])}"))
    return self.by_category

  def get_bundle_closure(self):
    """Return the set of external .so *paths* to internalize into lib/
    (the homebrew-closure analog). Resolves symlinks to real files."""
    if not self._walked:
      self.walk()
    return set(self.by_category[self.BUNDLE])

  def get_missing(self):
    if not self._walked:
      self.walk()
    return set(self.by_category[self.MISSING])

  def dump_manifest(self):
    if not self._walked:
      self.walk()
    print(deco.val("=" * 60))
    print(deco.val("ELF Dependency Walk Manifest"))
    print(deco.val("=" * 60))
    for cat in (self.STAGING, self.SYSTEM, self.BUNDLE, self.MISSING):
      items = sorted(self.by_category[cat])
      print(deco.val(f"  [{cat}] ({len(items)}):"))
      for it in items[:20]:
        print(deco.val(f"    {it}"))
      if len(items) > 20:
        print(deco.val(f"    ... and {len(items)-20} more"))

###############################################################################

class ElfRelocator:
  """Rewrites ELF RPATHs for a fully relocatable deployment.

  Analog of MachoRelocator, but collapses to essentially one operation:
  set each object's RPATH to a $ORIGIN-relative reach to lib/ (and pyvenv/lib/).
  There is NO id-change, NO per-dep rewrite, and NO codesign on Linux.
  """

  def __init__(self, target_dir, force_rpath=True):
    self.target_dir = path.Path(target_dir)
    self.lib_dir = self.target_dir / "lib"
    self.pyvenv_dir = self.target_dir / "pyvenv"
    self.force_rpath = force_rpath
    self.modified_files = set()

  @staticmethod
  def compute_origin_to(binary_path, target_dir):
    """Return '$ORIGIN/<rel>' reaching target_dir from the binary's directory
    (the ELF analog of @loader_path/<rel>). '$ORIGIN' itself if same dir."""
    binary_dir = os.path.dirname(str(binary_path))
    rel = os.path.relpath(str(target_dir), binary_dir)
    return "$ORIGIN" if rel == "." else "$ORIGIN/" + rel

  def relocate_needed(self, binary_path):
    """Fix any DT_NEEDED entry that is NOT a bare SONAME (has a path separator
    or is absolute) down to its basename. Normal builds have bare SONAMEs so
    this is usually a no-op."""
    binary_str = str(binary_path)
    for dep in elf_enumerate_needed(binary_str):
      if "/" in dep:
        elf_replace_needed(binary_str, dep, os.path.basename(dep))
        self.modified_files.add(binary_str)

  def relocate_rpath(self, binary_path):
    """Add $ORIGIN-relative reaches to lib/ (and pyvenv/lib/ for objects under
    pyvenv), while PRESERVING any existing $ORIGIN-relative entries.

    Preserving matters for auditwheel/manylinux wheels: their extension modules
    carry a self-referential rpath like `$ORIGIN/../pkg.libs` that lets them
    find their bundled sibling libraries. Clobbering it breaks the wheel. We
    keep every existing $ORIGIN entry and drop only absolute entries (build-host
    staging paths that leak and won't exist post-move)."""
    binary_str = str(binary_path)
    # Keep existing self-relative entries (vendored .libs reaches, etc.);
    # absolute entries are dropped by simply not carrying them over.
    rpaths = [rp for rp in elf_enumerate_rpaths(binary_str)
              if rp.startswith("$ORIGIN")]
    def _add(rp):
      if rp not in rpaths:
        rpaths.append(rp)
    _add(self.compute_origin_to(binary_path, self.lib_dir))
    pyvenv_lib = self.pyvenv_dir / "lib"
    if pyvenv_lib.exists() and str(self.pyvenv_dir) in binary_str:
      _add(self.compute_origin_to(binary_path, pyvenv_lib))
    # a self-reach ($ORIGIN) is cheap insurance for sibling dylibs in lib/
    _add("$ORIGIN")
    elf_set_rpath(binary_str, rpaths, force_rpath=self.force_rpath)
    self.modified_files.add(binary_str)

  def relocate_binary(self, binary_path, is_dylib=False):
    """Full relocation of one ELF object. `is_dylib` is accepted for signature
    parity with MachoRelocator.relocate_binary but is unused (no id-change on
    ELF)."""
    self.relocate_needed(binary_path)
    self.relocate_rpath(binary_path)

  def relocate_all(self, skip_dirs=None):
    """Relocate every ELF object in the target tree."""
    if skip_dirs is None:
      skip_dirs = DEPLOY_SKIP_DIRS
    all_elfs = discover_elf_files(self.target_dir, skip_dirs=skip_dirs)
    print(deco.val(f"Relocating {len(all_elfs)} ELF binaries ($ORIGIN)..."))
    for i, elf in enumerate(all_elfs):
      try:
        self.relocate_binary(elf)
      except Exception as e:
        print(deco.val(f"  WARNING: relocate failed for {elf}: {e}"))
      if (i + 1) % 50 == 0:
        print(deco.val(f"  Relocated {i+1}/{len(all_elfs)}..."))
    print(deco.val(f"  Relocated all {len(all_elfs)} binaries"))

  def resign_all(self):
    """No-op on Linux — ELF needs no re-signing after patchelf. Present only
    for signature parity with MachoRelocator."""
    return

###############################################################################

class ElfVerifier:
  """Verifies that every ELF in a relocated tree resolves its deps inside the
  bundle (or against an allowed host lib) with a CLEAN environment.

  Analog of MachoVerifier: runs ldd with LD_LIBRARY_PATH="" so resolution
  depends solely on the baked $ORIGIN RPATHs, then FAILs on any 'not found' or
  any dep that resolves to a non-allowed out-of-bundle path.
  """

  def __init__(self, root_dir, keep_on_host_extra=(), bundle_anyway=()):
    self.root_dir = path.Path(root_dir)
    self.keep_extra = set(keep_on_host_extra)
    self.bundle_anyway = set(bundle_anyway)
    self.results = {}
    self.pass_count = 0
    self.fail_count = 0
    self.warn_count = 0

  def verify(self):
    root_real = os.path.realpath(str(self.root_dir))
    all_elfs = discover_elf_files(self.root_dir, skip_dirs=DEPLOY_SKIP_DIRS)
    print(deco.val(f"Verifying {len(all_elfs)} ELF binaries (clean env)..."))
    self.pass_count = self.fail_count = self.warn_count = 0
    for elf in all_elfs:
      elf_str = str(elf)
      dep_results = []
      for soname, tgt in ldd_resolve(elf, extra_ld_library_path="").items():
        if tgt is None:
          if is_keep_on_host(soname, self.keep_extra, self.bundle_anyway):
            # a keep-on-host lib absent in the clean check env is only a warning
            dep_results.append((soname, "WARN", "host lib not found in env"))
            self.warn_count += 1
          else:
            dep_results.append((soname, "FAIL", "not found"))
            self.fail_count += 1
          continue
        rp = os.path.realpath(tgt)
        if rp.startswith(root_real + os.sep):
          dep_results.append((soname, "OK", f"-> {tgt}"))
          self.pass_count += 1
        elif is_keep_on_host(soname, self.keep_extra, self.bundle_anyway):
          dep_results.append((soname, "OK", f"host -> {tgt}"))
          self.pass_count += 1
        else:
          dep_results.append((soname, "FAIL", f"resolves OUTSIDE bundle: {tgt}"))
          self.fail_count += 1
      self.results[elf_str] = dep_results
    total = self.pass_count + self.fail_count + self.warn_count
    print(deco.val(f"Verification: {self.pass_count} OK, {self.fail_count} FAIL, "
                   f"{self.warn_count} WARN (of {total} refs across "
                   f"{len(all_elfs)} binaries)"))
    return self.fail_count == 0

  def get_failures(self):
    failures = {}
    for binary, dep_results in self.results.items():
      fails = [(d, s, det) for d, s, det in dep_results if s == "FAIL"]
      if fails:
        failures[binary] = fails
    return failures

  def dump_report(self):
    print(deco.val("=" * 60))
    print(deco.val("ELF Verification Report"))
    print(deco.val("=" * 60))
    print(deco.val(f"Total binaries: {len(self.results)}"))
    print(deco.val(f"Pass: {self.pass_count}  Fail: {self.fail_count}  "
                   f"Warn: {self.warn_count}"))
    failures = self.get_failures()
    if failures:
      print(deco.val("FAILURES:"))
      for binary, fails in sorted(failures.items()):
        rel = os.path.relpath(binary, str(self.root_dir))
        print(deco.val(f"  {rel}:"))
        for dep, status, detail in fails:
          print(deco.val(f"    [{status}] {dep}  {detail}"))
    else:
      print(deco.val("All references resolved successfully!"))

###############################################################################
# compat aliases — let a platform selector do `relo = macos if IsOsx else linux`
# with minimal edits in deploy_phases. Names mirror obt.macos where the
# semantics line up 1:1.
###############################################################################
is_macho_binary        = is_elf_binary
macho_enumerate_dylibs = elf_enumerate_needed
macho_enumerate_rpaths = elf_enumerate_rpaths
macho_change_id        = elf_set_soname
discover_macho_files   = discover_elf_files
MachoDependencyWalker  = ElfDependencyWalker
MachoRelocator         = ElfRelocator
MachoVerifier          = ElfVerifier
