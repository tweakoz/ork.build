import os,sys, platform, subprocess

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

    ###########################################################################

    def exec(self):

        child_process = subprocess.Popen( self.command_list,
                                          universal_newlines=True,
                                          env=self.env )
        child_process.communicate()
        child_process.wait()

        return child_process.returncode

