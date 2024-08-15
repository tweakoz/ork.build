#!/usr/bin/env python3

################################################################################

from obt import path, wget, crypt 
import sys, os, random, numpy, argparse
import base64

parser = argparse.ArgumentParser(description='assetpak generator')
parser.add_argument("-o", '--output', type=str, help='output file', required=True)
parser.add_argument("-i", '--input', type=str, help='input file', required=False)
parser.add_argument("-s", '--string', type=str, help='string', required=False)
parser.add_argument("-p", '--passphrase', type=str, help='passphrase', required=True)
args = vars(parser.parse_args())

output = args['output']
input = args.get('input')
input_string = args.get('string')
passphrase = args['passphrase']

if input_string:
    # Encrypt the string
    encrypted_data = crypt.encrypt_string(input_string, passphrase)
    # Encode the encrypted data to an alphanumeric string using base64
    encoded_string = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    
    # Write the encoded string to the output file
    with open(output, 'w') as f:
        f.write(encoded_string)
else:
    if not input:
        print("Error: You must provide either an input file or a string.")
        sys.exit(1)

    # Encrypt the file
    crypt.encrypt_file(input, output, passphrase)
