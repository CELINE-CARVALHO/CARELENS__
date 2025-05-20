from pyexpat import model
import bcrypt
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
from neo4j import GraphDatabase
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, session
from flask import Flask, render_template, request
from PIL import Image, ImageEnhance
import pytesseract
import os
import re
import wikipedia
from py2neo import Graph, Node
import nltk
nltk.download('punkt')

# Translation dependencies
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from aimped.nlp.translation import text_translate
import torch
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
from transformers import AutoProcessor, AutoModelForImageClassification
from PIL import Image
import torch
from neo4j import GraphDatabase
import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageClassification
from neo4j import GraphDatabase
from inference_sdk import InferenceHTTPClient
from PIL import Image
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session



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

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Logged out successfully"}), 200

NEO4J_URI = "bolt://localhost:7687"  # Or your connection string
NEO4J_USER = "neo4j"                 # Default username
NEO4J_PASSWORD = "the8@21052005"     # Your password

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ---------- Combined Login Route ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST login logic:
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error':'Both fields are required'}),400

    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {email:$email}) RETURN u.password AS pw", email=email
        )
        record = result.single()
        if record and bcrypt.checkpw(password.encode(), record['pw'].encode()):
            return jsonify({'message':'Login successful!'}),200

    return jsonify({'error':'Invalid credentials'}),401

# ---------- Signup Routes (GET & POST) ----------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    # POST signup logic:
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not name or not email or not password:
        return jsonify({'error':'All fields are required'}),400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with driver.session() as session:
        exists = session.run(
            "MATCH(u:User{email:$email}) RETURN u", email=email
        ).single()
        if exists:
            return jsonify({'error':'Email already registered'}),409

        session.run(
            "CREATE(:User{name:$name,email:$email,password:$pw})",
            name=name,email=email,pw=hashed
        )
    return jsonify({'message':'User registered successfully!'}),201




# ─── Prescription Routes ────────────────────────────────────────────────────────────────────
from inference_sdk import InferenceHTTPClient  # Roboflow

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="eNNQh2V5u1TrHzw24YMO"
)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Connect to Neo4j
graph = Graph("bolt://localhost:7687", auth=("neo4j", "the8@21052005"))  # Change credentials

# Enhance image contrast
def enhance_image(image_path):
    image = Image.open(image_path)
    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(2)
    enhanced.save(image_path)

# Get medicine info from Wikipedia
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

# API endpoint for processing prescription
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

    for key, match in data.items():
        if isinstance(match, re.Match):
            data[key] = match.group(1).strip()
        elif match is None and key not in ["medications", "additional_notes"]:
            data[key] = "Not available"

    # Medicine extraction (basic & table format)
    added_meds = set()
    lines = extracted_text.splitlines()

    for line in lines:
        med_match = re.search(r'([A-Z][a-zA-Z\s]+)\s+(\d+\s*(?:mg|ml|g|mcg|%))', line)
        if med_match:
            med_name = med_match.group(1).strip()
            dosage = med_match.group(2).strip()
            frequency_match = re.search(r'\b(once|twice|thrice|\d+\s*(times)?\s*(a|per)?\s*(day|week))\b', line, re.IGNORECASE)
            duration_match = re.search(r'\b(for\s+)?(\d+\s*(days?|weeks?|months?))\b', line, re.IGNORECASE)
            frequency = frequency_match.group().strip() if frequency_match else "Not available"
            duration = duration_match.group(2).strip() if duration_match else "Not available"

            if med_name.lower() not in added_meds:
                med_info = get_medicine_info(med_name)
                data["medications"].append({
                    "medication_name": med_name,
                    "dosage": dosage,
                    "frequency": frequency,
                    "duration": duration,
                    "information": med_info["information"],
                    "uses": med_info["uses"],
                    "side_effects": med_info["side_effects"]
                })
                added_meds.add(med_name.lower())

    # Enhanced note detection
    note_patterns = [
        r'Note[:\- ]*(.+)',
        r'Instructions[:\- ]*(.+)',
        r'Advice[:\- ]*(.+)',
        r'Remarks[:\- ]*(.+)',
        r'Additional Info[:\- ]*(.+)'
    ]
    notes = []
    for pattern in note_patterns:
        found = re.findall(pattern, extracted_text, re.IGNORECASE)
        notes.extend(found)

    if notes:
        data["additional_notes"] = [f"- {note.strip()}" for note in notes if note.strip()]
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


# For basic HTML upload view (optional)
@app.route('/upload_prescription')
def upload_prescription():
    return render_template('upload_prescription.html')




# ─── Skin Routes ──────────────────────────────────────────────────────────────────────

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Neo4j Setup
neo4j_uri = "bolt://localhost:7687"
neo4j_user = "neo4j"
neo4j_password = "the8@21052005"
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

from inference_sdk import InferenceHTTPClient

rf = Roboflow(api_key="eNNQh2V5u1TrHzw24YMO")
project = rf.workspace().project("skin-disease-identification-ae3yb")
model = project.version(4).model

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

        if 'predictions' in result and result['predictions']:
            prediction = result['predictions'][0]
            raw_label = prediction.get('class', 'Other Causes')  # Use default if 'class' is missing
            confidence = prediction.get('confidence', 0.0)  # Default confidence if missing
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
@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    with driver.session() as session:
        session.run("""
            CREATE (m:Message {
                name: $name,
                email: $email,
                message: $message,
                submittedAt: datetime()
            })
        """, name=name, email=email, message=message)

    return jsonify({"message": "Thanks for contacting us! We'll get back to you shortly."})

def save_collaboration(tx, name, email, org, org_type, message):
    tx.run("""
        CREATE (c:Collaboration {
            name: $name,
            email: $email,
            organization: $org,
            type: $org_type,
            message: $message,
            timestamp: timestamp()
        })
    """, name=name, email=email, org=org, org_type=org_type, message=message)

def save_collaboration(tx, name, email, organization, org_type, message):
    timestamp = datetime.utcnow().isoformat()
    tx.run(
        """
        CREATE (c:Collaboration {
            name: $name,
            email: $email,
            organization: $organization,
            type: $org_type,
            message: $message,
            timestamp: $timestamp
        })
        """,
        name=name,
        email=email,
        organization=organization,
        org_type=org_type,
        message=message,
        timestamp=timestamp
    )

@app.route("/collaboration")
def collaboration():
    return render_template("collaboration.html")

@app.route('/api/collaborate', methods=['POST'])
def add_collaboration():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    organization = data.get("organization")
    org_type = data.get("type")
    message = data.get("message", "")

    if not all([name, email, organization, org_type]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        with driver.session() as session:
            session.write_transaction(save_collaboration, name, email, organization, org_type, message)
        return jsonify({"message": "Collaboration saved successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/collaborate', methods=['GET'])
def get_collaborations():
    try:
        with driver.session() as session:
            result = session.run("MATCH (c:Collaboration) RETURN c ORDER BY c.timestamp DESC")
            data = []
            for record in result:
                node = record["c"]
                data.append({
                    "name": node.get("name"),
                    "email": node.get("email"),
                    "organization": node.get("organization"),
                    "type": node.get("type"),
                    "message": node.get("message"),
                    "timestamp": node.get("timestamp")
                })
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5050)
