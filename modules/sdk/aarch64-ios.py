import obt.xcode 
import obt.command 
import obt.env
import obt.path 
import os

class sdkinfo:
  #################################################
  # env_init invoked once at container startup time
  #################################################
  def env_init(self):
    _xcodesdkstr = obt.command.capture([
      "xcodebuild",
      "-version",
      "-sdk"])
    has_iossdk15_2 = _xcodesdkstr.find("(iphoneos15.2)")>0
    has_iossdk15_5 = _xcodesdkstr.find("(iphoneos15.5)")>0
    print("has_iossdk15_2<%s>"%has_iossdk15_2)
    print("has_iossdk15_5<%s>"%has_iossdk15_5)
    if has_iossdk15_2:
      _iossdkstr = obt.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", "iphoneos15.2",
        "Path"],do_log=False).splitlines()
      obt.env.append("OBT_IOS_SDK","iphoneos15.2")
      obt.env.append("OBT_IOS_SDK_DIR",_iossdkstr)
    if has_iossdk15_5:
      _iossdkstr = obt.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", "iphoneos15.5",
        "Path"],do_log=False).splitlines()
      obt.env.append("OBT_IOS_SDK","iphoneos15.5")
      obt.env.append("OBT_IOS_SDK_DIR",_iossdkstr)
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
  #############################################
  def misc(self):
    return {
      "sdkdir": self.sdkdir
    }

