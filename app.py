from flask import Flask, render_template, request, session
import pytesseract
import roboflow
from werkzeug.utils import secure_filename
from flask_cors import CORS
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import easyocr
from flask import Flask, render_template, request, redirect, url_for
import easyocr
from deep_translator import GoogleTranslator
from py2neo import Graph, Node
from PIL import Image, ImageEnhance
import wikipedia
import re
import os
from flask import Flask, render_template, request, redirect, url_for, session
##from roboflow import InferenceHTTPClient
import os
from werkzeug.utils import secure_filename
from neo4j import GraphDatabase
from roboflow import Roboflow
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from neo4j import GraphDatabase
import os
from werkzeug.utils import secure_filename
from roboflow import Roboflow


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

reader = easyocr.Reader(['en'])

# Connect to Neo4j Database
graph = Graph("bolt://localhost:7687", auth=("neo4j", "the8@21052005"))
# ─── Load environment variables ────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

# ─── Upload folder setup ───────────────────────────────────────────────────────
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



# ─── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return an empty response for favicon requests

# ─── Prescription Routes ────────────────────────────────────────────────────────────────────
@app.route('/upload_prescription')
def upload_prescription():
    return render_template('upload_prescription.html')

def enhance_image(image_path):
    image = Image.open(image_path)
    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(2)  # Increase contrast
    enhanced.save(image_path)

# Get Medicine Info from Wikipedia
def get_medicine_info(medicine_name):
    try:
        summary = wikipedia.summary(medicine_name, sentences=3)
        return {
            "information": summary,
            "uses": "Refer to Wikipedia summary.",
            "side_effects": "Refer to Wikipedia summary."
        }
    except:
        return {
            "information": f"No reliable information found for {medicine_name}.",
            "uses": "Not available.",
            "side_effects": "Not available."
        }

