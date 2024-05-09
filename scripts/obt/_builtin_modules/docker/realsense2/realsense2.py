from obt import dep, path, command, docker, wget, pathtools
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

class dockerinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self.type = docker.Type.SINGLE
      self._name = "realsense2"
      self.imagename = "obt-realsense2:latest"
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      #git@github.com:bebbo/amiga-gcc.git
      #fetcher = dep.GithubFetcher(name="realsense2",
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
    ###############################################
    # launch docker container
    ###############################################
    def launch(self,launch_args,environment=None,mounts=None):
        CWD = os.getcwd()
        builddir = path.builds()/"realsense2-test1"
        sourcedir = this_dir/"test1"
        pathtools.mkdir(builddir,clean=True)
        home = os.getenv("HOME")
        cmd = [
          "docker", "run",
            "--gpus","all",
          	"-v", "/dev/bus/usb:/dev/bus/usb",
            "-v", "/dev/video0:/dev/video0",
          	"-v", "/dev/video1:/dev/video1",
          	"-v", "/dev/video2:/dev/video2",
          	"-v", "/dev/video3:/dev/video3",
          	"-v", "/dev/video4:/dev/video4",
            "-v", "/dev/video5:/dev/video5",
          	"-v", "/dev/video6:/dev/video6",
            "-v", "/dev/video7:/dev/video7",
            "-v", "/dev/video8:/dev/video8",
            "-v", "/dev/video9:/dev/video9",
          	"-v", "/tmp/.X11-unix:/tmp/.X11-unix",
          	"-v", "%s/.Xauthority:/home/realsense2/.Xauthority"%(home),
          	"-e", "DISPLAY=%s" % os.environ["DISPLAY"],
            "-e","QT_X11_NO_MITSHM=1",
            #"-v", "%s/.ssh:/home/realsense2/.ssh"%(home),
        ]
        if environment!=None:
          for k in environment.keys():
            v = environment[k]
            cmd += ["-e","%s=%s"%(k,v)]
        if mounts!=None:
          for m in mounts:
            print(m)
            cmd += ["--mount",m]

        if len(launch_args)==0:
          cmd += [
            "-it",
            self.imagename,
            "/bin/bash"
          ]
        else:
          cmd += [
            "-it",
            self.imagename,
          ]
          cmd += launch_args[0].split()
        ####################
        command.run(cmd,do_log=True)
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "image_name": self.imagename,
      }
    ###############################################