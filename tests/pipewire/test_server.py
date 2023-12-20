#!/usr/bin/env python3

from obt import command, path, wget
import threading, time

this_dir = path.directoryOfInvokingModule()

command.run(["cp",
             this_dir/"pipewire.conf",
             path.stage()/"etc"/"pipewire.conf"])

############################################
def thread_pipewire_daemon():
 environ = {
  "PIPEWIRE_DEBUG": "3",
  "PIPEWIRE_CONFIG_DIR": path.stage()/"etc"
 }
 command.run(["pipewire"],environment=environ)
thr1 = threading.Thread(target=thread_pipewire_daemon)
thr1.start()
time.sleep(1)
############################################
def thread_wireplumber_daemon():
 command.run(["wireplumber"],do_log=True)
thr2 = threading.Thread(target=thread_wireplumber_daemon)
thr2.start()
time.sleep(3)
############################################
#print("STARTING SOUND... %s"%wav_path)
#print(wav_path)
#play_cmd = command.Command(["pw-play",str(wav_path)],
#                           do_log=True)
#print(play_cmd.command_list)
#play_cmd.exec(use_shell=False)
print("in another shell, run pw-play %s" % wav_path)
############################################
thr1.join()
thr2.join()
