from ork import dep, path, command, docker, wget, pathtools
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
      self.type = docker.Type.SINGLE
      self._name = "amigadev"
      self.imagename = "obt-amigadev:latest"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      #git@github.com:bebbo/amiga-gcc.git
      #fetcher = dep.GithubFetcher(name="amigadev",
      #                            repospec="bebbo/amiga-gcc",
      #                            revision="b9ed9db219bc82a0ce570a51b260b7477dc5b75c",
      #                            recursive=False)
      #fetcher.fetch(self.builddir)
      UID = os.getuid()
      GID = os.getgid()
      os.chdir(str(this_dir))
      cmdlist = ["docker", "build"]
      cmdlist += ["--build-arg", "UID=%d"%UID]
      cmdlist += ["--build-arg", "GID=%d"%GID]
      cmdlist += [".", "-t", self.imagename]
      command.run(cmdlist)
      command.run(["docker","pull","sebastianbergmann/amitools"])
    ###############################################
    # launch docker container
    ###############################################
    def launch(self,launch_args):
        builddir = path.builds()/"amigadev-test1"
        sourcedir = this_dir/"test1"
        pathtools.mkdir(builddir,clean=True)
        command.run([
            "docker", "run",
            "-it",
            "--mount","type=bind,source=%s,target=/home/amigadev/test1,readonly"%sourcedir,
            "--mount","type=bind,source=%s,target=/home/amigadev/test1-build"%builddir,
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