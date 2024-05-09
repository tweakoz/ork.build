import obt.xcode 
import obt.command 
import obt.env
import obt.path 
import os, re, sys
import subprocess

class _iossdk_private:

  _instance = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._initialize()
    return cls._instance

  def _initialize(self):

    self._xcodesdkstr = obt.command.capture([
      "xcodebuild",
      "-version",
      "-sdk"])

    lines = self._xcodesdkstr.splitlines()

    class SDKVER:
      def __init__(self, match):
        self.number = a.group(1)
        self.name = a.group(0)
        self.major,self.minor = self.number.split(".")
        self.path = obt.command.capture([
          "xcodebuild",
          "-version",
          "-sdk", self.name,
          "Path"],do_log=False).splitlines()

      def __repr__(self):
        return "%s : %s " % (self.name, self.path)

    self.versions = dict()    

    for line in lines:
      regex = re.compile(r"iphoneos(\d+.\d+)")    
      a = regex.search(line)
      if a is not None:
        sdk = SDKVER(a)
        self.versions[sdk.number] = sdk
      
    #print(self.versions)  

    sorted = list(self.versions.keys())
    sorted.sort()
    
    highest = self.versions[sorted[-1]]
    
    self._iossdkstr = highest.path
    self._iossdkver = highest.number

    print(f"Using SDK: {self._iossdkver} {self._iossdkstr}")
    
    try:
      # Use xcrun to find the path to clang for the current SDK
      clang_path = subprocess.check_output([
        "xcrun",
        "-find",
        "clang"
      ], text=True).strip()
      clangpp_path = subprocess.check_output([
        "xcrun",
        "-find",
        "clang++"
      ], text=True).strip()

      # Set environment variable for the compiler path
      self._clang_path = clang_path
      self._clangpp_path = clangpp_path

    except subprocess.CalledProcessError as e:
      print(f"Error executing command: {e}")
    except Exception as e:
      print(f"An unexpected error occurred: {e}")

    #assert(False)


class sdkinfo:
  #################################################
  # env_init invoked once at container startup time
  #################################################

  #############################################
  def __init__(self):
    self.identifier = "aarch64-ios"
    self.architecture = "aarch64"
    self.os = "ios"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["x86_64-macos","aarch64-macos"]
  #############################################
  @property
  def sdkdir(self):
    return obt.path.Path(os.environ["OBT_IOS_SDK_DIR"])
  @property
  def _sdkdir(self):
    IOS_SDK = _iossdk_private()
    return IOS_SDK._iossdkstr
  @property
  def _sdkver(self):
    IOS_SDK = _iossdk_private()
    return IOS_SDK._iossdkver
  @property
  def _clang_path(self):
    IOS_SDK = _iossdk_private()
    return IOS_SDK._clang_path
  @property
  def _clangpp_path(self):
    IOS_SDK = _iossdk_private()
    return IOS_SDK._clang_path
  #############################################
  @property
  def _environment(self):
    IOS_SDK = _iossdk_private()
    return {
      "IOS_SDK_DIR": self._sdkdir,
      "IOS_SDK_VER": self._sdkver,
      "IOS_CLANG_PATH": self._clang_path,
      "IOS_CLANGPP_PATH": self._clangpp_path,
      #"CMAKE_TOOLCHAIN_FILE": prefix/"ios.toolchain.cmake",
      #"OBT_SUBSPACE_PROMPT": self._gen_sysprompt(),
      "OBT_TARGET": "aarch64-ios",
      "IOS_PREFIX": obt.path.subspace_root()/"ios",
      #"OBT_SUBSPACE": "ios",
    }
  #############################################
  def install_app(self,bundle_id,app_bundle_dir):
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
    print(f"Installing app {bundle_id} from {app_bundle_dir} to iphone")
    subprocess.check_output(["ideviceinstaller", "-U", bundle_id])
    subprocess.check_output(["ideviceinstaller", "-i", app_bundle_dir])
  #############################################
  def misc(self):
    return {
      "sdkdir": self.sdkdir,
      "_sdkdir": self._sdkdir,
      "_sdkver": self._sdkver,
      "_clang_path": self._clang_path,
      "_clangpp_path": self._clangpp_path
    }

