#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, multiprocessing, json

as_main = (__name__ == '__main__')

###########################################

Path = pathlib.Path
curwd = Path(os.getcwd())
file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
sys.path.append(str(file_dir))

###########################################

parser = argparse.ArgumentParser(description='obt.build environment creator')
parser.add_argument('--stagedir', metavar="createdir", help='create staging folder and enter session' )
parser.add_argument('--project', action='append', metavar="PROJECTLIST", help='append project directory' )
parser.add_argument('--prompt', metavar="prompt", help='prompt suffix' )
parser.add_argument("--numcores", metavar="numcores", help="numcores for environment")
parser.add_argument("--quiet", action="store_true", help="no output")
parser.add_argument('--novars', action="store_true", help='do not set env vars' )
parser.add_argument('--obttrace',action="store_true",help='enable OBT buildtrace logging')

parser.add_argument('--wipe', action="store_true", help='wipe old staging folder' )
parser.add_argument('--sshkey',metavar="sshkey",help='ssh key to use with OBT/GIT')
parser.add_argument('--pipeline', action="store_true",
    help='build mandatory deps via obt.dep.pipeline.py (concurrent fetch+build) '
         'instead of the serial loop. Lets xz/openssl/cmake/vulkan/etc. run '
         'in parallel where the DAG allows.')
parser.add_argument('--prefetch', default=None, metavar="DEPS",
    help='comma-separated dep names whose source should be fetched (but not '
         'built) in parallel with the bootstrap. Overrides the built-in '
         'default list (llvm, boost, ffmpeg, openexr, assimp, bullet, openblas).')
parser.add_argument('--no-prefetch', action="store_true",
    help='disable source prefetching entirely. By default, --pipeline fetches '
         'a baked-in list of heavyweight deps (llvm, boost, ffmpeg, openexr, '
         'assimp, bullet, openblas) concurrently with the bootstrap.')

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###########################################
# parse args and generate config / core environment vars
###########################################

from _obt_config import configFromCommandLine, initializeDependencyEnvironments
obt_config = configFromCommandLine(args)
      
###########################################
# wipe old staging folder ?
###########################################

if obt_config.stage_dir.exists() and args["wipe"]==False:
  print("Not going to wipe your staging folder<%s> unless you ask... use --wipe"%obt_config.stage_dir)
  sys.exit(0)
if args["wipe"] and obt_config.stage_dir.exists():
  import time
  _sd = str(obt_config.stage_dir)
  for _attempt in range(5):
    os.system("rm -rf %s" % _sd)
    if not obt_config.stage_dir.exists():
      break
    # macOS/APFS: `rm -rf` on a huge tree (e.g. boost's thousands of
    # headers) intermittently fails mid-recursion with "Directory not
    # empty" — rmdir races its own just-issued unlinks. A retry clears
    # the remainder. (Same race that bit moltenvk/External and the
    # obt.test.nohomebrew.py safe_wipe.)
    print("staging wipe incomplete (attempt %d/5) — retrying..." % (_attempt+1))
    time.sleep(1)
  if obt_config.stage_dir.exists():
    print("ERROR: could not fully wipe %s after 5 attempts.\n"
          "       A process is likely holding files open inside it — "
          "check for stale cmake/build processes:\n"
          "         ps -ef | grep %s | grep -v grep"
          % (_sd, _sd))
    sys.exit(1)

###########################################

if args["obttrace"]==True:
  import obt._globals as _glob
  _glob.enableBuildTracing()

##########################################

import obt._envutils 
envsetup = obt._envutils.EnvSetup(obt_config)

###########################################
# Create staging folder, scripts
###########################################

import obt.path

obt.path.prefix().mkdir(parents=True,exist_ok=False)
envsetup.lazyMakeDirs()
envsetup.genBashRc(obt_config,obt_config.stage_dir/".bashrc")
envsetup.genLaunchScript(out_path=obt_config.stage_dir/"obt-launch-env")

initializeDependencyEnvironments(envsetup)

###########################################
# build mandatory dependencies
###########################################

print(os.environ)
print(os.environ["OBT_MODULES_PATH"])
os.system("ls %s" % os.environ["OBT_MODULES_PATH"])

MANDATORY_DEPS = ["cmake","python","pydefaults","pybind11","vulkan"]

# Deps whose source is worth pre-fetching during the bootstrap. Large
# tarballs / slow upstreams / git-clones-with-submodules — anything that
# benefits from overlapping with the CPU-bound bootstrap builds. Excludes
# vulkan (already in MANDATORY_DEPS). Order roughly biggest-first so the
# slowest fetches launch earliest in the fetch pool.
PREFETCH_DEFAULTS = [
    "llvm", "sox", "libpng", "jpegturbo", "boost", "ffmpeg",
    "openvdb", "oiio", "openexr", "assimp", "bullet", "openblas",
    "glfw", "luajit", "zstd", "libsodium", "lz4", 
    "libpng", "libwebp", "glm", "dsp", "dspstretch",
    "pytorch", "torchvision", "torchaudio"
]

if args.get("pipeline"):
  # Run all mandatory deps as a single Chain through the parallel scheduler.
  # The DAG (root → pydefaults → python → xz/openssl, plus cmake/vulkan
  # independent) gives us xz+openssl parallel, then python, then pydefaults,
  # then cmake+vulkan parallel.
  import subprocess
  pipeline_script = Path(sys.prefix) / "obt" / "bin_priv" / "obt.dep.pipeline.py"
  if not pipeline_script.exists():
    print("ERROR: pipeline script not found at %s" % pipeline_script)
    sys.exit(2)

  # Resolve prefetch list:
  #   --no-prefetch     → no prefetch at all
  #   --prefetch <list> → explicit list (overrides defaults)
  #   neither           → PREFETCH_DEFAULTS (the default)
  if args.get("no_prefetch"):
    prefetch_arg = None
  elif args.get("prefetch"):
    prefetch_arg = args.get("prefetch")
  else:
    prefetch_arg = ",".join(PREFETCH_DEFAULTS)

  cmd = [sys.executable, str(pipeline_script)] + MANDATORY_DEPS
  if prefetch_arg:
    cmd += ["--prefetch", prefetch_arg]

  rc = subprocess.run(cmd, env=os.environ).returncode
  sys.exit(0 if rc == 0 else rc)
else:
  import obt.dep
  for item in MANDATORY_DEPS:
    dep = obt.dep.instance(item)
    dep.provide()
