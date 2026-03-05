#!/usr/bin/env python3
###############################################################################
import sys, os, subprocess
from obt import host, path, pathtools
from obt.command import capture, run
from obt.command import Deco
deco = Deco()
###############################################################################
def find_replace(inpstring, dictionary):
  print(dictionary)
  for item in inpstring:
    if item in dictionary.keys():
      print("replacing item<%s>"%item)
      inpstring = inpstring.replace(item, dictionary[item])
  return inpstring

###############################################################################

def macho_enumerate_dylibs(mach_o_path):
  assert (host.IsOsx)
  loadlines = capture(["otool","-l",mach_o_path],do_log=False).splitlines()
  cmdindex = 0
  cmd = None
  name = None
  state = 0
  dylib_paths = list()
  for line in loadlines:
    tokens = line.split(" ")
    tokens = [i for i in tokens if i]
    if state==0:
      if tokens[0]=="Load" and tokens[1]=="command":
        cmdindex = int(tokens[2])
        state = 1
    elif state==1:
      if tokens[0]=="cmd" and tokens[1]=="LC_LOAD_DYLIB":
        cmd = "LC_LOAD_DYLIB"
        state = 2
    elif state==2:
      if tokens[0] == "name":
        dylib_paths += [tokens[1]]
        state=0
    else:
      assert(False)
  return dylib_paths

###############################################################################

def macho_get_all_dylib_dependencies(file_path, seen=None):
  """Recursively get a list of dynamic library dependencies for the file."""
  if seen is None:
    seen = set()
  if not os.path.exists(file_path) or not os.path.isfile(file_path):
    return seen
  deps = subprocess.check_output(['otool', '-L', file_path]).decode()
  for line in deps.splitlines()[1:]:
    dylib = line.split()[0]
    if dylib not in seen:
      seen.add(dylib)
      macho_get_all_dylib_dependencies(dylib, seen)
  return seen

###############################################################################

def macho_replace_loadpaths(mach_o_path,search,replace):
  assert (host.IsOsx)
  str_search = str(search)
  str_replace = str(replace)
  dylib_paths = macho_enumerate_dylibs(mach_o_path)
  for inpitem in dylib_paths:
    outitem = inpitem.replace(str_search, str_replace)
    #print("mach_o_path: " + str(mach_o_path) + " inp: " + inpitem + " search: " + str_search + " replace: " + str_replace)
    if outitem!=inpitem:
      run(["install_name_tool","-change",inpitem,outitem,mach_o_path],do_log=False)

###############################################################################

def macho_change_id(mach_o_path,id_str):
  assert (host.IsOsx)
  run(["install_name_tool","-id",'%s'%id_str,mach_o_path],do_log=False)

###############################################################################

def macho_get_id(mach_o_path):
  assert (host.IsOsx)
  return capture(["otool","-D",mach_o_path],do_log=False)

##############################################################################

def macho_dump(mach_o_path):
  print(deco.val("/////////////////////////////////////////////////////////"))
  print(deco.val("MachO Dump: ") + deco.val(mach_o_path))
  print(deco.val("/////////////////////////////////////////////////////////"))
  dylib_paths = macho_enumerate_dylibs(mach_o_path)
  for item in dylib_paths:
    print(deco.val("dylib: ")+deco.path(item))
  print(deco.val("/////////////////////////////////////////////////////////"))

##############################################################################

def enumerateOrkLibs(basepath):
  return pathtools.recursive_patglob(basepath,"libork*.dylib")

##############################################################################

def enumerateOrkPyMods(basepath):
  return pathtools.recursive_patglob(basepath,"*.so")

##############################################################################

class DylibReference(object):
  def __init__(self):
    self.references = set()

##############################################################################

def is_macho_binary(file_path):
  """Check if a file is a Mach-O binary."""
  try:
    result = subprocess.run(['file', str(file_path)], capture_output=True, text=True)
    return 'Mach-O' in result.stdout
  except:
    return False

##############################################################################

