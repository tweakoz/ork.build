from obt import dep, path, command, docker, wget, pathtools, host, target
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

class subspaceinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self._name = "host"
      is_linux = host.IsLinux 
      is_arm = host.IsAARCH64
      if is_linux:
        if is_arm:
          self._target = target.descriptor("aarch64","linux")
        else:
          self._target = target.descriptor("x86_64","linux")
      else:
        if is_arm:
          self._target = target.descriptor("aarch64","macos")
        else:
          self._target = target.descriptor("x86_64","macos")
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(this_dir)
      print("build host")
    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args):
      print("launch host")
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "host",
        "prefix": path.stage(),
      }
    ###############################################

