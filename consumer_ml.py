import json
import joblib
import pandas as pd
from confluent_kafka import Consumer
from elasticsearch import Elasticsearch
from datetime import datetime, UTC
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

KAFKA_CONF = {'bootstrap.servers': 'localhost:9092', 'group.id': 'ml-group-final', 'auto.offset.reset': 'latest'}
ES = Elasticsearch(['http://localhost:9200'])
model = joblib.load('blood_pressure_model.pkl')

def predict_and_index():
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe(['blood_pressure_topic'])
    print(" IA PRÉDICTIVE ACTIVÉE : Analyse des flux Kafka en cours...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        
        data = json.loads(msg.value().decode('utf-8'))
        
        try:
            # Extraction des valeurs FHIR
            sys = data['component'][0]['valueQuantity']['value']
            dia = data['component'][1]['valueQuantity']['value']
            age = 45 # Valeur par défaut
            gen = 0  # Male par défaut
            
            # Préparation pour le modèle
            input_data = pd.DataFrame([[sys, dia, age, gen]], columns=['sys', 'dia', 'patient_age', 'gen_val'])
            
            # Prédiction
            res = model.predict(input_data)[0]
            labels = {0: 'Low', 1: 'Moderate', 2: 'High', 3: 'Critical'}
            prediction = labels[res]

            # Indexation
            doc = {
                'timestamp': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'systolic': sys,
                'diastolic': dia,
                'ml_predicted_risk': prediction
            }
            ES.index(index="blood_pressure_ml_predictions", document=doc)
            print(f"🔮 IA -> BP: {sys}/{dia} | RISQUE PRÉDIT: {prediction}")

        except Exception as e:
            print(f" Erreur : {e}")

if __name__ == "__main__":
    predict_and_index()