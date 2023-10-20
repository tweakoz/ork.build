from obt import dep, path, command, docker, wget
from obt.deco import Deco
import obt.module
import time, re, socket, os, sys
from pathlib import Path
deco = obt.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

VERSION = "9.6"
MD5SUM = "bd07b8596c44133dd6be58b55dccca16"

###############################################################################

class dockerinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self.type = docker.Type.SINGLE
      self._name = "sagemath"
      self.containername = "obt-sagemath"
      self.imagename = "obt/sagemath-jupyter"
      self.tryipaddr = socket.gethostbyname(socket.gethostname())
      self.archivename = "sage-%s.tar.gz" % VERSION
    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args):
      os.chdir(path.stage())
      URL = "http://sage.mirror.garr.it/mirrors/sage/src/%s"%self.archivename
      _archive_path = wget.wget(urls=[URL],
                       md5val=MD5SUM,
                       output_name=self.archivename)
      print(_archive_path)
      if _archive_path!=None:
        command.run([
          "docker", "build", "-f", this_dir/"Dockerfile", "-t", self.imagename, "." ] )
    ###############################################
    # kill active docker container
    ###############################################
    def kill(self):
        os.chdir(this_dir)
        retstr = command.capture([
            "docker-compose",
            "-f","docker-compose.yml",
            "down"
        ])
    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args,environment=None,mounts=None):
        #self.kill()
        os.chdir(this_dir)
        command.run([
            "docker-compose",
            "-f","docker-compose.yml",
            "up","--remove-orphans",
            "--detach"
        ])
        time.sleep(2)
        command.run([
            "docker-compose","logs"
        ])
        ######################
        #print("%s<%s>"%(deco.key("URL"),deco.val(url)))
        #print("%s<%s>"%(deco.key("TOKEN"),deco.val(token)))
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "container_name": self.containername,
        "image_name": self.imagename,
        "version": VERSION
      }
    ###############################################