#!/usr/bin/env python3

from obt import path, wget
import os

url=["http://www.tweakoz.com/resources/audio/Feb142023.mp3"]
md5="d6ade30fdc8f9c80a7c846c983b4877a"
#url = ["https://www.kozco.com/tech/c304-2.wav"]
#md5 = "df22f8d0f920eb8cdd52a7bb84a1dc03"
#url = ["https://www2.cs.uic.edu/~i101/SoundFiles/ImperialMarch60.wav"]
#md5 = "4f4ce82317b15ee9cebc9b75c90509c0"

wav_path = wget.wget(urls=url,
                     output_name=path.temp()/"test.mp3",
                     md5val=md5)

assert(wav_path!=None)  

os.system("ffmpeg -i %s -f wav - | pw-play -" % wav_path)
