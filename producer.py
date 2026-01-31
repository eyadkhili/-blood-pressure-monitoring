import json
import time
import sys

try:
    from confluent_kafka import Producer
except ImportError:
    print(" confluent-kafka n'est pas installé!")
    print("  Installez-le avec: pip install confluent-kafka")
    sys.exit(1)

from fhir_generator import generate_fhir_observation

# ============================================
# CONFIGURATION (CORRIGÉE EN 127.0.0.1)
# ============================================
KAFKA_BOOTSTRAP_SERVERS = '127.0.0.1:9092'
KAFKA_TOPIC = 'blood_pressure_topic'
MESSAGE_INTERVAL = 30
PATIENTS_PER_BATCH = 10


def delivery_report(err, msg):
    """Callback pour confirmer la livraison du message."""
    if err is not None:
        print(f" Erreur livraison: {err}")


def create_producer():
    """Crée le producteur Kafka avec confluent-kafka."""
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'client.id': 'blood-pressure-producer'
    }
    
    try:
        producer = Producer(conf)
        print(" Connexion à Kafka réussie (127.0.0.1)!")
        return producer
    except Exception as e:
        print(f" Erreur Kafka : {e}")
        sys.exit(1)


def extract_info_from_fhir(fhir_message):
    """Extrait les infos pour affichage."""
    systolic = fhir_message['component'][0]['valueQuantity']['value']
    diastolic = fhir_message['component'][1]['valueQuantity']['value']
    patient_name = fhir_message['subject']['display']
    patient_id = fhir_message['subject']['reference'].split('/')[-1]
    
    location = {}
    category = "unknown"
    
    for ext in fhir_message.get('extension', []):
        if ext.get('url') == 'measurement-location':
            location = json.loads(ext.get('valueString', '{}'))
        if ext.get('url') == 'blood-pressure-category':
            category = ext.get('valueString', 'unknown')
    
    return {
        'patient_id': patient_id,
        'patient_name': patient_name,
        'systolic': systolic,
        'diastolic': diastolic,
        'location': location,
        'category': category
    }


def send_message(producer, message):
    """Envoie un message au topic Kafka."""
    try:
        patient_id = message['subject']['reference'].split('/')[-1]
        
        producer.produce(
            KAFKA_TOPIC,
            key=patient_id.encode('utf-8'),
            value=json.dumps(message, ensure_ascii=False).encode('utf-8'),
            callback=delivery_report
        )
        producer.poll(0)
        
        info = extract_info_from_fhir(message)
        emoji_map = {
            'normal': '✅', 'elevated': '🟡', 'hypertension_stage_1': '🟠',
            'hypertension_stage_2': '🔴', 'hypertensive_crisis': '🚨', 'hypotension': '🔵'
        }
        emoji = emoji_map.get(info['category'], '❓')
        
        print(f"{emoji} [{time.strftime('%H:%M:%S')}] {info['patient_name'][:25]:25} | "
              f"BP: {info['systolic']}/{info['diastolic']} | {info['category']:20} | "
              f"{info['location'].get('city', 'N/A')}")
        return True
    except Exception as e:
        print(f" Erreur : {e}")
        return False


def run_producer(num_batches=None):
    """Exécute le producteur Kafka."""
    print("=" * 80)
    print(" KAFKA PRODUCER - Pression Artérielle (Python 3.14 Compatible)")
    print("=" * 80)
    print(f" Kafka: {KAFKA_BOOTSTRAP_SERVERS} | Topic: {KAFKA_TOPIC}")
    print(f" Intervalle: {MESSAGE_INTERVAL}s | Patients/batch: {PATIENTS_PER_BATCH}")
    print("=" * 80)
    
    producer = create_producer()
    batch_count = 0
    total_messages = 0
    
    try:
        print(f"\n🔄 Envoi de {PATIENTS_PER_BATCH} patients toutes les {MESSAGE_INTERVAL} secondes...\n")
        
        while True:
            batch_count += 1
            print(f"\n BATCH #{batch_count} - {time.strftime('%H:%M:%S')}")
            print("-" * 80)
            
            for _ in range(PATIENTS_PER_BATCH):
                fhir_message = generate_fhir_observation()
                send_message(producer, fhir_message)
                total_messages += 1
            
            # Flush pour s'assurer que tous les messages sont envoyés
            producer.flush()
            
            print(f"\n Batch #{batch_count}: {PATIENTS_PER_BATCH} envoyés | Total: {total_messages}")
            
            if num_batches and batch_count >= num_batches:
                break
            
            print(f"⏳ Prochain batch dans {MESSAGE_INTERVAL} secondes...")
            time.sleep(MESSAGE_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n Arrêt...")
    finally:
        producer.flush()
        print(f"\n RÉSUMÉ: {batch_count} batches | {total_messages} messages")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-batches', type=int, default=None)
    parser.add_argument('-i', '--interval', type=int, default=30)
    parser.add_argument('-p', '--patients', type=int, default=10)
    args = parser.parse_args()
    
    if args.interval:
        MESSAGE_INTERVAL = args.interval
    if args.patients:
        PATIENTS_PER_BATCH = args.patients
    
    run_producer(num_batches=args.num_batches)