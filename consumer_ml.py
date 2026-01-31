import json
import joblib
import pandas as pd
from confluent_kafka import Consumer
from elasticsearch import Elasticsearch
from datetime import datetime, UTC
import warnings

# On ignore les warnings pour un affichage propre dans le terminal
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================
# CONFIGURATION (CORRIGÉE EN 127.0.0.1)
# ============================================
KAFKA_CONF = {
    'bootstrap.servers': '127.0.0.1:9092', 
    'group.id': 'ml-group-final', 
    'auto.offset.reset': 'latest'
}
ES = Elasticsearch(['http://127.0.0.1:9200'])

# Chargement du modèle entraîné
try:
    model = joblib.load('blood_pressure_model.pkl')
except Exception as e:
    print(f"❌ Erreur : Impossible de charger blood_pressure_model.pkl. Assurez-vous que le fichier est présent.")
    model = None

def predict_and_index():
    if model is None: return

    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe(['blood_pressure_topic'])
    print("=" * 80)
    print(" 🧠 IA PRÉDICTIVE ACTIVÉE - Analyse des flux Kafka en temps réel")
    print("=" * 80)
    print("📡 En attente de données pour prédiction...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        if msg.error(): continue
        
        try:
            # Extraction des données FHIR
            data = json.loads(msg.value().decode('utf-8'))
            
            # Extraction des valeurs numériques
            sys = data['component'][0]['valueQuantity']['value']
            dia = data['component'][1]['valueQuantity']['value']
            
            # Récupération de l'âge depuis les extensions si disponible (sinon 45 par défaut)
            age = 45
            for ext in data.get('extension', []):
                if ext['url'] == 'patient-demographics':
                    demo = json.loads(ext['valueString'])
                    age = demo.get('age', 45)
            
            # Préparation pour le modèle (Format exact attendu par le RandomForest)
            input_data = pd.DataFrame([[sys, dia, age, 0]], columns=['sys', 'dia', 'patient_age', 'gen_val'])
            
            # Prédiction via le modèle ML
            res = model.predict(input_data)[0]
            labels = {0: 'Low', 1: 'Moderate', 2: 'High', 3: 'Critical'}
            prediction = labels[res]

            # Indexation dans l'index spécialisé pour le ML
            doc = {
                'timestamp': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'systolic': sys,
                'diastolic': dia,
                'patient_age': age,
                'ml_predicted_risk': prediction
            }
            
            ES.index(index="blood_pressure_ml_predictions", document=doc)
            
            # Affichage console pour la démo
            emoji_ml = "🔮"
            print(f"{emoji_ml} IA -> BP: {sys}/{dia} | ÂGE: {age} | PRÉDICTION ML: {prediction}")

        except Exception as e:
            print(f" ⚠️ Erreur lors de la prédiction : {e}")

if __name__ == "__main__":
    predict_and_index()