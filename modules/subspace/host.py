from ork import dep, path, command, docker, wget, pathtools
from ork.deco import Deco
import ork.module
import time, re, socket, os, sys
from pathlib import Path
deco = ork.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

class subspaceinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self._name = "host"
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
      }
    ###############################################

