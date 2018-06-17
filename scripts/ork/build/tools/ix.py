###############################################################################
# Orkid SCONS Build System
# Copyright 2010, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import glob
import re
import string
import os
import sys
import ork.build.slnprj
import ork.build.localopts as localopts

from SCons.Script.SConscript import SConsEnvironment

print "Using Ix Build Env"

cxx_comp = localopts.CXX()
cxx_std = localopts.STD()
c_comp = localopts.CXX()

###############################################################################
# Python Module Export Declaration

__all__ = [ "DefaultBuildEnv" ]
__version__ = "1.0"

###############################################################################
# Basic Build Environment


USE_DEBUG_CXX = False

def DefaultBuildEnv( env, prj ):
	##
	DEFS = ' IX GCC '
	if USE_DEBUG_CXX:
		DEFS += ' _GLIBCXX_DEBUG '
	if prj.IsLinux:
		DEFS += "LINUX ORK_LINUX"
	CCFLG = ' '
	CXXFLG = ' '
	LIBS = "m rt pthread"
	LIBPATH = ' . '
	if USE_DEBUG_CXX:
		LIBPATH += ' /usr/lib/x86_64-linux-gnu/debug '
	LINK = ''
	##
	env.Replace( CXX = cxx_comp, CC = c_comp )
	env.Replace( LINK = cxx_comp )
	env.Replace( CPPDEFINES = string.split(DEFS) )
	env.Replace( CCFLAGS = string.split(CCFLG) )
	env.Replace( CXXFLAGS = string.split(CXXFLG) )
	env.Replace( CPPPATH  = [ '.' ] )
	env.Replace( LINKFLAGS=string.split(LINK) )
	env.Replace( LIBS=string.split(LIBS) )
	env.Replace( LIBPATH=string.split(LIBPATH) )

	CxFLG = '-ffast-math -fPIC -fno-common -fno-strict-aliasing -g -Wno-switch-enum -Wno-c++11-narrowing'
	prj.XCCFLG += CxFLG
	prj.XCXXFLG += CxFLG + " --std=%s -fexceptions " % cxx_std

	prj.CompilerType = 'gcc'

	prj.XLINK = '-v -g -Wl,-rpath,/projects/redux/stage/lib'