def framework_enumerate_binaries(framework_path):
  """
  Find all Mach-O binaries in a framework.
  Returns list of paths to binaries (dylibs, main binary, .cti files, etc.)
  """
  binaries = []
  framework_path = path.Path(framework_path)

  # Walk the framework directory
  for root, dirs, files in os.walk(str(framework_path)):
    # Skip dSYM directories (debug symbols)
    dirs[:] = [d for d in dirs if not d.endswith('.dSYM')]

    for fname in files:
      fpath = os.path.join(root, fname)
      # Check common extensions and verify it's actually Mach-O
      if fname.endswith(('.dylib', '.cti', '.so')) or (
          '.' not in fname and os.path.isfile(fpath) and is_macho_binary(fpath)):
        if is_macho_binary(fpath):
          binaries.append(path.Path(fpath))

  return binaries

##############################################################################

def install_framework_to_stage(src_framework_path, framework_name=None, stage_lib_dir=None, force=False):
  """
  Copy a macOS framework to the staging lib directory and fix all install names.

  Changes hardcoded /Library/Frameworks/xxx.framework/... paths to
  @rpath/xxx.framework/... so consumers only need staging lib in their RPATH.

  Args:
    src_framework_path: Path to source framework (e.g., /path/to/xxx.framework)
    framework_name: Name of framework (derived from path if not provided)
    stage_lib_dir: Destination lib directory (defaults to path.libs())
    force: If True, reinstall even if framework already exists

  Returns:
    Path to installed framework
  """
  assert host.IsOsx, "install_framework_to_stage only works on macOS"

  src_framework_path = path.Path(src_framework_path)

  # Derive framework name from path if not provided
  if framework_name is None:
    framework_name = src_framework_path.name
    if framework_name.endswith('.framework'):
      framework_name = framework_name[:-10]  # Remove .framework suffix

  # Default to staging lib directory
  if stage_lib_dir is None:
    stage_lib_dir = path.libs()
  else:
    stage_lib_dir = path.Path(stage_lib_dir)

  dest_framework_path = stage_lib_dir / f"{framework_name}.framework"

  # Skip if already installed (unless force=True)
  if dest_framework_path.exists() and not force:
    print(deco.val(f"Framework {framework_name} already installed at {dest_framework_path}"))
    return dest_framework_path

  print(deco.val(f"Installing framework: {framework_name}"))
  print(deco.val(f"  Source: {src_framework_path}"))
  print(deco.val(f"  Dest:   {dest_framework_path}"))

  # Remove quarantine from source first (in case it was cloned/downloaded)
  print(deco.val(f"  Removing quarantine attribute from source..."))
  run(["xattr", "-rd", "com.apple.quarantine", str(src_framework_path)], do_log=True)

  # Copy framework to staging (preserve symlinks with -a)
  pathtools.mkdir(stage_lib_dir, parents=True)
  # Don't use pathtools.copydir - it uses cp -r which dereferences symlinks
  # Use cp -a to preserve symlinks, which is critical for framework structure
  if dest_framework_path.exists():
    run(["rm", "-rf", str(dest_framework_path)], do_log=True)
  run(["cp", "-a", str(src_framework_path), str(dest_framework_path)], do_log=True)

  # Remove quarantine extended attribute from destination as well
  print(deco.val(f"  Removing quarantine attribute from destination..."))
  run(["xattr", "-rd", "com.apple.quarantine", str(dest_framework_path)], do_log=True)

  # Find all Mach-O binaries in the installed framework
  binaries = framework_enumerate_binaries(dest_framework_path)

  # The old prefix we're replacing
  old_prefix = f"/Library/Frameworks/{framework_name}.framework"
  # The new prefix using @rpath
  new_prefix = f"@rpath/{framework_name}.framework"

  for binary in binaries:
    print(deco.val(f"  Fixing: {binary.name}"))

    # Get current install name ID
    current_id = macho_get_id(str(binary)).strip().split('\n')[-1].strip()

    # Fix the install name ID if it contains the old prefix
    if old_prefix in current_id:
      new_id = current_id.replace(old_prefix, new_prefix)
      print(deco.val(f"    ID: {current_id} -> {new_id}"))
      macho_change_id(str(binary), new_id)

    # Fix load commands that reference the old prefix
    macho_replace_loadpaths(str(binary), old_prefix, new_prefix)

  # Re-sign with ad-hoc signature (required after install_name_tool modifications)
  # Sign in proper order: nested libraries first, then main binary, then framework bundle
  # Use hardened runtime for better Gatekeeper compatibility
  # IMPORTANT: Must sign actual files, not symlinks - use resolve() to follow symlinks
  print(deco.val(f"  Re-signing framework (ad-hoc with hardened runtime)..."))

  sign_args = ["codesign", "-s", "-", "--force", "--options", "runtime"]

  # Find the actual Versions directory (follow Current symlink)
  versions_current = dest_framework_path / "Versions" / "Current"
  if versions_current.is_symlink():
    actual_version_dir = versions_current.resolve()
  else:
    actual_version_dir = versions_current

  # Sign nested libraries first (use actual paths, not symlinks)
  libraries_dir = actual_version_dir / "Libraries"
  if libraries_dir.exists():
    for lib in libraries_dir.iterdir():
      real_lib = lib.resolve() if lib.is_symlink() else lib
      if real_lib.is_file() and is_macho_binary(str(real_lib)):
        print(deco.val(f"    Signing: {lib.name}"))
        run(sign_args + [str(real_lib)], do_log=True)

  # Sign main binary (use actual path, not symlink)
  main_binary = actual_version_dir / framework_name
  if main_binary.exists():
    real_main = main_binary.resolve() if main_binary.is_symlink() else main_binary
    print(deco.val(f"    Signing: {framework_name} (main binary)"))
    run(sign_args + [str(real_main)], do_log=True)

  # Sign the framework bundle
  print(deco.val(f"    Signing: {framework_name}.framework (bundle)"))
  run(sign_args + [str(dest_framework_path)], do_log=True)

  print(deco.val(f"  Framework installed successfully"))
  return dest_framework_path

