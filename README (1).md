# 🩺 Système de Surveillance de Pression Artérielle avec Kafka

## 📋 Description du Projet

Ce projet implémente un système complet de surveillance des données de pression artérielle des patients en temps réel. Il utilise le standard **FHIR** (Fast Healthcare Interoperability Resources) pour générer des observations médicales, **Apache Kafka** pour le streaming de données, **Elasticsearch** pour l'indexation des anomalies, et **Kibana** pour la visualisation.

### Architecture du Système

```
┌─────────────────┐     ┌─────────┐     ┌──────────────┐     ┌───────────────┐
│ FHIR Generator  │────▶│  Kafka  │────▶│   Consumer   │────▶│ Elasticsearch │
│   (producer.py) │     │  Topic  │     │ (consumer.py)│     │    + Kibana   │
└─────────────────┘     └─────────┘     └──────────────┘     └───────────────┘
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │ Consumer ML (IA)     │
                                    │ (consumer_ml.py)     │
                                    └──────────────────────┘
```

---

## 🛠️ Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Docker** et **Docker Compose** (version 3.8+)
- **Python 3.10+**
- **pip** (gestionnaire de paquets Python)

---

## 🚀 Guide de Lancement - Étape par Étape

### Étape 1 : Cloner ou Préparer le Projet

Créez un dossier pour votre projet et placez-y tous les fichiers :

```bash
mkdir blood-pressure-monitoring
cd blood-pressure-monitoring
```

Fichiers requis dans le dossier :
- `docker-compose.yml`
- `producer.py`
- `consumer.py`
- `consumer_ml.py`
- `fhir_generator.py`
- `train_ml.py`
- `requirements.txt`

---

### Étape 2 : Installation des Dépendances Python

```bash
# Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate
# Sur Linux/Mac :
source venv/bin/activate

# Installer toutes les dépendances
pip install -r requirements.txt
```

---

### Étape 3 : Démarrer l'Infrastructure Docker

Lancez tous les services (Zookeeper, Kafka, Elasticsearch, Kibana) :

```bash
docker-compose up -d
```

**Vérification du statut des conteneurs :**

```bash
docker-compose ps
```

Vous devriez voir 4 conteneurs en état "Up" :
- `zookeeper`
- `kafka`
- `elasticsearch`
- `kibana`

**Attendre que tous les services soient prêts (~30-60 secondes) :**

```bash
# Vérifier que Elasticsearch répond
curl http://localhost:9200

# Vérifier que Kafka est prêt
docker logs kafka 2>&1 | grep "started"
```

---

### Étape 4 : Lancer le Consumer (Terminal 1)

Ouvrez un **premier terminal** et lancez le consumer qui écoute les messages Kafka :

```bash
# Activer l'environnement virtuel si nécessaire
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Lancer le consumer
python consumer.py
```

Vous verrez :
```
📡 Consumer prêt. Affichage détaillé activé...
```

Le consumer va :
- Écouter le topic Kafka `blood_pressure_topic`
- Indexer les anomalies (hypertension, hypotension, crise) dans Elasticsearch
- Sauvegarder les données normales dans `normal_data/patients_sains.json`

---

### Étape 5 : Lancer le Producer (Terminal 2)

Ouvrez un **deuxième terminal** et lancez le producer :

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac

# Lancer le producer (mode continu)
python producer.py

