from flask import Flask, request, jsonify
import pandas as pd
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np
from difflib import get_close_matches
import os

app = Flask(__name__)

# Configure Tesseract path (change only for local test, ignore on Render)
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", r"C:\\Users\\Dell\\Desktop\\Tesseract-OCR\\tesseract.exe")

# Expected subjects and columns
matieres_attendues = ['Arabe', 'Math', 'Physique', 'Science', 'Islamic', 'Histoire_Geo', 'Français', 'Anglais', 'Sport']
colonnes = ['coef', 'evaluation', 'tp', 'moy_devoirs', 'exam', 'moy', 'moy_x_coef']

def corriger_nom_matiere(nom_ocr):
    return get_close_matches(nom_ocr.capitalize(), matieres_attendues, n=1, cutoff=0.6)

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    filepath = os.path.join("temp", file.filename)
    os.makedirs("temp", exist_ok=True)
    file.save(filepath)

    try:
        image_cv = cv2.imread(filepath)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        temp_path = "temp/temp_ocr_image.png"
        cv2.imwrite(temp_path, thresh)

        img = Image.open(temp_path)
        txt = pytesseract.image_to_string(img)

        lignes = [ligne.strip() for ligne in txt.split('\n') if ligne.strip()]
        data = {}

        for ligne in lignes:
            parts = re.split(r'\s+', ligne)
            if len(parts) < 2:
                continue
            nom_ocr = parts[0]
            valeurs = parts[1:]
            correction = corriger_nom_matiere(nom_ocr)
            if correction and len(valeurs) == len(colonnes):
                data[correction[0]] = valeurs

        df = pd.DataFrame.from_dict(data, orient='index', columns=colonnes)
        df = df.reindex(matieres_attendues)
        df['moy'] = pd.to_numeric(df['moy'], errors='coerce')
        matieres_faibles = df[df['moy'] < 10]

        weak_subjects = matieres_faibles.index.tolist()
        return jsonify({'low_subjects': weak_subjects})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(filepath)
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
