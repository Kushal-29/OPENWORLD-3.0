# Healthcare Chatbot Using AI 🏥🤖

**Published in:** IJRASET, Volume 12, Issue IV, April 2024  
**DOI:** https://doi.org/10.22214/ijraset.2024.61249  
**Institution:** Department of Computer Science and Engineering, SMSMPITR, Akluj, Maharashtra, India

---

## 📋 Project Overview

An AI-powered healthcare chatbot that provides:
- 🩺 **Symptom analysis** using a Decision Tree classifier
- 💊 **Disease prediction** with precautions
- 🏥 **Nearby hospital finder** with map integration
- 📅 **Appointment booking**
- 💬 **24/7 AI chat support**

---

## 🗂️ Project Structure

```
healthcare_chatbot/
│
├── manage.py                        # Django project manager
├── requirements.txt                 # Python dependencies
├── setup.sh                         # Auto-setup script
├── README.md                        # This file
│
├── healthcare_chatbot/              # Django project settings
│   ├── __init__.py
│   ├── settings.py                  # Project configuration
│   ├── urls.py                      # Root URL config
│   └── wsgi.py
│
└── chatbot/                         # Main Django app
    ├── __init__.py
    ├── models.py                    # UserProfile, ChatHistory models
    ├── views.py                     # All view functions
    ├── urls.py                      # App URL routing
    ├── ml_engine.py                 # Decision Tree AI engine
    ├── migrations/
    │   └── __init__.py
    └── templates/
        └── chatbot/
            ├── base.html            # Base template with navbar & footer
            ├── register.html        # Sign Up page (Fig a in paper)
            ├── login.html           # Login page
            ├── home.html            # Home page (Fig b in paper)
            ├── nearby_hospitals.html # Hospital map (Fig c in paper)
            ├── chat.html            # AI Chat Room (Fig d in paper)
            ├── services.html        # Services & appointment
            └── contact.html         # Contact page
```

---

## ⚙️ Technologies Used

| Category | Technology |
|----------|-----------|
| Backend Framework | Django 4.2 |
| AI/ML | Scikit-learn (Decision Tree Classifier) |
| NLP | Custom symptom extraction |
| Frontend | Bootstrap 5, HTML5, CSS3, JavaScript |
| Database | SQLite3 (default) |
| Data Processing | NumPy, Pandas |
| Maps | OpenStreetMap (free) / Google Maps API |

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.9 or higher
- pip

---

### Method 1: Using Setup Script (Linux/Mac)

```bash
# 1. Navigate to project directory
cd healthcare_chatbot

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Start server
source venv/bin/activate
python manage.py runserver
```

---

### Method 2: Manual Setup (Windows/Linux/Mac)

#### Step 1: Create & activate virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

#### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Run database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 4: (Optional) Create admin superuser

```bash
python manage.py createsuperuser
```

#### Step 5: Start the development server

```bash
python manage.py runserver
```

#### Step 6: Open in browser

```
http://127.0.0.1:8000
```

---

## 🌐 Application URLs

| URL | Page |
|-----|------|
| `/` | Login Page |
| `/register/` | Sign Up Page |
| `/home/` | Home Page |
| `/services/` | Services & Appointment |
| `/nearby_hosp/` | Nearby Hospitals Map |
| `/chat/` | AI Chat Room |
| `/contact/` | Contact Us |
| `/admin/` | Django Admin Panel |

---

## 🤖 How the AI Works

The chatbot uses a **Decision Tree Classifier** algorithm:

```
User Types Symptoms
        ↓
Symptom Extraction (NLP parsing)
        ↓
Feature Vector Creation (all known symptoms)
        ↓
Decision Tree Classifier
        ↓
Disease Prediction + Severity
        ↓
Precautions Displayed to User
```

### Supported Diseases
- Flu, Common Cold, COVID-19
- Malaria, Dengue, Pneumonia
- Diabetes, Hypertension
- Gastroenteritis, Migraine
- Asthma, Anemia

### Example Chat Inputs
```
"I have fever, headache and body ache"
"feeling nausea, vomiting and diarrhea"
"I have chest pain and shortness of breath"
"frequent urination, fatigue, blurred vision"
```

---

## 🗺️ Map Feature

The Nearby Hospitals page uses **OpenStreetMap** (free, no API key needed) by default.

**To use Google Maps** (optional, for live hospital search):
1. Get a Google Maps API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable: Maps JavaScript API + Places API
3. In `nearby_hospitals.html`, add before `</body>`:
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places&callback=initMap" async defer></script>
```

---

## 👩‍💻 Team

| Name | Role |
|------|------|
| Ms. Puja D. Satpute | Student Developer |
| Ms. Shravani M. Babar | Student Developer |
| Ms. Aparna A. Magar | Student Developer |
| Ms. Gauri S. Kumbhar | Student Developer |
| Ms. Poonam N. Gore | Student Developer |
| Prof. Sachin D. Pandhare | Guide (Assistant Professor) |

---

## 📞 Contact

- **Phone:** +91 76201 83093 | +91 90221 91155  
- **Email:** Healthcareai@gmail.com  
- **Institution:** SMSMPITR, Akluj, Maharashtra, India

---

## ⚠️ Disclaimer

This chatbot provides **AI-based preliminary assessments only**. It does **not** replace professional medical diagnosis or treatment. Always consult a qualified doctor for proper medical advice.
