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
    # NEVER os.chdir() here — process-global, races under the parallel
    # fetch pool. One worker's chdir into build_dest "leaks" into another
    # worker's tar/unzip, which then extracts into the wrong dep's tree
    # (seen in the wild: xz tarball extracted into $OBT_STAGE/builds/zstd/).
    # Pass working_dir= to Command instead — that's per-subprocess via cwd=.
    if( archive_type=="zip" ):
        Command(["unzip"]+arc_options+[arcpath], working_dir=build_dest).exec()
    elif archive_type=="tgz":
        Command(["tar","xvf",arcpath], working_dir=build_dest).exec()
    elif archive_type=="none":
        run(["cp",arcpath,build_dest/outname],do_log=True)
        pass
    else:
        print(arcpath)
        # tarfile.extractall takes an explicit path= — already safe under
        # parallel workers (no chdir involved). Left as-is.
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath
