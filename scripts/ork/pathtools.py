###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib
import fnmatch

###############################################################################

def posixpath(path):
	return '/'.join(os.path.normpath(path).split(os.sep))

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
		for i in os.listdir(path):
			if os.path.isdir(path+i):
				d.append(os.path.basename(i))
	except:pass
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
