#
#conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch -y
#git clone git@github.com:pytorch/examples.git
#cd examples/mnist
#pip install -r requirements.txt
#python main.py

#cd examples/vae
#pip install -r requirements.txt
#python main.py

from ork import dep, path, command, host, wget, pathtools
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
      self._name = "conda"
      self._prefix = path.subspace_root()/"conda"

    ###############################################
    @property 
    def conda_executable(self):
      return self._prefix/"bin"/"conda"

    ###############################################
    # build conda subspace
    ###############################################
    def build(self,build_args):
      ########################################
      if host.IsLinux:
        if host.IsX86_64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-MacOSX-x86_64.sh"
          MD5SUM = "5319de6536212892dd2da8b70d602ee1"
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
        command.run(["chmod","ugo+x",_archive_path])
        command.run([_archive_path,"-b","-p",self._prefix])

        self.launch(conda_cmd="config",
                    launch_args=["--system","--set", "env_prompt", '"({default_env})|"'
        ])

    ###############################################
    # launch subprocess in conda subspace
    ###############################################
    def launch(self,working_dir=None,
                    environment=None,
                    conda_cmd="run",
                    do_log=False,
                    launch_args=[]):
      conda_cmdlist = [self.conda_executable,conda_cmd]
      if do_log:
        conda_cmdlist += ["--no-capture-output"]

      if environment!=None:
        conda_cmdlist += ["--name",environment]
      if len(launch_args)==0:
        assert(False)
      environ = {
        "CONDA_PREFIX": self._prefix,
      }        
      conda_cmdlist += launch_args
      print(conda_cmdlist)
      command.run(conda_cmdlist,working_dir=working_dir,environment=environ)

    ###############################################
    def env(self,args=[],
                 working_dir=None,
                 environment=None,
                 do_log=False):
      self.launch(conda_cmd="env",
                  launch_args=args,
                  working_dir=working_dir,
                  environment=environment,
                  do_log=do_log)
    ###############################################
    def run(self,args=[],
                 working_dir=None,
                 environment=None,
                 do_log=False):
      self.launch(conda_cmd="run",
                  launch_args=args,
                  working_dir=working_dir,
                  environment=environment,
                  do_log=do_log)
    ###############################################
    # launch conda subspace shell
    ###############################################
    def shell(self,working_dir=None,environment=None):

      TEMP_PATH = path.temp()

      conda_cmdlist = [self.conda_executable,"run","--no-capture-output"]

      if environment!=None:
        conda_cmdlist += ["--name",environment]

      conda_cmdlist += ["bash"]
      
      print(conda_cmdlist)

      import _envutils 
      sub_name = os.environ["OBT_PROJECT_NAME"]+"/conda"
      sub_env = _envutils.EnvSetup(project_name=sub_name)

      BASHRC = sub_env.genBashRc()
      BASHRC += (path.stage()/".bashrc").read_text()
      BASHRC += "\n\n"
      BASHRC += "%s --stack\n"%(self._prefix/"bin"/"activate")

      fname = None
      with tempfile.NamedTemporaryFile(dir=path.temp(),mode="w",delete=False) as tempf:
        fname = tempf.name
        tempf.write(BASHRC)
        tempf.close()
        print(fname)

        conda_cmdlist += ["--rcfile",fname, "-i"]

        environ = {
          "CONDA_PREFIX": self._prefix,
          "OBT_SUBSPACE": "conda" if (environment==None) else environment
        }        

        command.run(conda_cmdlist,working_dir=working_dir,environment=environ)

      print(fname)
    ###############################################
    def _command(self,args,conda_cmd="run"):
      self.launch(args,conda_cmd=conda_cmd)
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "conda",
        "prefix": self._prefix,
      }
    ###############################################

