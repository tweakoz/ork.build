###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import git
from git import RemoteProgress
from ork.deco import Deco

deco = Deco()

###############################################################################
class MyProgressPrinter(RemoteProgress):
  def update(self, op_code, cur_count, max_count=None, message=''):
    pct = 100*cur_count / (max_count or 100.0)
    a = "GIT object<%s> of<%s> pct<%s> <%s>                                 \r" \
      % (deco.inf("%s"%cur_count),
         deco.inf("%s"%max_count),
         deco.inf("%f"%pct),
         deco.inf(message or ""))
    print(a, end="")
###############################################################################
def Clone(url,dest,rev="master"):
  if dest.exists():
    repo = git.Repo(str(dest))
    print("Updating URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest)))
    origin = git.remote.Remote(repo,'origin')
    origin.fetch(progress=MyProgressPrinter())
  else:
    repo = git.Repo.init(str(dest))
    print("Cloning URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest)))
    origin = repo.create_remote('origin',str(url))
    origin.fetch(progress=MyProgressPrinter())
    origin.pull(origin.refs[0].remote_head)
    #repo.checkout(rev)
###############################################################################

