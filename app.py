import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_file, make_response, flash
from werkzeug.utils import secure_filename
from weasyprint import HTML

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Config
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

DB_NAME = 'resumes.db'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            summary TEXT,
            education TEXT,
            experience TEXT,
            skills TEXT,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    summary = request.form.get('summary')
    education = request.form.get('education')
    experience = request.form.get('experience')
    skills = request.form.get('skills')

    # Handle image upload
    image_file = request.files.get('image')
    image_filename = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_filename = filename

    # Save to DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO resumes (name, email, phone, summary, education, experience, skills, image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, summary, education, experience, skills, image_filename))
    conn.commit()
    resume_id = c.lastrowid
    conn.close()

    flash('Resume saved! You can download the PDF now.')
    return redirect(url_for('download_pdf', resume_id=resume_id))

@app.route('/download/<int:resume_id>')
def download_pdf(resume_id):
    # Fetch resume from DB
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM resumes WHERE id = ?', (resume_id,))
    resume = c.fetchone()
    conn.close()

    if not resume:
        return "Resume not found", 404

    # Render HTML template with resume data
    rendered = render_template('resume_template.html', resume=resume)

    # Generate PDF with WeasyPrint
    pdf = HTML(string=rendered, base_url=request.base_url).write_pdf()

    # Send PDF file as response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={resume["name"]}_resume.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
