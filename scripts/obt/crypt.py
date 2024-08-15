import subprocess
from obt import path 

def encrypt_string(plain_text, passphrase):
    process = subprocess.Popen(
        ['gpg', '--symmetric', '--cipher-algo', 'AES256', '--passphrase', passphrase, '--batch'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    encrypted_data, error = process.communicate(input=plain_text.encode())

    if process.returncode != 0:
        raise Exception(f"Encryption failed: {error.decode()}")

    return encrypted_data

# Example usage
#plain_text = "This is a secret message."
#passphrase = "yourpassphrase"
#encrypted_string = encrypt_string(plain_text, passphrase)
#print(encrypted_string)

def decrypt_string(encrypted_data, passphrase):
    process = subprocess.Popen(
        ['gpg', '--decrypt', '--passphrase', passphrase, '--batch'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    decrypted_data, error = process.communicate(input=encrypted_data)

    if process.returncode != 0:
        raise Exception(f"Decryption failed: {error.decode()}")

    return decrypted_data.decode()

# Example usage
#decrypted_string = decrypt_string(encrypted_string, passphrase)
#print(decrypted_string)

def encrypt_file(input_file, output_file, passphrase):
    process = subprocess.Popen(
        ['gpg', '--symmetric', '--cipher-algo', 'AES256', '--passphrase', passphrase, '--batch', '--output', output_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    with open(input_file, 'rb') as f:
        input_data = f.read()

    encrypted_data, error = process.communicate(input=input_data)

    if process.returncode != 0:
        raise Exception(f"Encryption failed: {error.decode()}")

    return output_file

# Example usage
#input_file = 'example.txt'
#output_file = 'example.txt.gpg'
#passphrase = 'yourpassphrase'
#encrypt_file(input_file, output_file, passphrase)

def decrypt_file(input_file, output_file, passphrase):
    p_output = path.Path(output_file)
    if p_output.exists():
      p_output.unlink()
    process = subprocess.Popen(
        ['gpg', '--decrypt', '--passphrase', passphrase, '--batch', '--output', output_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    with open(input_file, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data, error = process.communicate(input=encrypted_data)

    if process.returncode != 0:
        raise Exception(f"Decryption failed: {error.decode()}")

    return output_file

# Example usage
#input_file = 'example.txt.gpg'
#output_file = 'example_decrypted.txt'
#passphrase = 'yourpassphrase'
#decrypt_file(input_file, output_file, passphrase)
