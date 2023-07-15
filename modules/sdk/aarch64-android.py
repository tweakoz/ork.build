from obt.wget import wget
from obt import path, command, env, pathtools
from yarl import URL 
import os, sys

class sdkinfo:
  ##################################################################
  def __init__(self):
    self.identifier = "aarch64-android"
    self.architecture = "aarch64"
    self.os = "android"
    self.c_compiler = "clang"
    self.cxx_compiler = "clang++"
    self.supports_host = ["aarch64-macos"]
    self.sdk_dir = path.sdks()/"android-sdk"
    self.ANDROID_VERSION="28" 
    self.ANDROID_BUILD_TOOLS_VERSION="27.0.3"
    self.ANDROID_NDK_VERSION = "20.0.5594570"

  ##################################################################
  def misc(self):
    return {
      "hello": "yo"
    }
  ##################################################################
  def env_init(self):
    env.append("ANDROID_HOME",self.sdk_dir)
    env.append("ANDROID_VERSION",self.ANDROID_VERSION)
    env.append("ANDROID_BUILD_TOOLS_VERSION",self.ANDROID_BUILD_TOOLS_VERSION)
    env.append("JAVA_HOME",'/Applications/Android Studio.app/Contents/jre/Contents/Home')
    # TODO - activate following only in SDK subshell
    env.append("PATH",path.sdks()/"cmdline-tools"/"bin")
    env.append("PATH",self.sdk_dir/"build-tools"/self.ANDROID_BUILD_TOOLS_VERSION/"bin")
    env.append("PATH",self.sdk_dir/"tools"/"bin")
    env.append("PATH",self.sdk_dir/"tools"/"bin")
    env.append("PATH",self.sdk_dir/"platform-tools")
    env.append("PATH",self.sdk_dir/"gradle-5.6.4"/"bin")

  ##################################################################
  def install(self):
    STUDIO_VERSION = "2021.2.1.14"
    dlgoogle = URL("https://dl.google.com/android/repository")
    redirector = URL("https://redirector.gvt1.com/edgedl/android/studio/install")/STUDIO_VERSION

    studio_name = "android-studio-%s-mac_arm.dmg"%STUDIO_VERSION
    ndk_name = "android-ndk-r22b-darwin-x86_64.zip"
    cltools_name = "commandlinetools-mac-8512546_latest.zip"

    gradle_path = wget(urls=["https://services.gradle.org/distributions/gradle-5.6.4-bin.zip"],
                       output_name="gradle.zip",
                       md5val="d1456582f1513c1c04d4bd4ae952f25d")

    studio_path = wget(urls=[redirector/studio_name], 
                output_name = studio_name,
                md5val = "0c2b3c364510d4941d77ab879c901859" )

    #ndk_zip_path = wget(urls=[dlgoogle/ndk_name], 
    #             output_name = ndk_name,
    #             md5val = "3e22f5eefb5f0dfaf0d779d60f85685b" )

    clt_zip_path = wget(urls=[dlgoogle/cltools_name], 
                 output_name = cltools_name,
                 md5val = "769ecd04e00367458de6e948b944c20e" )

    if (gradle_path==None) or (studio_path==None) or (clt_zip_path==None):
      print( "Could not complete downloads for Android SDK")
      sys.exit(-2)

    path.sdks().chdir()

    pathtools.ensureDirectoryExists(self.sdk_dir)
    pathtools.ensureDirectoryExists(self.sdk_dir/"licenses")
    os.system('echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_HOME/licenses/android-sdk-license"')

    command.run(["open",studio_path])
    command.run(["unzip","-o",clt_zip_path])
    command.run(["unzip","-o",gradle_path])

    command.run(["sdkmanager",
                 "--sdk_root=%s" % self.sdk_dir,
                 "--update"],
                 do_log=True)

    command.run(["sdkmanager", 
                 "--sdk_root=%s" % self.sdk_dir, 
                 "build-tools;%s" % self.ANDROID_BUILD_TOOLS_VERSION],
                 do_log=True)

    command.run(["sdkmanager",
                 "--sdk_root=%s" % self.sdk_dir, 
                 "platforms;android-%s" % self.ANDROID_VERSION],
                 do_log=True)

    command.run(["sdkmanager",
                 "--sdk_root=%s" % self.sdk_dir, 
                 "ndk;%s" % self.ANDROID_NDK_VERSION],
                 do_log=True)

    command.run(["sdkmanager", 
                 "--sdk_root=%s" % self.sdk_dir, 
                 "platform-tools"],
                 do_log=True)


    sys.exit(-1)




  ##################################################################
