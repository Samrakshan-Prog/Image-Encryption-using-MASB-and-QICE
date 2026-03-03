from flask import Flask, request, jsonify, render_template
import os
import subprocess
import uuid
import json
import base64
from benchmark import run_benchmark 
import cloudinary
import cloudinary.uploader
from flask import send_from_directory 
from dotenv import load_dotenv
load_dotenv()
import cv2
import numpy as np
import math
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from skimage.measure import shannon_entropy
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

cloudinary.config(
  cloud_name="dbosjllm7",
  api_key="729367223699857",
  api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
def mse(imgA, imgB):
    return np.mean((imgA.astype("float") - imgB.astype("float")) ** 2)

def psnr(mse_value):
    if mse_value == 0:
        return 100
    PIXEL_MAX = 255.0
    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse_value))

def ncc(imgA, imgB):
    a = imgA - np.mean(imgA)
    b = imgB - np.mean(imgB)
    return np.sum(a * b) / np.sqrt(np.sum(a**2) * np.sum(b**2))

def npcr(imgA, imgB):
    diff = imgA != imgB
    return np.sum(diff) / diff.size * 100

def uaci(imgA, imgB):
    return np.mean(np.abs(imgA - imgB) / 255) * 100



@app.route('/compare', methods=['POST'])
def compare():
    img1 = request.files['image1']
    img2 = request.files['image2']

    path1 = os.path.join(app.config['UPLOAD_FOLDER'], img1.filename)
    path2 = os.path.join(app.config['UPLOAD_FOLDER'], img2.filename)
    img1.save(path1)
    img2.save(path2)

    # ---- File sizes ----
    sizeA = os.path.getsize(path1) / (1024 * 1024)  # Convert to MB
    sizeB = os.path.getsize(path2) / (1024 * 1024)

    file_size_A = f"{sizeA:.2f} MB" if sizeA >= 1 else f"{sizeA*1024:.2f} KB"
    file_size_B = f"{sizeB:.2f} MB" if sizeB >= 1 else f"{sizeB*1024:.2f} KB"

    # Load and compute info
    infoA = Image.open(path1)
    infoB = Image.open(path2)

    # ---------- Basic Metrics ----------
    result = {
        "Size_Match": infoA.size == infoB.size,
        "Size_A (W,H)": infoA.size,
        "Size_B (W,H)": infoB.size,
        "File_Size_A": file_size_A,
        "File_Size_B": file_size_B,
        "Aspect_Ratio_Match": (infoA.width/infoA.height) == (infoB.width/infoB.height),
        "Channels_Match": infoA.mode == infoB.mode,
        "Channel_A": infoA.mode,
        "Channel_B": infoB.mode,
        "Format_Match": infoA.format == infoB.format,
        "Format_A": infoA.format,
        "Format_B": infoB.format,
    }


    # ---------- Channel Correction (Fix you needed) ----------
    if infoA.mode != infoB.mode:
        infoA = infoA.convert("RGB")
        infoB = infoB.convert("RGB")
        infoA.save(path1)
        infoB.save(path2)
        result["Channels_Match"] = True
        result["Channel_A"] = "RGB"
        result["Channel_B"] = "RGB"

    # ---------- Read with OpenCV ----------
    imgA_color = cv2.imread(path1)
    imgB_color = cv2.imread(path2)

    imgA_gray = cv2.cvtColor(imgA_color, cv2.COLOR_BGR2GRAY)
    imgB_gray = cv2.cvtColor(imgB_color, cv2.COLOR_BGR2GRAY)

    # If not same size — show only basic metrics
    if imgA_gray.shape != imgB_gray.shape:
        return render_template("result.html",
                               results=result,
                               img1=img1.filename,
                               img2=img2.filename)

    # ---------- Advanced Metrics ----------
    mse_val = mse(imgA_gray, imgB_gray)

    result.update({
        "MSE": round(mse_val, 4),
        "PSNR": round(psnr(mse_val), 4),
        "SSIM": round(ssim(imgA_gray, imgB_gray), 4),
        "NCC": round(ncc(imgA_gray, imgB_gray), 4),
        "Entropy_A": round(shannon_entropy(imgA_gray), 4),
        "Entropy_B": round(shannon_entropy(imgB_gray), 4),
        "NPCR": round(npcr(imgA_gray, imgB_gray), 2),
        "UACI": round(uaci(imgA_gray, imgB_gray), 2),
    })

    plot_name = f"corr_{uuid.uuid4().hex}.png"
    plot_path = os.path.join('static/plots', plot_name)

    os.makedirs('static/plots', exist_ok=True)

       # Flatten pixel values
    x = imgA_gray.flatten()
    y = imgB_gray.flatten()

    # Linear regression best-fit line
    m, b = np.polyfit(x, y, 1)
    line = m * x + b

    plt.figure(figsize=(7,5), dpi=160)
    plt.scatter(x, y, s=1, alpha=0.4, color="white", label="Pixel Values")

    plt.plot(x, line, linewidth=2.5, color="#00ffd5", label="Correlation Line")


    plt.title("Correlation Analysis")
    plt.xlabel("Original Pixel Values")
    plt.ylabel("Compared Pixel Values")
    plt.text(10, 240, f"NCC = {result['NCC']}", fontsize=10,
             bbox=dict(boxstyle="round", fc="black", ec="cyan"))

    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, facecolor='#111', edgecolor='none')
    plt.close()

    return render_template("result.html",
                           results=result,
                           img1=img1.filename,
                           img2=img2.filename,
                           plot_img=plot_name)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/comp')
