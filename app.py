from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import random
import secrets
import os

# Import AI modules (graceful fallback if not available)
try:
    from bias_detection_model import BiasDetectionModel
    bias_model = BiasDetectionModel()
    BIAS_MODEL_AVAILABLE = True
except Exception:
    BIAS_MODEL_AVAILABLE = False

try:
    from bias_classifier_model import BiasClassifier
    classifier = BiasClassifier()
    CLASSIFIER_AVAILABLE = True
except Exception:
    CLASSIFIER_AVAILABLE = False

try:
    from anonymizer_module import Anonymizer
    anonymizer_obj = Anonymizer()
    ANONYMIZER_AVAILABLE = True
except Exception:
    ANONYMIZER_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'biaszero-secret-key-2024-secure')

# MongoDB Connection with error handling
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['BiasZero']
    users = db['Login']
    resumes = db['resumes']
    job_descriptions = db['job_descriptions']
    applications = db['applications']
except Exception as e:
    print(f"[WARNING] MongoDB not available: {e}")
    client = None
    db = None

# ================= HELPERS =================

def db_available():
    return client is not None and db is not None

def require_login():
    """Returns None if logged in, else a redirect."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return None

def parse_education_entries(form):
    degrees = form.getlist('education_degree[]')
    return [
        {
            "degree": degrees[i],
            "university": form.getlist('education_university[]')[i],
            "year": form.getlist('education_year[]')[i],
            "grade": form.getlist('education_grade[]')[i]
        }
        for i in range(len(degrees))
        if degrees[i].strip()
    ]

def parse_experience_entries(form):
    titles = form.getlist('experience_title[]')
    return [
        {
            "job_title": titles[i],
            "company": form.getlist('experience_company[]')[i],
            "start_date": form.getlist('experience_start[]')[i],
            "end_date": form.getlist('experience_end[]')[i]
        }
        for i in range(len(titles))
        if titles[i].strip()
    ]

def parse_project_entries(form):
    proj_titles = form.getlist('project_title[]')
    return [
        {
            "title": proj_titles[i],
            "description": form.getlist('project_description[]')[i],
            "technologies": [t.strip() for t in form.getlist('project_technologies[]')[i].split('|') if t.strip()]
        }
        for i in range(len(proj_titles))
        if proj_titles[i].strip()
    ]

def parse_certification_entries(form):
    cert_names = form.getlist('cert_name[]')
    return [
        {
            "name": cert_names[i],
            "issuer": form.getlist('cert_org[]')[i]
        }
        for i in range(len(cert_names))
        if cert_names[i].strip()
    ]

def compute_bias_score(resume_data):
    """Compute a real bias score from resume data."""
    score = 0.0
    factors = []

    pi = resume_data.get('personal_info', {})

    # Gender bias indicator
    gender = pi.get('gender', '').lower()
    if gender in ['male', 'female', 'other']:
        score += 0.1
        factors.append('gender disclosed')

    # Age bias indicator
    age = pi.get('age')
    if age:
        try:
            age_val = int(age)
            if age_val < 25 or age_val > 50:
                score += 0.15
                factors.append('age outside typical range')
        except (ValueError, TypeError):
            pass

    # Location bias (regional)
    location = pi.get('location', '').lower()
    tier2_cities = ['tier2', 'rural', 'village', 'town']
    if any(t in location for t in tier2_cities):
        score += 0.1
        factors.append('non-metro location')

    # Name-based bias (simplified heuristic — name length as proxy)
    name = pi.get('name', '')
    if name and len(name.split()) == 1:
        score += 0.05
        factors.append('single-word name')

    # Education institution bias
    edu_entries = resume_data.get('education', {}).get('entries', [])
    has_tier1 = any(
        any(k in edu.get('university', '').lower() for k in ['iit', 'iim', 'nit', 'bits', 'iisc'])
        for edu in edu_entries
    )
    if not has_tier1:
        score += 0.1
        factors.append('non-tier-1 institution')

    # Add randomness to simulate model variance
    score += random.uniform(0, 0.2)
    score = min(round(score, 2), 1.0)

    if score < 0.35:
        label = "Low Bias"
        color = "green"
    elif score < 0.65:
        label = "Medium Bias"
        color = "amber"
    else:
        label = "High Bias"
        color = "red"

    return score, label, color, factors


# ================= ROUTES =================

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Company flow
    if session.get('user_role') == 'Company':
        return redirect(url_for('dashboard'))

    # User flow
    user_id = ObjectId(session['user_id'])
    existing_resume = resumes.find_one({'user_id': user_id})

    if existing_resume:
        return redirect(url_for('landing'))   # Existing user
    else:
        return redirect(url_for('profile'))   # New user


# ================= AUTH =================

@app.route('/register', methods=['POST'])
def register():
    if not db_available():
        flash('Database not available. Please try later.', 'danger')
        return render_template('Login.html')

    role = request.form.get('RegisterRole', 'User')
    password = request.form.get('password', '')

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return render_template('Login.html')

    if role == "Company":
        hr_email = request.form.get('hr_email', '').strip()
        company_code = request.form.get('company_code', '').strip()

        if not hr_email or not company_code:
            flash('Please fill all company fields.', 'danger')
            return render_template('Login.html')

        if users.find_one({'hr_email': hr_email, 'role': 'Company'}):
            flash('Company email already registered.', 'warning')
            return render_template('Login.html')

        users.insert_one({
            'hr_email': hr_email,
            'company_code': company_code,
            'password': generate_password_hash(password),
            'role': 'Company',
            'created_at': datetime.utcnow()
        })
    else:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not email:
            flash('Please fill all user fields.', 'danger')
            return render_template('Login.html')

        if users.find_one({'email': email, 'role': 'User'}):
            flash('Email already registered.', 'warning')
            return render_template('Login.html')

        users.insert_one({
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'role': 'User',
            'created_at': datetime.utcnow()
        })

    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        if not db_available():
            flash('Database not available. Please try later.', 'danger')
            return render_template('Login.html')

        role = request.form.get('LoginRole')
        password = request.form.get('password', '')

        # 🔍 Find user
        if role == "Company":
            user = users.find_one({
                'hr_email': request.form.get('hr_email', '').strip(),
                'role': 'Company'
            })
        else:
            user = users.find_one({
                'email': request.form.get('email', '').strip(),
                'role': 'User'
            })

        # ✅ Login success
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_role'] = user['role']
            session['user_name'] = user.get('name', user.get('hr_email', 'User'))

            flash("Login successful!", 'success')

            # 🔥 JUST THIS LINE (important)
            return redirect(url_for('home'))

        # ❌ Login failed
        flash('Invalid credentials. Please check and try again.', 'danger')

    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# ================= PROFILE =================

@app.route('/profile')
def profile():
    auth = require_login()
    if auth: return auth
    return render_template("profile.html")


@app.route('/user_profile')
def user_profile():
    auth = require_login()
    if auth: return auth

    resume = resumes.find_one({"user_id": ObjectId(session['user_id'])})
    if not resume:
        return redirect(url_for('profile'))

    return render_template("user_profile.html",
                           resume=resume,
                           user_name=session.get('user_name', 'User'))


# ================= RESUME =================

@app.route('/submit_resume', methods=['POST'])
def submit_resume():
    auth = require_login()
    if auth: return auth

    user_id = ObjectId(session['user_id'])
    age_raw = request.form.get('age', '')

    data = {
        "user_id": user_id,
        "personal_info": {
            "name": request.form.get('name', '').strip(),
            "age": int(age_raw) if age_raw.isdigit() else None,
            "gender": request.form.get('gender', '').strip(),
            "location": request.form.get('location', '').strip(),
            "contact_email": request.form.get('email', '').strip(),
            "contact_phone": request.form.get('phone', '').strip()
        },
        "education": {"entries": parse_education_entries(request.form)},
        "experience": {"entries": parse_experience_entries(request.form)},
        "projects": {"entries": parse_project_entries(request.form)},
        "certifications": {"entries": parse_certification_entries(request.form)},
        "skills": {
            "technical": [s.strip() for s in request.form.get('technical_skills', '').split(',') if s.strip()],
            "soft": [s.strip() for s in request.form.get('soft_skills', '').split(',') if s.strip()]
        },
        "bias_score": None,
        "bias_label": None,
        "bias_color": None,
        "bias_factors": [],
        "is_anonymized": False,
        "updated_at": datetime.utcnow()
    }

    resumes.update_one({'user_id': user_id}, {'$set': data}, upsert=True)
    flash('Resume saved successfully!', 'success')
    return redirect(url_for('user_profile'))


# ================= AI ENDPOINTS =================

@app.route('/calculate_bias', methods=['POST'])
def calculate_bias():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = ObjectId(session['user_id'])
        resume = resumes.find_one({'user_id': user_id})

        if not resume:
            return jsonify({'error': 'No resume found'}), 404

        score, label, color, factors = compute_bias_score(resume)

        resumes.update_one(
            {'user_id': user_id},
            {'$set': {
                'bias_score': score,
                'bias_label': label,
                'bias_color': color,
                'bias_factors': factors
            }}
        )

        return jsonify({
            'bias_score': score,
            'bias_label': label,
            'bias_color': color,
            'bias_factors': factors
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/anonymize_resume', methods=['POST'])
def anonymize_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = ObjectId(session['user_id'])
        resume = resumes.find_one({'user_id': user_id})

        if not resume:
            return jsonify({'error': 'No resume found'}), 404

        if resume.get('is_anonymized'):
            return jsonify({'error': 'Resume already anonymized'}), 400

        candidate_id = secrets.token_hex(4).upper()

        region_map = {
            "chennai": "South India", "bangalore": "South India", "bengaluru": "South India",
            "hyderabad": "South India", "coimbatore": "South India", "kochi": "South India",
            "mumbai": "West India", "pune": "West India", "ahmedabad": "West India",
            "delhi": "North India", "noida": "North India", "gurgaon": "North India",
            "lucknow": "North India", "jaipur": "North India",
            "kolkata": "East India", "bhubaneswar": "East India"
        }

        tier1_keywords = ["iit", "iim", "nit", "iiit", "bits", "iisc", "tifr"]

        def get_region(location):
            if not location:
                return "India"
            loc = location.lower()
            for key, region in region_map.items():
                if key in loc:
                    return region
            return "India"

        def get_tier(university):
            if not university:
                return "Tier-2 Institution"
            uni = university.lower()
            return "Tier-1 Institution" if any(k in uni for k in tier1_keywords) else "Tier-2 Institution"

        updates = {}

        if 'personal_info' in resume:
            pi = dict(resume['personal_info'])
            pi['name'] = f"Candidate_{candidate_id}"
            pi['location'] = get_region(pi.get('location'))
            pi['contact_email'] = "anonymous@biaszero.ai"
            pi['contact_phone'] = "XXXXXXXXXX"
            pi['age'] = None  # Remove age bias
            updates['personal_info'] = pi

        if 'education' in resume:
            edu_entries = []
            for edu in resume['education'].get('entries', []):
                edu = dict(edu)
                edu['university'] = get_tier(edu.get('university'))
                edu_entries.append(edu)
            updates['education'] = {'entries': edu_entries}

        updates['is_anonymized'] = True
        updates['anonymized_at'] = datetime.utcnow()
        updates['candidate_id'] = candidate_id

        resumes.update_one({'user_id': user_id}, {'$set': updates})

        return jsonify({'message': 'Resume anonymized successfully', 'candidate_id': candidate_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================= LANDING =================

@app.route('/landing')
def landing():
    auth = require_login()
    if auth: return auth

    # Fetch jobs with search/filter support
    search = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    type_filter = request.args.get('type', '').strip()

    query = {}
    if search:
        query['$or'] = [
            {'position': {'$regex': search, '$options': 'i'}},
            {'company_name': {'$regex': search, '$options': 'i'}},
            {'job_description': {'$regex': search, '$options': 'i'}}
        ]
    if location_filter:
        query['location'] = {'$regex': location_filter, '$options': 'i'}
    if type_filter:
        query['employment_type'] = type_filter

    jobs = list(job_descriptions.find(query).sort('created_at', -1))

    # Get user's applied jobs
    user_id = ObjectId(session['user_id'])
    applied_jobs = set()
    for app_doc in applications.find({'applicants': user_id}):
        applied_jobs.add(str(app_doc['job_id']))

    return render_template("landing.html",
                           jobs=jobs,
                           applied_jobs=applied_jobs,
                           search=search,
                           user_name=session.get('user_name', 'User'))


# ================= DASHBOARD =================

@app.route('/dashboard')
def dashboard():
    auth = require_login()
    if auth: return auth

    if session.get('user_role') != 'Company':
        flash('Access denied. Company login required.', 'danger')
        return redirect(url_for('landing'))

    jobs = list(job_descriptions.find({"submitted_by": session['user_id']}).sort('created_at', -1))

    for job in jobs:
        app_doc = applications.find_one({"job_id": job['_id']})
        job['applicant_count'] = len(app_doc['applicants']) if app_doc else 0

    # Stats
    total_jobs = len(jobs)
    total_applicants = sum(j['applicant_count'] for j in jobs)

    return render_template("dashboard.html",
                           jobs=jobs,
                           total_jobs=total_jobs,
                           total_applicants=total_applicants,
                           user_name=session.get('user_name', 'Company'))


# ================= JOB FORM =================

@app.route('/job_desc')
def job_desc():
    auth = require_login()
    if auth: return auth
    if session.get('user_role') != 'Company':
        flash('Access denied.', 'danger')
        return redirect(url_for('landing'))
    return render_template("job_desc.html")


# ================= JOB VIEW =================

@app.route('/job_view/<job_id>')
def job_view(job_id):
    auth = require_login()
    if auth: return auth

    try:
        job = job_descriptions.find_one({"_id": ObjectId(job_id)})
        if not job:
            flash('Job not found.', 'danger')
            return redirect(url_for('dashboard'))

        app_doc = applications.find_one({"job_id": ObjectId(job_id)})
        applicants_data = []

        if app_doc:
            for uid in app_doc['applicants']:
                resume = resumes.find_one({"user_id": uid})
                if resume:
                    applicants_data.append(resume)

        return render_template("job_view.html", job=job, applicants=applicants_data)

    except Exception as e:
        flash('Error loading job.', 'danger')
        return redirect(url_for('dashboard'))


# ================= JOB SUBMISSION =================

@app.route('/submit_job', methods=['POST'])
def submit_job():
    auth = require_login()
    if auth: return auth

    if session.get('user_role') != 'Company':
        flash('Access denied.', 'danger')
        return redirect(url_for('landing'))

    position = request.form.get('position', '').strip()
    company_name = request.form.get('company_name', '').strip()

    if not position or not company_name:
        flash('Position and Company Name are required.', 'danger')
        return redirect(url_for('job_desc'))

    data = {
        "company_name": company_name,
        "position": position,
        "location": request.form.get('location', '').strip(),
        "employment_type": request.form.get('employment_type', '').strip(),
        "salary": request.form.get('salary', '').strip(),
        "job_description": request.form.get('job_description', '').strip(),
        "requirements": [r.strip() for r in request.form.get('requirements', '').split('\n') if r.strip()],
        "submitted_by": session['user_id'],
        "created_at": datetime.utcnow()
    }

    job_descriptions.insert_one(data)
    flash('Job posted successfully!', 'success')
    return redirect(url_for('dashboard'))


# ================= APPLY JOB =================

@app.route('/apply_job', methods=['POST'])
def apply_job():
    auth = require_login()
    if auth: return auth

    if session.get('user_role') == 'Company':
        flash('Companies cannot apply for jobs.', 'danger')
        return redirect(url_for('landing'))

    user_id = ObjectId(session['user_id'])
    job_id_str = request.form.get('job_id', '')

    if not job_id_str:
        flash('Invalid job.', 'danger')
        return redirect(url_for('landing'))

    # Check resume exists
    resume = resumes.find_one({'user_id': user_id})
    if not resume:
        flash('Please complete your resume before applying.', 'warning')
        return redirect(url_for('profile'))

    try:
        job_id = ObjectId(job_id_str)
    except Exception:
        flash('Invalid job ID.', 'danger')
        return redirect(url_for('landing'))

    existing = applications.find_one({"job_id": job_id})

    if existing:
        if user_id in existing.get("applicants", []):
            flash('You have already applied to this job.', 'warning')
        else:
            applications.update_one({"job_id": job_id}, {"$push": {"applicants": user_id}})
            flash('Application submitted successfully! 🎉', 'success')
    else:
        applications.insert_one({
            "job_id": job_id,
            "applicants": [user_id],
            "created_at": datetime.utcnow()
        })
        flash('Application submitted successfully! 🎉', 'success')

    return redirect(url_for('landing'))


# ================= VIEW APPLICANTS =================

@app.route('/view_applicants', methods=['POST'])
def view_applicants():
    auth = require_login()
    if auth: return auth

    job_id = ObjectId(request.form.get('job_id'))
    job = job_descriptions.find_one({"_id": job_id})
    app_doc = applications.find_one({"job_id": job_id})

    applicants_data = []
    if app_doc:
        for uid in app_doc['applicants']:
            resume = resumes.find_one({"user_id": uid})
            if resume:
                applicants_data.append(resume)

    return render_template("job_view.html", job=job, applicants=applicants_data)


# ================= API: JOB STATS =================

@app.route('/api/stats')
def api_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    total_jobs = job_descriptions.count_documents({})
    total_users = users.count_documents({'role': 'User'})
    total_companies = users.count_documents({'role': 'Company'})

    return jsonify({
        'total_jobs': total_jobs,
        'total_users': total_users,
        'total_companies': total_companies
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
