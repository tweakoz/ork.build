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
    # build conda subspace
    ###############################################
    def build(self,build_args):
      ########################################
      if host.IsLinux:
        url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh"
        MD5SUM = "a01150aff48fcb6fcd6472381652de04"
      elif host.IsOsx:
        if host.IsX86_64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-MacOSX-x86_64.sh"
          MD5SUM = "5319de6536212892dd2da8b70d602ee1"
        elif host.IsAARCH64:
          url = "https://repo.anaconda.com/archive/Anaconda3-2022.05-MacOSX-arm64.sh"
          MD5SUM = "c35c8bdbeeda5e5ffa5b79d1f5ee8082"
      ########################################

      _archive_path = wget.wget(urls=[url],
                     md5val=MD5SUM,
                     output_name="anaconda.sh")

      print(_archive_path)

      if _archive_path!=None:
        command.run(["chmod","ugo+x",_archive_path])
        command.run([_archive_path,"-b","-p",self._prefix])

      self.launch([
        "conda", "config", "--system",
        "--set", "env_prompt", '"({default_env})|"'
      ])
        #

    ###############################################
    # launch docker container
    #  print out connection info
    ###############################################
    def launch(self,launch_args):


      if len(launch_args)==0:
        decostr = deco.yellow('Entering Conda Subspace')
        decostr += deco.white(' (type exit to pop to parent OBT shell)')
      else:
        decostr = deco.yellow('Running Command %s In Conda Subspace'%deco.white(launch_args))

      conda = self._prefix/"bin"/"conda"
      conda_cmd = "$(command %s 'shell.bash' 'hook' 2> /dev/null)" % conda

      BASHRC = ""
      BASHRC += (path.stage()/".bashrc").read_text()
      BASHRC += "\n\n"
      BASHRC += 'eval "%s"\n' % conda_cmd
      #BASHRC += "%s --stack\n"%(self._prefix/"bin"/"activate")
      BASHRC += "echo '%s'\n"%decostr

      fname = None
      with tempfile.NamedTemporaryFile(dir=path.temp(),mode="w",delete=False) as tempf:
        fname = tempf.name
        tempf.write(BASHRC)
        tempf.close()

      #command.run(["chmod","u+x",fname])

      if len(launch_args)>0:
        largs = " ".join(command.procargs(launch_args))
        cmdlist = ["bash", "--rcfile", fname, "-ci", largs]
      else:
        cmdlist = ["bash", "--rcfile", fname,"-i"]


      command.run(cmdlist)

    ###############################################
    def command(self,args):
      self.launch(["conda"]+args)
    ###############################################
    # information dictionary
    ###############################################
    def info(self):
      return {
        "name": "conda",
      }
    ###############################################

