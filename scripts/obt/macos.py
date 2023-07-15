#!/usr/bin/env python3
###############################################################################
import sys
from obt import host, path
from obt.command import capture
from obt.command import Deco
deco = Deco()
###############################################################################
def find_replace(inpstring, dictionary):
  print(dictionary)
  for item in inpstring:
    if item in dictionary.keys():
      print("replacing item<%s>"%item)
      inpstring = inpstring.replace(item, dictionary[item])
  return inpstring

###############################################################################
def macho_enumerate_dylibs(mach_o_path):
  assert (host.IsOsx)
  loadlines = capture(["otool","-l",mach_o_path],do_log=False).splitlines()
  cmdindex = 0
  cmd = None
  name = None
  state = 0
  dylib_paths = list()
  for line in loadlines:
    tokens = line.split(" ")
    tokens = [i for i in tokens if i]
    if state==0:
      if tokens[0]=="Load" and tokens[1]=="command":
        cmdindex = int(tokens[2])
        state = 1
    elif state==1:
      if tokens[0]=="cmd" and tokens[1]=="LC_LOAD_DYLIB":
        cmd = "LC_LOAD_DYLIB"
        state = 2
    elif state==2:
      if tokens[0] == "name":
        dylib_paths += [tokens[1]]
        state=0
    else:
      assert(False)
  return dylib_paths
###############################################################################
def macho_replace_loadpaths(mach_o_path,search,replace):
  assert (host.IsOsx)
  str_search = str(search)
  str_replace = str(replace)
  dylib_paths = macho_enumerate_dylibs(mach_o_path)
  for inpitem in dylib_paths:
    outitem = inpitem.replace(str_search, str_replace)
    #print("mach_o_path: " + str(mach_o_path) + " inp: " + inpitem + " search: " + str_search + " replace: " + str_replace)
    if outitem!=inpitem:
      capture(["install_name_tool","-change",inpitem,outitem,mach_o_path],do_log=False)
###############################################################################
def macho_change_id(mach_o_path,id_str):
  assert (host.IsOsx)
  capture(["install_name_tool","-id",'%s'%id_str,mach_o_path],do_log=False)
###############################################################################
def macho_get_id(mach_o_path):
  assert (host.IsOsx)
  return capture(["otool","-D",mach_o_path],do_log=False)
##############################################################################
def macho_dump(mach_o_path):
  print(deco.val("/////////////////////////////////////////////////////////"))
  print(deco.val("MachO Dump: ") + deco.val(mach_o_path))
  print(deco.val("/////////////////////////////////////////////////////////"))
  dylib_paths = macho_enumerate_dylibs(mach_o_path)
  for item in dylib_paths:
    print(deco.val("dylib: ")+deco.path(item))
  print(deco.val("/////////////////////////////////////////////////////////"))
