#!/usr/bin/env python3

import os, sys, subprocess, argparse

from obt import command, path, pathtools
from obt import sdk, dep, subspace, conan

IOS_SUBSPACE_DIR = subspace.descriptor("ios")._subsrc
IOS_SDK = sdk.descriptor("aarch64","ios")
prefix = path.subspace_dir()

assert(subspace.current() == "ios")

##############################################

os.chdir(prefix)

##############################################

the_environ = os.environ.copy()
the_environ.update(conan.environment())
the_environ.update(IOS_SDK._environment)
the_environ.update({
  "OBT_SUBSPACE_BUILD_DIR": prefix/"builds",
  "OBT_SUBSPACE_LIB_DIR": prefix/"lib",
  "OBT_SUBSPACE_BIN_DIR": prefix/"bin",
})

##############################################

file_list = [
  "CMakeLists.txt",
  "Info.plist",
  "ios.toolchain.cmake",
]

for f in file_list:
  src = IOS_SUBSPACE_DIR / f
  dst = prefix / f
  command.run(["cp", src, dst], do_log=True)
  
command.run(["cp", IOS_SUBSPACE_DIR/"InfoMinimal.plist", prefix/"Info.plist"], do_log=True)
  
##############################################

the_environ["VERBOSE"] = "1"

print( "############## begin envdump ##############")

for item in the_environ:
  print(f"{item}={the_environ[item]}")

print( "############## end envdump ##############")

##############################################

pathtools.mkdir(prefix/".build-minimal",clean=True)
os.chdir(prefix/".build-minimal")
command.run(["cmake", "..", "-G", "Xcode"], environment=the_environ, do_log=True)
command.run(["cmake", "--build", ".","--config", "Release"], environment=the_environ, do_log=True)

##############################################

app_bundle_dir = prefix / ".build-minimal/Release-iphoneos/ios_minimal_app.app"
# Verify the executable exists within the bundle
executable_path = app_bundle_dir / "ios_minimal_app"
if not os.path.exists(executable_path):
    print(f"Executable not found at {executable_path}")
    sys.exit(1)

##############################################
# Install the app on the connected device
##############################################

IOS_SDK.install_app("com.example.minimalapp", app_bundle_dir)
