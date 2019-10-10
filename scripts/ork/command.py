###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os,sys, platform, subprocess
from ork.deco import Deco
from ork.log import log
deco = Deco()

###############################################################################

class Command:

    """run a command with a provided environment"""

    ###########################################################################

    def __init__(self, command_list, environment=dict()):

        self.env = os.environ
        for k in environment.keys():
            self.env[k]=str(environment[k])

        if isinstance(command_list, str):
            self.command_list = shlex.split(command_list)

        elif isinstance(command_list,list):
            newlist = []
            for item in command_list:
                newlist.append(str(item))
            self.command_list = newlist

        log(deco.white(self.command_list))

    ###########################################################################

    def exec(self):

        child_process = subprocess.Popen( self.command_list,
                                          universal_newlines=True,
                                          env=self.env )
        child_process.communicate()
        child_process.wait()

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

def run(command_list, environment=dict()):
    Command(command_list,environment).exec()

def system(command_list):
    joined = " ".join(command_list)
    print("cmd<%s>"%deco.key(joined))
    os.system(joined)

###############################################################################

__all__ =   [ "Command" ]
