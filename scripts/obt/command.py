###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os,io,sys, platform, subprocess, threading
import shlex, errno, pty, select, signal, time

from obt.deco import Deco
from obt import log, pathtools, buildtrace

import obt.path 
deco = Deco()

###########################################################################

def eval_bash_source_env(sourcefile_path):
  command = shlex.split("env -i bash --noprofile -c 'source %s && env'" % sourcefile_path)
  proc = subprocess.Popen(command, stdout = subprocess.PIPE)
  output_env = dict()
  for line in proc.stdout:
    as_str = format(line.decode('utf-8'))
    (key, _, value) = as_str.partition("=")
    value = value.replace("\n","")
    output_env[key] = value
  proc.communicate()
  return output_env

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

    def __init__(self, 
                 command_list, 
                 environment=dict(),
                 do_log=True,
                 working_dir=None,
                 use_shell=False):
        #print(command_list)
        assert(type(command_list)==list)
        self.env = os.environ
        self.working_dir = working_dir
        for k in environment.keys():
            self.env[k]=str(environment[k])
        self.command_list = procargs(command_list)
        #print(self.command_list)
        self._do_log = do_log
        self._use_shell = use_shell

    ###########################################################################

    def exec(self,use_shell=False):

        cur_dir = obt.path.Path(os.getcwd())
        
        if self.working_dir!=None:
          pathtools.chdir(self.working_dir)
        else:
          self.working_dir = cur_dir

        if self._do_log:
          log.output("cmdexec: %s"%deco.bright(self.command_list))

        buildtrace.buildTrace({  
         "op": "command(cmd.exec)",
         "working_dir": self.working_dir,
         "arglist": self.command_list, 
         "os_env": dict(self.env), 
         "use_shell": use_shell or self._use_shell })

        child_process = subprocess.Popen( self.command_list,
                                          universal_newlines=True,
                                          env=self.env,
                                          shell=use_shell or self._use_shell )
        child_process.communicate()
        child_process.wait()

        if self.working_dir!=None:
          pathtools.chdir(cur_dir)

        return child_process.returncode


    def exec_filtered(self,use_shell=False,on_line=None):
        assert(on_line!=None)

        buildtrace.buildTrace({  
         "op": "command(cmd.exec_filtered)",
         "curwd": os.getcwd(),
         "arglist": self.command_list, 
         "os_env": dict(self.env), 
         "use_shell": use_shell or self._use_shell })

        def output_reader(child_process):
          for line in iter(child_process.stdout.readline, b''):
            on_line(format(line.decode('utf-8')))

        if self._do_log:
          log.output("cmdexecf %s"%deco.bright(self.command_list))

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

        buildtrace.buildTrace({  
         "op": "command(cmd.capture)",
         "curwd": os.getcwd(),
         "arglist": self.command_list, 
         "os_env": dict(self.env), 
         "use_shell": False })

        return subprocess.check_output(self.command_list,
                                       universal_newlines=True,
                                       env=self.env )
      
    ###########################################################################

    def execr(self):

        os.execve(self.command_list[0],self.command_list[1:],self.env)


###############################################################################

def run(command_list, 
        environment=dict(),
        working_dir=None,
        do_log=False):
  assert(type(command_list)==list)
  return Command(command_list,environment,do_log=do_log,working_dir=working_dir).exec()

###############################################################################

def deferredRun(command_list, 
                environment=dict(),
                working_dir=None,
                do_log=False):
  assert(type(command_list)==list)
  return lambda: run(command_list,
                     environment=environment,
                     working_dir=working_dir,
                     do_log=do_log)

###############################################################################

def run_filtered(command_list, environment=dict(),on_line=None,do_log=False):
  return Command(command_list,environment,do_log=do_log).exec_filtered(on_line=on_line)
###############################################################################

def capture(command_list,environment=dict(),do_log=True):
  return Command(command_list,environment,do_log=do_log).capture()

###############################################################################
# Command Chain
#  often you need a list of commands to be executed with exit codes tested
#  if any command in the chain fails (returns non zero exit code)
#   then the chain is terminated (subsequent commands will not be executed)
#  Use a command chain when you dont want to look at a bunch of nested conditional
#   command.run blocks
###############################################################################

class chain:
  def __init__(self):
    self._rval = 0
  def run(self,cmdlist): # conditional run (if all previous succeeded, then run next)
    if self._rval == 0:
      self._rval = run(cmdlist)
    return self._rval
  def ok(self): # have all commands run succeeded so far ?
    return self._rval==0


class chain2:
  def __init__(self,do_log=False):
    self._rval = 0
    self._list = list()
    self._do_log = do_log
  def add(self,cmd_or_list,working_dir=None): 
    if(callable(cmd_or_list)):
      self._list += [cmd_or_list]
    else:
      assert(type(cmd_or_list)==list)
      defcmd = deferredRun(cmd_or_list,working_dir=working_dir,do_log=self._do_log)
      self._list += [defcmd]
  def execute(self): 
    for item in self._list:
      assert(callable(item))
      self._rval = item()
      if self._rval!=0:
        return self._rval 
    return 0
  def ok(self): # have all commands run succeeded so far ?
    return self._rval==0

###############################################################################

def system(command_list,working_dir=None,do_log=False):
  buildtrace.buildTrace({  
   "op": "command(system)",
   "curwd": os.getcwd(),
   "arglist": command_list, 
   "os_env": dict(os.environ) })
  args = procargs(command_list)
  joined = " ".join(args)
  if working_dir!=None:
    os.chdir(str(working_dir))
  if do_log:
    log.output("cmdsys: [%s]"%deco.bright(joined))
  return os.system(joined)

###############################################################################

def subshell(directory=None,prompt=None,environment=dict()):
    cur_dir = os.getcwd()
    os.chdir(str(directory))
    curprompt = os.environ["PS1"]
    bdeco = Deco(bash=True)
    PROMPT = bdeco.promptL('[ <<Dep.Build ]')
    PROMPT += bdeco.promptC("\\w")
    PROMPT += bdeco.promptR("[ %s ]"%prompt)
    PROMPT += bdeco.bright("> ")
    os.environ["PS1"] = PROMPT
    retc = Command(["bash","--norc"],environment=environment).exec()
    os.chdir(cur_dir)
    os.environ["PS1"] = curprompt
    return retc

###############################################################################

cmd = Command 

class factory:
  def __init__(self,prefix=[],wdir=None,do_log=True):
    self._working_dir = wdir 
    self._do_log = do_log
    self._clprefix = prefix
  def cmd(self,*args,extra_args=[]):
    return Command( self._clprefix + list(args) + extra_args, #
                    working_dir=self._working_dir, #
                    do_log=self._do_log )

__all__ =   [ "Command", "cmd","factory" ]
