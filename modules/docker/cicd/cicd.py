from ork import dep, path, command, docker, wget, pathtools, host
from ork.deco import Deco
import ork.module
import time, re, socket, os, sys
from pathlib import Path
deco = ork.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

class dockerinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self.type = docker.Type.COMPOSITE
      self._name = "cicd"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(this_dir)
      chain = command.chain()
      #######################################
      chain.run(["bin/build_master_image.py"])
      chain.run(["bin/build_worker_ub20_image.py"])
      chain.run(["bin/build_worker_ub22_image.py"])
      chain.run(["bin/build_worker_android_image.py"])
      return chain.ok()
    ###############################################
    # kill active docker container
    ###############################################
    def kill(self):
      pass
    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args):
      os.chdir(this_dir)
      command.run(["bin/launch_testnossl.sh"])
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
      }
    ###############################################