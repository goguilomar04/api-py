from flask import Flask, request, jsonify
import os
import easyocr
import numpy as np
import cv2

app = Flask(__name__)

# إنشاء كائن OCR يدعم اللغة الفرنسية والعربية
reader = easyocr.Reader(['fr', 'ar'])

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    os.makedirs("temp", exist_ok=True)
    filepath = os.path.join("temp", file.filename)
    file.save(filepath)

    try:
        image = cv2.imread(filepath)
        result = reader.readtext(image, detail=0)  # استخراج النصوص من الصورة (ببساطة)

        # المواد المدرسية المتوقعة
        matieres_attendues = ['Arabe', 'Math', 'Physique', 'Science', 'Islamic', 'Histoire_Geo', 'Français', 'Anglais', 'Sport']

        # استخراج المواد الضعيفة (مثال مبسط: كل المواد التي ظهرت)
        low_subjects = []
        for text in result:
            for mat in matieres_attendues:
                if mat.lower() in text.lower() and mat not in low_subjects:
                    low_subjects.append(mat)

        return jsonify({'low_subjects': low_subjects})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True)
