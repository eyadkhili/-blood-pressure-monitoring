# 🩺 Système de Surveillance de Pression Artérielle en Temps Réel

## 📋 Problématique

### Contexte
L'hypertension artérielle est un problème de santé publique majeur en France, touchant environ **17 millions de personnes**. Elle est souvent appelée le "tueur silencieux" car elle ne présente généralement pas de symptômes mais peut entraîner des complications graves : AVC, infarctus, insuffisance rénale.

### Problème à résoudre
**Comment surveiller en temps réel les mesures de pression artérielle de multiples patients, détecter automatiquement les anomalies nécessitant une intervention médicale urgente, et visualiser géographiquement la répartition des cas critiques ?**

### Solution proposée
Un système de streaming Big Data utilisant :
- **Apache Kafka** : pour la transmission en temps réel des données
- **Elasticsearch** : pour le stockage et l'indexation des anomalies
- **Kibana** : pour la visualisation et le monitoring en temps réel
- **Format FHIR** : standard international d'interopérabilité des données de santé

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE DU SYSTÈME                          │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐         ┌──────────────┐         ┌──────────────────┐
  │   PRODUCER   │         │    KAFKA     │         │    CONSUMER      │
  │   (Python)   │────────▶│    BROKER    │────────▶│    (Python)      │
  │              │         │              │         │                  │
  │ • 10 patients│         │    Topic:    │         │ • Classification │
  │   aléatoires │         │ blood_       │         │ • Risk Level     │
  │ • Toutes 30s │         │ pressure_    │         │ • Routage données│
  │ • Format FHIR│         │ topic        │         │                  │
  │ • + Location │         │              │         │                  │
  └──────────────┘         └──────────────┘         └────────┬─────────┘
                                                             │
                                          ┌──────────────────┴──────────────────┐
                                          │                                     │
                                    ┌─────▼─────┐                        ┌──────▼──────┐
                                    │  FICHIERS │                        │ELASTICSEARCH│
                                    │   JSON    │                        │             │
                                    │  (Normal) │                        │ (Anomalies) │
                                    └───────────┘                        └──────┬──────┘
                                                                                │
                                                                         ┌──────▼──────┐
                                                                         │   KIBANA    │
                                                                         │  Dashboard  │
                                                                         │ • Graphiques│
                                                                         │ • Carte GPS │
                                                                         │ • Alertes   │
                                                                         └─────────────┘
```

---

## 📊 Classification de la Pression Artérielle

| Catégorie | Systolique (mmHg) | Diastolique (mmHg) | Niveau de Risque |
|-----------|-------------------|-------------------|------------------|
| **Normal** | < 120 | ET < 80 | 🟢 Low |
| **Elevated** | 120-129 | ET < 80 | 🟢 Low |
| **Hypertension Stage 1** | 130-139 | OU 80-89 | 🟠 Moderate |
| **Hypertension Stage 2** | ≥ 140 | OU ≥ 90 | 🟠 Moderate / 🔴 High |
| **Hypertensive Crisis** | > 180 | OU > 120 | 🚨 Critical |
| **Hypotension** | < 90 | OU < 60 | 🟠 Moderate / 🔴 High |

---

## 🚀 Guide de Démarrage

### 1. Prérequis
- Docker et Docker Compose

- pip

### 2. Installation

```bash
# Installer les dépendances
python -m pip install kafka-python-ng elasticsearch faker

python -m pip uninstall kafka-python-ng kafka-python


python -m pip install confluent-kafka

### 3. Démarrer l'infrastructure

```bash
# Lancer Kafka, Elasticsearch, Kibana
docker-compose up -d
( au cas ou il marche pas je dois faire ca
 docker rm -f kibana
 docker-compose up -d)
# Vérifier le statut
docker-compose ps

# Attendre 30-60 secondes que tout démarre
```

### 4. Lancer le système

**Terminal 1 - Consumer :**
```bash
python consumer.py
```

**Terminal 2 - Producer :**
```bash
python producer.py
```

### 5. Accéder à Kibana
- URL : http://localhost:5601

---

## 📈 VISUALISATIONS KIBANA À CRÉER

### Étape 1 : Supprimer l'ancien index (si existant)

Dans **Dev Tools** (Menu → Management → Dev Tools) :
```json
DELETE blood_pressure_anomalies
```

### Étape 2 : Relancer Consumer puis Producer

### Étape 3 : Créer le Data View

1. **Menu** → **Stack Management** → **Data Views**
2. **Create data view**
3. Configurer :
   - Name : `blood_pressure_anomalies`
   - Index pattern : `blood_pressure_anomalies`
   - Timestamp field : `timestamp`
4. **Save**

### Étape 4 : Créer les Visualisations