##############################################################################

class DylibReferenceDatabase(object):
  def __init__(self):
    self.referencers = dict()
    self.references = set()
  def probe(self,dylib_list):
    for item in dylib_list:
      deps = macho_enumerate_dylibs(item)
      for dep in deps:
        if str(homebrew_dir) in dep:
          key = str(item)
          print(key)
          self.referencers.setdefault(key, DylibReference()).references.add(dep)
          self.references.add(dep)
  def probe_in(self,directory,dylib_list):
    for item in dylib_list:
      deps = macho_enumerate_dylibs(item)
      for dep in deps:
        if str(directory) in dep:
          key = str(item)
          print(key)
          self.referencers.setdefault(key, DylibReference()).references.add(dep)
          self.references.add(dep)
      #macho_dump(item)
  def dump_referencers(self):
    for item in self.referencers:
      print(item)
  def dump_references(self):
    for item in self.references:
      print(item)

##############################################################################
# Deployment infrastructure — helpers and classes for relocatable deployment
##############################################################################

def macho_enumerate_rpaths(mach_o_path):
  """Extract all LC_RPATH entries from a Mach-O binary."""
  assert (host.IsOsx)
  loadlines = capture(["otool","-l",mach_o_path],do_log=False).splitlines()
  state = 0
  rpaths = list()
  for line in loadlines:
    tokens = line.split(" ")
    tokens = [i for i in tokens if i]
    if len(tokens) < 2:
      continue
    if state==0:
      if tokens[0]=="Load" and tokens[1]=="command":
        state = 1
    elif state==1:
      if tokens[0]=="cmd" and tokens[1]=="LC_RPATH":
        state = 2
    elif state==2:
      if tokens[0] == "path":
        rpaths.append(tokens[1])
        state = 0
    else:
      assert(False)
  return rpaths

##############################################################################

