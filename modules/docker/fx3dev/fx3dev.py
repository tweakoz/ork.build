from obt import dep, path, command, docker, wget, pathtools
from obt.deco import Deco
from obt.git import fetch_tarball_from_github
import obt.module
import obt.path
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
      self._name = "fx3dev"
      self.imagename = "obt-fx3dev:latest"
      self.sdk_dir = this_dir/"fx3dev-sdk"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      repospec = "tweakoz/cypress-fx3-sdk-linux"
      revision = "master"
      md5val = "20d04241f9bd28fc2be23eb0326e6222"
      ret = fetch_tarball_from_github( repospec=repospec,
                                       revision=revision,
                                       md5val=md5val,
                                       destdir=self.sdk_dir)
      if ret!=0:
        print("Error fetching tarball")
        return
      command.run(["cp",this_dir/"Dockerfile",self.sdk_dir/"Dockerfile"])
      os.chdir(self.sdk_dir)
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
            "--mount","type=bind,source=%s,target=/home/fx3dev/Makefile.cfg"%makedotcfg,
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
        builddir = path.builds()/"fx3dev-test1"
        pathtools.ensureDirectoryExists(builddir)
        command.run([
            "docker", "run",
            "--mount","type=bind,source=%s,target=/home/fx3dev/testprograms"%testprogdir,
            "--mount","type=bind,source=%s,target=/home/fx3dev/.build-out"%builddir,
            "--mount","type=bind,source=%s,target=/home/fx3dev/Makefile.cfg"%makedotcfg,
            #"-v","testprogram/Makefile:/home/fx3dev/testprogram/Makefile:rw",
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