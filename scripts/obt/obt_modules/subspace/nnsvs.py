from obt import dep, path, command, docker, wget, pathtools, pip, _envutils
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
      self._name = "nnsvs"
      self.python = dep.DepNode.nodeForName("python").instance
      self.venv_dir = self.python.virtualenv_dir/"nnsvs"
      self._manifest_path = path.manifests()/self._name
    ###############################################
    # build the NNSVS namespace
    ###############################################
    def build(self,build_args,do_wipe=False):
      print("build nnsvs")
      venv_exists = self.venv_dir.exists()
      if do_wipe or not venv_exists:
        pathtools.rmdir(self.venv_dir,force=True)
        cmd_list = [self.python.executable,"-m","venv",self.venv_dir]
        command.run(cmd_list,do_log=True)
      dep.require("_nnsvs")
      pathtools.chdir(path.builds()/"_nnsvs")
      def pip_install(package):
        cmd_list = [self.venv_dir/"bin"/"pip3","install",package]
        command.run(cmd_list,do_log=True)
      pip_install(".")
      pip_install("git+https://github.com/tweakoz/pysinsy.git@master#egg=pysinsy")
    ###############################################
    # launch NNSVS namespace
    #  print out connection info
    ###############################################
    def launch(self,launch_args):
      print("launch nnsvs")
      #cmd_list = [self.venv_dir/"bin"/"activate"]
      #command.run(cmd_list,do_log=True)
    ###############################################
    def _gen_sysprompt(self,container=None):
      return "🎤-NNSVS" if (container==None) else "🎤-%s"%container
    ###############################################
    def _gen_environment(self,container=None):
      TEMP_PATH = path.temp()
      PYTHON_HOME = self.venv_dir
      if container!=None:
        PYTHON_HOME = self.venv_dir/"envs"/container

      PYTHON_DEP = dep.instance("python")

      SITE_PKG = PYTHON_HOME/"lib"/PYTHON_DEP._deconame/"site-packages"

      pypath = os.environ["OBT_SCRIPTS_DIR"]
      pypath += ":"+str(SITE_PKG)
      pypath += ":"+os.environ["PYTHONPATH"]

      ldlibpath = str(PYTHON_HOME/"lib")
      ldlibpath += ":"+os.environ["LD_LIBRARY_PATH"]

      the_environ = {
        "LD_LIBRARY_PATH": ldlibpath,
        "OBT_PYTHON_SUBSPACE_BUILD_DIR": PYTHON_HOME/"builds",
        "OBT_SUBSPACE_LIB_DIR": PYTHON_HOME/"lib",
        "OBT_SUBSPACE_DIR": PYTHON_HOME,
        "OBT_SUBSPACE_BIN_DIR": PYTHON_HOME/"bin",
        "PYTHONPATH": pypath,
        "OBT_PYTHONHOME": PYTHON_HOME,
        "OBT_PYPKG": SITE_PKG,
        "CONDA_PREFIX": self.venv_dir,
        "OBT_SUBSPACE": "nnsvs" if (container==None) else container,
        "OBT_SUBSPACE_PROMPT": self._gen_sysprompt(container=container),
        "NNSVS_ROOT": path.builds()/"_nnsvs",
        "NNSVS_SCRIPTS": path.modules()/"subspace"/"nnsvs",
      }        
      return the_environ
    ###############################################
    def shell(self,working_dir=None,container=None):
      print("launch nnsvs")
      #venv_py = self.venv_dir/"bin"/"python3"
      #cmd_list = [venv_py]
      #command.run(cmd_list,do_log=True)
      sub_name = os.environ["OBT_PROJECT_NAME"]
      sub_env = _envutils.EnvSetup(project_name=sub_name)

      override_sysprompt = self._gen_sysprompt(container=container)

      BASHRC = sub_env.genBashRc()
      BASHRC += "\n\n"
      BASHRC += "source %s --stack\n"%(self.venv_dir/"bin"/"activate")

      fname = None

      rval = 0

      environ = self._gen_environment(container)

      import tempfile
      with tempfile.NamedTemporaryFile(dir=path.temp(),mode="w",delete=False) as tempf:
        fname = tempf.name
        tempf.write(BASHRC)
        tempf.close()
        print(fname)

        conda_cmdlist  = ["bash"]
        conda_cmdlist += ["--rcfile",fname, "-i"]



        rval = command.run(conda_cmdlist,working_dir=working_dir,environment=environ,do_log=True)
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "nnsvs",
      }
    ###############################################

