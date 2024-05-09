#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import sys, argparse, multiprocessing
from obt import exeinfo, deco, path
deco = deco.Deco()

###########################################

parser = argparse.ArgumentParser(description='obt.exedump')
parser.add_argument('--exe', metavar="exe", help='executable to dump' )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

stage = str(path.stage())
project = str(path.project_root())

bin_none = []
bin_prj = []
bin_stage = []
bin_sys = []

if "exe" in args and args["exe"] != None:
  libs = exeinfo.getLinkedLibraries(args["exe"])
  for key in libs.keys():

    val = libs[key]
    val_color = deco.white

    outstr = "%-50s"%deco.cyan(key)
    outstr += " : "

    if (val!=None) and (stage in val):
       val = val.replace(stage,"<STAGE>")
       outstr += "%-60s"% deco.yellow(val)
       bin_stage += [outstr]
    elif (val!=None) and (project in val):
       val = val.replace(project,"<PRJ>")
       outstr += "%-60s"% deco.orange(val)
       bin_prj += [outstr]
    elif val==None:
       outstr += "%-60s"% deco.magenta(val)
       bin_none += [outstr]
    else:
       outstr += "%-60s"% deco.white(val)
       bin_sys += [outstr]
       
for item in bin_none:
   print(item)
for item in bin_sys:
   print(item)
for item in bin_stage:
   print(item)
for item in bin_prj:
   print(item)



