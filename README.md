# BiasZero.ai

> **AI-powered hiring bias detection and resume anonymization platform**

BiasZero is a full-stack Flask web application that helps eliminate demographic bias from the hiring process. It provides a dual-portal system — one for job candidates and one for companies — with AI-driven bias scoring, smart resume anonymization, and a fair job application board.

---

## ✨ Features

### For Candidates
- **Resume Builder** — Multi-step form covering Personal Info, Education, Experience, Projects, Certifications, and Skills
- **Bias Analyser** — Computes a bias score (0–1) based on demographic factors like age, gender, location, and institution tier
- **Smart Anonymization** — Replaces name, contact details, and location with a Candidate ID while preserving skills and experience
- **Job Board** — Browse and filter all posted jobs; apply with one click
- **Applied Status** — Track which jobs you've applied to

### For Companies
- **Dashboard** — View all posted jobs with stats (total jobs, total applicants, avg applicants/job)
- **Post Jobs** — Create listings with company, position, location, type, salary, and description
- **Applicant Viewer** — Flip-card UI to browse applicants; see resume data and bias scores
- **Anonymized Candidates** — Employers see anonymized data if candidate chose to anonymize

---

## 🛠 Tech Stack

| Layer        | Technology                          |
|-------------|-------------------------------------|
| Backend     | Python 3.10+, Flask                 |
| Database    | MongoDB (pymongo)                   |
| Auth        | Werkzeug password hashing, sessions |
| ML/AI       | scikit-learn, fairlearn, numpy, pandas |
| Frontend    | Vanilla HTML/CSS/JS (no framework)  |
| Fonts       | Syne (display) + DM Sans (body)     |

---

## 📂 Project Structure

```
BiasZero.ai/
├── app.py                      # Main Flask application
├── bias_detection_model.py     # Bias detection ML model
├── bias_classifier_model.py    # Bias classification model
├── anonymizer_module.py        # Resume anonymization logic
├── Transformer_model.py        # Transformer-based model
├── requirements.txt
├── README.md
│
├── Database/
│   ├── connection.py           # MongoDB connection helper
│   └── CRUD.py                 # Database CRUD operations
│
├── static/
│   ├── css/
│   │   ├── globals.css         # Design system & CSS variables
│   │   ├── navbar.css          # Navigation bar
│   │   ├── login.css           # Login/Register page
│   │   ├── landing.css         # Job board page
│   │   ├── dashboard.css       # Company dashboard
│   │   ├── profile.css         # Resume builder & viewer
│   │   └── job.css             # Job post & job view pages
│   └── js/
│       └── (inline JS in templates)
│
└── templates/
    ├── Login.html              # Auth page (login + register)
    ├── landing.html            # Job listings board
    ├── dashboard.html          # Company dashboard
    ├── profile.html            # Resume creation wizard
    ├── user_profile.html       # Resume view + edit + bias analysis
    ├── job_desc.html           # Post a new job
    └── job_view.html           # Job detail + applicant flip cards
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- MongoDB running on `localhost:27017`

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/TheAnekar/BiasZero.ai.git
cd BiasZero.ai

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start MongoDB
# Make sure mongod is running on localhost:27017

# 5. Run the app
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 🗃 MongoDB Collections

| Collection        | Purpose                                |
|------------------|----------------------------------------|
| `Login`          | User and company accounts              |
| `resumes`        | Candidate resume data                  |
| `job_descriptions` | Company job postings                 |
| `applications`   | Job application records (job ↔ users)  |

---

## 🔐 Authentication Flow

```
/login  ─→  User (email + password)     ─→  landing page (job board)
        ─→  Company (hr_email + company_code + password) ─→  dashboard
```

New users must create a resume before seeing the job board.

---

## 🤖 Bias Scoring

The bias score (0.0 – 1.0) is computed from these heuristic factors:

| Factor                | Weight | Logic                                        |
|----------------------|--------|----------------------------------------------|
| Gender disclosed     | +0.10  | Providing gender adds a known bias vector     |
| Age outside typical  | +0.15  | Age < 25 or > 50 triggers bias risk           |
| Non-metro location   | +0.10  | Tier-2/rural location detected               |
| Non-Tier-1 institution | +0.10 | No IIT/IIM/NIT/BITS/IISC in education       |
| Model variance       | +0–0.20| Simulated model randomness                   |

**Labels:**
- 🟢 `Low Bias` — score < 0.35
- 🟡 `Medium Bias` — 0.35 ≤ score < 0.65
- 🔴 `High Bias` — score ≥ 0.65

---

## 🎭 Anonymization

When a candidate anonymizes their resume:
- **Name** → `Candidate_XXXXXX` (hex token)
- **Email** → `anonymous@biaszero.ai`
- **Phone** → `XXXXXXXXXX`
- **Age** → removed
- **Location** → Regional label (e.g. "South India", "North India")
- **University** → `Tier-1 Institution` or `Tier-2 Institution`
- Skills, experience, and projects are **preserved**

---

## 🌐 Routes Reference

| Route                  | Method | Access  | Description                  |
|-----------------------|--------|---------|------------------------------|
| `/`                   | GET    | Public  | Redirect to login or home    |
| `/login`              | GET/POST | Public | Login page                   |
| `/register`           | POST   | Public  | User/company registration    |
| `/logout`             | GET    | Auth    | Clear session                |
| `/landing`            | GET    | User    | Job board with filters       |
| `/profile`            | GET    | User    | Resume creation wizard       |
| `/user_profile`       | GET    | User    | View/edit/analyse resume     |
| `/submit_resume`      | POST   | User    | Save resume                  |
| `/calculate_bias`     | POST   | User    | Run bias analysis (JSON)     |
| `/anonymize_resume`   | POST   | User    | Apply anonymization (JSON)   |
| `/apply_job`          | POST   | User    | Submit job application       |
| `/dashboard`          | GET    | Company | View all posted jobs         |
| `/job_desc`           | GET    | Company | Job posting form             |
| `/submit_job`         | POST   | Company | Save job listing             |
| `/job_view/<id>`      | GET    | Company | View job detail + applicants |
| `/view_applicants`    | POST   | Company | View applicants (alternate)  |

---

## 📦 requirements.txt

```
flask
pymongo
werkzeug
numpy
pandas
scikit-learn
fairlearn
joblib
```

---

## 📝 Known Limitations

- Bias scoring currently uses heuristic rules + randomness; replace `compute_bias_score()` in `app.py` with the trained `bias_detection_model.pkl` for production
- Anonymization is **irreversible** within the current session model
- No email verification on registration
- No HTTPS / production WSGI config included (use gunicorn + nginx for deployment)

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

---

## 📄 License

MIT License — see `LICENSE` for details.

---

*Built with ❤️ by [@TheAnekar](https://github.com/TheAnekar)*
