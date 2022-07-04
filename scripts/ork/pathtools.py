###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib
import fnmatch
from ork import buildtrace

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
        print(x)
        for i in x:
          y = path+i
          print(i,y)
          if os.path.isdir(y):
            d.append(os.path.basename(i))
    except:
        print("error")
        pass
    return d

###############################################################################

def globber( folderbase, wildcard, subdirlist, excludelist=[] ):
	globs = []
	filtered_globs = []
	for s in subdirlist:
		str_glob = folderbase
		if s!=".":
			 str_glob += s + '/'
		str_glob += wildcard
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

def mkdir(p,clean=False,parents=False):
  buildtrace.buildTrace({"op":"mkdir(%s)"%str(p),"clean":clean,"parents":parents})
  if clean:
  	if p.exists():
  	  os.system("rm -rf %s"%p)
  if False==p.exists():
     p.mkdir(parents=parents)

def rmdir(p):
  buildtrace.buildTrace({"op":"rmdir(%s)"%str(p)})
  os.system("rm -rf %s"%p)

###############################################################################

def ensureDirectoryExists(p):
  buildtrace.buildTrace({"op":"ensureDirExists(%s)"%str(p)})
  if False==p.exists():
     p.mkdir()

###############################################################################

def chdir(p):
  print(p)
  print(str(p))
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
