from ork import dep, path, command, docker, wget, pathtools, host, xcode
from ork.deco import Deco
import ork.module
import time, re, socket, os, sys, tempfile
from pathlib import Path
deco = ork.deco.Deco()

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

###############################################################################

class subspaceinfo:
    ###############################################
    def __init__(self):
      super().__init__()
      self._name = "ios"
      self._prefix = path.subspace_root()/"ios"
      self._manifests_path = self._prefix/"manifests"

    ###############################################
    # build the docker image
    ###############################################
    def build(self,build_args,do_wipe=False):
      assert host.IsOsx
      IOS_SDK_DIR = path.Path(os.environ["OBT_IOS_SDK_DIR"])
      print( deco.yellow("Building IOS subspace") )
      print( deco.yellow("IOS SDK: %s" % str(IOS_SDK_DIR) ) )
      print( deco.yellow("manifest dir: %s" % self._manifests_path ) )
      self._manifests_path.mkdir(parents=True,exist_ok=True)
        
    ###############################################
    def shell(self,working_dir=None,container=None):
      import ork._envutils 
      sub_name = os.environ["OBT_PROJECT_NAME"]
      sub_env = ork._envutils.EnvSetup(project_name=sub_name)

      override_sysprompt = "📱-IOS" if (container==None) else "📱-%s"%container

      BASHRC = sub_env.genBashRc()
      BASHRC += "\n\n"
      #BASHRC += "%s --stack\n"%(self._prefix/"bin"/"activate")

      fname = None

      rval = 0

      the_environ = {
        "OBT_SUBSPACE": "ios" if (container==None) else container,
        "OBT_SUBSPACE_PROMPT": override_sysprompt,
        "OBT_PYTHON_SUBSPACE_BUILD_DIR": self._prefix/"builds",
        "OBT_SUBSPACE_LIB_DIR": self._prefix/"lib",
        "OBT_SUBSPACE_DIR": self._prefix,
        #"OBT_SUBSPACE_BIN_DIR": self._prefix/"bin",
      }

      with tempfile.NamedTemporaryFile(dir=path.temp(),mode="w",delete=False) as tempf:
        fname = tempf.name
        tempf.write(BASHRC)
        tempf.close()
        print(fname)

        bash_cmd_list = ["bash", "--rcfile",fname, "-i"]

        rval = command.run(bash_cmd_list,working_dir=working_dir,environment=the_environ,do_log=True)
      return rval
      

    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args):
      print("launch ios")
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "ios",
        "prefix": path.stage(),
      }
    ###############################################

