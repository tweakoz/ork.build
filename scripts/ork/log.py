import os

def log(x):
    if not "OBT_QUIET" in os.environ:
      print(x)
