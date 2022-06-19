import os, inspect, tarfile
from pathlib import Path
import importlib.util
import ork.path, ork.host
from ork.command import Command, run
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git, host

deco = Deco()

###############################################################################

def downloadAndExtract(urls,
                       outname,
                       archive_type,
                       md5val,
                       build_dest,
                       arc_options=[]):

  arcpath = wget( urls = urls,
                  output_name = outname,
                  md5val = md5val )


  if arcpath:
    if build_dest.exists():
      Command(["rm","-rf",build_dest]).exec()
    print("extracting<%s> to build_dest<%s>"%(deco.path(arcpath),deco.path(build_dest)))
    print(archive_type)
    build_dest.mkdir()
    if( archive_type=="zip" ):
        os.chdir(str(build_dest))
        Command(["unzip"]+arc_options+[arcpath]).exec()
    elif archive_type=="tgz":
        os.chdir(str(build_dest))
        Command(["tar","xvf",arcpath]).exec()
    else:
        print(arcpath)
        #assert(tarfile.is_tarfile(str(arcpath)))
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath
