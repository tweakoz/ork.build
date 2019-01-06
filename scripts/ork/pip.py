import ork.deco
from ork.command import Command

def install(name_or_list):
  if(isinstance(name_or_list,str)):
    Command(["pip3","install",modname]).exec()
  elif (isinstance(name_or_list,list)):
    for item in name_or_list:
      Command(["pip3","install",item]).exec()

