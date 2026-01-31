# 🔧 Guide d'Installation et Dépannage

## Installation Rapide

### 1. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 2. Lancer l'infrastructure Docker

```bash
docker-compose up -d
```

### 3. Lancer le système

```bash
# Terminal 1 : Consumer
python consumer.py

# Terminal 2 : Producer
python producer.py
#Partie 2 : ML
# Terminal 3  : train ML
python train_ml.py
# Terminal 4  : Consumer ML
python consumer_ml.py
```

### 4. Accéder aux interfaces

- **Kibana** : http://localhost:5601
- **Elasticsearch** : http://localhost:9200

---

## ❌ Problèmes Fréquents et Solutions

### Problème 1 : Container already in use

**Erreur :**
```
Error response from daemon: Conflict. The container name "/elasticsearch" is already in use
```

**Solution :**
```bash
# Arrêter tous les containers
docker stop zookeeper elasticsearch kafka kibana

# Supprimer les containers
docker rm zookeeper elasticsearch kafka kibana

# Relancer
docker-compose up -d
```

---

### Problème 2 : Erreur Microsoft Visual C++

**Erreur :**
```
distutils.errors.DistutilsPlatformError: Microsoft Visual C++ 14.0 or greater is required
```

**Solution :**
```bash
pip install confluent-kafka elasticsearch faker scikit-learn pandas joblib
```

---

### Problème 3 : Kafka ne démarre pas

**Erreur :** Kafka ne répond pas ou erreur de connexion

**Solution :**
```bash
# Attendre 30 secondes puis redémarrer Kafka
docker-compose restart kafka
```

---

### Problème 4 : Consumer ne reçoit pas de messages

**Cause :** Le group.id est déjà utilisé

**Solution :** Modifier `consumer.py` ligne 17 :
```python
# Changer le numéro (v9 → v10)
KAFKA_GROUP_ID = 'health-monitor-final-v10'
```

---

### Problème 5 : Elasticsearch ne démarre pas

**Erreur :** Container elasticsearch s'arrête immédiatement

**Solution :**
```bash
# Vérifier les logs
docker logs elasticsearch

# Si problème de mémoire, augmenter la RAM Docker
# Ou réduire la mémoire dans docker-compose.yml :
# ES_JAVA_OPTS=-Xms256m -Xmx256m
```

---

### Problème 6 : Port déjà utilisé

**Erreur :**
```
Bind for 0.0.0.0:9200 failed: port is already allocated
```

**Solution :**
```bash
# Trouver le processus qui utilise le port
netstat -ano | findstr :9200

# Arrêter tous les containers Docker
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Relancer
docker-compose up -d
```

---

### Problème 7 : Version attribute obsolete

**Warning :**
```
the attribute `version` is obsolete, it will be ignored
```

**Solution :** Ce n'est qu'un warning, pas une erreur. Tu peux l'ignorer ou supprimer la ligne `version: '3.8'` dans `docker-compose.yml`

---

## 🔄 Reset Complet

Si rien ne marche, faire un reset complet :

```bash
# Arrêter tout
docker-compose down

# Supprimer tous les containers
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Supprimer les volumes (attention : supprime les données)
docker volume prune -f

# Relancer
docker-compose up -d
```

---

## ✅ Vérifier que tout fonctionne

```bash
# Vérifier les containers
docker ps

# Doit afficher 4 containers : zookeeper, kafka, elasticsearch, kibana

# Tester Elasticsearch
curl http://localhost:9200

# Tester Kibana (ouvrir dans navigateur)
# http://localhost:5601
```
