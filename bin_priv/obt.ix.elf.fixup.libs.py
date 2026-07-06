#!/usr/bin/env python3
###############################################################################
# ELF analog of obt.osx.macho.fixup.libs.py.
#
# On macOS the fixup rewrites bad @executable_path install_names to @rpath.
# The ELF failure mode is different: orkid's own libs and rpath-aware deps
# install with RUNPATH -> staging/lib, but many third-party deps (bullet,
# glslang, SPIRV-Tools, plutovg, tbb, ffmpeg, ...) install shared objects
# with NO rpath at all. DT_RUNPATH is non-transitive, so their inter-lib
# NEEDED entries only resolve if LD_LIBRARY_PATH carries staging/lib — which
# the dev environment must NOT do (a staged libLLVM.so.18.1 on the global
# loader path breaks the system clang's libclang-cpp).
#
# Fix: stamp '$ORIGIN' (libs) / an absolute staging-lib reach (pymods) onto
# every object that has no rpath. Objects that already carry one are left
# alone — deploy-time normalization is ElfRelocator's job, not ours.
# Fix-if-missing makes the sweep idempotent and cheap to run on every build.
###############################################################################

from obt import path, pathtools, linux, host, deco
import os, argparse, sys
deco = deco.Deco()

parser = argparse.ArgumentParser(description='stamp rpaths on rpath-less staged ELF objects')
parser.add_argument('--alllibs', action="store_true", help='do all libs in stage/lib' )
parser.add_argument('--orklibs', action="store_true", help='do orkid libs' )
parser.add_argument('--orkpymods', action="store_true", help='do orkid python modules' )

_args = vars(parser.parse_args())

assert host.IsLinux, "obt.ix.elf.fixup.libs.py is Linux-only (see obt.osx.macho.fixup.libs.py)"

###############################################################################

def fixup_if_bare(elf_path, rpaths):
  """Stamp `rpaths` onto elf_path IFF it currently has no RPATH/RUNPATH.
  Returns True if the object was patched."""
  elf_str = str(elf_path)
  if os.path.islink(elf_str) or not linux.is_elf_binary(elf_str):
    return False
  if linux.elf_enumerate_rpaths(elf_str):
    return False
  print(deco.yellow(os.path.basename(elf_str)), "->", deco.val(":".join(rpaths)))
  linux.elf_set_rpath(elf_str, rpaths)
  return True

def sweep(items, rpaths, label):
  count = sum(1 for item in items if fixup_if_bare(item, rpaths))
  print(deco.inf("elf.fixup[%s]: patched %d objects" % (label, count)))

###############################################################################

if _args["alllibs"]!=False:
  # staged libs reach their siblings relative to themselves so the stamp
  # survives a relocated deployment untouched
  sweep(pathtools.patglob(path.stage()/"lib","*.so*"), ["$ORIGIN"], "alllibs")

if _args["orklibs"]!=False:
  # normally a no-op — orkid's cmake installs these with RUNPATH already
  sweep(pathtools.recursive_patglob(path.stage()/"lib","libork*.so"), ["$ORIGIN"], "orklibs")

if _args["orkpymods"]!=False:
  from obt import dep
  PYTHON = dep.instance("python")
  stage_lib = str(path.stage()/"lib")
  # same subpackage list as the macOS fixup — ecs/ecssim slipped through once
  ork_subpkgs = ["core", "lev2", "ecs", "ecssim"]
  mods = []
  for sub in ork_subpkgs:
    pkgdir = PYTHON.site_packages_dir/"orkengine"/sub
    if pkgdir.exists():
      mods += pathtools.recursive_patglob(pkgdir,"*.so")
  # absolute reach, matching what orkid's cmake stamps on these at install
  sweep(mods, [stage_lib], "orkpymods")
