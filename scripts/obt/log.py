import os
from obt.deco import Deco

global deco

deco = Deco()

def output(x):
    if not "OBT_QUIET" in os.environ:
      print(x)

def rgb(r,g,b,string):
    if not "OBT_QUIET" in os.environ:
      print(deco.rgbstr(r,g,b,string))

def marker(string):
  output(deco.bright(string))
