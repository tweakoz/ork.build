from ork import path, pathtools, command
from ork.buildtrace import buildTrace
import shutil, os

###############################################################################

def _install_over(what, directory,mode):
  #os.chmod(where, 777) #?? still can raise exception
  filename = os.path.split(what)[1]
  if not directory.exists():
    cmdlist = ["mkdir","-p",directory]
    command.run(cmdlist,do_log=True)
  cmdlist = ["install","-m",mode,what,directory/filename]
  command.run(cmdlist,do_log=True)
  #command.run(cmdlist,do_log=True)

###############################################################################

def rmdir(p,force=False):
  #####################################
  class _X:
    def __init__(self):
      pass
    def __call__(self):
      print({"rmdir":"path(%s)"%str(p)})
      pathtools.rmdir(p,force=force)
  #####################################
  return [_X()]

###############################################################################

def mkdir(p,
          clean=False,
          parents=False):
  #####################################
  class _X:
    def __init__(self):
      pass
    def __call__(self):
      print({"mkdir":"path(%s) clean(%d) parents(%d) "%(str(p),int(clean),int(parents))})
      pathtools.mkdir(p,
                      clean=clean,
                      parents=parents)
  #####################################
  return [_X()]

###############################################################################

def install_files(src_dir=None,
                  dst_dir=None,
                  patterns=None,
                  mode="0644"):
  assert(src_dir!=None)
  assert(dst_dir!=None)
  assert(patterns!=None)
  class _X:
    def __init__(self,patterns):
      if isinstance(patterns,str):
        patterns = [patterns]
      self.patterns = patterns
    def __call__(self):
      if False:
        print("##############################################")
        print( "copy_files: { " )
        print( "  src_dir: '%s'" % str(src_dir) )
        print( "  dst_dir: '%s'" % str(dst_dir) )
        print( "  patterns: '%s'" % str(self.patterns) )
        print( "  mode: '%s'" % mode )
        print( "} " )
        print("##############################################")
      for pattern in self.patterns:
        matched = pathtools.patglob(src_dir,pattern)
        for src_item in matched:
          orig_src = src_item
          s_path = os.path.split(src_item)
          dest_path = dst_dir/src_item
          dest_path = os.path.split(dest_path)
          #print("copy %s to %s"%(src_item,dest_path))
          _install_over(orig_src,path.Path(dest_path[0]),mode)
  return [_X(patterns)]

###############################################################################

def r_install_files(src_dir=None,
                    recursive_src_strip=None,
                    dst_dir=None,
                    patterns=None,
                    mode="0644"):
  assert(src_dir!=None)
  assert(dst_dir!=None)
  assert(patterns!=None)
  class _X:
    def __init__(self,patterns):
      if isinstance(patterns,str):
        patterns = [patterns]
      self.patterns = patterns
    def __call__(self):

      if False:
        print("##############################################")
        print( "r_install_files: { " )
        print( "  src_dir: '%s'" % str(src_dir) )
        print( "  recursive_src_strip: '%s'" % str(recursive_src_strip) )
        print( "  dst_dir: '%s'" % str(dst_dir) )
        print( "  patterns: '%s'" % self.patterns )
        print( "  mode: '%s'" % mode )
        print( "} " )
        print("##############################################")

      for pattern in self.patterns:
        matched = pathtools.recursive_patglob(src_dir,pattern)

        rss = str(recursive_src_strip)
        lenofrss = len(rss)

        for src_item in matched:
          orig_src = src_item
          if src_item.find(rss) >= 0:
            src_item = src_item[lenofrss+1:]
          dest_path = dst_dir/src_item
          dest_path = os.path.split(dest_path)
          if False:
            print("##############################################")
            print( "copy: { " )
            print( "  src: '%s'" % str(src_item) )
            print( "  dst: '%s'" % str(dest_path) )
            print( "} " )
          _install_over(orig_src,path.Path(dest_path[0]),mode)
  return [_X(patterns)]