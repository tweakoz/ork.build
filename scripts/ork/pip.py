import ork.deco
from ork.path import Path
from ork.command import Command

def _command(name_or_list,cmd):
  python_prefix_cmd = ["python3-config","--prefix"]
  python_prefix = Command(python_prefix_cmd).capture().replace("\n","")
  python_prefix = Path(python_prefix)
  pip_executable = python_prefix/"bin"/"pip"
  pip_executable = python_prefix/"bin"/"pip3"
  ## try pip3 first
  if False==pip_executable.exists():
      ## if there is no pip3, hopefully the pip pointed to by the
      ##  above python3-config is a python3 pip
      pip_executable = python_prefix/"bin"/"pip"
  rval = 0
  if(isinstance(name_or_list,str)):
    r = Command([pip_executable,cmd,name_or_list]).exec()
    rval = r
  elif (isinstance(name_or_list,list)):
    for item in name_or_list:
      if rval==0:
        r = Command([pip_executable,cmd,item]).exec()
        rval = r

  return rval

def install(name_or_list):
  return _command(name_or_list,"install")

def uninstall(name_or_list):
  return _command(name_or_list,"uninstall")
