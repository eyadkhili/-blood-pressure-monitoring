import json
import os
import sys
import time
from datetime import datetime

try:
    from confluent_kafka import Consumer, KafkaError
except ImportError:
    print(" confluent-kafka n'est pas installé! Installez-le avec: pip install confluent-kafka")
    sys.exit(1)

from elasticsearch import Elasticsearch

# ============================================
# CONFIGURATION
# ============================================
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'blood_pressure_topic'
# Changement de group.id pour s'assurer de lire les nouveaux messages avec le bon mapping
KAFKA_GROUP_ID = 'health-monitor-final-v9' 

ELASTICSEARCH_HOST = 'http://localhost:9200'
ELASTICSEARCH_INDEX = 'blood_pressure_anomalies'

NORMAL_DATA_FOLDER = 'normal_data'

# ============================================
# FONCTIONS ELASTICSEARCH
# ============================================

def create_index_if_not_exists(es):
    """Crée l'index avec le mapping keyword pour le nom (indispensable pour Kibana)."""
    if not es.indices.exists(index=ELASTICSEARCH_INDEX):
        mapping = {
            "mappings": {
                "properties": {
                    "patient_id": {"type": "keyword"},
                    "patient_name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "patient_gender": {"type": "keyword"},
                    "patient_age": {"type": "integer"},
                    "systolic_pressure": {"type": "integer"},
                    "diastolic_pressure": {"type": "integer"},
                    "category": {"type": "keyword"},
                    "risk_level": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "location": {"type": "geo_point"},
                    "city": {"type": "keyword"}
                }
            }
        }
        es.indices.create(index=ELASTICSEARCH_INDEX, body=mapping)
        print(f"🆕 Index '{ELASTICSEARCH_INDEX}' créé avec succès.")

def index_to_elasticsearch(es, data):
    """Envoie l'anomalie vers Elasticsearch et affiche le log détaillé."""
    try:
        timestamp_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        document = {
            'patient_id': data['patient_id'],
            'patient_name': data['patient_name'],
            'patient_gender': data['patient_gender'],
            'patient_age': data['patient_age'],
            'systolic_pressure': data['systolic'],
            'diastolic_pressure': data['diastolic'],
            'category': data['category'],
            'risk_level': data['risk_level'],
            'timestamp': timestamp_iso,
            'location': {
                'lat': data['location'].get('lat', 0),
                'lon': data['location'].get('lon', 0)
            },
            'city': data['location'].get('city', 'Inconnue')
        }
        
        es.index(index=ELASTICSEARCH_INDEX, document=document)
        
        # --- AFFICHAGE DÉTAILLÉ (COMME DANS VOTRE PRODUCER) ---
        emoji_map = {
            'Critical': '🚨', 'High': '🔴', 'Moderate': '🟠', 'Low': '🔵'
        }
        emoji = emoji_map.get(data['risk_level'], '⚠️')
        
        print(f"{emoji} [{time.strftime('%H:%M:%S')}] {data['patient_name'][:25]:25} | "
              f"BP: {data['systolic']}/{data['diastolic']} | {data['risk_level']:10} | "
              f"{document['city']}")
              
    except Exception as e:
        print(f" Erreur Indexation ES: {e}")

# ============================================
# TRAITEMENT DES DONNÉES
# ============================================

def extract_fhir_data(fhir_msg):
    """Extrait les infos et définit les 4 niveaux de risque demandés."""
    try:
        patient_info = {}
        location_info = {}
        category = "Unknown"
        
        for ext in fhir_msg.get('extension', []):
            if ext['url'] == 'patient-demographics':
                patient_info = json.loads(ext['valueString'])
            elif ext['url'] == 'measurement-location':
                location_info = json.loads(ext['valueString'])
            elif ext['url'] == 'blood-pressure-category':
                category = ext['valueString']

        # LOGIQUE DES 4 NIVEAUX DE RISQUE
        risk_level = "Low"
        if category == "hypertensive_crisis":
            risk_level = "Critical"
        elif category == "hypertension_stage_2":
            risk_level = "High"
        elif category == "hypertension_stage_1" or category == "elevated":
            risk_level = "Moderate"
        elif category == "hypotension":
            risk_level = "Low"

        return {
            'patient_id': patient_info.get('patient_id'),
            'patient_name': patient_info.get('name'),
            'patient_gender': patient_info.get('gender'),
            'patient_age': patient_info.get('age'),
            'systolic': fhir_msg['component'][0]['valueQuantity']['value'],
            'diastolic': fhir_msg['component'][1]['valueQuantity']['value'],
            'category': category,
            'risk_level': risk_level,
            'location': location_info
        }
    except Exception as e:
        print(f" Erreur Extraction: {e}")
        return None

def save_normal_locally(data):
    """Sauvegarde locale pour les patients sains."""
    os.makedirs(NORMAL_DATA_FOLDER, exist_ok=True)
    filename = os.path.join(NORMAL_DATA_FOLDER, "patients_sains.json")
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")
    print(f" [{time.strftime('%H:%M:%S')}] {data['patient_name'][:25]:25} | Normal")

# ============================================
# BOUCLE PRINCIPALE
# ============================================

if __name__ == "__main__":
    es = Elasticsearch([ELASTICSEARCH_HOST])
    create_index_if_not_exists(es)

    # Configuration correcte pour confluent-kafka (utilisation des points)
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID, 
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_TOPIC])

    print("📡 Consumer prêt. Affichage détaillé activé...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error(): continue

            fhir_message = json.loads(msg.value().decode('utf-8'))
            data = extract_fhir_data(fhir_message)

            if data:
                # Si ce n'est pas "normal", on indexe (anomalies)
                if data['category'].lower() != "normal":
                    index_to_elasticsearch(es, data)
                else:
                    save_normal_locally(data)

    except KeyboardInterrupt:
        print("\n Arrêt du système.")
    finally:
        consumer.close()