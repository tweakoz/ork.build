#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, string, re
import obt.path
import obt.dep
from obt.path import *
import obt.deco
deco = obt.deco.Deco()

#################################################################################

def find(word, case_insensitive=False, regex=False, whole_word=False, invert_match=False):
 """
 Create a finder function with specified search options.
 """
 # Prepare the search pattern
 if regex:
  if case_insensitive:
   pattern = re.compile(word, re.IGNORECASE)
  else:
   pattern = re.compile(word)
 elif whole_word:
  # Add word boundaries for whole word matching
  word_pattern = r'\b' + re.escape(word) + r'\b'
  if case_insensitive:
   pattern = re.compile(word_pattern, re.IGNORECASE)
  else:
   pattern = re.compile(word_pattern)
 elif case_insensitive:
  # Simple case-insensitive substring search
  word_lower = word.lower()
  pattern = None
 else:
  # Default: simple substring search
  pattern = None
 
 def _find(path):
  if os.path.exists(str(path)):
    with open(path, "rb") as fp:
     for n, line in enumerate(fp):
      try:
        line_as_str = line.decode("utf-8")
        matched = False
        
        if pattern:  # Regex or whole-word search
          matched = bool(pattern.search(line_as_str))
        elif case_insensitive:  # Case-insensitive substring
          matched = word_lower in line_as_str.lower()
        else:  # Simple substring
          matched = word in line_as_str
        
        # Apply invert-match if requested
        if invert_match:
          matched = not matched
        
        if matched:
          yield n+1, line_as_str
      except Exception:
        pass
 return _find

def find_multiple_and(patterns, case_insensitive=False, regex=True, whole_word=False, invert_match=False):
 """
 Create a finder function that matches ALL patterns (AND logic).
 Used when multiple -r options are provided.
 """
 # Compile all patterns
 compiled_patterns = []
 for pattern_str in patterns:
  if case_insensitive:
   compiled_patterns.append(re.compile(pattern_str, re.IGNORECASE))
  else:
   compiled_patterns.append(re.compile(pattern_str))
 
 def _find(path):
  if os.path.exists(str(path)):
    with open(path, "rb") as fp:
     for n, line in enumerate(fp):
      try:
        line_as_str = line.decode("utf-8")
        
        # Check if ALL patterns match
        all_matched = True
        for pattern in compiled_patterns:
          if not pattern.search(line_as_str):
            all_matched = False
            break
        
        # Apply invert-match if requested
        if invert_match:
          all_matched = not all_matched
        
        if all_matched:
          yield n+1, line_as_str
      except Exception:
        pass
 return _find

#################################################################################

class result:
 def __init__(self,path,lineno,text):
  self.path = path
  self.lineno = lineno
  self.text = text

#################################################################################

default_ext_set = set(os.environ["OBT_SEARCH_EXTLIST"].split(":"))

#################################################################################

ignore_folder_keys = set(["/obj/", "/pluginobj/","/.build/"])

#################################################################################

def search_at_root(word, root, ignore_set=ignore_folder_keys, ext_set=None, 
                  case_insensitive=False, regex=False, whole_word=False, 
                  invert_match=False, files_only=False):
 if ext_set is None:
  ext_set = default_ext_set
 finder = find(word, case_insensitive, regex, whole_word, invert_match)
 results = list()
 found_files = set()  # Track files with matches for files_only mode
 
 for root, dirs, files in os.walk(root):
  for f in files:
   path = os.path.join(root, f)
   spl = os.path.splitext(path)
   ext = spl[1]
   ignore = False
   for item in ignore_set:
       if (spl[0].find(item)!=-1):
           ignore = True
   if not ignore:
    if (finder!=None) and ext in ext_set:
     if files_only:
      # For files_only mode, just check if file has any match
      for line_number, line in finder(path):
       found_files.add(path)
       break  # Only need to find one match per file
     else:
      # Normal mode: collect all matching lines
      for line_number, line in finder(path):
       line = line.replace("\n","")
       res = result(path,line_number,line)
       results.append(res)
 
 # Convert found_files to results for files_only mode
 if files_only:
  for path in sorted(found_files):
   res = result(path, 0, "")  # Line number 0 indicates file-only result
   results.append(res)
 
 return results

#################################################################################

def search_at_root_multiple_and(patterns, root, ignore_set=ignore_folder_keys, ext_set=None,
                               case_insensitive=False, invert_match=False, files_only=False):
 """
 Search for lines matching ALL patterns (AND logic).
 Used when multiple -r options are provided.
 """
 if ext_set is None:
  ext_set = default_ext_set
 finder = find_multiple_and(patterns, case_insensitive, True, False, invert_match)
 results = list()
 found_files = set()  # Track files with matches for files_only mode
 
 for root, dirs, files in os.walk(root):
  for f in files:
   path = os.path.join(root, f)
   spl = os.path.splitext(path)
   ext = spl[1]
   ignore = False
   for item in ignore_set:
       if (spl[0].find(item)!=-1):
           ignore = True
   if not ignore:
    if (finder!=None) and ext in ext_set:
     if files_only:
      # For files_only mode, just check if file has any match
      for line_number, line in finder(path):
       found_files.add(path)
       break  # Only need to find one match per file
     else:
      # Normal mode: collect all matching lines
      for line_number, line in finder(path):
       line = line.replace("\n","")
       res = result(path,line_number,line)
       results.append(res)
 
 # Convert found_files to results for files_only mode
 if files_only:
  for path in sorted(found_files):
   res = result(path, 0, "")  # Line number 0 indicates file-only result
   results.append(res)
 
 return results

