from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey'


client = MongoClient('mongodb://localhost:27017/')
db = client['BiasZero']
users = db['Login']
resumes = db['resumes']
job_descriptions = db['job_descriptions']


def parse_education_entries(form):
    degrees = form.getlist('education_degree[]')
    universities = form.getlist('education_university[]')
    years = form.getlist('education_year[]')
    grades = form.getlist('education_grade[]')

    entries = []
    for i in range(len(degrees)):
        entries.append({
            "degree": degrees[i],
            "university": universities[i],
            "year": years[i],
            "grade": grades[i]
        })
    return entries


def parse_experience_entries(form):
    titles = form.getlist('experience_title[]')
    companies = form.getlist('experience_company[]')
    starts = form.getlist('experience_start[]')
    ends = form.getlist('experience_end[]')

    entries = []
    for i in range(len(titles)):
        entries.append({
            "job_title": titles[i],
            "company": companies[i],
            "start_date": starts[i],
            "end_date": ends[i]
        })
    return entries


def parse_project_entries(form):
    titles = form.getlist('project_title[]')
    descs = form.getlist('project_description[]')
    techs = form.getlist('project_technologies[]')

    entries = []
    for i in range(len(titles)):
        entries.append({
            "title": titles[i],
            "description": descs[i],
            "technologies": techs[i].split('|')
        })
    return entries


def parse_certification_entries(form):
    names = form.getlist('cert_name[]')
    orgs = form.getlist('cert_org[]')

    entries = []
    for i in range(len(names)):
        entries.append({
            "name": names[i],
            "issuer": orgs[i]
        })
    return entries




@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
@app.route('/register', methods=['POST'])
def register():

    role = request.form.get('RegisterRole', 'User')
    password = request.form.get('password')

    if role == "Company":
        hr_email = request.form.get('hr_email')
        company_code = request.form.get('company_code')

        if not hr_email or not company_code or not password:
            flash('Please fill all company fields', 'danger')
            return render_template('Login.html')

        existing = users.find_one({
            'hr_email': hr_email,
            'company_code': company_code,
            'role': 'Company'
        })

        if existing:
            flash('Company already registered.', 'warning')
            return render_template('Login.html')

        users.insert_one({
            'hr_email': hr_email,
            'company_code': company_code,
            'password': generate_password_hash(password),
            'role': 'Company',
            'created_at': datetime.utcnow()
        })

    else:
        name = request.form.get('name')
        email = request.form.get('email')

        if not name or not email or not password:
            flash('Please fill all user fields', 'danger')
            return render_template('Login.html')

        existing = users.find_one({
            'email': email,
            'role': 'User'
        })

        if existing:
            flash('Email already registered.', 'warning')
            return render_template('Login.html')

        users.insert_one({
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'role': 'User',
            'created_at': datetime.utcnow()
        })

    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        role = request.form.get('LoginRole')
        password = request.form.get('password')

        if role == "Company":
            hr_email = request.form.get('hr_email')
            company_code = request.form.get('company_code')

            user = users.find_one({
                'hr_email': hr_email,
                'company_code': company_code,
                'role': 'Company'
            })

        else:
            email = request.form.get('email')

            user = users.find_one({
                'email': email,
                'role': 'User'
            })

        if user and check_password_hash(user.get('password', ''), password):

            session['user_id'] = str(user['_id'])
            session['user_role'] = user.get('role')

            if session['user_role'] == 'Company':
                return redirect(url_for('dashboard'))


            existing_profile = resumes.find_one({'user_id': ObjectId(session['user_id'])})

            if existing_profile:
                return redirect(url_for('landing'))

            else:
                return redirect(url_for('profile', mode='create'))

        flash('Invalid credentials.', 'danger')
        return render_template('Login.html')

    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mode = request.args.get('mode', 'view')
    user_id = session['user_id']
    resume = resumes.find_one({'user_id': user_id})
    return render_template('profile.html', resume=resume, mode=mode)

@app.route('/submit_resume', methods=['POST'])
def submit_resume():
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = ObjectId(session['user_id'])

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
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'Company':
        flash('Access denied.', 'danger')
        return redirect(url_for('profile', mode='view'))

    user_id = session['user_id']

    jobs = list(job_descriptions.find({
        "submitted_by": user_id
    }).sort("created_at", -1))

    return render_template(
        "dashboard.html",
        jobs=jobs
    )




@app.route('/job_desc', methods=['GET'])
def job_desc():
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_role') != 'Company':
        flash('Access denied: only companies can post job descriptions.', 'danger')
        return redirect(url_for('profile', mode='view'))
    return render_template('job_desc.html')

@app.route('/submit_job', methods=['POST'])
def submit_job():
    
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
    return redirect(url_for('dashboard'))


@app.route('/landing')
def landing():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    jobs = list(db.job_descriptions.find())

    return render_template(
        "landing.html",
        jobs=jobs
    )

@app.route('/user_profile')
def user_profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    resume = resumes.find_one({'user_id': ObjectId(session['user_id'])})


    return render_template('user_profile.html', resume=resume)


if __name__ == '__main__':
    app.run(debug=True)
