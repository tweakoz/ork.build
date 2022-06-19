import ork.xcode 

class sdkinfo:
  def __init__(self):
    self.identifier = "aarch64-macos"
    self.architecture = "aarch64"
    self.os = "macos"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["x86_64-macos","aarch64-macos"]
  #################################################
  # env_init invoked once at container startup time
  #################################################
  def env_init(self):
    _xcodesdkstr = ork.command.capture([
      "xcodebuild",
      "-version",
      "-sdk","macosx"]).splitlines()
    for l in _xcodesdkstr:
      x = l.split(": ")
      if x[0]=="Path":
        ork.env.append("OBT_MACOS_SDK_DIR",x[1])
      if x[0]=="PlatformVersion":
        ork.env.append("OBT_MACOS_PLATFORM_VERSION",x[1])

