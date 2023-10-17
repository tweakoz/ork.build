###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, hashlib, glob
import fnmatch
from obt import buildtrace

###############################################################################

def posixpath(path):
    return '/'.join(os.path.normpath(path).split(os.sep))

###############################################################################

def patglob(path,pattern):
    path = str(path)
    l=[]
    if path[-1]!='/':
        path=path+'/'
    try:
        dirlist = os.listdir(path)
        for i in dirlist:
            ii=i
            i=path+i
            #print(i,os.path.isfile(i),pattern)
            if os.path.isfile(i):
                if fnmatch.fnmatch(os.path.basename(i),pattern):
                    #print("match %s"%i)
                    l.append(i)
    except:
        pass

    return l

###############################################################################

def recursive_patglob(path,pattern):
    path = str(path)
    l=[]
    if path[-1]!='/':
        path=path+'/'
    for i in recursive_glob_get_dirs(path):
        #print(path+i)
        l=l+recursive_patglob(path+i,pattern)
    try:
        dirlist = os.listdir(path)
        for i in dirlist:
            ii=i
            i=path+i
            #print(i,os.path.isfile(i),pattern)
            if os.path.isfile(i):
                if fnmatch.fnmatch(os.path.basename(i),pattern):
                    #print("match %s"%i)
                    l.append(i)
    except:
        pass

    return l

###############################################################################

def recursive_glob(path):
    l=[]
    if path[-1]!='/':
        path=path+'/'
    for i in recursive_glob_get_dirs(path):
        #print path+i
        l=l+recursive_glob(path+i)
    try:
        dirlist = os.listdir(path)
        for i in dirlist:
            ii=i
            i=path+i
            if os.path.isfile(i):
                #print i
                #if fnmatch.fnmatch(ii,pattern):
                #print "Matched %s" % (i)
                l.append(i)
    except:
        pass

    return l

###############################################################################

def recursive_glob_get_dirs(path):
    d=[]
    try:
        x = os.listdir(path)
        #print(x)
        for i in x:
          y = path+i
          #print(i,y)
          if os.path.isdir(y):
            d.append(os.path.basename(i))
    except:
        print("error")
        pass
    return d

############################
def md5_of_file(fname):
    fil = open(str(fname),"rb")
    data = fil.read()
    fil.close()
    md5obj = hashlib.md5()
    md5obj.update(data)
    return md5obj.hexdigest()

###############################################################################

def globber( folderbase, 
             wildcard="*", 
             subdirlist=None, 
             excludelist=[] ):
    globs = []
    filtered_globs = []
    if subdirlist==None:
        subdirlist = [ "." ]
    for s in subdirlist:
        str_glob = folderbase
        if s!=".":
             str_glob += s + '/'
        str_glob = str(str_glob)+"/"+wildcard
        print(str_glob)
        these_globs = glob.glob( str_glob )
        globs += these_globs
        #print "globbing %s" % ( str_glob )
    for s in globs:
        incfil = int(1)
        for t in excludelist:
            regex = re.compile( t )
            matchobj = re.search( t, s )
            if( matchobj ):
                #print "excluding " + s + " : (matches " + t + " )"
                incfil = int(0)
        if incfil == 1:
            filtered_globs += [ posixpath(s) ]
    #print filtered_globs
    return filtered_globs

###############################################################################
class EnumFileInfo(object):
   def __init__(self, path, size, md5):
      self.path = path
      self.size = size
      self.md5 = md5
   def __repr__(self):
        return "fileinfo[ path<%s> size<%d> md5<%s>]"%(self.path,self.size,self.md5)
