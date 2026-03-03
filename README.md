# 🔐 Image Encryption using MASB and QICE

> A secure image encryption and decryption system powered by **Multi-Agent Swarm Behavior (MASB)** and **Quantum-Inspired Chaotic Encoding (QICE)** — delivering high randomness, low pixel correlation, and lossless image recovery.

---

## 📌 Overview

This system applies swarm-based pixel permutation combined with quantum-inspired chaotic encoding to transform images into secure encrypted forms. It features a Flask-based web interface, cloud integration via Cloudinary, and a benchmarking module for security analysis.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 Advanced Encryption | MASB swarm permutation + QICE chaotic encoding |
| 🔄 Lossless Decryption | Exact pixel-perfect image recovery |
| 📊 Benchmark Analysis | Correlation metrics and performance plots |
| 🌐 Flask Web Interface | Upload, encrypt, decrypt via browser |
| ☁️ Cloudinary Integration | Cloud-based image handling and storage |
| 📁 File Support | Upload and download encrypted/decrypted images |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Image Processing:** Pillow, NumPy
- **Visualization:** Matplotlib
- **Cloud Storage:** Cloudinary
- **Frontend:** HTML, CSS

---

## 📂 Project Structure

```
Image-Encryption-using-MASB-and-QICE/
│
├── app.py               # Flask application entry point
├── encryptor.py         # MASB + QICE encryption logic
├── decryptor.py         # Decryption and key verification
├── benchmark.py         # Correlation and performance analysis
├── check.py             # Utility/validation checks
├── requirements.txt     # Python dependencies
│
├── static/
│   ├── uploads/         # Uploaded images
│   └── plots/           # Generated benchmark plots
│
└── templates/
    ├── index.html        # Home / upload page
    ├── result.html       # Encryption result view
    ├── about.html        # About the project
    └── use.html          # Usage instructions
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Samrakshan-Prog/Image-Encryption-using-MASB-and-QICE.git
cd Image-Encryption-using-MASB-and-QICE
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
python app.py
```

Then open your browser and navigate to:

```
http://127.0.0.1:5000/
```

---

## 📊 Benchmark Module

To run correlation and performance analysis:

```bash
python benchmark.py
```

This generates plots saved to `static/plots/` showing pixel correlation and encryption performance metrics.

---

## 🔑 Encryption Workflow

```
1. Upload image via the web interface
       ↓
2. MASB applies swarm-based pixel permutation
       ↓
3. QICE applies quantum-inspired chaotic encoding
       ↓
4. Encrypted image and secret key are generated
       ↓
5. Decryption using the key reconstructs the exact original image
```

---

## 📈 Security Highlights

- **High randomness** — chaotic encoding ensures unpredictable output
- **Low pixel correlation** — adjacent pixels are statistically independent after encryption
- **Key-based reversibility** — only the correct key can decrypt the image
- **Lossless decryption** — zero data loss; original image is recovered exactly

---

## 👨‍💻� Author

**Sri Samrakshan Parthiban**  
B.Sc Information Technology

[![LinkedIn](www.linkedin.com/in/srisamrakshan)

> 💡 *Replace the LinkedIn URL above with your actual profile link.*

---

## 📄 License

This project is open source. Feel free to use, modify, and distribute with attribution.
