import os, subprocess

########################################################

def procargs(command_list):
  newlist = []
  for item in command_list:
      newlist.append(str(item))
  return newlist

########################################################

def sync_subprocess(command_list):
  cmd_list = " ".join(procargs(command_list))
  print(command_list)
  print(cmd_list)
  child_process = subprocess.Popen( cmd_list,
                                    universal_newlines=True,
                                    env=os.environ,
                                    shell=True )
  child_process.communicate()
  child_process.wait()


