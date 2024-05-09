from obt import dep, path, command, docker, wget, pathtools
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
      self._name = "yo"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(this_dir)
      print("build yo")
    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args):
      print("launch yo")
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "yo",
      }
    ###############################################

