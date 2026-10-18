###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, time
from pathlib import Path
import hashlib
import obt.path
from obt.command import Command
from obt.retry import retry_until_rc_zero

###############################################################################

def _md5(file_path):
  the_md5 = hashlib.md5()
  the_md5.update(file_path.read_bytes())
  return the_md5.hexdigest()

STALE_PART_SECONDS = 6*3600

def remove_stale_parts(output_path,max_age=STALE_PART_SECONDS):
  """A SIGKILLed download leaves <name>.part.<pid>; reap old ones."""
  cutoff = time.time()-max_age
  for item in output_path.parent.glob(output_path.name+".part.*"):
    try:
      if item.is_file() and item.stat().st_mtime < cutoff:
        item.unlink()
    except OSError:
      pass

###############################################################################

def check_hash(output_path,desired):
  if output_path.exists():
    actual = _md5(output_path)
    if actual==desired:
      return True
    else:
      print("path<%s>"%output_path)
      print("desired<%s>"%desired)
      print("actual<%s>"%actual)
  return False

###############################################################################
# caching download
###############################################################################

def wget(urls=[],
         output_name=None,
         md5val=None):

  assert(obt.path.downloads().exists())
  output_path = obt.path.downloads()/output_name
  remove_stale_parts(output_path)
  hash_ok = False
  if md5val!=None:
    hash_ok = check_hash(output_path,md5val)
    if hash_ok:
      return output_path

  if False==hash_ok:
    # Download to a per-process temp file beside the destination, then
    # atomically replace. The downloads cache is machine-shared, so
    # concurrent builds must never observe (or clobber) a partial file.
    tmp_path = output_path.parent/("%s.part.%d"%(output_path.name,os.getpid()))
    mismatches = []
    try:
      for url in urls:
        res = retry_until_rc_zero(
            lambda u=url: Command(["wget",
                                   "-O",
                                   tmp_path,
                                   #"--show-progress",
                                   u]).exec(),
            label="wget %s" % url,
        )

        if res==0:
          if md5val != None:
            if False==check_hash(tmp_path,md5val):
              mismatches.append((url,_md5(tmp_path)))
              tmp_path.unlink()
              continue # a mirror may still serve the pinned tarball
          os.replace(tmp_path,output_path)
          return output_path
    finally:
      if tmp_path.exists():
        tmp_path.unlink()

  if mismatches:
    print("wget<%s>: md5 mismatch on every url; expected<%s>"%(output_name,md5val))
    for url,actual in mismatches:
      print("  actual<%s> from<%s>"%(actual,url))
    print("  re-pin md5val in the dep module if upstream re-rolled the tarball")
  return None

################################################################################
# batch downloads
################################################################################
def batch_wget(fset):
  for k in fset.keys():
    v = fset[k]
    wget(urls=[k],output_name=v[0],md5val=v[1])
