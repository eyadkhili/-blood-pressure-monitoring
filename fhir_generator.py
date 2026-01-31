"""
=============================================================================
GÉNÉRATEUR DE MESSAGES FHIR - Pression Artérielle
=============================================================================
Génère des patients ALÉATOIRES avec Faker + localisation France(pour mieux presenter notre travail)
=============================================================================
"""

import json
import random
import uuid
from datetime import datetime
from faker import Faker

fake = Faker('fr_FR')

# ============================================
# VILLES FRANÇAISES AVEC COORDONNÉES GPS
# ============================================
FRENCH_CITIES = [
    {"city": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"city": "Marseille", "lat": 43.2965, "lon": 5.3698},
    {"city": "Lyon", "lat": 45.7640, "lon": 4.8357},
    {"city": "Toulouse", "lat": 43.6047, "lon": 1.4442},
    {"city": "Nice", "lat": 43.7102, "lon": 7.2620},
    {"city": "Nantes", "lat": 47.2184, "lon": -1.5536},
    {"city": "Strasbourg", "lat": 48.5734, "lon": 7.7521},
    {"city": "Bordeaux", "lat": 44.8378, "lon": -0.5792},
    {"city": "Lille", "lat": 50.6292, "lon": 3.0573},
    {"city": "Dijon", "lat": 47.3220, "lon": 5.0415},
    {"city": "Rennes", "lat": 48.1173, "lon": -1.6778},
    {"city": "Montpellier", "lat": 43.6108, "lon": 3.8767},
    {"city": "Grenoble", "lat": 45.1885, "lon": 5.7245},
    {"city": "Toulon", "lat": 43.1242, "lon": 5.9280},
    {"city": "Angers", "lat": 47.4784, "lon": -0.5632},
]


def generate_random_patient():
    """Génère un patient ALÉATOIRE avec Faker."""
    patient_id = f"patient-{uuid.uuid4().hex[:8]}"
    gender = random.choice(['male', 'female'])
    name = fake.name_male() if gender == 'male' else fake.name_female()
    age = random.randint(18, 90)
    city_info = random.choice(FRENCH_CITIES)
    
    location = {
        "city": city_info["city"],
        "lat": round(city_info["lat"] + random.uniform(-0.05, 0.05), 6),
        "lon": round(city_info["lon"] + random.uniform(-0.05, 0.05), 6)
    }
    
    return {
        "patient_id": patient_id,
        "name": name,
        "gender": gender,
        "age": age,
        "location": location
    }


def classify_blood_pressure(systolic, diastolic):
    """Classifie la pression artérielle selon les seuils AHA."""
    if systolic > 180 or diastolic > 120:
        return "hypertensive_crisis"
    if systolic < 90 or diastolic < 60:
        return "hypotension"
    if systolic >= 140 or diastolic >= 90:
        return "hypertension_stage_2"
    if systolic >= 130 or diastolic >= 80:
        return "hypertension_stage_1"
    if 120 <= systolic <= 129 and diastolic < 80:
        return "elevated"
    return "normal"


def generate_blood_pressure_values():
    """Génère des valeurs de pression artérielle réalistes."""
    rand = random.random()
    
    if rand < 0.40:
        systolic = random.randint(90, 119)
        diastolic = random.randint(60, 79)
    elif rand < 0.55:
        systolic = random.randint(120, 129)
        diastolic = random.randint(60, 79)
    elif rand < 0.70:
        systolic = random.randint(130, 139)
        diastolic = random.randint(80, 89)
    elif rand < 0.85:
        systolic = random.randint(140, 179)
        diastolic = random.randint(90, 119)
    elif rand < 0.90:
        systolic = random.randint(181, 220)
        diastolic = random.randint(121, 140)
    else:
        systolic = random.randint(70, 89)
        diastolic = random.randint(40, 59)
    
    return systolic, diastolic


def generate_fhir_observation():
    """Génère une observation FHIR complète."""
    patient = generate_random_patient()
    systolic, diastolic = generate_blood_pressure_values()
    category = classify_blood_pressure(systolic, diastolic)
    observation_time = datetime.now()
    
    fhir_observation = {
        "resourceType": "Observation",
        "id": f"obs-{uuid.uuid4().hex[:12]}",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }],
            "text": "Vital Signs"
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel"
            }],
            "text": "Blood Pressure"
        },
        "subject": {
            "reference": f"Patient/{patient['patient_id']}",
            "display": patient["name"]
        },
        "effectiveDateTime": observation_time.isoformat(),
        "component": [
            {
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}],
                    "text": "Systolic Blood Pressure"
                },
                "valueQuantity": {"value": systolic, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
            },
            {
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}],
                    "text": "Diastolic Blood Pressure"
                },
                "valueQuantity": {"value": diastolic, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
            }
        ],
        "meta": {"lastUpdated": datetime.now().isoformat(), "source": "blood-pressure-monitoring-system"},
        "extension": [
            {"url": "patient-demographics", "valueString": json.dumps({"patient_id": patient["patient_id"], "name": patient["name"], "gender": patient["gender"], "age": patient["age"]})},
            {"url": "measurement-location", "valueString": json.dumps(patient["location"])},
            {"url": "blood-pressure-category", "valueString": category}
        ]
    }
    
    return fhir_observation


def generate_batch(count=10):
    """Génère un lot de messages FHIR."""
    return [generate_fhir_observation() for _ in range(count)]


if __name__ == "__main__":
    print("Test du générateur FHIR")
    sample = generate_fhir_observation()
    print(json.dumps(sample, indent=2, ensure_ascii=False))