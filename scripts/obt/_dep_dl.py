import os, inspect, tarfile
from pathlib import Path
import importlib.util
import obt.path, obt.host
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, cmake, make, path, git, host

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
    elif archive_type=="none":
        os.chdir(str(build_dest))
        run(["cp",arcpath,build_dest/outname],do_log=True)
        pass
    else:
        print(arcpath)
        #assert(tarfile.is_tarfile(str(arcpath)))
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath
