import obt.xcode 

class sdkinfo:
  def __init__(self):
    self.identifier = "x86_64-macos"
    self.architecture = "x86_64"
    self.os = "macos"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["x86_64-macos","aarch64-macos"]

  def env_init(self):
    _xcodesdkstr = obt.command.capture([
      "xcodebuild",
      "-version",
      "-sdk","macosx"]).splitlines()
    for l in _xcodesdkstr:
      x = l.split(": ")
      if x[0]=="Path":
        obt.env.set("OBT_MACOS_SDK_DIR",x[1])
      if x[0]=="PlatformVersion":
        obt.env.set("OBT_MACOS_PLATFORM_VERSION",x[1])

