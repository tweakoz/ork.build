import ork.deco
from ork.path import Path
from ork.command import Command

def install(name_or_list):
  python_prefix_cmd = ["python3-config","--prefix"]
  python_prefix = Command(python_prefix_cmd).capture().replace("\n","")
  python_prefix = Path(python_prefix)
  pip_executable = python_prefix/"bin"/"pip"
  rval = 0
  if(isinstance(name_or_list,str)):
    r = Command([pip_executable,"install",name_or_list]).exec()
    rval = r
  elif (isinstance(name_or_list,list)):
    for item in name_or_list:
      if rval==0:
        r = Command([pip_executable,"install",item]).exec()
        rval = r

  return rval
