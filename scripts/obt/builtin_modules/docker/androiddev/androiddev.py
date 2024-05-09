from obt import dep, path, command, docker, wget, pathtools, host
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
      self._name = "androiddev"
      self.imagename = "obt-androiddev:latest"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(this_dir)
      #######################################
      if host.IsAARCH64:
        BASE_IMAGE = "arm64v8/gradle:6-jdk8"
      else:
        BASE_IMAGE = "gradle:5.6.4-jdk8"
      #######################################
      command.run([
        "docker", "build", "--platform", "linux/amd64",
        "--build-arg", "BASE_IMAGE=%s"%BASE_IMAGE,
        ".", 
        "-t", self.imagename ])
    ###############################################
    # kill active docker container
    ###############################################
    def kill(self):
      pass
    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args,environment=None,mounts=None):
        command.run([
            "docker", "run",
            "-it",
            #"--mount","type=bind,source=%s,target=/home/androiddev/Makefile.cfg"%makedotcfg,
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