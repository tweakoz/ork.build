#!/usr/bin/env python3

from obt import path, command, subspace
import librosa, pysinsy, wavio, io
import numpy as np
from nnmnkwii.io import hts
from nnsvs.pretrained import create_svs_engine
import nnsvs, random

#############################################################
# create synth
#############################################################
    
engine = create_svs_engine("r9y9/yoko_latest")

class HTSLabelGenerator:
    def __init__(self):
        self.phonemes = ['pau', 'a', 'i', 'u', 'e', 'o', 'k', 's', 't', 'n', 'h', 'm', 'y', 'r', 'w', 'g', 'z', 'd', 'b', 'p']
        self.positions_in_syllable = ['0', '1', '2', '3', '4']
        self.positions_in_word = ['0', '1', '2', '3', '4']
        self.positions_in_phrase = ['0', '1', '2', '3', '4']
        self.durations = ['1000000', '2000000', '3000000', '4000000', '5000000']
        #self.pitches = ['9', '10', '11', '12', '13']
        self.midi_notes = [60, 62, 64, 65, 67, 69, 71, 72, 74]

    def generate_relative_pitch(self):
        shift = 24
        midi_note = random.choice(self.midi_notes)+shift
        min_midi_note = min(self.midi_notes)+shift
        max_midi_note = max(self.midi_notes)+shift
        relative_pitch = int(((midi_note - min_midi_note) / (max_midi_note - min_midi_note)) * 15) + 1
        return relative_pitch

    def generate_random_hts_label(self):
        prev_phoneme = random.choice(self.phonemes)
        curr_phoneme = random.choice(self.phonemes)
        next_phoneme = random.choice(self.phonemes)

        phoneme_context = f"{prev_phoneme}@xx^xx-{curr_phoneme}+{next_phoneme}={curr_phoneme}_xx%xx"
        position_in_syllable = random.choice(self.positions_in_syllable)
        position_in_word = random.choice(self.positions_in_word)
        position_in_phrase = random.choice(self.positions_in_phrase)
        duration = random.choice(self.durations)
        pitch = self.generate_relative_pitch()*3

        label = f"{phoneme_context}/A:{position_in_syllable}-{position_in_word}-{position_in_phrase}@xx~xx/B:1_1_1@xx|xx/C:2+1+1@JPN&0/D:xx!xx#xx$xx%xx|xx&xx;xx-xx/E:xx]xx^0=2/4~{duration}!1@109#48+xx]1$1|0[10&0]48=0^100~xx#xx_xx;xx$xx&xx%xx[xx|0]0-n^xx+xx~xx=xx@xx$xx!xx%xx#xx|xx|xx-xx&xx&xx+xx[xx;xx]xx;xx~xx~xx^xx^xx@xx[xx#xx=xx!xx~xx+xx!xx^xx/F:A4#{pitch}#0-2/4$110$1+40%18;xx"
        return label

labels = hts.HTSLabelFile()
label_generator = HTSLabelGenerator()
curtime = 0.0
for _ in range(15):
    duration = random.randint(10000000, 20000000)
    random_label = label_generator.generate_random_hts_label()
    labels.append((curtime, curtime+duration, random_label))
    curtime += duration

print( "#################################################")
#contexts = pysinsy.extract_fullcontext(nnsvs.util.example_xml_file("song070_f00001_063"))
#labels = hts.HTSLabelFile.create_from_contexts(contexts)
#print(labels)
#assert(False)
#print( "#################################################")
#print(labels)
#print( "#################################################")
#assert(False)
#############################################################
# synthesize
##############################################################

wav, sample_rate = engine.svs(labels)

#############################################################
# write output
#############################################################

wavio.write("output.wav", wav, sample_rate, sampwidth=2)  # sampwidth=2 for 16-bit PCM