#### 📊 Visualisation 1 : Répartition par Catégorie (Pie Chart)
- **Type** : Pie
- **Metric** : Count
- **Bucket** : Terms → Field: `category`
- **Titre** : "Répartition des Anomalies par Catégorie"

#### 📊 Visualisation 2 : Répartition par Niveau de Risque (Donut)
- **Type** : Pie (Donut)
- **Metric** : Count
- **Bucket** : Terms → Field: `risk_level`
- **Titre** : "Distribution des Niveaux de Risque"

#### 📊 Visualisation 3 : Évolution Temporelle (Line Chart)
- **Type** : Line
- **Y-axis** : Count
- **X-axis** : Date Histogram → Field: `timestamp` → Interval: 30 seconds
- **Split Series** : Terms → Field: `category`
- **Titre** : "Évolution des Anomalies dans le Temps"

#### 📊 Visualisation 4 : Moyenne des Pressions (Metrics)
- **Type** : Metric
- **Metrics** : 
  - Average → `systolic_pressure`
  - Average → `diastolic_pressure`
- **Titre** : "Moyennes de Pression Artérielle"

#### 📊 Visualisation 5 : Anomalies par Ville (Bar Chart)
- **Type** : Horizontal Bar
- **Metric** : Count
- **Bucket** : Terms → Field: `city`
- **Titre** : "Nombre d'Anomalies par Ville"

#### 📊 Visualisation 6 : Compteurs (Metrics)
- **Type** : Metric
- **Metrics** :
  - Count (Total des anomalies)
  - Unique Count → `patient_id` (Patients uniques)
- **Titre** : "Statistiques Globales"

#### 🗺️ Visualisation 7 : Carte Géographique (Maps)
1. **Menu** → **Maps**
2. **Add layer** → **Documents**
3. Index pattern : `blood_pressure_anomalies`
4. Le champ `location` (geo_point) sera détecté automatiquement
5. **Tooltip fields** : patient_name, category, risk_level, city
6. **Titre** : "Localisation Géographique des Anomalies"

#### 📊 Visualisation 8 : Distribution par Âge (Histogram)
- **Type** : Bar
- **Metric** : Count
- **Bucket** : Histogram → Field: `patient_age` → Interval: 10
- **Titre** : "Distribution des Anomalies par Tranche d'Âge"

#### 📊 Visualisation 9 : Table des Dernières Anomalies
- **Type** : Data Table
- **Columns** : timestamp, patient_name, systolic_pressure, diastolic_pressure, category, risk_level, city
- **Sort** : timestamp (descending)
- **Titre** : "Dernières Anomalies Détectées"

### Étape 5 : Créer le Dashboard

1. **Menu** → **Dashboard** → **Create dashboard**
2. Ajouter toutes les visualisations créées
3. Disposer de manière logique :
   - En haut : Compteurs et Métriques
   - Milieu : Graphiques temporels et répartitions
   - Bas : Carte et Table détaillée
4. **Save** : "Dashboard Surveillance Pression Artérielle"

---

## 📁 Structure du Projet

```
blood-pressure-monitoring/
├── docker-compose.yml      # Infrastructure Docker
├── requirements.txt        # Dépendances Python
├── fhir_generator.py       # Génération messages FHIR + patients aléatoires
├── producer.py             # Producteur Kafka (10 patients / 30 sec)
├── consumer.py             # Consommateur + classification + risk_level
├── README.md               # Ce fichier
├── normal_data/            # Données normales (JSON local)
└── anomaly_data/           # Backup anomalies si ES indisponible
```

---

## 🔑 Points Clés pour la Présentation

### 1. Technologies utilisées
- **Apache Kafka** : Streaming temps réel, haute disponibilité
- **Elasticsearch** : Stockage distribué, recherche rapide
- **Kibana** : Visualisation interactive, dashboards
- **FHIR** : Standard international santé (HL7)
- **Python** : Faker, kafka-python-ng, elasticsearch

### 2. Fonctionnalités principales
- Génération de **10 patients aléatoires** toutes les **30 secondes**
- Classification automatique selon les **seuils médicaux AHA**
- Calcul du **niveau de risque** (low, moderate, high, critical)
- **Géolocalisation** des mesures (15 villes de France)
- Séparation : anomalies → Elasticsearch, normaux → fichiers locaux

### 3. Valeur ajoutée
- Détection précoce des cas critiques
- Visualisation géographique pour allocation des ressources
- Monitoring temps réel pour les équipes médicales
- Traçabilité complète des données (format FHIR)

---

## 👥 Auteurs

Projet Big Data - Système de Surveillance de Pression Artérielle
ML 
python -m pip install scikit-learn pandas joblib