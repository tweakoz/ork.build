from obt import dep, path, command, docker, wget, pathtools, sdk, conan
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))
PREFIX = path.subspace_root()/"ios"

###############################################################################

cmake_tc = """
set(IOS_SDK_PATH $ENV{IOS_SDK_DIR})
set(CMAKE_SYSTEM_NAME iOS)

# Specify the architectures to build for (e.g., arm64 for actual devices)
set(CMAKE_OSX_ARCHITECTURES arm64)

# Specify the minimum iOS deployment target
set(CMAKE_OSX_DEPLOYMENT_TARGET $ENV{IOS_SDK_VER})

# Specify the path to the compiler
set(CMAKE_C_COMPILER $ENV{IOS_CLANG_PATH})
set(CMAKE_CXX_COMPILER $ENV{IOS_CLANGPP_PATH})
set(CMAKE_INSTALL_PREFIX $ENV{OBT_SUBSPACE_BUILD_DIR})
"""

###############################################################################

conan_host_profile = """
[settings]
os=iOS
os.version=17.0
arch=armv8
compiler=apple-clang
compiler.version=15.0
compiler.libcxx=libc++
build_type=Release
os.sdk=iphoneos
"""

conan_build_profile = """
[settings]
os=Macos
arch=armv8  
compiler=apple-clang
compiler.version=15.0
compiler.libcxx=libc++
build_type=Release
"""


###############################################################################

class _iossubspace_private:

  _instance = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._initialize()
    return cls._instance

  def _initialize(self):
    pathtools.ensureDirectoryExists(PREFIX)
    pathtools.ensureDirectoryExists(PREFIX/"manifests")
    pathtools.ensureDirectoryExists(PREFIX/"builds")
    pathtools.ensureDirectoryExists(PREFIX/"include")
    pathtools.ensureDirectoryExists(PREFIX/"lib")
    pathtools.ensureDirectoryExists(PREFIX/"bin")
    pathtools.ensureDirectoryExists(PREFIX/"conan")
    host_profile_path = PREFIX/"ios.host.profile"
    build_profile_path = PREFIX/"ios.build.profile"
    if not host_profile_path.exists():
      with open(host_profile_path,"w") as f:
        f.write(conan_host_profile)
    if not build_profile_path.exists():
      with open(build_profile_path,"w") as f:
        f.write(conan_build_profile)

###############################################################################

class subspaceinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self._name = "ios"
      self._subsrc = this_dir
      self._prefix = PREFIX
      self._manifest_path = path.manifests()/self._name
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args,do_wipe=False):
      self._private = _iossubspace_private()
      os.chdir(self._prefix)
      #####################
      # generate cmake toolchain
      #####################
      tc_output = self._prefix/"ios.toolchain.cmake"
      with open(tc_output,"w") as f:
        f.write(cmake_tc)     
    ###############################################
    def _gen_sysprompt(self):
      return "ios"
    ###############################################
    def _gen_environment(self):
      
      if "DEVELOPMENT_TEAM" not in os.environ:
        print(deco.err("DEVELOPMENT_TEAM not set"))
        assert(False)
      
      TEMP_PATH = path.temp()
      IOS_SDK = sdk.descriptor("aarch64","ios")
      SDK_DIR = IOS_SDK._sdkdir
      SDK_VER = IOS_SDK._sdkver
      
      orig_path = os.environ["PATH"]
      the_environ = {
        "OBT_SUBSPACE_BUILD_DIR": self._prefix/"builds",
        "OBT_SUBSPACE_LIB_DIR": self._prefix/"lib",
        "OBT_SUBSPACE_DIR": self._prefix,
        "OBT_SUBSPACE_BIN_DIR": self._prefix/"bin",
        "IOS_PREFIX": self._prefix,
        "IOS_SDK_DIR": SDK_DIR,
        "IOS_SDK_VER": SDK_VER,
        "IOS_CLANG_PATH": IOS_SDK._clang_path,
        "IOS_CLANGPP_PATH": IOS_SDK._clangpp_path,
        "OBT_SUBSPACE": "ios",
        "CMAKE_TOOLCHAIN_FILE": self._prefix/"ios.toolchain.cmake",
        "OBT_SUBSPACE_PROMPT": self._gen_sysprompt(),
        "OBT_TARGET": "aarch64-ios",
        "PATH": orig_path+":"+str(this_dir/"bin"),
      }       
      the_environ.update(conan.environment()) 
      return the_environ
    ###############################################
    # launch conda subspace shell
    ###############################################
    def shell(self,working_dir=None,container=None):
      self._private = _iossubspace_private()
      sys.path.append(os.environ["OBT_BIN_PUB_DIR"])
      from _obt_config import configFromEnvironment
      import obt._envutils 
      obt_config = configFromEnvironment()
      sub_env = obt._envutils.EnvSetup(obt_config)
      #############################
      BASHRC = sub_env.genBashRc()
      BASHRC += "\n\n"
      BASHRC += "%s --stack\n"%(self._prefix/"bin"/"activate")
      fname = None
      rval = 0
      environ = self._gen_environment()
      import tempfile
      bash_command = ["bash"]
      with tempfile.NamedTemporaryFile(dir=path.temp(),mode="w",delete=False) as tempf:
        fname = tempf.name
        tempf.write(BASHRC)
        tempf.close()
        print(fname)
        bash_command += ["--rcfile",fname, "-i"]
        rval = command.run(bash_command,working_dir=working_dir,environment=environ,do_log=True)
      #############################
      return rval

    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args):
      self._private = _iossubspace_private()
      print("launch ios")
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "ios",
        "prefix": self._prefix,
      }
    ###############################################

