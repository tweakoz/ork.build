import obt.xcode 
import obt.command 
import obt.env
import obt.path 
import os, re
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
  def misc(self):
    return {
      "sdkdir": self.sdkdir,
      "_sdkdir": self._sdkdir,
      "_sdkver": self._sdkver,
      "_clang_path": self._clang_path,
      "_clangpp_path": self._clangpp_path
    }