###############################################################################
class EnumDirInfo(object):
    ############################################
    def __init__(self, folderbase,wildcard="*"):
        self.glob = recursive_patglob(folderbase, wildcard)
        self.contents_by_hash = dict()
        self.contents_by_path = dict()
        self.bytes_by_hash = dict()
        for item in self.glob:
            if(os.path.isfile(item)):
              h = md5_of_file(item)
              size = os.path.getsize(item)
              if h not in self.contents_by_hash:
                self.contents_by_hash[h] = []
              if h not in self.bytes_by_hash:
                self.bytes_by_hash[h] = 0
              self.bytes_by_hash[h] += size
            finfo = EnumFileInfo(item, size, h)
            self.contents_by_hash[h].append(finfo)
            self.contents_by_path[item] = finfo
    ############################################
    def numDuplicateBytes(self):
        numdupebytes = 0
        for hash in self.contents_by_hash.keys():
            file_list = self.contents_by_hash[hash]
            if len(file_list)>1:
              for item in file_list:
                numdupebytes += item.size
        return numdupebytes
    ############################################
    def numBytes(self):
        numbytes = 0
        for p in self.contents_by_path.keys():
            item = self.contents_by_path[p]
            numbytes += item.size
        return numbytes
    ############################################
    def dump(self):
        for p in self.contents_by_path:
            v = self.contents_by_path[p]
            print(v)
    ############################################
    def dump_duplicates(self):
        numdupebytes = 0
        for hash in self.contents_by_hash.keys():
            file_list = self.contents_by_hash[hash]
            if len(file_list)>1:
              #print(file_list)
              for item in file_list:
                numdupebytes += item.size
        print("numdupebytes<%d>"%numdupebytes)       
###############################################################################
def enumerateContents(folderbase, 
                      wildcard="*"):
    return EnumDirInfo(folderbase,wildcard)

###############################################################################

def mkdir(p,
          clean=False,
          parents=False):
  buildtrace.buildTrace({"op":"mkdir(%s)"%str(p),"clean":clean,"parents":parents})

  if clean:
    if p.exists():
      cmd_str = "chmod -R u+w %s"%str(p)
      print(cmd_str)
      os.system(cmd_str)
      cmd_str = "rm -rf %s"%str(p)
      print(cmd_str)
      os.system(cmd_str)
  if False==p.exists():
     p.mkdir(parents=parents)

###############################################################################
def rmdir(p,force=False):
  buildtrace.buildTrace({"op":"rmdir(%s)"%str(p)})
  if force:
    os.system("chmod -R u+wx %s"%p)
  os.system("rm -rf %s"%p)

###############################################################################

def ensureDirectoryExists(p):
  buildtrace.buildTrace({"op":"ensureDirExists(%s)"%str(p)})
  if False==p.exists():
     p.mkdir()

###############################################################################

def sizeOfDirectory(start_path):
  total_size = 0
  for dirpath, dirnames, filenames in os.walk(start_path):
    for f in filenames:
      fp = os.path.join(dirpath, f)
      total_size += os.path.getsize(fp)
  return total_size

###############################################################################

def chdir(p):
  buildtrace.buildTrace({"op":"chdir(%s)"%str(p)})
  os.chdir(str(p))

###############################################################################

def copyfile(file_from,file_dest,modeset=""):
  buildtrace.buildTrace({"op":"copyfile", "from": str(file_from), "dest": str(file_dest), "modeset": modeset})
  os.system("cp \"%s\" \"%s\"" % (str(file_from), str(file_dest)))
  if modeset!="":
    os.system("chmod %s %s"%(modeset,str(file_dest)))

def copydir(src_dir,dest_dir):
  rmdir(dest_dir)
  buildtrace.buildTrace({"op":"copydir", "from": str(src_dir), "dest": str(dest_dir)})
  os.system("cp -r %s %s"%(str(src_dir),str(dest_dir)))

def copyfiles(file_from,dest_dir,modeset=""):
  buildtrace.buildTrace({"op":"copyfiles", "from": str(file_from), "dest_dir": str(dest_dir), "modeset": modeset})
  os.system("cp -r \"%s\" \"%s/\"" % (str(file_from), str(dest_dir)))
  if modeset!="":
    os.system("chmod %s %s/*"%(modeset,str(dest_dir)))

