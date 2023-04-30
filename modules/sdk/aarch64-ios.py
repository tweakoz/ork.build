import ork.xcode 
import ork.command 
import ork.env
import ork.path 
import ork.log
import os

class sdkinfo:
  #################################################
  # env_init invoked once at container startup time
  #################################################
  def env_init(self):
    _xcodesdkstr = ork.command.capture([
      "xcodebuild",
      "-version",
      "-sdk"])
    has_iossdk16_4 = _xcodesdkstr.find("(iphoneos16.4)")>0
    has_iossdk15_2 = _xcodesdkstr.find("(iphoneos15.2)")>0
    has_iossdk15_5 = _xcodesdkstr.find("(iphoneos15.5)")>0
    print("has_iossdk16_4<%s>"%has_iossdk16_4)
    print("has_iossdk15_5<%s>"%has_iossdk15_5)
    print("has_iossdk15_2<%s>"%has_iossdk15_2)
    #############################################
    def do_sdk(sdkname):
      _iossdkstr = ork.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", sdkname,
        "Path"],do_log=False).splitlines()
      ork.env.append("OBT_IOS_SDK","iphoneos16.4")
      ork.env.append("OBT_IOS_SDK_DIR",_iossdkstr)
      ork.log.marker("registering IOS SDK: %s"%sdkname)
    #############################################
    if has_iossdk16_4:
      do_sdk("iphoneos16.4")
    elif has_iossdk15_5:
      do_sdk("iphoneos15.5")
    elif has_iossdk15_2:
      do_sdk("iphoneos15.2")
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
    return ork.path.Path(os.environ["OBT_IOS_SDK_DIR"])
  #############################################
  def misc(self):
    return {
      "sdkdir": self.sdkdir
    }

