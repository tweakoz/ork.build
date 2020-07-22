###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os,io,sys, platform, subprocess, threading
import shlex, errno, pty, select, signal, time

from ork.deco import Deco
from ork import log
deco = Deco()

###############################################################################

def procargs(command_list):
    rval = list()
    if isinstance(command_list, str):
        rval = shlex.split(command_list)
    elif isinstance(command_list,list):
        newlist = []
        for item in command_list:
            newlist.append(str(item))
        rval = newlist
    return rval

###############################################################################

class Command:

    """run a command with a provided environment"""

    ###########################################################################

    def __init__(self, command_list, environment=dict(),do_log=True):

        self.env = os.environ
        for k in environment.keys():
            self.env[k]=str(environment[k])
        self.command_list = procargs(command_list)
        if do_log:
          log.output(deco.white(self.command_list))

    ###########################################################################

    def exec(self,use_shell=False):

        child_process = subprocess.Popen( self.command_list,
                                          universal_newlines=True,
                                          env=self.env,
                                          shell=use_shell )
        child_process.communicate()
        child_process.wait()

        return child_process.returncode


    def exec_filtered(self,use_shell=False,on_line=None):
        assert(on_line!=None)
        def output_reader(child_process):
          for line in iter(child_process.stdout.readline, b''):
            on_line(format(line.decode('utf-8')))


        child_process = subprocess.Popen(self.command_list,
                                         universal_newlines=False,
                                         shell=use_shell,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT)

        thr = threading.Thread(target=output_reader,
                               args=(child_process,))

        try:
          thr.start()
          time.sleep(0.25)
          keep_going = True
          while keep_going:
            time.sleep(0.25)
            keep_going = (child_process.poll() == None)
          child_process.stdout.close()
        finally:
          child_process.terminate()
          try:
             child_process.wait(timeout=0.2)
          except subprocess.TimeoutExpired:
             assert(False)
        thr.join()
        return child_process.returncode

    ###########################################################################

    def capture(self):

        return subprocess.check_output(self.command_list,
                                       universal_newlines=True,
                                       env=self.env )

    ###########################################################################

    def execr(self):

        os.execve(self.command_list[0],self.command_list[1:],self.env)


###############################################################################

def run(command_list, environment=dict(),do_log=False):
  return Command(command_list,environment,do_log=do_log).exec()
def run_filtered(command_list, environment=dict(),on_line=None,do_log=False):
  return Command(command_list,environment,do_log=do_log).exec_filtered(on_line=on_line)

def capture(command_list,environment=dict(),do_log=True):
  return Command(command_list,environment,do_log=do_log).capture()

###############################################################################

def system(command_list):
  args = procargs(command_list)
  joined = " ".join(args)
  print("cmd<%s>"%deco.key(joined))
  return os.system(joined)

###############################################################################

__all__ =   [ "Command" ]
