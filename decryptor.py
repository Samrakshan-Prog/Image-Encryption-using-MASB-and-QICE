import cv2
import numpy as np
import os
import json
import sys
from Crypto.Cipher import AES
import base64

def inverse_shuffle(channel, shuffle_key):
    inverse = np.zeros_like(shuffle_key)
    for i, val in enumerate(shuffle_key):
        inverse[val] = i
    flat = channel.flatten()
    unshuffled = flat[inverse]
    return unshuffled.reshape(channel.shape)

def reverse_qice_modulation(channel, quantum_key):
    demodulated = (channel.astype(np.int16) - quantum_key[:channel.size].reshape(channel.shape)) % 256
    return demodulated.astype(np.uint8)

def decrypt_image(enc_path, key_path, output_path):
    AES_KEY = b'1234567890abcdef'  

    
    with open(key_path, 'r') as f:
        enc_str = f.read()
    encrypted_bytes = base64.b64decode(enc_str)
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(encrypted_bytes)
    pad_len = decrypted_padded[-1]
    json_bytes = decrypted_padded[:-pad_len]
    key_data = json.loads(json_bytes)

    shuffle_key = np.array(key_data['shuffle_key'])
    quantum_key = np.array(key_data['quantum_key'], dtype=np.uint8)
    is_gray = key_data['is_gray']
    shape = tuple(key_data['shape'])

    img = cv2.imread(enc_path)
    if img is None:
        raise FileNotFoundError(f"Could not read {enc_path}")

    if is_gray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        demodulated = reverse_qice_modulation(gray, quantum_key)
        unshuffled = inverse_shuffle(demodulated, shuffle_key)
        recovered = cv2.cvtColor(unshuffled, cv2.COLOR_GRAY2BGR)
        cv2.imwrite(output_path, recovered, [cv2.IMWRITE_PNG_COMPRESSION, 1])
    else:
        b, g, r = cv2.split(img)
        decrypted_channels = []
        for ch in [b, g, r]:
            demodulated = reverse_qice_modulation(ch, quantum_key)
            unshuffled = inverse_shuffle(demodulated, shuffle_key)
            decrypted_channels.append(unshuffled)
        decrypted_img = cv2.merge(decrypted_channels)
        cv2.imwrite(output_path, decrypted_img, [cv2.IMWRITE_PNG_COMPRESSION, 9])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python decryptor.py <encrypted_image> <key_file>")
        sys.exit(1)

    enc_path = sys.argv[1]
    key_path = sys.argv[2]


    AES_KEY = b'1234567890abcdef'
    with open(key_path, 'r') as f:
        enc_str = f.read()
    encrypted_bytes = base64.b64decode(enc_str)
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(encrypted_bytes)
    pad_len = decrypted_padded[-1]
    json_bytes = decrypted_padded[:-pad_len]
    key_data = json.loads(json_bytes)

    name = os.path.splitext(os.path.basename(enc_path))[0].replace("encrypted_", "")
    ext = key_data.get("ext", ".png")
    os.makedirs("decrypted", exist_ok=True)
    output_path = f"decrypted/decrypted_{name}{ext}"

    decrypt_image(enc_path, key_path, output_path)
    print(f"✅ Decrypted image saved to {output_path}")