@app.route('/process_prescription', methods=['POST'])
def process_prescription():
    if 'image' not in request.files:
        return "No file uploaded.", 400

    image = request.files['image']
    upload_path = os.path.join('static/uploads', image.filename)
    image.save(upload_path)

    enhance_image(upload_path)  # Preprocess the image

    extracted_text = pytesseract.image_to_string(Image.open(upload_path))

    translated_text = GoogleTranslator(source='auto', target='en').translate(extracted_text)

    # Extract Information
    data = {
        "patient_name": re.search(r'Patient[:\- ]*(.*)', extracted_text, re.IGNORECASE),
        "patient_age": re.search(r'Age[:\- ]*([\d]+)', extracted_text, re.IGNORECASE),
        "patient_gender": re.search(r'Gender[:\- ]*(Male|Female|Other)', extracted_text, re.IGNORECASE),
        "doctor_name": re.search(r'Dr\.?\s*(.*)', extracted_text),
        "doctor_license": re.search(r'License[:\- ]*(\S+)', extracted_text, re.IGNORECASE),
        "prescription_date": re.search(r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b', extracted_text),
        "medications": [],
        "additional_notes": []
    }

    # Clean extracted fields
    for key, match in data.items():
        if isinstance(match, re.Match):
            data[key] = match.group(1).strip()
        elif match is None and key not in ["medications", "additional_notes"]:
            data[key] = "Not available"

    # Dummy medicine extraction logic
    meds = re.findall(r'\b([A-Z][a-z]+)\b\s+(\d+mg)', extracted_text)
    for med_name, dosage in meds:
        med_info = get_medicine_info(med_name)
        data["medications"].append({
            "medication_name": med_name,
            "dosage": dosage,
            "frequency": "Not available",
            "duration": "Not available",
            "information": med_info["information"],
            "uses": med_info["uses"],
            "side_effects": med_info["side_effects"]
        })

    # Dummy additional notes
    notes = re.findall(r'Note[:\- ]*(.+)', extracted_text, re.IGNORECASE)
    if notes:
        data["additional_notes"] = [f"- {note.strip()}" for note in notes]
    else:
        data["additional_notes"] = ["- No additional instructions available."]

    # Store in Neo4j
    try:
        prescription_node = Node("Prescription",
                                 original_text=extracted_text,
                                 translated_text=translated_text,
                                 structured_data=str(data))
        graph.create(prescription_node)
        status_message = "✅ Successfully stored in the database."
    except Exception as e:
        status_message = f"❌ Failed to store in Neo4j: {e}"

    return render_template('prescription_result.html',
                           data=data,
                           status_message=status_message)
# ─── Skin Routes ──────────────────────────────────────────────────────────────────────

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Neo4j Setup
neo4j_uri = "bolt://localhost:7687"
neo4j_user = "neo4j"
neo4j_password = "the8@21052005"
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Roboflow Setup
rf = Roboflow(api_key="eNNQh2V5u1TrHzw24YMO")
project = rf.workspace().project("skin-disease-rdias")
model = project.version(1).model


# Disease Info Dictionary
skin_info = {
    "Acne": {
        "cause": "Blocked hair follicles from oil and dead skin cells.",
        "home_remedies": ["Gentle cleansing", "Tea tree oil", "Aloe vera"],
        "treatment": "Topical creams, retinoids, antibiotics if severe."
    },
    "Chickenpox": {
        "cause": "Varicella-zoster virus infection.",
        "home_remedies": ["Oatmeal baths", "Calamine lotion", "Cool compresses"],
        "treatment": "Antiviral medications and supportive care."
    },
    "Eczema": {
        "cause": "Overactive immune response to irritants.",
        "home_remedies": ["Moisturize frequently", "Avoid triggers", "Use oatmeal baths"],
        "treatment": "Steroid creams, antihistamines, avoiding allergens."
    },
    "Psoriasis": {
        "cause": "Autoimmune condition speeding up skin cell turnover.",
        "home_remedies": ["Aloe vera", "Oatmeal baths", "Coconut oil"],
        "treatment": "Topical steroids, light therapy, immunosuppressants."
    },
    "Monkeypox": {
        "cause": "Monkeypox virus (Orthopoxvirus family).",
        "home_remedies": ["Hydration", "Calamine lotion", "Rest"],
        "treatment": "Antivirals and supportive care."
    },
    "Ringworm": {
        "cause": "Fungal infection of the skin.",
        "home_remedies": ["Tea tree oil", "Apple cider vinegar", "Coconut oil"],
        "treatment": "Antifungal creams or oral antifungal medication."
    },
    "basal cell carcinoma": {
        "cause": "Excessive sun exposure damaging DNA in skin cells.",
        "home_remedies": ["None, medical attention required."],
        "treatment": "Surgical removal, topical chemotherapy, radiation."
    },
    "vitiligo": {
        "cause": "Loss of skin pigment due to autoimmune destruction of melanocytes.",
        "home_remedies": ["Protect skin from sun", "Ginger juice", "Turmeric paste"],
        "treatment": "Topical steroids, light therapy, depigmentation therapy."
    },
    "tinea-versicolor": {
        "cause": "Overgrowth of yeast on the skin.",
        "home_remedies": ["Tea tree oil", "Coconut oil", "Apple cider vinegar"],
        "treatment": "Antifungal shampoos and creams."
    },
    "warts": {
        "cause": "Human Papillomavirus (HPV) infection.",
        "home_remedies": ["Salicylic acid pads", "Duct tape method", "Banana peel rub"],
        "treatment": "Cryotherapy, laser therapy, salicylic acid treatment."
    },
    "Pimple": {
        "cause": "Blocked sebaceous glands by oil and dead skin.",
        "home_remedies": ["Warm compress", "Honey mask", "Green tea extract"],
        "treatment": "Cleansing, benzoyl peroxide, salicylic acid creams."
    },
    "Allergic Reaction": {
        "cause": "Contact with allergens (foods, plants, chemicals).",
        "home_remedies": ["Cold compress", "Aloe vera gel", "Oatmeal baths"],
        "treatment": "Antihistamines, corticosteroid creams, avoidance."
    },
    "Mild Skin Rash (Non-specific)": {
        "cause": "Heat, friction, or temporary skin irritation.",
        "home_remedies": ["Cool compress", "Aloe vera", "Oatmeal bath"],
        "treatment": "Usually resolves on its own, moisturizing helps."
    },
    "Other Causes": {
        "cause": "Could be a rare skin condition or unknown issue.",
        "home_remedies": ["Hydrate, avoid irritants", "Use mild moisturizers"],
        "treatment": "Consult a dermatologist for accurate diagnosis."
    }
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def classify_skin_condition(prediction_label, confidence):
    threshold = 0.45  # Confidence cutoff
    if confidence < threshold:
        if "rash" in prediction_label.lower():
            fallback_label = "Mild Skin Rash (Non-specific)"
        elif "allergy" in prediction_label.lower():
            fallback_label = "Allergic Reaction"
        else:
            fallback_label = "Other Causes"
    else:
        fallback_label = prediction_label
    info = skin_info.get(fallback_label, skin_info["Other Causes"])
    return fallback_label, info

@app.route('/skin_upload')
def skin_upload():
    return render_template('skin_upload.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        session['image'] = filename
        return redirect(url_for('questions'))
    return 'File not allowed', 400

@app.route('/questions', methods=['GET', 'POST'])
def questions():
    if request.method == 'POST':
        answers = {
            'pain': request.form.get('pain'),
            'itchy': request.form.get('itchy'),
            'rash_type': request.form.get('rash_type'),
            'duration': request.form.get('duration'),
            'fever': request.form.get('fever'),
            'allergen_contact': request.form.get('allergen_contact'),
            'skin_type': request.form.get('skin_type'),
            'previous_conditions': request.form.get('previous_conditions'),
            'sun_exposure': request.form.get('sun_exposure'),
            'skincare_products': request.form.get('skincare_products'),
            'medication': request.form.get('medication')
        }
        session['answers'] = answers

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], session['image'])
        result = model.predict(image_path).json()

        if result['predictions']:
            raw_label = result['predictions'][0]['class']
            confidence = result['predictions'][0]['confidence']
        else:
            raw_label = "Other Causes"
            confidence = 0.0

        label, info = classify_skin_condition(raw_label, confidence)

        save_to_neo4j(session['image'], answers, label)

        return render_template('skin_result.html', predicted_condition=label, info=info, confidence=confidence)
    return render_template('skin_questions.html')

def save_to_neo4j(filename, answers, predicted_condition):
    with driver.session() as db_session:
        query = """
        MERGE (s:SkinCondition {image: $filename})
        SET s += $answers,
            s.predicted_condition = $predicted_condition
        """
        db_session.run(query, filename=filename, answers=answers, predicted_condition=predicted_condition)



# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5050)
