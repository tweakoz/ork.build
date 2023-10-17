#
#conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch -y
#git clone git@github.com:pytorch/examples.git
#cd examples/mnist
#pip install -r requirements.txt
#python main.py

#cd examples/vae
#pip install -r requirements.txt
#python main.py

from obt import dep, path, command, host, wget, pathtools, subspace
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
      self._name = "conda"
      self._prefix = path.subspace_root()/"conda"
      self._manifest_path = path.manifests()/self._name
    ###############################################
    @property 
    def conda_executable(self):
      return self._prefix/"bin"/"conda"
    ###############################################
    @property
    def envdir(self):
      return self._prefix/"envs"
    ###############################################
    # build conda subspace
    ###############################################
    def build(self,build_args,do_wipe=False):
      print( deco.yellow("Building Conda subspace") )
      if do_wipe:
        self._wipe()
      ########################################
      if host.IsLinux:
        if host.IsX86_64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh"
          MD5SUM = "a01150aff48fcb6fcd6472381652de04"
        elif host.IsAARCH64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-aarch64.sh"
          MD5SUM = "7e822f5622fa306c0aa42430ba884454"
      elif host.IsOsx:
        if host.IsX86_64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-MacOSX-x86_64.sh"
          MD5SUM = "5319de6536212892dd2da8b70d602ee1"
        elif host.IsAARCH64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-MacOSX-arm64.sh"
          MD5SUM = "24d985d2d380c51364d4793eb1840d29"
      ########################################

      _archive_path = wget.wget(urls=[url],
                     md5val=MD5SUM,
                     output_name="anaconda.sh")

      print(_archive_path)

      if _archive_path==None:
        assert(False)
      else:
        command.run(["rm","-rf",self._prefix])
        command.run(["chmod","ugo+x",_archive_path])
        command.run([_archive_path,"-b","-p",self._prefix])

        OK = self.launch(conda_cmd="config",
                           launch_args=["--system","--set", "env_prompt", '"({default_env})|"'])==0
        if OK:
          OK = self.launch(launch_args=["pip3","install","ork.build"])==0
          if OK:
            self._manifest_path.touch()
        return OK 

    ###############################################
    # launch subprocess in conda subspace
    ###############################################
    def launch(self,working_dir=None,
                    container=None,
                    conda_cmd="run",
                    do_log=False,
                    launch_args=[]):

      conda_cmdlist = [self.conda_executable,conda_cmd]
      if do_log:
        conda_cmdlist += ["--no-capture-output"]

      if container!=None:
        conda_cmdlist += ["--name",container]
      if len(launch_args)==0:
        assert(False)

      environ = self._gen_environment(container)

      conda_cmdlist += launch_args
      print(conda_cmdlist)
      os.environ["LD_LIBRARY_PATH"]=""
      return command.run(conda_cmdlist,working_dir=working_dir,environment=environ)

    ###############################################
    def _gen_sysprompt(self,container=None):
      return "🐍-conda" if (container==None) else "🐍-%s"%container
    ###############################################
    def _gen_environment(self,container=None):
      TEMP_PATH = path.temp()
      PYTHON_HOME = self._prefix
      if container!=None:
        PYTHON_HOME = self._prefix/"envs"/container

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
        "CONDA_PREFIX": self._prefix,
        "OBT_SUBSPACE": "conda" if (container==None) else container,
        "OBT_SUBSPACE_PROMPT": self._gen_sysprompt(container=container)
      }        
      return the_environ
    ###############################################
    def env(self,args=[],
                 working_dir=None,
                 container=None,
                 do_log=False):
      return self.launch(conda_cmd="env",
                         launch_args=args,
                         working_dir=working_dir,
                         container=container,
                         do_log=do_log)
    ###############################################
    def run(self,launch_args=[],
                 working_dir=None,
                 container=None,
                 do_log=False):
      return self.launch(conda_cmd="run",
                         launch_args=launch_args,
                         working_dir=working_dir,
                         container=container,
                         do_log=do_log)
    ###############################################
    # launch conda subspace shell
    ###############################################
    def shell(self,working_dir=None,container=None):

      conda_cmdlist = [self.conda_executable,"run","--no-capture-output"]

      TEMP_PATH = path.temp()
      PYTHON_HOME = self._prefix
      if container!=None:
        conda_cmdlist += ["--name",container]
        PYTHON_HOME = self._prefix/"envs"/container

      conda_cmdlist += ["bash"]
      
      print(conda_cmdlist)

      import obt._envutils 
      sub_name = os.environ["OBT_PROJECT_NAME"]
      sub_env = obt._envutils.EnvSetup(project_name=sub_name)

      override_sysprompt = "🐍-conda" if (container==None) else "🐍-%s"%container

      BASHRC = sub_env.genBashRc()
      BASHRC += "\n\n"
      BASHRC += "%s --stack\n"%(self._prefix/"bin"/"activate")

      fname = None

      rval = 0

      environ = self._gen_environment(container)

      import tempfile
      with tempfile.NamedTemporaryFile(dir=path.temp(),mode="w",delete=False) as tempf:
        fname = tempf.name
        tempf.write(BASHRC)
        tempf.close()
        print(fname)

        conda_cmdlist += ["--rcfile",fname, "-i"]



        rval = command.run(conda_cmdlist,working_dir=working_dir,environment=environ,do_log=True)

      return rval

    ###############################################
    def _command(self,args,conda_cmd="run"):
      return self.launch(args,conda_cmd=conda_cmd)
    ###############################################
    def _wipe(self):
      print( deco.yellow("Wiping Conda subspace") )
      command.run(["rm",self._manifest_path],do_log=True)
      command.run(["rm","-rf",self._prefix],do_log=True)
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "conda",
        "prefix": self._prefix,
      }
    ###############################################

