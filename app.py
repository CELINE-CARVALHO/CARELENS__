from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import uuid
import pytesseract
from PIL import Image
import re
from datetime import datetime
from neo4j import GraphDatabase, basic_auth
from neo4j import GraphDatabase
import torch
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import os
from flask import Flask, render_template, request, redirect, url_for, session

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

import os
app.secret_key = os.urandom(24)
# Upload folder setup
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Configure Neo4j
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "the8@21052005")
driver = GraphDatabase.driver(neo4j_uri, auth=basic_auth(neo4j_user, neo4j_password))


# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def store_prescription_data(data):
    try:
        with driver.session() as session:
            query = """
                CREATE (p:Prescription {
                    PrescriptionID: $PrescriptionID,
                    OriginalText: $OriginalText,
                    TranslatedText: $TranslatedText
                })
            """
            session.run(query, data)
        return True
    except Exception as e:
        print("Error storing data in Neo4j:", e)
        return False


def ocr_prescription(filepath):
    try:
        image = Image.open(filepath)
        raw_text = pytesseract.image_to_string(image)
        return parse_prescription(raw_text)
    except Exception as e:
        return {"error": str(e)}


def parse_prescription(raw_text):
    data = {
        "patient_name": "Not available",
        "patient_age": "Not available",
        "patient_gender": "Not available",
        "doctor_name": "Not available",
        "doctor_license": "Not available",
        "prescription_date": "Not available",
        "medications": [],
        "notes": []
    }

    lines = raw_text.split('\n')
    for line in lines:
        clean_line = line.strip()

        if re.search(r'\bPatient\b', clean_line, re.IGNORECASE):
            data['patient_name'] = re.sub(r'Patient[:\s]*', '', clean_line, flags=re.IGNORECASE).strip()

        age_match = re.search(r'(\d+)\s*(?:y|yrs|years)?', clean_line, re.IGNORECASE)
        if age_match:
            data['patient_age'] = age_match.group(1)

        gender_match = re.search(r'\b(Male|Female|Other)\b', clean_line, re.IGNORECASE)
        if gender_match:
            data['patient_gender'] = gender_match.group(1).capitalize()

        if re.search(r'\bDoctor\b', clean_line, re.IGNORECASE):
            data['doctor_name'] = re.sub(r'Doctor[:\s]*', '', clean_line, flags=re.IGNORECASE).strip()

        if re.search(r'License\s*No[:\s]*', clean_line, re.IGNORECASE):
            data['doctor_license'] = re.sub(r'License\s*No[:\s]*', '', clean_line, flags=re.IGNORECASE).strip()

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', clean_line)
        if date_match:
            try:
                datetime.strptime(date_match.group(1), '%Y-%m-%d')
                data['prescription_date'] = date_match.group(1)
            except ValueError:
                pass

        if any(keyword in clean_line.lower() for keyword in ["mg", "tablet", "capsule"]):
            med_parts = re.split(r',|;', clean_line)
            med_data = {
                "name": med_parts[0].strip() if len(med_parts) > 0 else "Unknown",
                "dosage": med_parts[1].strip() if len(med_parts) > 1 else "Unknown",
                "frequency": med_parts[2].strip() if len(med_parts) > 2 else "Unknown",
                "duration": med_parts[3].strip() if len(med_parts) > 3 else "Unknown",
                "information": med_parts[4].strip() if len(med_parts) > 4 else "Unknown",
                "uses": med_parts[5].strip() if len(med_parts) > 5 else "Unknown",
                "side_effects": med_parts[6].strip() if len(med_parts) > 6 else "Unknown"
            }
            data['medications'].append(med_data)
        elif clean_line and not any(keyword in clean_line.lower() for keyword in ['patient', 'doctor', 'license', 'mg', 'tablet', 'capsule', 'date']):
            data['notes'].append(f"- {clean_line}")

    return data


# Routes
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            extracted_data = ocr_prescription(filepath)
            prescription_id = str(uuid.uuid4())
            
            # Store extracted data in Neo4j
            store_prescription_data({
                "PrescriptionID": prescription_id,
                "OriginalText": extracted_data.get("raw_text", ""),
                "TranslatedText": extracted_data.get("translated_text", "")
            })
            
            # Redirect to the result page with the extracted data
            return redirect(url_for('result_page', 
                                    prescription_id=prescription_id,
                                    patient_name=extracted_data['patient_name'],
                                    patient_age=extracted_data['patient_age'],
                                    patient_gender=extracted_data['patient_gender'],
                                    prescription_date=extracted_data['prescription_date']))
        except Exception as e:
            return jsonify({'error': 'Error processing the image', 'details': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg, gif, bmp'}), 400


@app.route('/result/<prescription_id>', methods=['GET'])
def result_page(prescription_id):
    # Get the data from the URL query parameters
    patient_name = request.args.get('patient_name', 'Not Available')
    patient_age = request.args.get('patient_age', 'Not Available')
    patient_gender = request.args.get('patient_gender', 'Not Available')
    prescription_date = request.args.get('prescription_date', 'Not Available')

    data = {
        'PrescriptionID': prescription_id,
        'patient_name': patient_name,
        'patient_age': patient_age,
        'patient_gender': patient_gender,
        'prescription_date': prescription_date,
        'medicines': [],  # Populate with actual medicines data if available
        'diagnosis': ''   # Replace with actual diagnosis if available
    }
    return render_template('result.html', data=data)


# Model
model_name = "google/vit-base-patch16-224"
model = ViTForImageClassification.from_pretrained(model_name)
processor = ViTImageProcessor.from_pretrained(model_name)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

def predict_condition(image_path):
    image = Image.open(image_path).convert('RGB')
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = logits.argmax(-1).item()
    predicted_class = model.config.id2label[str(predicted_class_idx)]
    return predicted_class

def save_to_neo4j(image_name, disease, answers=None):
    with driver.session() as session:
        session.run("""
            CREATE (r:Result {image: $image, disease: $disease, answers: $answers})
        """, image=image_name, disease=disease, answers=str(answers) if answers else "")

@app.route('/')
def upload_page():
    return render_template('skin_upload.html')

@app.route('/skin_upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        prediction = predict_condition(filepath)

        session['image_name'] = file.filename
        session['prediction'] = prediction

        save_to_neo4j(file.filename, prediction)  # Store initial prediction
        return redirect(url_for('skin_questions'))
    return 'No image uploaded.'

@app.route('/skin_questions', methods=['GET', 'POST'])
def questions_page():
    if request.method == 'POST':
        answers = request.form.to_dict()
        save_to_neo4j(session['image_name'], session['prediction'], answers)
        return redirect(url_for('result_page'))
    return render_template('skin_questions')

@app.route('/skin_result')
def skin_result():
    return render_template('skin_result.html', prediction=session.get('prediction'))






if __name__ == '__main__':
    app.run(debug=True, port=5050)
