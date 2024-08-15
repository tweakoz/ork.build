#!/usr/bin/env python3

################################################################################

from obt import path, wget, crypt 
import sys, os, random, numpy, argparse
import base64

parser = argparse.ArgumentParser(description='assetpak generator')
parser.add_argument("-o", '--output', type=str, help='output file', required=False)
parser.add_argument("-i", '--input', type=str, help='input file', required=False)
parser.add_argument("-s", '--string', type=str, help='string', required=False)
parser.add_argument("-p", '--passphrase', type=str, help='passphrase', required=True)
args = vars(parser.parse_args())

output = args['output']
input = args.get('input')
input_string = args.get('string')
passphrase = args['passphrase']

if input_string:
  #strip quotes surrounding the string if they exist
  if input_string[0] == '"' and input_string[-1] == '"':
    input_string = input_string[1:-1]

  # Encrypt the string
  encrypted_data = crypt.encrypt_string(input_string, passphrase)
  # Encode the encrypted data to an alphanumeric string using base64
  encoded_string = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
  print(encoded_string)
  # Write the encoded string to the output file
else:
  crypt.encrypt_file(input, output, passphrase)
