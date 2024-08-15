#!/usr/bin/env python3

import sys, os 
from obt import path, pathtools

def walk(directory: path.Path) -> list:
  data_files = []
  for root, dirs, files in os.walk(str(directory)):
    delta = root.replace(str(directory), '').strip('/')
    for filename in files:
      if not (filename.endswith('.pyc') or '.egg-info' in root or '__pycache__' in root):
        filepath = os.path.join(root, filename)
        #dest_dir = os.path.join('obt', root)
        data_files.append((filename, delta))
  return data_files

################################################

this_dir =path.Path(os.path.dirname(os.path.realpath(__file__)))
obt_data_dir = path.obt_data_base()
obt_root_dir = (path.Path(os.environ['OBT_ROOT'])/"..").norm

################################################

module_files = walk(this_dir/'modules')
for item in module_files:
  src = this_dir/"modules"/item[1]/item[0]
  dest = obt_data_dir/"modules"/item[1]/item[0]
  pathtools.copyfile(src,dest)

################################################

bin_pub_files = walk(this_dir/"bin_pub")
for item in bin_pub_files:
  src = this_dir/"bin_pub"/item[1]/item[0]
  dest = obt_root_dir/"bin"/item[1]/item[0]
  #print(src,dest)
  pathtools.copyfile(src,dest)

################################################

bin_priv_files = walk(this_dir/"bin_priv")
for item in bin_priv_files:
  src = this_dir/"bin_priv"/item[1]/item[0]
  dest = obt_data_dir/"bin_priv"/item[1]/item[0]
  #print(src,dest)
  pathtools.copyfile(src,dest)

################################################

obt_scripts_dir = (path.Path(path.__get_obt_root())/"..").norm
scripts_files = walk(this_dir/"scripts")
for item in scripts_files:
  src = this_dir/"scripts"/item[1]/item[0]
  dest_dir = obt_scripts_dir/item[1]
  pathtools.mkdir(dest_dir,parents=True)
  dest = dest_dir/item[0]
  #print(src,dest)
  pathtools.copyfile(src,dest)
