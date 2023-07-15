from obt import pathtools
from obt.buildtrace import buildTrace
import shutil, os

###############################################################################

def _copy_over(what, where):
  #os.chmod(where, 777) #?? still can raise exception
  shutil.copy(what, where)

###############################################################################

def rmdir(p,force=False):
  #####################################
  class _X:
    def __init__(self):
      pass
    def __call__(self):
      print({"l_rmdir":"src_dir(%s)"%str(p)})
      pathtools.rmdir(p,force=force)
  #####################################
  return _X()

###############################################################################

def mkdir(p,
          clean=False,
          parents=False):
  #####################################
  class _X:
    def __init__(self):
      pass
    def __call__(self):
      print({"l_mkdir":"src_dir(%s)"%str(p)})
      pathtools.mkdir(p,
                      clean=clean,
                      parents=parents)
  #####################################
  return _X()

###############################################################################

def copy_files(src_dir=None,
               dst_dir=None,
               pattern=None,
               modeset=""):
  class _X:
    def __init__(self):
      pass
    def __call__(self):
      print({"l_copyfiles":"src_dir(%s)"%str(src_dir)})
      print(src_dir)            
      print(pattern)            
      print(dst_dir)            
      print(modeset)            
      matched = pathtools.patglob(src_dir,pattern)
      for src_item in matched:
        s_path = os.path.split(src_item)
        dest_path = dst_dir/s_path[1]
        print("copy %s to %s"%(src_item,dest_path))
        _copy_over(src_item,dest_path)
  return _X()
