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

if 0:
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
cmake_minimum_required(VERSION 3.28.3)
project(ios_minimal_app LANGUAGES CXX OBJCXX)
set(CMAKE_OSX_SYSROOT %s CACHE PATH "The iOS SDK sysroot")

include(${CMAKE_CURRENT_SOURCE_DIR}/ios.toolchain.cmake)

# Find the required frameworks
find_library(UIKit UIKit REQUIRED)
find_library(Foundation Foundation REQUIRED)
find_library(CoreGraphics CoreGraphics REQUIRED)

add_executable(${PROJECT_NAME} main.mm)

# Link against the required frameworks
target_link_libraries(${PROJECT_NAME} PRIVATE ${UIKit} ${Foundation} ${CoreGraphics})

set_target_properties(${PROJECT_NAME} PROPERTIES
    XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "com.example.minimalapp"
    XCODE_ATTRIBUTE_DEVELOPMENT_TEAM "$ENV{DEVELOPMENT_TEAM}"
    XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "iPhone Developer"
    XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Automatic"
    MACOSX_BUNDLE_GUI_IDENTIFIER "com.example.minimalapp"
    MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist
)
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
    <string>ios_minimal_app</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.minimalapp</string>
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
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>arm64</string>
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
#import <UIKit/UIKit.h>


// Simple macro distinguishes iPhone from iPad

#define IS_IPHONE (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone)


@interface TestBedAppDelegate : NSObject <UIApplicationDelegate>

{

    UIWindow *window;

}

@end


@implementation TestBedAppDelegate

- (UIViewController *) helloController

{

    UIViewController *vc = [[UIViewController alloc] init];

    vc.view.backgroundColor = [UIColor greenColor];


    // Add a basic label that says "Hello World"

    UILabel *label = [[UILabel alloc] initWithFrame:

        CGRectMake(0.0f, 0.0f, window.bounds.size.width, 80.0f)];

    label.text = @"Hello World";

    label.center = CGPointMake(CGRectGetMidX(window.bounds),

        CGRectGetMidY(window.bounds));

    label.textAlignment = UITextAlignmentCenter;

    label.font = [UIFont boldSystemFontOfSize: IS_IPHONE ? 32.0f : 64.0f];

    label.backgroundColor = [UIColor clearColor];

    [vc.view addSubview:label];


    return vc;

}


- (BOOL)application:(UIApplication *)application

    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions

{

    window = [[UIWindow alloc] initWithFrame:

        [[UIScreen mainScreen] bounds]];

    window.rootViewController = [self helloController];

    [window makeKeyAndVisible];

    return YES;

}

@end


int main(int argc, char *argv[]) {

    @autoreleasepool {

        int retVal =

            UIApplicationMain(argc, argv, nil, @"TestBedAppDelegate");

        return retVal;

    }

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

command.run(["cmake", "..", "-G", "Xcode"], environment=the_environ, do_log=True)

# ... (previous code remains the same)

# Build the project with CMake
command.run(["cmake", "--build", ".","--config", "Release"], environment=the_environ, do_log=True)

app_bundle_dir = prefix / ".build/Release-iphoneos/ios_minimal_app.app"
# Verify the executable exists within the bundle
executable_path = app_bundle_dir / "ios_minimal_app"
if not os.path.exists(executable_path):
    print(f"Executable not found at {executable_path}")
    sys.exit(1)

# Check if the device is connected
device_info = subprocess.check_output(["idevice_id", "-l"], universal_newlines=True).strip()
if not device_info:
    print("No iOS device connected. Please connect an iOS device and try again.")
    sys.exit(1)

command.run(["ideviceinstaller", "-U", "com.example.minimalapp"], do_log=True)

# Install the app on the connected device
command.run(["ideviceinstaller", "-i", app_bundle_dir], do_log=True)