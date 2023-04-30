from ork import xcode, log, env

class sdkinfo:
  def __init__(self):
    self.identifier = "x86_64-macos"
    self.architecture = "x86_64"
    self.os = "macos"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["x86_64-macos","aarch64-macos"]

  def env_init(self):
    log.marker("registering Macos SDK")
    env.set("OBT_MACOS_SDK_DIR","")
    _xcodesdkstr = xcode.macsdkstr()
    for l in _xcodesdkstr:
      x = l.split(": ")
      if x[0]=="Path":
        env.append("OBT_MACOS_SDK_DIR",x[1])
      if x[0]=="PlatformVersion":
        env.append("OBT_MACOS_PLATFORM_VERSION",x[1])

