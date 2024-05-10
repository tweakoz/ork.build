from obt import dep, path, command, docker, wget, pathtools
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_dir = path.directoryOfInvokingModule()

makedotcfg = this_dir/"Makefile.cfg"

###############################################################################

class dockerinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self.type = docker.Type.SINGLE
      self._name = "ps1dev"
      self.imagename = "obt-ps1dev:latest"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(this_dir)
      command.run([
        "docker", "build", ".", "-t", self.imagename ])
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
            "--mount","type=bind,source=%s,target=/home/ps1dev/Makefile.cfg"%makedotcfg,
            self.imagename,
            "/bin/bash"
        ])
    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def test(self):
        os.chdir(this_dir)
        testprogdir = this_dir/"testprograms"
        builddir = path.builds()/"ps1dev-test1"
        pathtools.ensureDirectoryExists(builddir)
        command.run([
            "docker", "run",
            "--mount","type=bind,source=%s,target=/home/ps1dev/testprograms"%testprogdir,
            "--mount","type=bind,source=%s,target=/home/ps1dev/.build-out"%builddir,
            "--mount","type=bind,source=%s,target=/home/ps1dev/Makefile.cfg"%makedotcfg,
            #"-v","testprogram/Makefile:/home/ps1dev/testprogram/Makefile:rw",
            self.imagename,
            "/bin/bash", "-c", 
            #"find"
            "cd ~/testprograms/test1; make"
            #"cd ~/examples/mandel; make"
        ])
        print("builddir<%s>"%builddir)
        command.run(["ls","-l",builddir])
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "image_name": self.imagename,
      }
    ###############################################