###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import glob, re, string, sys, os, shutil, fnmatch

###############################################################################

def builddir_replace( filelist, searchkey, replacekey ):
	a = [s.replace(searchkey,replacekey) for s in filelist]
	#print a
	return a

###############################################################################

def replace( file, searchkey, replacekey ):
	regex = re.compile( searchkey )
	str_file = str(file)
	str_rep = regex.sub( replacekey, string.join( str_file, '' ) )
	return posixpath(str_rep)

###############################################################################

def rmdirforce(basepath):
	if os.path.isdir(basepath):
		for root, dirs, files in os.walk(basepath, topdown=False):
			for name in files:
				os.remove(os.path.join(root, name))
			for name in dirs:
				os.rmdir(os.path.join(root, name))
		os.rmdir(basepath)


###############################################################################

def RunUnitTest(env,target,source):
	import subprocess
	app = str(source[0].abspath)
	if not subprocess.call(app):
		open(str(target[0]),'w').write("PASSED\n")

