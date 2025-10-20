from flask import *
from Database.connection import *
from Database.CRUD import *
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "Simply Lovely"


@app.route('/')
def index():
    return render_template('Login.html')

@app.route('/home')
def home():
    return render_template('profile.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('LoginRole')

        user_list = read_document("Login",email)

        if user_list and len(user_list) > 0:
            user = user_list[0]  

            if user['password'] == password and user['role'] == role:
                session['user'] = email
                session['role'] = role
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid password or role mismatch', 'error')
                return redirect(url_for('login'))
        else:
            flash('No user found with that email.', 'error')
            return redirect(url_for('home'))

    return render_template('Login.html')


@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('RegisterRole')  

    existing_user = read_document("Login", {"email": email})
    if existing_user:
        flash('E-mail already registered. Please log in.', 'warning')
        return redirect(url_for('login'))

    new_user = {
        "name": name,
        "email": email,
        "password": password,
        "role": role
    }

    create_document("Login",new_user)
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('login'))

@app.route('/submit', methods=['POST'])
def submit_resume():
    data = {
        "personal_info": {
            "name": request.form.get('name'),
            "age": int(request.form.get('age')),
            "gender": request.form.get('gender'),
            "location": request.form.get('location'),
            "contact_email": request.form.get('email'),
            "contact_phone": request.form.get('phone')
        },
        "education": {
            "has_education": request.form.get('has_education') == 'true',
            "entries": parse_education_entries(request.form)
        },
        "experience": {
            "has_experience": request.form.get('has_experience') == 'true',
            "entries": parse_experience_entries(request.form)
        },
        "projects": {
            "has_projects": request.form.get('has_projects') == 'true',
            "entries": parse_project_entries(request.form)
        },
        "certifications": {
            "has_certifications": request.form.get('has_certifications') == 'true',
            "entries": parse_certification_entries(request.form)
        },
        "skills": {
            "has_skills": request.form.get('has_skills') == 'true',
            "technical": request.form.get('technical_skills', '').split(','),
            "soft": request.form.get('soft_skills', '').split(',')
        }
    }
    
    return jsonify({'success': True, 'data': data})


if __name__ == "__main__":
    app.run(debug=True)