###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, shutil, git
import obt.path
from yarl import URL
from pathlib import PosixPath
from obt.wget import wget
from obt.deco import Deco
from obt.command import run
from obt.retry import retry_until_rc_zero

deco = Deco()

###############################################################################
# Checkout and/or update to a specific branch
#  TODO - handle local changes and other exceptions correctly
###############################################################################

def checkout_update(dest_path,rev,origin="origin"):
    # working_dir threaded through; no os.chdir (process-global, racy).
    retc = run(["git","checkout",rev], working_dir=dest_path, do_log=True)
    retc = run(["git","pull",origin, rev], working_dir=dest_path, do_log=True)
    return (0 == retc)

###############################################################################

def Clone(url,
          dest,
          rev="master",
          recursive=False,
          cache=True,
          shallow=False):

  cwd = os.getcwd()
  rval = False
  retc = 0

  dest_path = PosixPath(dest)
  dest_name = dest_path.name
  cache_dest = obt.path.gitcache()/dest_name

  ##############################################################################

  def _checkoutrevandupdate():
    nonlocal retc
    nonlocal rev
    nonlocal dest_path
    nonlocal recursive
    OK = (0 == retc)
    # working_dir threaded through; no os.chdir. The previous version did
    # `os.chdir(dest_path)` then `run([...])` which depended on the parent
    # process's cwd staying put — racy under the parallel pipeline. The
    # symptom was `git submodule update` failing with "not a git repository"
    # because another worker had chdir'd elsewhere between our two commands.
    if OK:
      retc = run(["git","checkout",rev], working_dir=dest_path, do_log=True)
      OK = (0 == retc)
      if OK and recursive:
        retc = run(["git","submodule","update","--init","--recursive"],
                   working_dir=dest_path, do_log=True)
        OK = (0 == retc)
    return OK

  ##############################################################################
  if recursive and (cache==False):
  ##############################################################################

    print("Cloning1 (recursive) URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest_path)))
    def _cleanup_dest():
      if dest_path.exists():
        shutil.rmtree(str(dest_path))
    retc = retry_until_rc_zero(
        lambda: run(["git",
                     "clone",
                     "-n",
                     str(url),
                     str(dest_path),
                     "--recursive"]),
        label="git clone --recursive %s" % url,
        cleanup=_cleanup_dest,
    )

    return _checkoutrevandupdate()

  ##############################################################################
  elif cache:
  ##############################################################################

    destpar = (dest_path/"..").resolve()
    print(destpar)
    if False==cache_dest.exists():
      print("Mirroring URL<%s> to dest<%s>"%(deco.path(url),deco.path(cache_dest)))
      def _cleanup_cache_dest():
        if cache_dest.exists():
          shutil.rmtree(str(cache_dest))
      retc = retry_until_rc_zero(
          lambda: run(["git",
                       "clone",
                       str(url),
                       str(cache_dest),
                       "--mirror"]),
          label="git mirror %s" % url,
          cleanup=_cleanup_cache_dest,
      )
    print("Cloning2 (from gitcache<%s>) to dest<%s> retc<%s>"%(deco.path(cache_dest),deco.path(dest),retc))
    if dest_path.exists():
      shutil.rmtree(str(dest_path))
    if 0 == retc:
      def _cleanup_dest_ref():
        if dest_path.exists():
          shutil.rmtree(str(dest_path))
      retc = retry_until_rc_zero(
          lambda: run(["git",
                       "clone",
                       "--reference",
                       str(cache_dest),
                       str(url),
                       str(dest_path)]),
          label="git clone --reference %s" % url,
          cleanup=_cleanup_dest_ref,
      )
      if 0 == retc:
        return _checkoutrevandupdate()

  ##############################################################################
  else:
  ##############################################################################

    print("Cloning3 URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest_path)))
    print("shallow<%d>"%shallow)
    if shallow:
      # shallow clone of specific rev. working_dir on each Command — no chdir.
      if dest_path.exists():
        shutil.rmtree(str(dest_path))
      dest_path.mkdir(parents=True, exist_ok=True)
      ####################
      retc = run(["git","init"], working_dir=dest_path, do_log=True)
      ####################
      if retc==0:
        retc = run(["git","remote","add","origin",url],
                   working_dir=dest_path, do_log=True)
      ####################
      if retc==0:
        retc = retry_until_rc_zero(
            lambda: run(["git","fetch","--depth","1","origin",rev],
                        working_dir=dest_path, do_log=True),
            label="git fetch --depth 1 %s" % rev,
        )
      ####################
      if retc==0:
        retc = run(["git","checkout","FETCH_HEAD"],
                   working_dir=dest_path, do_log=True)
      ####################
      if retc==0:
        munged_branch_name = rev
        if munged_branch_name.find("obt-")==-1:
           munged_branch_name = "obt-%s"%rev
        retc = run(["git","checkout","-b",munged_branch_name],
                   working_dir=dest_path, do_log=True)
      ####################
      if retc==0 and recursive:
         retc = run(["git","submodule","update","--init","--recursive"],
                    working_dir=dest_path, do_log=True)
      ####################
      print(retc)
      return (0 == retc)
    else:
        def _cleanup_dest_plain():
          if dest_path.exists():
            shutil.rmtree(str(dest_path))
        retc = retry_until_rc_zero(
            lambda: run(["git","clone",url,dest_path],do_log=True),
            label="git clone %s" % url,
            cleanup=_cleanup_dest_plain,
        )
        if 0 == retc:
          return _checkoutrevandupdate()

  ##############################################################################
  return False

#####################################################################################

def get_latest_commit(repo_path):
  try:
    repo = git.Repo(repo_path)
    latest_commit = repo.head.commit
    return {
         'commit_hash': latest_commit.hexsha,
         'author': latest_commit.author.name,
         'author_email': latest_commit.author.email,
         'date': latest_commit.committed_datetime,
         'message': latest_commit.message
    }
  except git.exc.InvalidGitRepositoryError:
    return "Invalid Git repository"
  except Exception as e:
    return str(e)

#####################################################################################

def fetch_tarball_from_github(repospec=None,revision=None,md5val=None,destdir=None):
  ghbase = URL("https://github.com")
  url = ghbase/repospec/"tarball"/revision
  print("URL: %s"%url)
  outfname = repospec+("-%s.tar.gz"%revision)
  outfname = outfname.replace("/","_")
  fetched_path = wget(urls=[url],output_name=outfname,md5val=md5val)
  if fetched_path==None:
    print(deco.red("url<%s> not fetched!"%url))
    return -1
  print("dest: %s"%destdir)
  print("destdir fetched_path: %s"%fetched_path)
  if destdir.exists():
    shutil.rmtree(str(destdir))
  destdir.mkdir(parents=True, exist_ok=True)
  # working_dir on tar — no chdir.
  return run(["tar","xvf",fetched_path,"--strip-components","1"],
             working_dir=destdir)