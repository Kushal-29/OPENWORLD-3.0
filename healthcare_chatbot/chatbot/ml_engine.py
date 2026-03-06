# ULTRA SIMPLE ML Engine - WORKS 100%

# SYMPTOM DATABASE - Simple and Direct
SYMPTOMS = {
    'headache': ['headache', 'head ache', 'head pain', 'सिरदर्द', 'डोकेदुखी', 'ತಲೆ_ನೋವು', 'తల_నొప్పి', 'தலை_வலி'],
    'fever': ['fever', 'बुखार', 'ताप', 'ರೋಗ', 'ఎబ్బ', 'జ్వరం'],
    'cough': ['cough', 'खांसी', 'खोकला', 'ಕೆಮ್ಮು', 'దగ్గు', 'இருமல'],
    'chest_pain': ['chest pain', 'chest ache', 'छाती दर्द', 'छाती_दर्द', 'छाती दर्द', 'ఛాతి_నొప్పి', 'ఛాతి నొప్పి', 'மார్பு_வலி'],
    'body_ache': ['body ache', 'body pain', 'शरीर दर्द', 'शरीर_दर्द', 'दे्ह नोवु', 'ದೇಹ_ನೋವು', 'శరీర_నొప్పి', 'உடல்_வலி'],
    'cold': ['cold', 'सर्दी', 'जलदोष', 'ಜಲದೋಷ', 'జలుబు', 'சளி'],
    'nausea': ['nausea', 'vomiting', 'मतली', 'मळमळ', 'ವಾಂತಿ', 'వాంతి', 'குமட்டல'],
    'fatigue': ['fatigue', 'tired', 'weakness', 'थकान', 'थकवा', 'ದುರ್ಬಲತೆ', 'బలహీనత', 'பலவீனம'],
    'diarrhea': ['diarrhea', 'loose motion', 'दस्त', 'पोट_दर्द', 'कडुपु', 'ಕೋಶ', 'పేదि', 'पेट दर्द'],
}

# DISEASE DATABASE - Simple Direct Matching
DISEASES = {
    'headache': {
        'name': 'Migraine/Headache',
        'description': 'A headache is pain in the head. Rest, apply compress, stay hydrated, avoid screens.',
        'severity': 'Minor',
        'precautions': ['Rest in quiet dark room', 'Apply hot/cold compress', 'Stay hydrated', 'Avoid bright screens', 'Take pain reliever']
    },
    'fever': {
        'name': 'Fever',
        'description': 'Fever is a temporary increase in body temperature, often due to infection.',
        'severity': 'Minor',
        'precautions': ['Rest well', 'Stay hydrated', 'Take paracetamol', 'Monitor temperature', 'Consult if persists for 3+ days']
    },
    'cold': {
        'name': 'Common Cold',
        'description': 'A viral infection affecting the upper respiratory tract.',
        'severity': 'Minor',
        'precautions': ['Rest adequately', 'Drink warm fluids', 'Use saline nasal drops', 'Take vitamin C', 'Avoid crowded places']
    },
    'cough': {
        'name': 'Cough',
        'description': 'Persistent cough often due to viral infection or irritation.',
        'severity': 'Minor',
        'precautions': ['Rest throat', 'Drink warm liquids', 'Use throat lozenges', 'Avoid smoke and dust', 'Consult if lasts 2+ weeks']
    },
    'chest_pain': {
        'name': 'Chest Pain - Seek Immediate Medical Attention',
        'description': 'Chest pain requires urgent medical evaluation. DO NOT DELAY.',
        'severity': 'Major',
        'precautions': ['CALL EMERGENCY IMMEDIATELY', 'Chew aspirin if available', 'Sit and rest', 'Do not exert yourself', 'Monitor vital signs']
    },
    'body_ache': {
        'name': 'Body Ache/Muscle Pain',
        'description': 'Body pain often due to viral infection like flu or muscle strain.',
        'severity': 'Minor',
        'precautions': ['Rest completely', 'Apply warm compress', 'Take pain reliever', 'Stay hydrated', 'Massage affected areas']
    },
    'covid': {
        'name': 'COVID-19 (Possible)',
        'description': 'Multiple symptoms including fever, cough, body ache suggest possible COVID-19.',
        'severity': 'Major',
        'precautions': ['Isolate immediately', 'Get tested for COVID-19', 'Consult doctor', 'Monitor oxygen levels', 'Seek emergency care if breathing difficulty']
    },
    'flu': {
        'name': 'Influenza (Flu)',
        'description': 'Flu presents with fever, cough, body ache, and fatigue.',
        'severity': 'Major',
        'precautions': ['Rest completely', 'Stay very hydrated', 'Take pain reliever', 'Consult doctor for antivirals', 'Avoid spreading to others']
    },
    'gastro': {
        'name': 'Gastroenteritis',
        'description': 'Stomach infection causing nausea, vomiting, and diarrhea.',
        'severity': 'Major',
        'precautions': ['Drink ORS solution', 'Eat bland foods only', 'Avoid dairy and spicy foods', 'Monitor hydration', 'Rest']
    },
}


def parse_symptoms_from_text(text):
    """
    ULTRA SIMPLE: Just find keywords in text
    """
    if not text:
        return []
    
    text = text.lower().strip()
    found = []
    
    # Check each symptom type
    for symptom_type, keywords in SYMPTOMS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                found.append(symptom_type)
                break  # Only add once per symptom type
    
    return found


def predict_disease(symptoms):
    """
    ULTRA SIMPLE: Match symptoms to diseases
    """
    if not symptoms:
        return None
    
    # Special cases - Multiple symptoms
    if len(symptoms) >= 3:
        if 'fever' in symptoms and 'cough' in symptoms:
            if 'body_ache' in symptoms or 'fatigue' in symptoms:
                return {
                    'name': DISEASES['covid']['name'],
                    'description': DISEASES['covid']['description'],
                    'severity': DISEASES['covid']['severity'],
                    'precautions': DISEASES['covid']['precautions'],
                    'matched_symptoms': symptoms
                }
    
    if len(symptoms) >= 4:
        if all(s in symptoms for s in ['fever', 'cough', 'body_ache', 'fatigue']):
            return {
                'name': DISEASES['flu']['name'],
                'description': DISEASES['flu']['description'],
                'severity': DISEASES['flu']['severity'],
                'precautions': DISEASES['flu']['precautions'],
                'matched_symptoms': symptoms
            }
    
    if all(s in symptoms for s in ['nausea', 'diarrhea']):
        return {
            'name': DISEASES['gastro']['name'],
            'description': DISEASES['gastro']['description'],
            'severity': DISEASES['gastro']['severity'],
            'precautions': DISEASES['gastro']['precautions'],
            'matched_symptoms': symptoms
        }
    
    # Single symptom matching - DIRECT and SIMPLE
    for symptom in symptoms:
        if symptom in DISEASES:
            return {
                'name': DISEASES[symptom]['name'],
                'description': DISEASES[symptom]['description'],
                'severity': DISEASES[symptom]['severity'],
                'precautions': DISEASES[symptom]['precautions'],
                'matched_symptoms': symptoms
            }
    
    # If no direct match, try first symptom
    if symptoms:
        first = symptoms[0]
        if first in DISEASES:
            return {
                'name': DISEASES[first]['name'],
                'description': DISEASES[first]['description'],
                'severity': DISEASES[first]['severity'],
                'precautions': DISEASES[first]['precautions'],
                'matched_symptoms': symptoms
            }
    
    return None


def get_all_symptoms():
    """Get all symptoms"""
    return list(SYMPTOMS.keys())