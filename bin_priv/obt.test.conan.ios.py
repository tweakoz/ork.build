#!/usr/bin/env python3

import os, sys, subprocess, argparse

from obt import command, path, pathtools, sdk, dep

parser = argparse.ArgumentParser(description='obt.build dep builder')
parser.add_argument('--gencert', action="store_true", help='generate ios certificate' )
parser.add_argument('--buildios', action="store_true", help='generate ios certificate' )

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

args = parser.parse_args()

##############################################

prefix = path.subspace_root()/"ios"
pathtools.ensureDirectoryExists(prefix)
pathtools.ensureDirectoryExists(prefix/"builds")
pathtools.ensureDirectoryExists(prefix/"lib")
pathtools.ensureDirectoryExists(prefix/"bin")
pathtools.ensureDirectoryExists(prefix/"conan")
os.chdir(prefix)

##############################################

CERTNAME = "APHIDSYSC"

def generate_csr(output_path, certificate_name):
    """Generate a Certificate Signing Request (CSR) and add key to keychain."""
    try:
        # Use openssl to generate a CSR and key
        subprocess.run(["openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes", #
                        "-keyout", f"{output_path}/{certificate_name}.key", # 
                        "-out", f"{output_path}/{certificate_name}.csr"], #
                        check=True)
        # Add the key to the keychain
        subprocess.run(["security", "import", f"{output_path}/{certificate_name}.key", "-k", "login.keychain", "-T", "/usr/bin/codesign"],
                        check=True)
        print("CSR generated and key added to keychain successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error generating CSR and adding key to keychain: {e}")
        raise

if args.gencert:
  print("Generating iOS certificate...")
  generate_csr(str(prefix), CERTNAME )
  print("Certificate generated successfully.")
  print("Now, upload the certificate signing request to the Apple Developer portal to create a certificate.")
  sys.exit(0)


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
  #"CMAKE_TOOLCHAIN_FILE": prefix/"ios.toolchain.cmake",
  #"OBT_SUBSPACE_PROMPT": self._gen_sysprompt(),
  "OBT_TARGET": "aarch64-ios",
  "CONAN_HOME": prefix/"conan",
  "CONAN_USER_HOME": prefix/"conan",
  "CONAN_CACHE_DIR": "~/.obt-global/conan2"
}     

##############################################
# generate cmake toolchain
##############################################

cmake_tc = """
set(IOS_SDK_PATH $ENV{IOS_SDK_DIR})
set(CMAKE_SYSTEM_NAME iOS)

# Specify the architectures to build for (e.g., arm64 for actual devices)
set(CMAKE_OSX_ARCHITECTURES arm64)

# Specify the minimum iOS deployment target
set(CMAKE_OSX_DEPLOYMENT_TARGET $ENV{IOS_SDK_VER})

# Specify the path to the compiler
set(CMAKE_C_COMPILER $ENV{IOS_CLANG_PATH})
set(CMAKE_CXX_COMPILER $ENV{IOS_CLANGPP_PATH})
set(CMAKE_INSTALL_PREFIX $ENV{OBT_SUBSPACE_BUILD_DIR})
"""

tc_output = prefix/"ios.toolchain.cmake"
with open(tc_output,"w") as f:
  f.write(cmake_tc)

##############################################
# generate conanfile
##############################################

# missing 
# glfw
# lexertl14
# parsertl14
# easyprof 
# rtmidi 
# cpppeglib 
# klein 
# portaudio 

# not working
#libigl/2.3.0
#openimageio/2.5.6
#rapidjson/cci.20230929 <incompatible with assimp/5.2.2>
#openblas/0.3.26 

lexertl = dep.instance("lexertl14")
print(lexertl)
#print(dir(lexertl))
print(lexertl._conanfile)

lexertl14_dir = prefix / "conan" / "lexertl14"
lexertl14_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
lrtl_output = lexertl14_dir / "conanfile.py"
with open(lrtl_output, "w") as f:
    f.write(lexertl._conanfile)  # Assuming lexertl._conanfile is the recipe text
os.chdir(str(lexertl14_dir))
#conan export . lexertl14/tweakoz-obt@user/channel
command.run(["conan","export",".",
             "--user=user",
             "--channel=channel"], #
             environment=the_environ,do_log=True ) 

conanfile = """
[requires]
zlib/1.2.11
boost/1.81.0
assimp/5.2.2
ptex/2.4.2
openexr/3.2.1
rapidjson/cci.20220822
eigen/3.4.0
glm/cci.20230113
bullet3/3.25
zeromq/4.3.5
cppzmq/4.10.0
sigslot/1.2.2 
moltenvk/1.2.2
lexertl14/tweakoz-obt

[generators]
CMakeDeps
CMakeToolchain
"""

cf_output = prefix/"conanfile.txt"
with open(cf_output,"w") as f:
  f.write(conanfile)

