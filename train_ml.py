import pandas as pd
import json
import os
import joblib
from sklearn.ensemble import RandomForestClassifier

def train_save_model():
    data = []
    path = "normal_data/patients_sains.json"
    
    if not os.path.exists(path):
        print(" Erreur : Fichier JSON introuvable.")
        return

    # 1. Lecture robuste du fichier
    print(" Chargement des données...")
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                data.append(json.loads(line))
            except Exception:
                # Si une ligne est mal formatée, on passe à la suivante
                continue
    
    # 2. Injection forcée de cas critiques pour corriger l'IA "aveugle"
    # On ajoute des exemples parfaits de crises pour que l'IA apprenne la différence
    data.append({"systolic": 210, "diastolic": 125, "patient_age": 65, "patient_gender": "Male", "risk_level": "Critical"})
    data.append({"systolic": 195, "diastolic": 118, "patient_age": 72, "patient_gender": "Female", "risk_level": "Critical"})
    data.append({"systolic": 180, "diastolic": 110, "patient_age": 55, "patient_gender": "Male", "risk_level": "Critical"})
    data.append({"systolic": 150, "diastolic": 95, "patient_age": 40, "patient_gender": "Female", "risk_level": "High"})

    df = pd.DataFrame(data)
    
    # Harmonisation intelligente des colonnes
    df['sys'] = df['systolic'].combine_first(df.get('systolic_pressure', df['systolic']))
    df['dia'] = df['diastolic'].combine_first(df.get('diastolic_pressure', df['diastolic']))
    df['gen_val'] = df['patient_gender'].map({'Male': 0, 'Female': 1}).fillna(0)
    
    risk_map = {'Low': 0, 'Moderate': 1, 'High': 2, 'Critical': 3}
    df['target'] = df['risk_level'].map(risk_map).fillna(0)

    # 3. Entraînement
    X = df[['sys', 'dia', 'patient_age', 'gen_val']]
    y = df['target']

    print(f"Apprentissage sur {len(df)} exemples variés...")
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    
    # Création du document pour le Consumer ML
    joblib.dump(model, 'blood_pressure_model.pkl')
    print(" TERMINÉ : Le modèle est prêt et l'IA est maintenant 'intelligente' !")

if __name__ == "__main__":
    train_save_model()