def comp():
    return render_template('comp.html')

@app.route('/use')
def use():
    return render_template('use.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    if 'image' not in request.files:
        return jsonify({'message': 'No image uploaded'})

    image = request.files['image']
    filename = image.filename
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    os.makedirs('input', exist_ok=True)
    os.makedirs('output', exist_ok=True)

    input_path = os.path.join('input', filename)
    image.save(input_path)

    # Run Encryption Script
    subprocess.run(['python', 'encryptor.py', input_path])

    # Expected output paths
    enc_filename = f"encrypted_{name}.png"
    key_filename = f"key_{name}.json"

    enc_path = os.path.join('output', enc_filename)
    key_path = os.path.join('output', key_filename)

    share_filename = f"share_{uuid.uuid4()}.png"
    share_path = os.path.join("static/uploads", share_filename)

    # Upload encrypted file to Cloudinary
    upload_result = cloudinary.uploader.upload(enc_path)
    share_url = upload_result["secure_url"]


    return jsonify({
    'message': 'Encryption Completed!',
    'encrypted_image': share_url,
    'key_file': f"/output/{key_filename}"
    })



@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'image' not in request.files or 'key' not in request.files:
        return jsonify({'message': 'Encrypted image and key (.json) are required'})

    image = request.files['image']
    key = request.files['key']
    img_name = image.filename
    key_name = key.filename

    os.makedirs('output', exist_ok=True)
    os.makedirs('decrypted', exist_ok=True)

    enc_path = os.path.join('output', img_name)
    key_path = os.path.join('output', key_name)

    image.save(enc_path)
    key.save(key_path)

    subprocess.run(['python', 'decryptor.py', enc_path, key_path])

    original_name = img_name.replace("encrypted_", "")
    original_path = os.path.join('input', original_name)
    decrypted_path = os.path.join('decrypted', f"decrypted_{os.path.splitext(original_name)[0]}.png")

    result = subprocess.run(
        ['python', 'verify.py', original_path, decrypted_path],
        capture_output=True,
        text=True
    )

    try:
        metrics = json.loads(result.stdout)

        share_filename = f"decrypted_{uuid.uuid4()}.png"
        share_path = os.path.join("static/uploads", share_filename)

        # Upload decrypted file to Cloudinary
        upload_result = cloudinary.uploader.upload(decrypted_path)
        dec_img_url = upload_result["secure_url"]

        return jsonify({
            'message': 'Decryption Completed!',
            'decrypted_image': dec_img_url,
            'original_size': metrics.get('original_size'),
            'decrypted_size': metrics.get('decrypted_size'),
            'psnr': f"{metrics.get('psnr', 0)} dB"
        })

    except Exception as e:
        print("Verification error:", str(e))
        return jsonify({'message': 'Decryption done but failed to verify PSNR.'})


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
DECRYPTED_FOLDER = os.path.join(BASE_DIR, "decrypted")


@app.route("/open-output")
def open_output_folder():
    try:
        print("Opening folder:", OUTPUT_FOLDER)
        os.startfile(OUTPUT_FOLDER)
        return "Output folder opened successfully!"
    except Exception as e:
        print("Error:", str(e))
        return f"Error opening output folder: {str(e)}"


@app.route("/open-decrypted")
def open_decrypted_folder():
    try:
        os.startfile(DECRYPTED_FOLDER)  
        return "Decrypted folder opened successfully!"
    except Exception as e:
        return f"Error opening decrypted folder: {str(e)}"


@app.route('/output/<path:filename>')
def download_key(filename):
    return send_from_directory('output', filename, as_attachment=True)

@app.route('/benchmark', methods=['POST'])
def benchmark():
    if 'image' not in request.files:
        return jsonify({"message": "No image uploaded"}), 400

    image = request.files['image']
    os.makedirs("benchmark_input", exist_ok=True)

    img_path = os.path.join("benchmark_input", image.filename)
    image.save(img_path)

    results = run_benchmark(img_path)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
