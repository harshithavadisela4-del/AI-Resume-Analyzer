from flask import Flask, render_template, request, jsonify
import os
import spacy
from PyPDF2 import PdfReader
import docx

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load spaCy English NLP model
nlp = spacy.load('en_core_web_sm')

# --- Function to extract text from PDF ---
def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, 'rb') as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# --- Function to extract text from DOCX ---
def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([p.text for p in doc.paragraphs])

# --- Compare two texts and calculate match ---
def calculate_similarity(resume_text, job_text):
    doc1 = nlp(resume_text)
    doc2 = nlp(job_text)
    similarity = doc1.similarity(doc2)
    return round(similarity * 100, 2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    file = request.files['resume']
    job_desc = request.form['jobDesc']

    if not file:
        return jsonify({'error': 'No file uploaded'})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Extract text based on file type
    if file.filename.endswith('.pdf'):
        resume_text = extract_text_from_pdf(filepath)
    elif file.filename.endswith('.docx'):
        resume_text = extract_text_from_docx(filepath)
    else:
        return jsonify({'error': 'Unsupported file format. Upload PDF or DOCX.'})

    # Calculate match score
    score = calculate_similarity(resume_text, job_desc)

    # --- Simple keyword extraction for missing skills ---
    job_keywords = [token.text.lower() for token in nlp(job_desc) if token.is_alpha]
    resume_keywords = [token.text.lower() for token in nlp(resume_text) if token.is_alpha]
    missing = [word for word in job_keywords if word not in resume_keywords]

    return jsonify({
        'score': score,
        'missingSkills': list(set(missing))[:10],  # Show top 10
        'suggestions': 'Try adding these missing keywords to your resume.'
    })

if __name__ == '__main__':
    app.run(debug=True)
