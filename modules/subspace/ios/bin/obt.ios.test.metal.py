#!/usr/bin/env python3

import os, sys, subprocess, argparse

from obt import command, path, pathtools
from obt import sdk, dep, subspace, conan

IOS_SUBSPACE_DIR = subspace.descriptor("ios")._subsrc
IOS_SDK = sdk.descriptor("aarch64","ios")
prefix = path.subspace_dir()

my_build_dir = prefix/"builds"/"metalapp"
pathtools.ensureDirectoryExists(my_build_dir)

assert(subspace.current() == "ios")

##############################################

os.chdir(my_build_dir)

lexertl = dep.require("lexertl14")
parsertl = dep.require("parsertl14")

conan.require(prefix,my_build_dir,[
  "zlib/1.2.11",
  "boost/1.81.0",
  "lexertl14/tweakoz-obt@user/channel",
])

##############################################

IOS_SDK = sdk.descriptor("aarch64","ios")
the_environ = conan.environment()
the_environ.update(IOS_SDK._environment)
the_environ.update({
  "OBT_SUBSPACE_BUILD_DIR": prefix/"builds",
  "OBT_SUBSPACE_LIB_DIR": prefix/"lib",
  "OBT_SUBSPACE_BIN_DIR": prefix/"bin",
})

##############################################

command.run(["cp", IOS_SUBSPACE_DIR/"CMakeListsMetal.txt", my_build_dir/"CMakeLists.txt"], do_log=True)
command.run(["cp", IOS_SUBSPACE_DIR/"InfoMetal.plist", my_build_dir/"Info.plist"], do_log=True)
  
##############################################


the_environ["VERBOSE"] = "1"

print( "############## begin envdump ##############")

for item in the_environ:
  print(f"{item}={the_environ[item]}")

print( "############## end envdump ##############")

##############################################

pathtools.mkdir(my_build_dir/".build-metal",clean=True)
os.chdir(my_build_dir/".build-metal")
command.run(["cmake", "..", "-G", "Xcode"], environment=the_environ, do_log=True)
command.run(["cmake", "--build", ".","--config", "Release"], environment=the_environ, do_log=True)

##############################################

app_bundle_dir = my_build_dir / ".build-metal/Release-iphoneos/ios_metal_app.app"
# Verify the executable exists within the bundle
executable_path = app_bundle_dir / "ios_metal_app"
if not os.path.exists(executable_path):
    print(f"Executable not found at {executable_path}")
    sys.exit(1)

##############################################
# Install the app on the connected device
##############################################

IOS_SDK.install_app("com.example.metalapp", app_bundle_dir)