#################################################################################

p = os.environ["OBT_ROOT"]
pthspec = p.split(":")

#################################################################################

if "OBT_SEARCH_PATH" in os.environ:
  p = os.environ["OBT_SEARCH_PATH"]
  pthspec += p.split(":")

#################################################################################

#print(pthspec)
default_pathlist = []
for p in pthspec:
  default_pathlist += [Path(p)]

#################################################################################

def execute(word, path_list=default_pathlist, ext_set=None):
  for path in path_list:
   results = search_at_root(word, str(path), ext_set=ext_set)
   have_results = len(results)!=0
   if have_results:
    print("/////////////////////////////////////////////////////////////")
    print("// path : %s" % path)
    print("/////////")
    root = str(obt.path.project_list())+"/"
    for item in results:
      pathstr = str(item.path)
      pathstr = pathstr.replace(str(root),"")
      # Use formatColumns for proper alignment
      column_configs = [
          (72, 'left'),   # Path column, left-aligned
          (8, 'right'),   # Line number column, right-aligned
          (None, 'left')  # Content column, no padding
      ]
      column_texts = [
          deco.path(pathstr),
          deco.yellow(str(item.lineno)),
          "  " + deco.val(item.text.strip())
      ]
      print(deco.formatColumns(column_configs, column_texts))

#################################################################################

def execute_at(word_list, path_list, remove_root=None, ext_set=None,
              case_insensitive=False, regex=False, whole_word=False,
              invert_match=False, files_only=False,
              before_context=0, after_context=0,
              multiple_regex_and=False):
  """
  Enhanced execute_at with support for all search options and aligned output.
  """
  # Use the new display function that collects results first
  from obt.search_display import collect_and_display_results
  
  collect_and_display_results(word_list, path_list, remove_root, ext_set,
                             case_insensitive, regex, whole_word,
                             invert_match, files_only,
                             before_context, after_context,
                             multiple_regex_and)
  return
  
  # OLD CODE BELOW (keeping for reference but unreachable)
  from obt.search_v2 import find_with_context
  
  for path in path_list:
   print("/////////////////////////////////////////////////////////////")
   print("// searching path : %s" % path)
   print("/////////")
   
   for word in word_list:
     # If using context, use the new context-aware search
     if before_context > 0 or after_context > 0:
       found_files = set()
       global_first_match = True  # Track if this is the very first match across all files
       for root, dirs, files in os.walk(str(path)):
         for f in files:
           filepath = os.path.join(root, f)
           spl = os.path.splitext(filepath)
           ext = spl[1]
           
           # Check if should ignore
           ignore = False
           for item in ignore_folder_keys:
             if item in spl[0]:
               ignore = True
               break
           
           if ignore or (ext_set and ext not in ext_set):
             continue
           
           for context_result in find_with_context(word, filepath, 
                                                  case_insensitive, regex, 
                                                  whole_word, invert_match,
                                                  before_context, after_context):
             
             # Print delimiter before match group (except for the very first match)
             if not global_first_match:
               print()  # Blank line delimiter between match groups
             global_first_match = False
             
             for line_num, line_text, is_match in context_result:
               pathstr = str(filepath)
               if remove_root:
                 r_root = str(remove_root) + "/"
                 pathstr = pathstr.replace(r_root, "")
               
               deco_path = "%-*s" % (72, deco.path(pathstr))
               
               if is_match:
                 # Highlight matching lines with better spacing
                 deco_lino = " %s " % (deco.yellow(line_num))
                 deco_lino = "%-*s" % (8, deco_lino)
                 deco_text = deco.val(line_text.strip())
               else:
                 # Context lines - use dimmer version of val color (not path color)
                 deco_lino = " %s " % (deco.cyan(str(line_num)))
                 deco_lino = "%-*s" % (8, deco_lino)
                 deco_text = deco.inf(line_text.strip())  # inf is typically dimmer
               
               print("%s %s %s" % (deco_path, deco_lino, deco_text))
     else:
       # Use the original search method
       results = search_at_root(word, str(path), ext_set=ext_set,
                               case_insensitive=case_insensitive,
                               regex=regex, whole_word=whole_word,
                               invert_match=invert_match,
                               files_only=files_only)
       have_results = len(results)!=0
       if have_results:
         for item in results:
           pathstr = str(item.path)
           if remove_root!=None:
             r_root = str(remove_root)+"/"
             pathstr = pathstr.replace(str(r_root),"")
           
           if files_only and item.lineno == 0:
             # Files-only mode: just print the path
             print(deco.path(pathstr))
           else:
             # Normal mode: print path, line number, and text with better spacing
             deco_path = "%-*s"%(72,deco.path(pathstr))
             deco_lino = " %s "%(deco.yellow(item.lineno))
             deco_lino = "%-*s"%(8,deco_lino)
             deco_text = deco.val(item.text.strip())
             print("%s %s %s" % (deco_path, deco_lino, deco_text))


#################################################################################

def visit(word, visitor, path_list=default_pathlist, ext_set=None):
  for path in path_list:
   results = search_at_root(word, str(path), ext_set=ext_set)
   have_results = len(results)!=0
   print(have_results)
   if have_results:
     visitor.onPath(path)
     for item in results:
       visitor.onItem(item)
