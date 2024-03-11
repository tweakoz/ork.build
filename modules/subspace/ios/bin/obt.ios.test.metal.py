#!/usr/bin/env python3

import os, sys, subprocess, argparse
from obt import command, path, pathtools
from obt import sdk, dep, subspace, conan, cmake_gen

this_dir = path.directoryOfInvokingModule()

argparser = argparse.ArgumentParser(description="Build and install the ios_metal_app")
argparser.add_argument("--clean", action="store_true", help="clean build")
argparser.add_argument("--install", action="store_true", help="install the app on the connected device")
args = argparser.parse_args()

do_install = args.install
do_clean = args.clean

##############################################

IOS_SUBSPACE_DIR = subspace.descriptor("ios")._subsrc
IOS_SDK = sdk.descriptor("aarch64","ios")
prefix = path.subspace_dir()
SRC_DIR = this_dir/".."

my_build_dir = prefix/"builds"/"metalapp"
pathtools.ensureDirectoryExists(my_build_dir)

assert(subspace.current() == "ios")

##############################################

IOS_SDK = sdk.descriptor("aarch64","ios")
lexertl = dep.require("lexertl14")
parsertl = dep.require("parsertl14")
the_environ = conan.environment()
the_environ.update(IOS_SDK._environment)
the_environ.update({
  "OBT_SUBSPACE_BUILD_DIR": prefix/"builds",
  "OBT_SUBSPACE_LIB_DIR": prefix/"lib",
  "OBT_SUBSPACE_BIN_DIR": prefix/"bin",
})

##############################################

os.chdir(my_build_dir)

##############################################

if not (my_build_dir/".build-metal").exists():
  do_clean = True

##############################################

command.run(["cp", IOS_SUBSPACE_DIR/"CMakeListsMetal.txt", my_build_dir/"CMakeLists.txt"], do_log=True)
command.run(["cp", IOS_SUBSPACE_DIR/"InfoMetal.plist", my_build_dir/"Info.plist"], do_log=True)

##############################################
# generate cmake project
##############################################

do_cmakegen = False

if do_cmakegen:
  WS = cmake_gen.workspace("ObtMetalApp")

  WS.findLibrary("UIKit")
  WS.findLibrary("Foundation")
  WS.findLibrary("CoreGraphics")
  WS.findLibrary("Metal")
  WS.findLibrary("QuartzCore")
  WS.findPackage("glm",CONFIG=True)
  WS.findPackage("ZLIB")
  WS.findPackage("Boost",COMPONENTS=["system","filesystem"])

  WS.setVar("DLL_NAME", "${PROJECT_NAME}_DLL")
  WS.setVar("APP_NAME", "${PROJECT_NAME}_APP")

  APP = WS.createExecutable("${APP_NAME}")
  DLL = WS.createSharedLibrary("${DLL_NAME}")
  APP.dependsOn(DLL)
  APP.add_src("${SRC_DIR}/main_metal.mm")
  DLL.add_src("${SRC_DIR}/dll.mm")


  EMITTER = cmake_gen.emitter("ios")
  WS.emit(EMITTER)
  assert(False)

##############################################
if do_clean: # CLEAN BUILD
##############################################
  conan.require(prefix,my_build_dir,[
    "zlib/1.2.11",
    "boost/1.84.0",
    "glm/cci.20230113",
    "zeromq/4.3.4",
    "zmqpp/4.2.0",
    #"openimageio/2.5.9.0",
    "stb/cci.20230920",
    "lexertl14/tweakoz-obt@user/channel",
  ])
  pathtools.mkdir(my_build_dir/".build-metal",clean=True)
  os.chdir(my_build_dir/".build-metal")
  command.run(["cmake", "..", "-G", "Xcode","-DSRC_DIR=%s"%str(SRC_DIR)], environment=the_environ, do_log=True)
  command.run(["cmake", "--build", ".","--config", "Release"], environment=the_environ, do_log=True)

##############################################
else: # INCREMENTAL BUILD
##############################################
  os.chdir(my_build_dir/".build-metal")
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

if do_install:
  IOS_SDK.install_app("com.example.metalapp", app_bundle_dir)