##############################################
# generate conan profile for ios
##############################################

conan_host_profile = """
[settings]
os=iOS
os.version=17.0
arch=armv8
compiler=apple-clang
compiler.version=15.0
compiler.libcxx=libc++
build_type=Release
os.sdk=iphoneos
"""

cp_output = prefix/"ios.host.profile"
with open(cp_output,"w") as f:
  f.write(conan_host_profile)

##############################################

conan_build_profile = """
[settings]
os=Macos
arch=armv8  
compiler=apple-clang
compiler.version=15.0
compiler.libcxx=libc++
build_type=Release
"""

cp_output = prefix/"ios.build.profile"
with open(cp_output,"w") as f:
  f.write(conan_build_profile)

##############################################
  
cmd =  ["conan","install","."]
cmd += [f"--profile:host={prefix}/ios.host.profile"]
cmd += [f"--profile:build={prefix}/ios.build.profile"]
cmd += ["--build=missing"]

command.run(cmd,environment=the_environ,do_log=True)

##############################################

cmake_lists_content = """
cmake_minimum_required(VERSION 3.15)
project(ios_minimal_app LANGUAGES CXX OBJCXX)
set(CMAKE_OSX_SYSROOT %s CACHE PATH "The iOS SDK sysroot")

#include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/ios.toolchain.cmake)

find_package(ZLIB REQUIRED)

add_executable(${PROJECT_NAME} main.mm)
set_target_properties(${PROJECT_NAME} PROPERTIES
    XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "com.example.minimalapp"
    XCODE_ATTRIBUTE_DEVELOPMENT_TEAM "YOUR_TEAM_ID"
    MACOSX_BUNDLE_GUI_IDENTIFIER "com.example.minimalapp"
    MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist
)
target_link_libraries(${PROJECT_NAME} PRIVATE ZLIB::ZLIB)
""" % SDK_DIR

with open(prefix / "CMakeLists.txt", "w") as f:
    f.write(cmake_lists_content)

##############################################

info_plist_content = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>MyApp</string>
    <key>CFBundleExecutable</key>
    <string>MyApp</string>
    <key>CFBundleIdentifier</key>
    <string>com.aphidsystems.myapp</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>MyApp</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
    </array>
</dict>
</plist>
"""

info_plist_path = prefix / "Info.plist"
with open(info_plist_path, "w") as f:
    f.write(info_plist_content)

##############################################

# main.mm
objc_plus_plus_source = """
#include <iostream>
#include <zlib.h>
#include <string>

int main(int argc, const char * argv[]) {
    std::string originalStr = "Hello, Conan and iOS World!";
    uLongf compressedDataSize = compressBound(originalStr.size());
    Bytef *compressedData = (Bytef*)malloc(compressedDataSize);

    if (compress(compressedData, &compressedDataSize, (Bytef*)originalStr.data(), originalStr.size()) == Z_OK) {
        std::cout << "Original string: " << originalStr << "\\n";
        std::cout << "Compressed size: " << compressedDataSize << "\\n";
    } else {
        std::cout << "Compression failed!" << "\\n";
    }

    free(compressedData);
    return 0;
}
"""

# Write the source to a file
app_source_file = prefix / "main.mm"
with open(app_source_file, "w") as f:
    f.write(objc_plus_plus_source)

pathtools.ensureDirectoryExists(prefix/".build")
os.chdir(prefix/".build")

the_environ["VERBOSE"] = "1"

print( "############## begin CMakelists.txt ##############")
print(cmake_lists_content)
print( "############## end CMakelists.txt ##############")

print( "############## begin envdump ##############")

for item in the_environ:
  print(f"{item}={the_environ[item]}")

print( "############## end envdump ##############")

command.run(["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"], environment=the_environ, do_log=True)
#command.run(["cmake", ".", "-DCMAKE_BUILD_TYPE=Release", environment=the_environ, do_log=True)

# Build the project with CMake
command.run(["cmake", "--build", "."], environment=the_environ, do_log=True)

# Create app bundle structure
app_bundle_dir = prefix / "MyApp.app"
os.makedirs(app_bundle_dir, exist_ok=True)

# Copy executable
executable_src = prefix / ".build/ios_minimal_app"  # Change this to the actual path of your executable
executable_dest = app_bundle_dir / "MyApp"  # Change "MyApp" to your app's name
pathtools.copyfile(executable_src, executable_dest)

# Copy Info.plist

# Add any other necessary resources (images, storyboards, etc.) to the Resources directory
pathtools.copyfile(prefix / "Info.plist", app_bundle_dir / "Info.plist")

# Code sign the app bundle (you may need to adjust this based on your code signing configuration)
command.run(["codesign", "-s", CERTNAME,  "--deep", app_bundle_dir], do_log=True)

command.run(["ideviceinstaller","-i",prefix/"MyApp.app"], do_log=True)