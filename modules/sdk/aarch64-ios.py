import obt.xcode 
import obt.command 
import obt.env
import obt.path 
import os
import subprocess

class _iossdk_private:
  def __init__(self):
    self._xcodesdkstr = obt.command.capture([
      "xcodebuild",
      "-version",
      "-sdk"])
    self.has_iossdk15_2 = self._xcodesdkstr.find("(iphoneos15.2)")>0
    self.has_iossdk15_5 = self._xcodesdkstr.find("(iphoneos15.5)")>0
    self.has_iossdk17_0 = self._xcodesdkstr.find("(iphoneos17.0)")>0
    print("has_iossdk15_2<%s>"%self.has_iossdk15_2)
    print("has_iossdk15_5<%s>"%self.has_iossdk15_5)
    print("has_iossdk17_0<%s>"%self.has_iossdk17_0)
    if self.has_iossdk15_2:
      self._iossdkver = "15.2"
      self._iossdkstr = obt.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", "iphoneos15.2",
        "Path"],do_log=False).splitlines()
      #obt.env.set("OBT_IOS_SDK","iphoneos15.2")
      #obt.env.set("OBT_IOS_SDK_DIR",self._iossdkstr)
    elif self.has_iossdk15_5:
      self._iossdkver = "15.5"
      self._iossdkstr = obt.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", "iphoneos15.5",
        "Path"],do_log=False).splitlines()
      #obt.env.set("OBT_IOS_SDK","iphoneos15.5")
      #obt.env.set("OBT_IOS_SDK_DIR",self._iossdkstr)
    elif self.has_iossdk17_0:
      self._iossdkstr = obt.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", "iphoneos17.0",
        "Path"],do_log=False).splitlines()[0]
      self._iossdkver = "17.0"
      #obt.env.set("OBT_IOS_SDK","iphoneos17.0")
      #obt.env.set("OBT_IOS_SDK_DIR",a)
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

