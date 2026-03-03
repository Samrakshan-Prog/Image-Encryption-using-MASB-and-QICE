from flask import Flask, render_template, request
import cv2
import numpy as np
import math
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from skimage.measure import shannon_entropy
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

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


@app.route('/')
def index():
    return render_template('comp.html')


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

    return render_template("result.html",
                           results=result,
                           img1=img1.filename,
                           img2=img2.filename)


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5001)

