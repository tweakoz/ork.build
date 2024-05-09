#!/usr/bin/env python3

import os, sys, subprocess, argparse

from obt import command, path, pathtools, sdk, dep

parser = argparse.ArgumentParser(description='obt.build dep builder')
parser.add_argument('--gencert', action="store_true", help='generate ios certificate' )
parser.add_argument('--build', action="store_true", help='build...' )

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

args = parser.parse_args()

##############################################

prefix = path.subspace_root()/"xros"

command.run(["rm","-rf",prefix/"builds"],do_log=True)

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
  print("Generating provisioning certificate...")
  generate_csr(str(prefix), CERTNAME )
  print("Certificate generated successfully.")
  print("Now, upload the certificate signing request to the Apple Developer portal to create a certificate.")
  sys.exit(0)


##############################################

TEMP_PATH = path.temp()
XROS_SDK = sdk.descriptor("aarch64","xros")
SDK_DIR = XROS_SDK._sdkdir
SDK_VER = XROS_SDK._sdkver
the_environ = {
  "OBT_SUBSPACE_BUILD_DIR": prefix/"builds",
  "OBT_SUBSPACE_LIB_DIR": prefix/"lib",
  "OBT_SUBSPACE_DIR": prefix,
  "OBT_SUBSPACE_BIN_DIR": prefix/"bin",
  "XROS_PREFIX": prefix,
  "XROS_SDK_DIR": SDK_DIR,
  "XROS_SDK_VER": SDK_VER,
  "XROS_CLANG_PATH": XROS_SDK._clang_path,
  "XROS_CLANGPP_PATH": XROS_SDK._clangpp_path,
  "OBT_SUBSPACE": "xros",
  "OBT_TARGET": "aarch64-xros",
  "CONAN_HOME": prefix/"conan",
  "CONAN_USER_HOME": prefix/"conan",
  "CONAN_CACHE_DIR": "~/.obt-global/conan2"
}     

##############################################
# generate cmake toolchain
##############################################

cmake_tc = """
set(XROS_SDK_PATH $ENV{XROS_SDK_DIR})
set(CMAKE_SYSTEM_NAME visionOS)

# Specify the architectures to build for (e.g., arm64 for actual devices)
set(CMAKE_OSX_ARCHITECTURES arm64)

# Specify the minimum xros deployment target
set(CMAKE_OSX_DEPLOYMENT_TARGET $ENV{XROS_SDK_VER})

# Specify the path to the compiler
set(CMAKE_C_COMPILER $ENV{XROS_CLANG_PATH})
set(CMAKE_CXX_COMPILER $ENV{XROS_CLANGPP_PATH})
set(CMAKE_INSTALL_PREFIX $ENV{OBT_SUBSPACE_BUILD_DIR})
"""

tc_output = prefix/"xros.toolchain.cmake"
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

[generators]
CMakeDeps
CMakeToolchain
"""

"""
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
"""

cf_output = prefix/"conanfile.txt"
with open(cf_output,"w") as f:
  f.write(conanfile)

##############################################
# generate conan profile for ios
##############################################

conan_host_profile = """
[settings]
os=visionOS
os.version=1.0
arch=armv8
compiler=apple-clang
compiler.version=15.0
compiler.libcxx=libc++
build_type=Release
os.sdk=xros
"""

cp_output = prefix/"xros.host.profile"
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

cp_output = prefix/"xros.build.profile"
with open(cp_output,"w") as f:
  f.write(conan_build_profile)

##############################################
  
cmd =  ["conan","install","."]
cmd += [f"--profile:host={prefix}/xros.host.profile"]
cmd += [f"--profile:build={prefix}/xros.build.profile"]
cmd += ["--build=missing"]

command.run(cmd,environment=the_environ,do_log=True)

##############################################

APPID = "com.example.minimalapp"
#BUNDLE_NAME = "MYAPP"

##############################################

cmake_lists_content = """
cmake_minimum_required(VERSION 3.15)
project(xros_minimal_app LANGUAGES CXX OBJCXX)
set(CMAKE_OSX_SYSROOT %s CACHE PATH "The xrOS SDK sysroot")
set(CMAKE_TOOLCHAIN_FILE %s)
#include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake)
include(${CMAKE_CURRENT_SOURCE_DIR}/xros.toolchain.cmake)

find_package(ZLIB REQUIRED)

add_executable(${PROJECT_NAME} main.mm)

set_target_properties(${PROJECT_NAME} PROPERTIES
    XCODE_ATTRIBUTE_DEVELOPMENT_TEAM "$ENV{DEVELOPMENT_TEAM}"
    XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "iPhone Developer"
    XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Automatic"
    XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "%s"
    MACOSX_BUNDLE_GUI_IDENTIFIER "%s"
    MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist
)

