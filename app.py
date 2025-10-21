from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey'

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['BiasZero']
users = db['Login']
resumes = db['sessionResumes']
job_descriptions = db['job_descriptions']

# ---------- Helper Parsers ----------
def parse_education_entries(form):
    entries = []
    total = int(form.get('edu_count', 0))
    for i in range(total):
        entries.append({
            "degree": form.get(f'edu_degree_{i}'),
            "university": form.get(f'edu_university_{i}'),
            "year": form.get(f'edu_year_{i}'),
            "grade": form.get(f'edu_grade_{i}')
        })
    return entries

def parse_experience_entries(form):
    entries = []
    total = int(form.get('exp_count', 0))
    for i in range(total):
        entries.append({
            "job_title": form.get(f'exp_job_{i}'),
            "company": form.get(f'exp_company_{i}'),
            "start_date": form.get(f'exp_start_{i}'),
            "end_date": form.get(f'exp_end_{i}'),
            "years_of_experience": form.get(f'exp_years_{i}'),
            "description": form.get(f'exp_desc_{i}')
        })
    return entries

def parse_project_entries(form):
    entries = []
    total = int(form.get('proj_count', 0))
    for i in range(total):
        entries.append({
            "title": form.get(f'proj_title_{i}'),
            "description": form.get(f'proj_desc_{i}'),
            "technologies": form.get(f'proj_tech_{i}', '').split(','),
            "year": form.get(f'proj_year_{i}')
        })
    return entries

def parse_certification_entries(form):
    entries = []
    total = int(form.get('cert_count', 0))
    for i in range(total):
        entries.append({
            "name": form.get(f'cert_name_{i}'),
            "issuer": form.get(f'cert_issuer_{i}'),
            "year": form.get(f'cert_year_{i}')
        })
    return entries

# ---------- Routes ----------

@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    """Handles registration — no separate register.html"""
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('RegisterRole', 'User')

    if not email or not password or not role:
        flash('Please fill in all required fields', 'danger')
        return render_template('Login.html')

    existing_user = users.find_one({'email': email})
    if existing_user:
        flash('Email already registered. Please log in.', 'warning')
        return render_template('Login.html')

    hashed_pw = generate_password_hash(password)
    users.insert_one({
        'name': name,
        'email': email,
        'password': hashed_pw,
        'role': role,
        'created_at': datetime.utcnow()
    })

    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles login logic and role-based redirection"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('LoginRole')

        user = users.find_one({'email': email})
        if user and check_password_hash(user.get('password', ''), password):
            session['user_id'] = str(user['_id'])
            session['user_role'] = user.get('role', 'User')

            # Check role for routing
            if user.get('role') == 'Company' and role == 'Company':
                return redirect(url_for('job_desc'))
            elif user.get('role') == 'User' and role == 'User':
                existing_profile = resumes.find_one({'user_id': session['user_id']})
                if existing_profile:
                    return redirect(url_for('profile', mode='view'))
                else:
                    return redirect(url_for('profile', mode='create'))
            else:
                flash('Invalid role selected for this account.', 'danger')
                return render_template('Login.html')

        flash('Invalid credentials. Try again.', 'danger')
        return render_template('Login.html')

    return render_template('Login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mode = request.args.get('mode', 'view')
    user_id = session['user_id']
    resume = resumes.find_one({'user_id': user_id})
    return render_template('profile.html', resume=resume, mode=mode)

@app.route('/submit_resume', methods=['POST'])
def submit_resume():
    """Handles resume submissions"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    data = {
        "user_id": user_id,
        "personal_info": {
            "name": request.form.get('name'),
            "age": int(request.form.get('age')) if request.form.get('age', '').isdigit() else None,
            "gender": request.form.get('gender'),
            "location": request.form.get('location'),
            "contact_email": request.form.get('email'),
            "contact_phone": request.form.get('phone')
        },
        "education": {"entries": parse_education_entries(request.form)},
        "experience": {"entries": parse_experience_entries(request.form)},
        "projects": {"entries": parse_project_entries(request.form)},
        "certifications": {"entries": parse_certification_entries(request.form)},
        "skills": {
            "technical": [s.strip() for s in request.form.get('technical_skills', '').split(',') if s.strip()],
            "soft": [s.strip() for s in request.form.get('soft_skills', '').split(',') if s.strip()]
        },
        "updated_at": datetime.utcnow()
    }

    existing_resume = resumes.find_one({'user_id': user_id})
    if existing_resume:
        resumes.update_one({'user_id': user_id}, {'$set': data})
    else:
        resumes.insert_one(data)
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile', mode='view'))

@app.route('/job_desc', methods=['GET'])
def job_desc():
    """Company job posting page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_role') != 'Company':
        flash('Access denied: only companies can post job descriptions.', 'danger')
        return redirect(url_for('profile', mode='view'))
    return render_template('job_desc.html')

@app.route('/submit_job', methods=['POST'])
def submit_job():
    """Handles job description submissions"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_role') != 'Company':
        flash('Access denied.', 'danger')
        return redirect(url_for('profile', mode='view'))

    data = {
        "company_name": request.form.get('company_name'),
        "position": request.form.get('position'),
        "location": request.form.get('location'),
        "employment_type": request.form.get('employment_type'),
        "job_description": request.form.get('job_description'),
        "submitted_by": session['user_id'],
        "created_at": datetime.utcnow()
    }

    job_descriptions.insert_one(data)
    flash('Job description submitted successfully!', 'success')
    return redirect(url_for('job_desc'))

if __name__ == '__main__':
    app.run(debug=True)
