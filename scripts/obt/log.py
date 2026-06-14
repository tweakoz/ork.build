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


def banner(text):
  if "OBT_NONDEV" in os.environ:   # quiet in non-dev ork.shell; shown in --dev
    return
  bar = "#"*92
  output(deco.orange(bar))
  output(deco.orange(text))
  output(deco.orange(bar))

def sdk_announce(string):
  if "OBT_NONDEV" in os.environ:   # quiet in non-dev ork.shell; shown in --dev
    return
  marker(string)
