#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string
import obt._globals
import obt.docker
from obt import dep, path
from obt.deco import Deco
deco = Deco()

def print_item(key,val):
 dstr = deco.inf(dockerid)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

###############################################################################

parser = argparse.ArgumentParser(description='obt.build docker launcher')
parser.add_argument('dockermodulename', metavar='D', type=str, help='a docker module to launch')
parser.add_argument('--env', nargs='*', action='append', type=str)
parser.add_argument('--mount', nargs='*', action='append', type=str)
parser.add_argument('--mapssh', action='store_true')

args, unknownargs = parser.parse_known_args()

_args = vars(args)

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

dockermodulename = _args["dockermodulename"]

obt._globals.setOption("dockermodulename",dockermodulename)

####################################
# parse environment arguments
####################################

environ=None
if ("env" in _args) and (_args["env"]!=None):
  environ=dict()
  _env = _args["env"]
  for item in _env:
    ev = item[0]
    kv = ev.split("=")
    environ[kv[0]]=kv[1]

####################################
# parse environment arguments
####################################

mounts=list()
if ("mount" in _args) and (_args["mount"]!=None):
  _mounts = _args["mount"]
  for item in _mounts:
    ev = item[0]
    mounts += [ev]

####################################
# map ssh ?
####################################

if ("mapssh" in _args) and (_args["mapssh"]==True):
  mounts += ["type=bind,source=%s,target=%s"%((os.environ["HOME"]+"/.ssh"),mapssh)]

####################################
# invoke on docker module
####################################

dockermodule = obt.docker.descriptor(dockermodulename)

if len(mounts)==0:
  mounts = None

if unknownargs==None:
  unknownargs = []
dockermodule.launch(unknownargs,environment=environ,mounts=mounts)

sys.exit(0)