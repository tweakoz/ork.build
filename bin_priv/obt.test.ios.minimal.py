#!/usr/bin/env python3

import os, sys, subprocess, argparse

from obt import command, path, pathtools, sdk, dep, subspace

##############################################

prefix = path.subspace_root()/"ios"
pathtools.ensureDirectoryExists(prefix)
pathtools.ensureDirectoryExists(prefix/"builds")
pathtools.ensureDirectoryExists(prefix/"lib")
pathtools.ensureDirectoryExists(prefix/"bin")
pathtools.ensureDirectoryExists(prefix/"conan")
os.chdir(prefix)

##############################################

IOS_SUBSPACE_DIR = subspace.descriptor("ios")._subsrc
print(IOS_SUBSPACE_DIR)

##############################################

TEMP_PATH = path.temp()
IOS_SDK = sdk.descriptor("aarch64","ios")
SDK_DIR = IOS_SDK._sdkdir
SDK_VER = IOS_SDK._sdkver
the_environ = {
  "OBT_SUBSPACE_BUILD_DIR": prefix/"builds",
  "OBT_SUBSPACE_LIB_DIR": prefix/"lib",
  "OBT_SUBSPACE_DIR": prefix,
  "OBT_SUBSPACE_BIN_DIR": prefix/"bin",
  "IOS_PREFIX": prefix,
  "IOS_SDK_DIR": SDK_DIR,
  "IOS_SDK_VER": SDK_VER,
  "IOS_CLANG_PATH": IOS_SDK._clang_path,
  "IOS_CLANGPP_PATH": IOS_SDK._clangpp_path,
  "OBT_SUBSPACE": "ios",
  "OBT_TARGET": "aarch64-ios",
}     

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
  
##############################################

the_environ["VERBOSE"] = "1"

print( "############## begin envdump ##############")

for item in the_environ:
  print(f"{item}={the_environ[item]}")

print( "############## end envdump ##############")

##############################################

pathtools.mkdir(prefix/".build",clean=True)
os.chdir(prefix/".build")
command.run(["cmake", "..", "-G", "Xcode"], environment=the_environ, do_log=True)
command.run(["cmake", "--build", ".","--config", "Release"], environment=the_environ, do_log=True)

##############################################

app_bundle_dir = prefix / ".build/Release-iphoneos/ios_minimal_app.app"
# Verify the executable exists within the bundle
executable_path = app_bundle_dir / "ios_minimal_app"
if not os.path.exists(executable_path):
    print(f"Executable not found at {executable_path}")
    sys.exit(1)

##############################################
# Check if the device is connected
##############################################

device_info = subprocess.check_output(["idevice_id", "-l"], universal_newlines=True).strip()
if not device_info:
    print("No iOS device connected. Please connect an iOS device and try again.")
    sys.exit(1)


##############################################
# Install the app on the connected device
##############################################

command.run(["ideviceinstaller", "-U", "com.example.minimalapp"], do_log=True)
command.run(["ideviceinstaller", "-i", app_bundle_dir], do_log=True)