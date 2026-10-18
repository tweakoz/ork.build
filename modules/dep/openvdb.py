###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, host, macos
from obt.dependency_artifacts import defines_version, python_extension_suffix
from pathlib import Path
import subprocess
###############################################################################
_EXE_LIB = "@executable_path/../lib/"

def rpath_openvdb_loads(mach_o_path, iolib):
  """Rewrite openvdb's load commands to @rpath, exactly and idempotently.

  Only these entries change (compared whole, never as substrings):
    <iolib> or @executable_path/../lib/<iolib>  -> @rpath/<iolib>
    @executable_path/../lib/<x>                 -> @rpath/<x>
    @rpath/@rpath/<x>                           -> @rpath/<x>
  Entries already of the form @rpath/<x> are left alone, so a rerun is a
  no-op. (A substring replace of <iolib> turned @rpath/<iolib> into
  @rpath/@rpath/<iolib>, which dyld cannot resolve.) Re-signs ad-hoc when
  anything changed. Returns the list of (old, new) changes.
  """
  changes = []
  for name in macos.macho_enumerate_dylibs(mach_o_path):
    new = None
    if name in (iolib, _EXE_LIB + iolib):
      new = "@rpath/" + iolib
    elif name.startswith(_EXE_LIB) and len(name) > len(_EXE_LIB):
      new = "@rpath/" + name[len(_EXE_LIB):]
    elif name.startswith("@rpath/@rpath/"):
      new = "@rpath/" + name[len("@rpath/@rpath/"):]
      while new.startswith("@rpath/@rpath/"):
        new = new[len("@rpath/"):]
    if new and new != name:
      changes.append((name, new))
  if changes:
    edits = []
    for old, new in changes:
      edits += ["-change", old, new]
    subprocess.run(["install_name_tool"] + edits + [str(mach_o_path)], check=True)
    subprocess.run(["codesign", "-s", "-", "-f", str(mach_o_path)], check=True)
  return changes

###############################################################################
class openvdb(dep.StdProvider):
  name = "openvdb"
  def __init__(self):
    super().__init__(openvdb.name)
    self.setSourceRoot(path.builds()/"openvdb-13.1.0")
    self.declareDep("cmake")
    self.declareDep("blosc")
    self.declareDep("boost")
    self.declareDep("tbb")
    self.declareDep("nanobind")
    self.declareDep("llvm")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    dep_python = dep.instance("python")
    self._builder.setCmVars({
      "BUILD_SHARED_LIBS": "ON",
      "OPENVDB_BUILD_PYTHON_MODULE": "ON",
      "OPENVDB_BUILD_AX": "ON",
      "LLVM_ROOT": path.stage(),
      "CMAKE_FIND_DEBUG_MODE": "OFF",
      "PYTHON_EXECUTABLE": path.pyvenv/"bin"/"python3",
      "PYTHON_LIBRARY": path.pyvenv/"lib"/dep_python.library_file,
      "Python_FIND_STRATEGY": "LOCATION",
      "Python_ROOT_DIR": path.pyvenv,
      "VDB_PYTHON_INSTALL_DIRECTORY": dep_python.pylib_dir/"site-packages",
      # openvdb's FindTBB walks default paths and grabs /opt/homebrew first.
      # Force it to use OBT's TBB (2022.0.0, INTERFACE_VERSION 12140) by
      # prefix-pinning + blacklisting brew. Without this, openvdb's
      # Threading.h sees TBB_INTERFACE_VERSION undefined and tries to
      # compile the legacy `tbb::task::self()` branch.
      "CMAKE_PREFIX_PATH": str(path.prefix()),
      "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
    })
    # mold linker — Linux-only, no-op on macOS.
    self._builder.useMold()

  def applyOrkidPatch(self):
    # Preserve the owner's node version/hash extensions, correcting one legacy
    # tile-as-child dereference in TopologyCopy1. The marker comment in the final
    # patch distinguishes it from the exact earlier port for incremental builds.
    patches = Path(__file__).parent/"patches"
    patch = patches/"openvdb-13.1.0-orkid.patch"
    legacy = patches/"openvdb-13.1.0-orkid-legacy.patch"
    cwd = str(self.source_root)
    def is_applied(p):
      return subprocess.run(["git", "apply", "--check", "--reverse", str(p)],
                            cwd=cwd, capture_output=True).returncode == 0
    if is_applied(patch):
      return
    migrate = is_applied(legacy)
    if migrate:
      subprocess.run(["git", "apply", "--reverse", str(legacy)], cwd=cwd, check=True)
    try:
      subprocess.run(["git", "apply", "--check", str(patch)], cwd=cwd, check=True)
      subprocess.run(["git", "apply", str(patch)], cwd=cwd, check=True)
    except Exception:
      # git apply is atomic. Restore the recognized legacy state if the final
      # application fails, rather than leaving the owner's extensions removed.
      if migrate:
        subprocess.run(["git", "apply", str(legacy)], cwd=cwd, check=True)
      raise

  def build(self):
    self.applyOrkidPatch()
    return super().build()

  def onPostInstall(self):
    # CMake already installs into the target Python site-packages directory.
    # Never copy a stale extension from a previous staging/lib installation.
    pyext_dst_path = self._python_module_path()
    if not pyext_dst_path.is_file():
      raise RuntimeError("OpenVDB did not install its target Python extension: " + str(pyext_dst_path))
    if host.IsDarwin:
      # boost lib arch suffix: a64 on Apple Silicon, x64 on Intel. This was
      # hardcoded to "a64", so on Intel Macs the rewrite silently matched
      # nothing and openvdb kept a bare libboost_iostreams-mt-x64 reference
      # that dyld cannot resolve (fixed 2026-09-09). Also patch libopenvdb_ax,
      # which carries the same bare reference and was previously missed.
      boost_arch = "a64" if host.IsAARCH64 else "x64"
      iolib = "libboost_iostreams-mt-%s.dylib" % boost_arch
      rpath_openvdb_loads(pyext_dst_path, iolib)
      macos.macho_dump(pyext_dst_path)
      for dllname in ("libopenvdb.dylib","libopenvdb_ax.dylib"):
        dll = path.stage()/"lib"/dllname
        rpath_openvdb_loads(dll, iolib)
        macos.macho_dump(dll)

    return True

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=openvdb.name,
                                repospec="AcademySoftwareFoundation/openvdb",
                                revision="v13.1.0",
                                md5val="38db693867593b4731ea8dbf566708f5", # v13.1.0
                                recursive=False)
    return fetcher
  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def _python_module_path(self):
    python = dep.instance("python")
    suffix = python_extension_suffix(python.executable)
    return python.pylib_dir/"site-packages"/("openvdb" + suffix)

  def areRequiredBinaryFilesPresent(self):
    if not (defines_version(path.includes()/"openvdb"/"version.h", "OPENVDB_LIBRARY_", "13.1.0", "_VERSION_NUMBER")
            and all((path.libs()/("lib" + lib + "." + self.shlib_extension)).is_file()
                    for lib in ("openvdb", "openvdb_ax"))):
      return False
    try:
      # The fork ABI and corrected topology-copy behavior must also be installed.
      internal = (path.includes()/"openvdb"/"tree"/"InternalNode.h").read_text()
      return ("Tile values are not child pointers and have no node version." in internal
              and self._python_module_path().is_file())
    except (OSError, UnicodeError, RuntimeError, subprocess.SubprocessError):
      return False

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()