# File extensions that indicate a Mach-O binary (checked before expensive `file` call)
_MACHO_EXTENSIONS = {'.dylib', '.so', '.bundle', '.cti'}

def discover_macho_files(root_dir, skip_dirs=None):
  """Find all Mach-O binaries under root_dir.

  Discovers dynamically — no hardcoded file lists or version numbers.
  Skips symlinks (returns only real files to avoid processing duplicates).

  Args:
    root_dir: Directory to scan
    skip_dirs: Set of directory names to skip (e.g. {'builds', 'include'})

  Returns:
    List of Path objects to Mach-O binaries
  """
  if skip_dirs is None:
    skip_dirs = set()
  root_dir = path.Path(root_dir)
  result = []
  for dirpath, dirnames, filenames in os.walk(str(root_dir), followlinks=False):
    dirnames[:] = [d for d in dirnames
                   if d not in skip_dirs
                   and not d.endswith('.dSYM')
                   and not d.endswith('.framework')]
    for fname in filenames:
      fpath = os.path.join(dirpath, fname)
      if os.path.islink(fpath):
        continue
      if not os.path.isfile(fpath):
        continue
      _, ext = os.path.splitext(fname)
      if ext in _MACHO_EXTENSIONS or ext == '' or (ext and ext[1:].isdigit()):
        if is_macho_binary(fpath):
          result.append(path.Path(fpath))
  # Also scan frameworks separately (since we skip .framework dirs above)
  for dirpath, dirnames, filenames in os.walk(str(root_dir), followlinks=False):
    fw_dirs = [d for d in dirnames if d.endswith('.framework')]
    dirnames[:] = [d for d in dirnames
                   if d not in skip_dirs
                   and not d.endswith('.dSYM')
                   and not d.endswith('.framework')]
    for fw in fw_dirs:
      fw_path = os.path.join(dirpath, fw)
      result.extend(framework_enumerate_binaries(fw_path))
  return result

##############################################################################

# Default directories to skip when scanning for deployment
DEPLOY_SKIP_DIRS = {'builds', 'include', 'manifests', 'buildlogs',
                    'nanobind', 'sdks', 'subspaces', 'tempdir',
                    'doc', 'apps'}

##############################################################################

