#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string
from pathlib import Path
import ork.deco
deco = ork.deco.Deco()

#################################################################################

def find(word):
 def _find(path):
  with open(path, "rb") as fp:
   for n, line in enumerate(fp):
    #print(word)
    #print(line)
    line_as_str = line.decode("utf-8") 
    if word in line_as_str:
     yield n+1, line_as_str
 return _find

#################################################################################

class result:
 def __init__(self,path,lineno,text):
  self.path = path
  self.lineno = lineno
  self.text = text

#################################################################################

def search_at_root(word, root):
 finder = find(word)
 results = list()
 for root, dirs, files in os.walk(root):
  for f in files:
   path = os.path.join(root, f)
   spl = os.path.splitext(path)
   ext = spl[1]
   not_obj = (spl[0].find("/obj/")==-1) and (spl[0].find("/pluginobj/")==-1)
   #print spl[0], fobj
   if not_obj:
    if ext==".c" or ext==".cpp" or ext==".cc" or ext==".h" or ext==".hpp" or ext==".inl" or ext==".qml" or ext==".m" or ext==".mm" or ext==".py":
     for line_number, line in finder(path):
      line = line.replace("\n","")
      res = result(path,line_number,line)
      results.append(res)
 return results  

#################################################################################

if "ORK_FIND_PATH" in os.environ:
  pathspl = [Path(os.environ["ORK_FIND_PATH"])]
else:
  pathspl = [Path(os.environ["OBT_ROOT"])]

#################################################################################

print(pathspl)
pathlist = ""
for p in pathspl:
  pathlist += "%s " % (p)

pathlist = pathlist.split()

#################################################################################

def search(word):
  for path in pathlist:
   results = search_at_root(word,str(path))
   have_results = len(results)!=0
   if have_results:
    print("/////////////////////////////////////////////////////////////")
    print("// path : %s" % path)
    print("/////////")
    for item in results:
      deco_path = "%-*s"%(60,deco.path(item.path))
      deco_lino = "%s %s"%(deco.magenta("Line"),deco.yellow(item.lineno))
      deco_lino = "%-*s"%(32,deco_lino)
      deco_text = deco.val(item.text)
      print("%s%s %s" % (deco_path, deco_lino, deco_text))

#################################################################################

if __name__ == "__main__":
 if not len(sys.argv) == 2:
  print("usage: word")
  sys.exit(1)
 word = sys.argv[1]
 search(word)
