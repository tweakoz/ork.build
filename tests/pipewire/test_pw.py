#!/usr/bin/env python3

from obt import command, path, wget
import threading, time

this_dir = path.directoryOfInvokingModule()

wav_path = wget.wget(urls=["https://www2.cs.uic.edu/~i101/SoundFiles/ImperialMarch60.wav"],
                     output_name=path.temp()/"sound.wav",
                     md5val="4f4ce82317b15ee9cebc9b75c90509c0")

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
#assert(wav_path!=None)  
#print(wav_path)
#play_cmd = command.Command(["pw-play",str(wav_path)],
#                           do_log=True)
#print(play_cmd.command_list)
#play_cmd.exec(use_shell=False)
print("in another shell, run pw-play %s" % wav_path)
############################################
thr1.join()
thr2.join()
