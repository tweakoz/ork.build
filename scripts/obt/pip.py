import obt.deco
from obt import path, dep
from obt.command import Command

def _command(name_or_list,cmd):
  #Command().exec()
  #pip_executable = path.stage()/"bin"/"pip3"
  PYTHON = dep.instance("python")
  python_executable = PYTHON.executable
  cmd_prefix = [python_executable,"-m","pip",cmd]

  rval = 0
  if(isinstance(name_or_list,str)):
    r = Command(cmd_prefix+[name_or_list]).exec()
    rval = r
  elif (isinstance(name_or_list,list)):
    r = Command(cmd_prefix+name_or_list).exec()
    rval = r

  return rval

def install(name_or_list):
  return _command(name_or_list,"install")

def uninstall(name_or_list):
  return _command(name_or_list,"uninstall")
