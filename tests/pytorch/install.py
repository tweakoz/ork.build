#!/usr/bin/env python3

from obt import subspace, host, path, pathtools
from obt.path import Path 

import os 

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

#####################################
# install conda pytorch modules
#####################################

conda = subspace.requires("conda")

cmdlist = [
  "install",
  "pytorch", "torchvision",
  "tensorboard"
]

if host.IsLinux:
  cmdlist += ["cudatoolkit=11.3"]
elif host.IsOsx and host.IsX86_64:
  cmdlist += ["torchaudio"]

cmdlist += [ "-c", "pytorch", "-y" ]

conda.command(cmdlist)

#####################################
# cd to temp so that traingin data 
#   download does not pollute git repo
#####################################

pathtools.chdir(path.temp()) 

#####################################
# launch a training test..
#####################################

conda.launch([this_dir/"training.py"])