find_library(UIKIT_FRAMEWORK UIKit)
target_link_libraries(${PROJECT_NAME} PRIVATE "${UIKIT_FRAMEWORK}")
#target_link_libraries(${PROJECT_NAME} PRIVATE ZLIB::ZLIB)
""" % (SDK_DIR,str(tc_output),APPID,APPID)

with open(prefix / "CMakeLists.txt", "w") as f:
    f.write(cmake_lists_content)

##############################################

info_plist_content = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>BuildMachineOSBuild</key>
	<string>23C71</string>
	<key>CFBundleDevelopmentRegion</key>
	<string>en</string>
	<key>CFBundleExecutable</key>
	<string>xros_minimal_app</string>
	<key>CFBundleIdentifier</key>
	<string>com.example.minimalapp</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>XROS_TEST</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>1.0</string>
	<key>CFBundleSupportedPlatforms</key>
	<array>
		<string>XRSimulator</string>
	</array>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>DTCompiler</key>
	<string>com.apple.compilers.llvm.clang.1_0</string>
	<key>DTPlatformBuild</key>
	<string>21N301</string>
	<key>DTPlatformName</key>
	<string>xrsimulator</string>
	<key>DTPlatformVersion</key>
	<string>1.0</string>
	<key>DTSDKBuild</key>
	<string>21N301</string>
	<key>DTSDKName</key>
	<string>xrsimulator1.0</string>
	<key>DTXcode</key>
	<string>1520</string>
	<key>DTXcodeBuild</key>
	<string>15C500b</string>
	<key>MinimumOSVersion</key>
	<string>1.0</string>
	<key>UIApplicationSceneManifest</key>
	<dict>
		<key>UIApplicationPreferredDefaultSceneSessionRole</key>
		<string>UIWindowSceneSessionRoleVolumetricApplication</string>
		<key>UIApplicationSupportsMultipleScenes</key>
		<true/>
		<key>UISceneConfigurations</key>
		<dict/>
	</dict>
	<key>UIDeviceFamily</key>
	<array>
		<integer>7</integer>
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
#import <zlib.h>
#import <string>
#import <iostream>

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    /*self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];
    UIViewController *viewController = [[UIViewController alloc] init];
    self.window.rootViewController = viewController;
    
    std::string originalStr = "Hello, Conan and iOS World!";
    uLongf compressedDataSize = compressBound(originalStr.size());
    Bytef *compressedData = (Bytef*)malloc(compressedDataSize);
    
    if (compress(compressedData, &compressedDataSize, (Bytef*)originalStr.data(), originalStr.size()) == Z_OK) {
        std::cout << "Original string: " << originalStr << "\n";
        std::cout << "Compressed size: " << compressedDataSize << "\n";
    } else {
        std::cout << "Compression failed!" << "\n";
    }
    
    free(compressedData);
    
    UILabel *label = [[UILabel alloc] initWithFrame:CGRectMake(20, 100, 300, 40)];
    label.numberOfLines = 0;
    label.text = [NSString stringWithFormat:@"Original: %lu, Compressed: %lu", originalStr.size(), compressedDataSize];
    [viewController.view addSubview:label];
    
    self.window.backgroundColor = [UIColor whiteColor];
    [self.window makeKeyAndVisible];*/
    return YES;
}

@end

int main(int argc, char * argv[]) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass([AppDelegate class]));
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

command.run([ "cmake", #
              "..", #
              "-GXcode", #
              "-DCMAKE_TOOLCHAIN_FILE=%s"%tc_output, #
              "-DCMAKE_BUILD_TYPE=Debug"], #
              environment=the_environ, #
              do_log=True)

# Build the project with CMake
command.run(["cmake", "--build", ".", "--target", "xros_minimal_app"], environment=the_environ, do_log=True)

# Code sign the app bundle (you may need to adjust this based on your code signing configuration)
#command.run(["codesign", "-s", CERTNAME,  "--deep", app_bundle_dir], do_log=True)


print( "INSTALLING TO SIMULATOR")
XROS_SIM_DEVID = os.environ["XROS_SIM_DEVID"]
command.run(["xcrun","simctl","install",XROS_SIM_DEVID,".build/Debug-xros/xros_minimal_app.app"], 
             working_dir=prefix,
             do_log=True)
command.run(["xcrun","simctl","launch",XROS_SIM_DEVID,".build/Debug-xros/xros_minimal_app.app"], 
             working_dir=prefix,
             do_log=True)

#command.run(["ideviceinstaller","-i",prefix/(BUNDLE_NAME+".app")], do_log=True)
