import time
import math
import numpy as np
import cv2
from Crypto.Cipher import AES, DES, PKCS1_OAEP
from Crypto.PublicKey import RSA
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# ------------ Utility functions ------------ #

def load_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image at {path}")
    # Work in RGB so it's consistent
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def image_to_bytes(img):
    # img is uint8 HxWxC
    return img.tobytes()

def bytes_to_image(data_bytes, shape):
    # shape = (h, w, c)
    total = shape[0] * shape[1] * shape[2]
    arr = np.frombuffer(data_bytes[:total], dtype=np.uint8)
    return arr.reshape(shape)

def compute_psnr(original, decoded):
    # Both are uint8 RGB
    psnr_val = cv2.PSNR(original, decoded)
    # Avoid inf for JSON (cap it)
    if math.isinf(psnr_val):
        psnr_val = 100.0
    return psnr_val

def compute_security(original, encrypted):
    """
    Security Score: Histogram difference normalized to 0–100%.
    Higher = more secure.
    """
    # Convert to grayscale
    orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
    enc_gray = cv2.cvtColor(encrypted, cv2.COLOR_RGB2GRAY)

    h, w = orig_gray.shape
    hist_o = cv2.calcHist([orig_gray], [0], None, [256], [0, 256])
    hist_e = cv2.calcHist([enc_gray], [0], None, [256], [0, 256])

    diff = np.sum(np.abs(hist_o - hist_e))

    # Maximum possible histogram difference
    max_possible = 256 * h * w

    # Normalize result
    score = (diff / max_possible) * 100.0

    # Ensure within 0–100%
    return round(min(score, 100.0), 2)

# ------------ AES test ------------ #

def aes_test(img):
    data = image_to_bytes(img)
    key = b'1234567890abcdef'
    cipher = AES.new(key, AES.MODE_ECB)

    block = 16
    pad_len = (block - (len(data) % block)) % block
    if pad_len == 0:
        pad_len = block
    padded = data + bytes([pad_len]) * pad_len

    # Encrypt
    t1 = time.time()
    enc_bytes = cipher.encrypt(padded)
    t2 = time.time()

    # Decrypt
    t3 = time.time()
    dec_bytes_full = cipher.decrypt(enc_bytes)
    t4 = time.time()
    dec_bytes = dec_bytes_full[:-pad_len]

    # Build images
    dec_img = bytes_to_image(dec_bytes, img.shape)
    enc_img = bytes_to_image(enc_bytes[:len(data)], img.shape)

    psnr_val = compute_psnr(img, dec_img)
    sec_val = compute_security(img, enc_img)

    return (t2 - t1) * 1000.0, (t4 - t3) * 1000.0, psnr_val, sec_val

# ------------ DES test ------------ #

def des_test(img):
    data = image_to_bytes(img)
    key = b'12345678'
    cipher = DES.new(key, DES.MODE_ECB)

    block = 8
    pad_len = (block - (len(data) % block)) % block
    if pad_len == 0:
        pad_len = block
    padded = data + bytes([pad_len]) * pad_len

    t1 = time.time()
    enc_bytes = cipher.encrypt(padded)
    t2 = time.time()

    t3 = time.time()
    dec_bytes_full = cipher.decrypt(enc_bytes)
    t4 = time.time()
    dec_bytes = dec_bytes_full[:-pad_len]

    dec_img = bytes_to_image(dec_bytes, img.shape)
    enc_img = bytes_to_image(enc_bytes[:len(data)], img.shape)

    psnr_val = compute_psnr(img, dec_img)
    sec_val = compute_security(img, enc_img)

    return (t2 - t1) * 1000.0, (t4 - t3) * 1000.0, psnr_val, sec_val

# ------------ RSA test ------------ #

def rsa_test(img):
    data = image_to_bytes(img)
    keypair = RSA.generate(2048)
    cipher = PKCS1_OAEP.new(keypair)

    chunk_size = 190
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    # Encrypt chunks
    t1 = time.time()
    enc_chunks = [cipher.encrypt(chunk) for chunk in chunks]
    t2 = time.time()

    # Decrypt chunks
    t3 = time.time()
    dec_chunks = [cipher.decrypt(chunk) for chunk in enc_chunks]
    t4 = time.time()

    enc_bytes = b"".join(enc_chunks)
    dec_bytes_full = b"".join(dec_chunks)
    dec_bytes = dec_bytes_full[:len(data)]

    dec_img = bytes_to_image(dec_bytes, img.shape)
    enc_img = bytes_to_image(enc_bytes[:len(data)], img.shape)

    psnr_val = compute_psnr(img, dec_img)
    sec_val = compute_security(img, enc_img)

    return (t2 - t1) * 1000.0, (t4 - t3) * 1000.0, psnr_val, sec_val

# ------------ MASB + QICE test ------------ #

def masb_qice_test(img):
    h, w, c = img.shape
    hw = h * w

    seed = int(np.sum(img, dtype=np.uint64)) % 1000
    rng = np.random.default_rng(seed)

    shuffle = rng.permutation(hw)
    inv_shuffle = np.empty_like(shuffle)
    inv_shuffle[shuffle] = np.arange(hw)

    qkey = np.random.default_rng(seed + 123).integers(0, 256, hw, dtype=np.uint8)

    flat = img.reshape(hw, c).astype(np.int16)

    # Encrypt
    t1 = time.time()
    enc_flat = (flat[shuffle] + qkey[:, None]) % 256
    enc = enc_flat.astype(np.uint8).reshape(h, w, c)
    t2 = time.time()

    # Decrypt
    t3 = time.time()
    dec_flat = (enc_flat - qkey[:, None]) % 256
    dec_flat = dec_flat[inv_shuffle]
    dec = dec_flat.astype(np.uint8).reshape(h, w, c)
    t4 = time.time()

    psnr_val = compute_psnr(img, dec)
    sec_val = compute_security(img, enc)

    return (t2 - t1) * 1000.0, (t4 - t3) * 1000.0, psnr_val, sec_val

# ------------ Public API for Flask ------------ #

def run_benchmark(image_path):
    img = load_image(image_path)

    results = {}

    # AES
    e, d, p, s = aes_test(img)
    results["AES"] = {
        "encrypt": float(e),
        "decrypt": float(d),
        "psnr": float(p),
        "security": float(s)
    }

    # DES
    e, d, p, s = des_test(img)
    results["DES"] = {
        "encrypt": float(e),
        "decrypt": float(d),
        "psnr": float(p),
        "security": float(s)
    }

    # RSA
    e, d, p, s = rsa_test(img)
    results["RSA"] = {
        "encrypt": float(e),
        "decrypt": float(d),
        "psnr": float(p),
        "security": float(s)
    }

    # MASB + QICE
    e, d, p, s = masb_qice_test(img)
    results["MASB+QICE"] = {
        "encrypt": float(e),
        "decrypt": float(d),
        "psnr": float(p),
        "security": float(s)
    }

    return results