class MachoDependencyWalker:
  """Recursively walks Mach-O dependencies building a complete closure.

  All discovery is dynamic — no hardcoded versions, paths, or file lists.
  The walker finds everything by following actual Mach-O load commands.
  """

  SYSTEM     = "SYSTEM"
  STAGING    = "STAGING"
  HOMEBREW   = "HOMEBREW"
  RPATH      = "RPATH"
  EXECPATH   = "EXECPATH"
  LOADERPATH = "LOADERPATH"
  PYVENV     = "PYVENV"
  UNKNOWN    = "UNKNOWN"

  def __init__(self, root_dir, homebrew_dir="/opt/homebrew"):
    self.root_dir = path.Path(root_dir)
    self.homebrew_dir = path.Path(homebrew_dir)
    self.seed_files = []
    self.binary_info = {}
    self.homebrew_closure = set()
    self._walked = False

  def discover_seeds(self, skip_dirs=None):
    """Find all Mach-O binaries in the root tree."""
    if skip_dirs is None:
      skip_dirs = DEPLOY_SKIP_DIRS
    self.seed_files = discover_macho_files(self.root_dir, skip_dirs=skip_dirs)
    return self.seed_files

  def classify_dep(self, dep_path):
    """Classify a dependency path into a category."""
    dep_str = str(dep_path)
    if dep_str.startswith("/usr/lib/") or dep_str.startswith("/System/"):
      return self.SYSTEM
    elif dep_str.startswith("@rpath/"):
      return self.RPATH
    elif dep_str.startswith("@executable_path/"):
      return self.EXECPATH
    elif dep_str.startswith("@loader_path/"):
      return self.LOADERPATH
    elif str(self.homebrew_dir) in dep_str:
      return self.HOMEBREW
    elif str(self.root_dir) in dep_str:
      pyvenv_dir = self.root_dir / "pyvenv"
      if str(pyvenv_dir) in dep_str:
        return self.PYVENV
      return self.STAGING
    else:
      return self.UNKNOWN

  def walk(self):
    """Walk from all seed Mach-O files, building full transitive closure."""
    if not self.seed_files:
      self.discover_seeds()

    print(deco.val(f"Walking {len(self.seed_files)} Mach-O binaries..."))

    for i, seed in enumerate(self.seed_files):
      self._process_binary(str(seed))
      if (i+1) % 100 == 0:
        print(deco.val(f"  Processed {i+1}/{len(self.seed_files)}..."))

    print(deco.val(f"  Processed {len(self.seed_files)} seed binaries"))
    print(deco.val(f"  Found {len(self.homebrew_closure)} direct homebrew references"))

    # Chase homebrew deps transitively
    queue = list(self.homebrew_closure)
    seen = set(self.homebrew_closure)
    transitive_count = 0

    while queue:
      hb_path = queue.pop()
      real_path = os.path.realpath(hb_path)
      if not os.path.isfile(real_path):
        continue
      try:
        deps = macho_enumerate_dylibs(real_path)
      except:
        continue
      for dep in deps:
        cat = self.classify_dep(dep)
        if cat == self.HOMEBREW and dep not in seen:
          seen.add(dep)
          real_dep = os.path.realpath(dep)
          if real_dep != dep:
            seen.add(real_dep)
          self.homebrew_closure.add(dep)
          queue.append(dep)
          transitive_count += 1

    print(deco.val(f"  Found {transitive_count} transitive homebrew deps"))
    print(deco.val(f"  Total homebrew closure: {len(self.homebrew_closure)} dylibs"))
    self._walked = True
    return self.binary_info

  def _process_binary(self, binary_path):
    """Process a single binary: extract deps and rpaths, classify deps."""
    deps = macho_enumerate_dylibs(binary_path)
    rpaths = macho_enumerate_rpaths(binary_path)
    classified = {}
    for dep in deps:
      cat = self.classify_dep(dep)
      classified[dep] = cat
      if cat == self.HOMEBREW:
        self.homebrew_closure.add(dep)
    self.binary_info[binary_path] = {
      "deps": deps,
      "rpaths": rpaths,
      "classified_deps": classified,
    }

  def get_homebrew_closure(self):
    """Return set of all homebrew dylib paths needed (with transitive deps)."""
    if not self._walked:
      self.walk()
    return self.homebrew_closure

  def get_manifest(self):
    """Return structured manifest of everything discovered."""
    if not self._walked:
      self.walk()

    by_category = {}
    binaries_with_issues = []

    for binary, info in self.binary_info.items():
      for dep, cat in info["classified_deps"].items():
        by_category.setdefault(cat, set()).add(dep)
      problems = []
      for dep, cat in info["classified_deps"].items():
        if cat in (self.STAGING, self.HOMEBREW, self.PYVENV,
                   self.EXECPATH, self.UNKNOWN):
          problems.append((dep, cat))
      if problems:
        binaries_with_issues.append((binary, problems))

    by_category_sorted = {}
    for cat in sorted(by_category.keys()):
      by_category_sorted[cat] = sorted(by_category[cat])

    return {
      "total_binaries": len(self.binary_info),
      "total_seeds": len(self.seed_files),
      "homebrew_closure_count": len(self.homebrew_closure),
      "by_category": by_category_sorted,
      "binaries_with_issues": binaries_with_issues,
    }

  def dump_manifest(self):
    """Pretty-print the manifest."""
    manifest = self.get_manifest()
    print(deco.val("=" * 60))
    print(deco.val("Mach-O Dependency Walk Manifest"))
    print(deco.val("=" * 60))
    print(deco.val(f"Total binaries scanned: {manifest['total_binaries']}"))
    print(deco.val(f"Homebrew closure size:  {manifest['homebrew_closure_count']}"))
    print()
    for cat, deps in manifest["by_category"].items():
      print(deco.val(f"  [{cat}] ({len(deps)} unique deps):"))
      for dep in deps[:10]:
        print(deco.val(f"    {dep}"))
      if len(deps) > 10:
        print(deco.val(f"    ... and {len(deps) - 10} more"))
      print()
    if manifest["binaries_with_issues"]:
      print(deco.val(f"Binaries needing fixup: {len(manifest['binaries_with_issues'])}"))

