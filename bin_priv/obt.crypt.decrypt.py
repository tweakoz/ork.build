#!/usr/bin/env python3

################################################################################

from obt import path, wget, crypt 
import sys, os, random, numpy, argparse
import base64

parser = argparse.ArgumentParser(description='assetpak tester')
parser.add_argument("-o", '--output', type=str, help='output file', required=False)
parser.add_argument("-i", '--input', type=str, help='input file', required=False)
parser.add_argument("-s", '--string', type=str, help='string', required=False)
parser.add_argument("-p", '--passphrase', type=str, help='passphrase', required=True)
args = vars(parser.parse_args())

output = args['output']
input = args['input']
passphrase = args['passphrase']
input_string = args.get('string')

if input_string:
  assert(input == None)
  assert(output == None)
  #strip quotes surrounding the string if they exist
  if input_string[0] == '"' and input_string[-1] == '"':
    input_string = input_string[1:-1]
  # Decode the base64 encoded string
  input_string = base64.urlsafe_b64decode(input_string)
  # Encrypt the string
  decrypted_string = crypt.decrypt_string(input_string, passphrase)
  print(decrypted_string)
  # Write the encoded string to the output file
else:
  crypt.decrypt_file(input, output, passphrase)