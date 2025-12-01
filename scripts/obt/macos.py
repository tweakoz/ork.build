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
