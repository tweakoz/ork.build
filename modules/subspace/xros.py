from obt import dep, path, command, docker, wget, pathtools, sdk
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

cmake_tc = """
set(XROS_SDK_PATH $ENV{XROS_SDK_DIR})
set(CMAKE_SYSTEM_NAME visionOS)

# Specify the architectures to build for (e.g., arm64 for actual devices)
set(CMAKE_OSX_ARCHITECTURES arm64)

# Specify the minimum visionOS deployment target
set(CMAKE_OSX_DEPLOYMENT_TARGET $ENV{XROS_SDK_VER})

# Specify the path to the compiler
set(CMAKE_C_COMPILER $ENV{XROS_CLANG_PATH})
set(CMAKE_CXX_COMPILER $ENV{XROS_CLANGPP_PATH})
set(CMAKE_INSTALL_PREFIX $ENV{OBT_SUBSPACE_BUILD_DIR})
"""

###############################################################################

class subspaceinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self._name = "xros"
      self._prefix = path.subspace_root()/"xros"
      self._manifest_path = path.manifests_root()/self._name
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args,do_wipe=False):
      pathtools.ensureDirectoryExists(self._prefix)
      pathtools.ensureDirectoryExists(self._prefix/"builds")
      pathtools.ensureDirectoryExists(self._prefix/"lib")
      pathtools.ensureDirectoryExists(self._prefix/"bin")
      os.chdir(self._prefix)
      #####################
      # generate cmake toolchain
      #####################
      tc_output = self._prefix/"xros.toolchain.cmake"
      with open(tc_output,"w") as f:
        f.write(cmake_tc)
      #####################

# You might need to set more variables depending on your setup

      
      print("build xros")
    ###############################################
    def _gen_sysprompt(self):
      return "xros"
    ###############################################
    def _gen_environment(self):
      TEMP_PATH = path.temp()
      XROS_SDK = sdk.descriptor("aarch64","xros")
      SDK_DIR = XROS_SDK._sdkdir
      SDK_VER = XROS_SDK._sdkver
      the_environ = {
        "OBT_SUBSPACE_BUILD_DIR": self._prefix/"builds",
        "OBT_SUBSPACE_LIB_DIR": self._prefix/"lib",
        "OBT_SUBSPACE_DIR": self._prefix,
        "OBT_SUBSPACE_BIN_DIR": self._prefix/"bin",
        "XROS_PREFIX": self._prefix,
        "XROS_SDK_DIR": SDK_DIR,
        "XROS_SDK_VER": SDK_VER,
        "XROS_CLANG_PATH": XROS_SDK._clang_path,
        "XROS_CLANGPP_PATH": XROS_SDK._clangpp_path,
        "OBT_SUBSPACE": "xros",
        "CMAKE_TOOLCHAIN_FILE": self._prefix/"ios.toolchain.cmake",
        "OBT_SUBSPACE_PROMPT": self._gen_sysprompt(),
        "OBT_TARGET": "aarch64-ios",
      }        
      return the_environ
    ###############################################
    # launch conda subspace shell
    ###############################################
    def shell(self,working_dir=None,container=None):
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
      print("launch xros")
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "xros",
        "prefix": self._prefix,
      }
    ###############################################