##############################################################################

class MachoRelocator:
  """Rewrites Mach-O load commands for a fully relocatable deployment.

  Uses @rpath + LC_RPATH strategy: all dylib references become @rpath/basename,
  and each binary gets LC_RPATH entries relative to itself via @loader_path.
  """

  def __init__(self, target_dir):
    self.target_dir = path.Path(target_dir)
    self.lib_dir = self.target_dir / "lib"
    self.pyvenv_dir = self.target_dir / "pyvenv"
    self.modified_files = set()

  @staticmethod
  def compute_loader_path_to(binary_path, target_dir):
    """Compute @loader_path/... relative path from binary's dir to target_dir.

    Args:
      binary_path: Absolute path to the Mach-O binary
      target_dir: Absolute path to the directory to reach

    Returns:
      String like "@loader_path/../lib" or "@loader_path/../../lib"
    """
    binary_dir = os.path.dirname(str(binary_path))
    relpath = os.path.relpath(str(target_dir), binary_dir)
    return "@loader_path/" + relpath

  def relocate_id(self, dylib_path):
    """Set a dylib's install name ID to @rpath/basename."""
    basename = os.path.basename(str(dylib_path))
    new_id = "@rpath/" + basename
    macho_change_id(str(dylib_path), new_id)
    self.modified_files.add(str(dylib_path))

  def relocate_rpaths(self, binary_path):
    """Remove absolute LC_RPATH entries and add relative ones."""
    binary_str = str(binary_path)
    current_rpaths = macho_enumerate_rpaths(binary_str)

    # Delete all existing absolute RPATHs (ones not starting with @)
    for rp in current_rpaths:
      if not rp.startswith("@"):
        run(["install_name_tool", "-delete_rpath", rp, binary_str], do_log=False)

    # Compute new relative RPATHs
    new_rpaths = set()

    # Every binary needs to reach lib/
    rp_to_lib = self.compute_loader_path_to(binary_path, self.lib_dir)
    new_rpaths.add(rp_to_lib)

    # Binaries inside pyvenv also need to reach pyvenv/lib/
    pyvenv_lib = self.pyvenv_dir / "lib"
    if pyvenv_lib.exists() and str(self.pyvenv_dir) in binary_str:
      rp_to_pyvenv_lib = self.compute_loader_path_to(binary_path, pyvenv_lib)
      if rp_to_pyvenv_lib != rp_to_lib:
        new_rpaths.add(rp_to_pyvenv_lib)

    # Add new RPATHs (skip if already present)
    current_after = macho_enumerate_rpaths(binary_str)
    for rp in new_rpaths:
      if rp not in current_after:
        run(["install_name_tool", "-add_rpath", rp, binary_str], do_log=False)

    self.modified_files.add(binary_str)

  def relocate_deps(self, binary_path, old_prefixes):
    """Rewrite dependency paths to use @rpath/basename.

    Args:
      binary_path: Path to binary to fix
      old_prefixes: List of path prefixes to replace
    """
    binary_str = str(binary_path)
    deps = macho_enumerate_dylibs(binary_str)

    for dep in deps:
      new_dep = None

      if dep.startswith("@executable_path/"):
        # @executable_path/../lib/libfoo.dylib → @rpath/libfoo.dylib
        basename = os.path.basename(dep)
        new_dep = "@rpath/" + basename
      elif dep.startswith("@rpath/") or dep.startswith("@loader_path/"):
        continue
      elif dep.startswith("/System/") or dep.startswith("/usr/lib/"):
        continue
      else:
        for prefix in old_prefixes:
          if dep.startswith(str(prefix)):
            basename = os.path.basename(dep)
            new_dep = "@rpath/" + basename
            break
        if new_dep is None and "/opt/homebrew/" in dep:
          basename = os.path.basename(dep)
          new_dep = "@rpath/" + basename
        # Handle bare-name references (no path separator) like boost libs:
        #   "libboost_atomic-mt-a64.dylib" → "@rpath/libboost_atomic-mt-a64.dylib"
        if new_dep is None and "/" not in dep and dep.endswith(".dylib"):
          new_dep = "@rpath/" + dep

      if new_dep and new_dep != dep:
        run(["install_name_tool", "-change", dep, new_dep, binary_str], do_log=False)
        self.modified_files.add(binary_str)

  def relocate_binary(self, binary_path, old_prefixes, is_dylib=False):
    """Full relocation of one binary."""
    if is_dylib:
      self.relocate_id(binary_path)
    self.relocate_rpaths(binary_path)
    self.relocate_deps(binary_path, old_prefixes)

  def relocate_all(self, old_staging_dir, homebrew_dir="/opt/homebrew"):
    """Relocate all Mach-O files in the target directory.

    Args:
      old_staging_dir: The original staging directory path to replace
      homebrew_dir: The homebrew directory path to replace
    """
    old_staging_str = str(old_staging_dir)
    homebrew_str = str(homebrew_dir)

    # Build list of all absolute prefixes to replace
    old_prefixes = [old_staging_str]
    # Add homebrew paths (opt, Cellar, lib variants)
    for hb_sub in [homebrew_str,
                   os.path.join(homebrew_str, "opt"),
                   os.path.join(homebrew_str, "Cellar"),
                   os.path.join(homebrew_str, "lib")]:
      if hb_sub not in old_prefixes:
        old_prefixes.append(hb_sub)

    # Discover all Mach-O files in target
    all_machos = discover_macho_files(self.target_dir, skip_dirs=DEPLOY_SKIP_DIRS)

    print(deco.val(f"Relocating {len(all_machos)} Mach-O binaries..."))

    for i, macho in enumerate(all_machos):
      macho_str = str(macho)
      basename = os.path.basename(macho_str)
      is_dylib = basename.endswith('.dylib')

      self.relocate_binary(macho, old_prefixes, is_dylib=is_dylib)

      if (i+1) % 50 == 0:
        print(deco.val(f"  Relocated {i+1}/{len(all_machos)}..."))

    print(deco.val(f"  Relocated all {len(all_machos)} binaries"))

  def resign_all(self):
    """Ad-hoc re-sign all modified binaries."""
    print(deco.val(f"Re-signing {len(self.modified_files)} modified binaries..."))
    for i, fpath in enumerate(sorted(self.modified_files)):
      run(["codesign", "--force", "--sign", "-", fpath], do_log=False)
      if (i+1) % 50 == 0:
        print(deco.val(f"  Signed {i+1}/{len(self.modified_files)}..."))
    print(deco.val(f"  Re-signed all {len(self.modified_files)} binaries"))

