import obt.xcode 
import obt.command 
import obt.env
import obt.path 
import os
import subprocess

class _xrossdk_private:
  def __init__(self):
    self._xcodesdkstr = obt.command.capture([
      "xcodebuild",
      "-version",
      "-sdk"])
    self.has_xrosdk_1 = self._xcodesdkstr.find("(xrsimulator1.0)")>0
    print("has_xrosdk_1<%s>"%self.has_xrosdk_1)
    if self.has_xrosdk_1:
      self._xrosdkver = "1.0"
      self._xrosdkstr = obt.command.capture([
        "xcodebuild",
        "-version",
        "-sdk", "xrsimulator1.0",
        "Path"],do_log=False).splitlines()[0].strip("\"")
    try:
      # Use xcrun to find the path to clang for the current SDK
      clang_path = subprocess.check_output([
        "xcrun",
        "-find",
        "clang"
      ], text=True).strip().strip("\"")
      clangpp_path = subprocess.check_output([
        "xcrun",
        "-find",
        "clang++"
      ], text=True).strip().strip("\"")

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
    self.identifier = "aarch64-xros"
    self.architecture = "aarch64"
    self.os = "xrossim"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["x86_64-macos","aarch64-macos"]
  #############################################
  @property
  def sdkdir(self):
    return obt.path.Path(os.environ["OBT_XROS_SDK_DIR"])
  @property
  def _sdkdir(self):
    IOS_SDK = _xrossdk_private()
    return IOS_SDK._xrosdkstr
  @property
  def _sdkver(self):
    IOS_SDK = _xrossdk_private()
    return IOS_SDK._xrosdkver
  @property
  def _clang_path(self):
    IOS_SDK = _xrossdk_private()
    return IOS_SDK._clang_path
  @property
  def _clangpp_path(self):
    IOS_SDK = _xrossdk_private()
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

