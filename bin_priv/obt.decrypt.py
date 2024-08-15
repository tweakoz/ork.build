#!/usr/bin/env python3

################################################################################

from obt import path, wget, crypt 
import sys, os, random, numpy, argparse

parser = argparse.ArgumentParser(description='assetpak tester')
parser.add_argument("-o", '--output', type=str, help='output file', required=True)
parser.add_argument("-i", '--input', type=str, help='input file', required=True)
parser.add_argument("-p", '--passphrase', type=str, help='passphrase', required=True)
args = vars(parser.parse_args())

output = args['output']
input = args['input']
passphrase = args['passphrase']

p_output = path.Path(output)
if p_output.exists():
  p_output.unlink()
  
crypt.decrypt_file(input, output, passphrase)