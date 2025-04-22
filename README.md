# 🩺 CareLens — Healthcare Assistant

CareLens is a Flask-based healthcare web application designed to assist users in understanding medical prescriptions and skin-related conditions. It uses Optical Character Recognition (OCR), Machine Learning, Neo4j, Wikipedia scraping, and Roboflow-powered models to deliver clear medical insights.

---

## 🚀 Features

- **Prescription Analysis**
  - Upload prescription images.
  - Automatic text extraction using `pytesseract` and `easyocr`.
  - Medicine information fetched via Wikipedia.
  - Automatic translation to English using Google Translate.
  - Prescription storage in Neo4j.

- **Skin Condition Detection**
  - Upload skin images.
  - Deep learning model prediction via Roboflow.
  - Dynamic follow-up questions for improved accuracy.
  - Outputs cause, home remedies, and medical treatment advice.
  - Records stored in Neo4j for future use.

---

## 🧑‍💻 Technologies Used

- **Backend:** Python, Flask  
- **OCR:** Tesseract, EasyOCR  
- **Machine Learning:** Roboflow API  
- **Database:** Neo4j Graph Database  
- **Translation:** Google Translator (via `deep-translator`)  
- **Wikipedia Scraper:** `wikipedia` Python module  
- **Image Preprocessing:** Pillow (`PIL`)  
- **Web:** HTML, CSS (Jinja templates)  

---

## ⚙️ Setup Instructions

1️⃣ **Clone the repository:**

```bash
git clone https://github.com/yourusername/carelens.git](https://github.com/CELINE-CARVALHO/CARELENS__.git
cd carelens
```

2️⃣ **Install Dependencies:**

```bash
pip install -r requirements.txt
```

3️⃣ **Configure Environment Variables:**

Create a `.env` file:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
ROBOFLOW_API_KEY=your_roboflow_api_key
```

4️⃣ **Tesseract OCR Setup:**

Make sure Tesseract is installed and its path is set in your code:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

5️⃣ **Run the Application:**

```bash
python app.py
```
Visit: `http://localhost:5050` in your browser.

---

## 💡 Project Structure

```
carelens/
│
├── static/
│   └── uploads/          # Uploaded files go here
│
├── templates/
│   ├── index.html
│   ├── upload_prescription.html
│   ├── prescription_result.html
│   ├── skin_upload.html
│   ├── skin_questions.html
│   └── skin_result.html
│
├── app.py                # Main application script
├── requirements.txt
└── README.md
```

---

## 🧪 Example Use Case

1. Upload a prescription or a skin image.
2. The system:
   - Extracts text or classifies the image.
   - Offers relevant health advice.
   - Stores the result in Neo4j for traceability.

---

## 🧑‍⚕️ Future Improvements

- Add real-time symptom chatbots.
- Integrate multilingual support for non-English prescriptions.
- Connect to healthcare APIs for verified treatment advice.
- User authentication and history retrieval.

---

## 📢 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)  
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)  
- [Roboflow](https://roboflow.com/)  
- [Neo4j Graph Database](https://neo4j.com/)  
- [Deep Translator](https://pypi.org/project/deep-translator/)  
- [Wikipedia API](https://pypi.org/project/wikipedia/)

---

## 👩‍💻 Author

**Celine**  
Passionate about combining healthcare and AI to deliver real-world solutions.

---

## 📬 License

This project is for academic, research, and non-commercial use only.  
For commercial licensing, please contact **Celine**.