# Ou avec des options personnalisées :
python producer.py -i 10 -p 5      # 5 patients toutes les 10 secondes
python producer.py -n 3            # Seulement 3 batches puis arrêt
```

**Options disponibles :**
| Option | Description | Défaut |
|--------|-------------|--------|
| `-i`, `--interval` | Intervalle entre les batches (secondes) | 30 |
| `-p`, `--patients` | Nombre de patients par batch | 10 |
| `-n`, `--num-batches` | Nombre total de batches (null = infini) | None |

Vous verrez des messages comme :
```
✅ [14:32:15] Jean Dupont               | BP: 115/75 | normal               | Paris
🟠 [14:32:15] Marie Martin              | BP: 135/85 | hypertension_stage_1 | Lyon
🚨 [14:32:15] Pierre Durand             | BP: 185/125| hypertensive_crisis  | Marseille
```

---

### Étape 6 : Accéder à Kibana pour la Visualisation

1. Ouvrez votre navigateur et allez sur : **http://localhost:5601**

2. **Créer un Data View (Index Pattern) :**
   - Menu → Stack Management → Data Views
   - Cliquer sur "Create data view"
   - Name : `blood_pressure_anomalies`
   - Index pattern : `blood_pressure_anomalies`
   - Timestamp field : `timestamp`
   - Cliquer sur "Save data view to Kibana"

3. **Explorer les données :**
   - Menu → Discover
   - Sélectionner le data view `blood_pressure_anomalies`
   - Vous verrez toutes les anomalies indexées

4. **Créer un Dashboard :**
   - Menu → Dashboard → Create dashboard
   - Ajouter des visualisations :
     - **Pie chart** : Distribution par `risk_level`
     - **Bar chart** : Anomalies par `city`
     - **Line chart** : Évolution temporelle
     - **Map** : Répartition géographique (champ `location`)
     - **Data table** : Liste des patients critiques

---

### Étape 7 (Optionnel) : Activer le Module Machine Learning

#### 7.1 Entraîner le modèle

Attendez d'avoir accumulé des données normales, puis :

```bash
python train_ml.py
```

Cela crée le fichier `blood_pressure_model.pkl`.

#### 7.2 Lancer le Consumer ML (Terminal 3)

```bash
python consumer_ml.py
```

Le consumer ML prédit le niveau de risque en temps réel :
```
🔮 IA -> BP: 145/92 | RISQUE PRÉDIT: High
🔮 IA -> BP: 118/78 | RISQUE PRÉDIT: Low
```

Les prédictions sont indexées dans : `blood_pressure_ml_predictions`

---

## 📊 Niveaux de Risque et Catégories

| Catégorie | Systolique (mmHg) | Diastolique (mmHg) | Niveau de Risque |
|-----------|-------------------|--------------------| -----------------|
| Normal | < 120 | ET < 80 | - (archivé localement) |
| Elevated | 120-129 | ET < 80 | Moderate |
| Hypertension Stage 1 | 130-139 | OU 80-89 | Moderate |
| Hypertension Stage 2 | ≥ 140 | OU ≥ 90 | High |
| Hypertensive Crisis | > 180 | ET/OU > 120 | Critical |
| Hypotension | < 90 | OU < 60 | Low |

---

## 📁 Structure des Fichiers

```
blood-pressure-monitoring/
│
├── docker-compose.yml      # Configuration Docker (Kafka, ES, Kibana)
├── requirements.txt        # Dépendances Python
│
├── fhir_generator.py       # Génération des messages FHIR
├── producer.py             # Producteur Kafka
├── consumer.py             # Consommateur + indexation ES
│
├── train_ml.py             # Entraînement du modèle ML
├── consumer_ml.py          # Prédictions en temps réel
├── blood_pressure_model.pkl # Modèle ML sauvegardé
│
└── normal_data/            # Dossier des données normales
    └── patients_sains.json
```

---

## 🔧 Commandes Utiles

### Gestion Docker

```bash
# Démarrer tous les services
docker-compose up -d

# Arrêter tous les services
docker-compose down

# Voir les logs d'un service
docker logs kafka -f
docker logs elasticsearch -f

# Redémarrer un service
docker-compose restart kafka

# Supprimer les volumes (reset complet)
docker-compose down -v
```

### Vérification des Services

```bash
# Tester Elasticsearch
curl http://localhost:9200/_cluster/health?pretty

# Lister les index Elasticsearch
curl http://localhost:9200/_cat/indices?v

# Compter les documents dans l'index
curl http://localhost:9200/blood_pressure_anomalies/_count

# Voir les topics Kafka
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Réinitialisation

```bash
# Supprimer l'index Elasticsearch
curl -X DELETE http://localhost:9200/blood_pressure_anomalies

# Supprimer les données locales
rm -rf normal_data/

# Supprimer le modèle ML
rm blood_pressure_model.pkl
```

---

## ❓ Dépannage

### Le Consumer ne reçoit pas de messages

1. Vérifiez que Kafka est bien démarré : `docker logs kafka`
2. Vérifiez que le Producer envoie bien : regardez les logs du Producer
3. Changez le `group.id` dans `consumer.py` (incrémentez la version)

### Elasticsearch ne démarre pas

1. Vérifiez la mémoire disponible (ES nécessite ~512MB)
2. Consultez les logs : `docker logs elasticsearch`
3. Augmentez la mémoire Docker si nécessaire

### Kibana affiche "No results found"

1. Vérifiez que des anomalies ont été indexées :
   ```bash
   curl http://localhost:9200/blood_pressure_anomalies/_count
   ```
2. Vérifiez le time range dans Kibana (étendez-le si nécessaire)
3. Recréez le Data View si le mapping a changé

### Erreur "confluent-kafka not installed"

```bash
pip install confluent-kafka --break-system-packages
# ou dans un venv :
pip install confluent-kafka
```

---

## 📝 Auteurs

Projet réalisé dans le cadre du cours de Big Data / Systèmes Distribués.

---

## 📚 Ressources

- [Standard FHIR](https://www.hl7.org/fhir/overview.html)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Elasticsearch Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Kibana Guide](https://www.elastic.co/guide/en/kibana/current/index.html)