##############################################################################

class MachoVerifier:
  """Verifies that all Mach-O references in a relocated tree resolve correctly."""

  def __init__(self, root_dir):
    self.root_dir = path.Path(root_dir)
    self.results = {}
    self.pass_count = 0
    self.fail_count = 0
    self.warn_count = 0

  def _resolve_rpath_dep(self, dep, binary_path, rpaths):
    """Try to resolve an @rpath/ dependency using the binary's LC_RPATH entries.

    Returns (resolved_path, True) if found, (None, False) if not.
    """
    suffix = dep[len("@rpath/"):]
    binary_dir = os.path.dirname(str(binary_path))

    for rp in rpaths:
      if rp.startswith("@loader_path/"):
        rp_resolved = os.path.normpath(
          os.path.join(binary_dir, rp[len("@loader_path/"):]))
      elif rp.startswith("@executable_path/"):
        continue
      elif rp.startswith("/"):
        rp_resolved = rp
      else:
        continue

      candidate = os.path.join(rp_resolved, suffix)
      if os.path.exists(candidate):
        return candidate, True

    return None, False

  def verify(self):
    """Walk all Mach-O files and verify every dependency reference resolves.

    Returns True if everything passes, False if there are failures.
    """
    all_machos = discover_macho_files(self.root_dir, skip_dirs=DEPLOY_SKIP_DIRS)

    print(deco.val(f"Verifying {len(all_machos)} Mach-O binaries..."))

    self.pass_count = 0
    self.fail_count = 0
    self.warn_count = 0

    for macho in all_machos:
      macho_str = str(macho)
      deps = macho_enumerate_dylibs(macho_str)
      rpaths = macho_enumerate_rpaths(macho_str)
      dep_results = []

      for dep in deps:
        if dep.startswith("/System/") or dep.startswith("/usr/lib/"):
          dep_results.append((dep, "OK", "system"))
          self.pass_count += 1
        elif dep.startswith("@rpath/"):
          resolved, found = self._resolve_rpath_dep(dep, macho, rpaths)
          if found:
            dep_results.append((dep, "OK", f"-> {resolved}"))
            self.pass_count += 1
          else:
            dep_results.append((dep, "FAIL",
              f"unresolvable (rpaths: {rpaths})"))
            self.fail_count += 1
        elif dep.startswith("@loader_path/"):
          binary_dir = os.path.dirname(macho_str)
          resolved = os.path.normpath(
            os.path.join(binary_dir, dep[len("@loader_path/"):]))
          if os.path.exists(resolved):
            dep_results.append((dep, "OK", f"-> {resolved}"))
            self.pass_count += 1
          else:
            dep_results.append((dep, "FAIL", f"not found: {resolved}"))
            self.fail_count += 1
        elif dep.startswith("@executable_path/"):
          dep_results.append((dep, "WARN",
            "@executable_path (may not work from dlopen)"))
          self.warn_count += 1
        elif dep.startswith("/opt/homebrew/"):
          dep_results.append((dep, "FAIL", "absolute homebrew path"))
          self.fail_count += 1
        elif dep.startswith("/Users/") or dep.startswith("/home/"):
          dep_results.append((dep, "FAIL", "absolute user path"))
          self.fail_count += 1
        elif dep.startswith("/"):
          dep_results.append((dep, "WARN", "absolute path (unknown)"))
          self.warn_count += 1
        else:
          dep_results.append((dep, "WARN", "unrecognized format"))
          self.warn_count += 1

      self.results[macho_str] = dep_results

    total = self.pass_count + self.fail_count + self.warn_count
    print(deco.val(f"Verification: {self.pass_count} OK, "
                   f"{self.fail_count} FAIL, {self.warn_count} WARN "
                   f"(of {total} total refs across {len(all_machos)} binaries)"))
    return self.fail_count == 0

  def get_failures(self):
    """Return only the failing results."""
    failures = {}
    for binary, dep_results in self.results.items():
      fails = [(dep, status, detail)
               for dep, status, detail in dep_results
               if status == "FAIL"]
      if fails:
        failures[binary] = fails
    return failures

  def dump_report(self):
    """Print a detailed verification report."""
    print(deco.val("=" * 60))
    print(deco.val("Mach-O Verification Report"))
    print(deco.val("=" * 60))
    print(deco.val(f"Total binaries: {len(self.results)}"))
    print(deco.val(f"Pass: {self.pass_count}  Fail: {self.fail_count}  "
                   f"Warn: {self.warn_count}"))
    print()

    failures = self.get_failures()
    if failures:
      print(deco.val("FAILURES:"))
      for binary, fails in sorted(failures.items()):
        rel = os.path.relpath(binary, str(self.root_dir))
        print(deco.val(f"  {rel}:"))
        for dep, status, detail in fails:
          print(deco.val(f"    [{status}] {dep}"))
          print(deco.val(f"           {detail}"))
      print()
    else:
      print(deco.val("All references resolved successfully!"))
