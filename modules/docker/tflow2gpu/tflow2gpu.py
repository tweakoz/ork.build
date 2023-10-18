from obt import dep, path, command, docker, wget, pathtools
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

makedotcfg = this_dir/"Makefile.cfg"

###############################################################################

class dockerinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self.type = docker.Type.SINGLE
      self._name = "tflow2"
      self.imagename = "obt-tflow2:latest"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(this_dir)
      UID = os.getuid()
      GID = os.getgid()
      cmdlist = ["docker", "build"]
      cmdlist += ["--build-arg", "UID=%d"%UID]
      cmdlist += ["--build-arg", "GID=%d"%GID]
      cmdlist += [".", "-t", self.imagename]
      command.run(cmdlist)
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
    
        command.run(["xhost","+localhost"])

        command.run([
            "docker", "run",
            "-it",
            "--gpus","all",
            "--mount","type=bind,source=%s/test_single_gpu.py,target=/home/tensorflow/test_single_gpu.py"%this_dir,
            "--mount","type=bind,source=%s/test_multi_gpu.py,target=/home/tensorflow/test_multi_gpu.py"%this_dir,
            "--mount","type=bind,source=%s/test_mediapipe.sh,target=/home/tensorflow/test_mediapipe.sh"%this_dir,
            "-v","/tmp/.X11-unix:/tmp/.X11-unix",
            "-e","DISPLAY=%s"%os.environ["DISPLAY"],
            "-e","QT_X11_NO_MITSHM=1",
            #"--mount","type=bind,source=%s,target=/home/tensorflow/Makefile.cfg"%makedotcfg,
            self.imagename,
            "/bin/bash"
        ])
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "image_name": self.imagename,
      }
    ###############################################