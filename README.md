# 🧠 Présentation
SentiCraft est une API de classification sentiment et catégorie thématique pour des avis clients.
Le projet inclut un pipeline MLOps complet :
```text
entraînement automatique du modèle

API FastAPI en production

conteneurisation Docker

publication de l’image dans GHCR

déploiement automatique sur Render

stockage des feedbacks dans Supabase

pipeline CI/CD GitHub Actions
```

# 📂 Structure du projet
```text
Code
senticraft-mlops/
│
├── src/
│   ├── app.py                # API FastAPI (production)
│   ├── train.py              # Entraînement du modèle
│   ├── data_prep.py          # Préparation du dataset
│   ├── model_utils.py        # Chargement / sauvegarde modèle
│   └── ...
│
├── models/
│   ├── training_runs/        # Historique des runs
│   └── model_latest.pkl      # Modèle de production
│
├── Dockerfile                # Image Docker de production
├── requirements.txt          # Dépendances
├── verif_supabase.py         # Vérification DB Supabase
└── .github/workflows/ci.yml  # Pipeline CI/CD complet
```
# 🚀 Installation locale
```text
1. Cloner le projet
bash
git clone https://github.com/abdessadekmostafa/senticraft-mlops.git
cd senticraft-mlops


2. Installer les dépendances
bash
pip install -r requirements.txt


3. Entraîner le modèle
bash
python src/train.py


4. Lancer l’API localement
bash
uvicorn src.app:app --reload --port 8000
```
# 🐳 Docker
🔨 Build local (test)
```text
bash
docker build -t senticraft-api .
```text
# ▶️ Run local
bash
docker run -p 8000:8000 senticraft-api


# 🐳 Docker — Build pour GHCR (production)
# 🔨 Build image GHCR
bash
docker build -t ghcr.io/abdessadekmostafa/senticraft-mlops/senticraft-api:latest

.
# 📤 Push vers GHCR
bash
docker push ghcr.io/abdessadekmostafa/senticraft-mlops/senticraft-api:latest


# 🌐 Déploiement Render
Render récupère automatiquement l’image GHCR.
```

# Variables d’environnement nécessaires :
```text
DATABASE_URL=postgresql://postgres.<project>:<password>@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

Endpoints exposés :
```text
/predict

/feedback

/health

/db-test
```

# 🗄️ Supabase — Table feedback
```text
Colonnes :

Nom	Type
id	SERIAL
timestamp	TIMESTAMP
text	TEXT
predicted_sentiment	TEXT
actual_sentiment	TEXT
predicted_category	TEXT
actual_category	TEXT
is_different	BOOLEAN
```

# 🔁 Feedback Loop
```text
Chaque feedback envoyé via /feedback est stocké dans Supabase.

Les feedbacks où is_different = TRUE sont utilisés pour :

améliorer le dataset

réentraîner le modèle

mettre à jour model_latest.pkl

déclencher un redeploy automatique via CI/CD
```
# ⚙️ CI/CD — GitHub Actions
```text
Le pipeline CI/CD (.github/workflows/ci.yml) exécute :

1. Qualité du code & tests
Ruff

Pytest

2. Entraînement du modèle
data_prep.py

train.py

validation des métriques (seuils de production)

3. Build Docker + Push GHCR
docker/build-push-action

tags : SHA + latest

4. Déploiement staging (GitOps simulé)
👉 Grâce à ce pipeline, aucune commande Docker manuelle n’est nécessaire pour la production.
```

# 📬 API Endpoints
```text
🔹 Prédiction
http
POST /predict
Body :

json
{
  "text": "Le produit est arrivé en retard"
}
🔹 Feedback
http
POST /feedback
Body :

json
{
  "text": "...",
  "predicted_sentiment": "...",
  "actual_sentiment": "...",
  "predicted_category": "...",
  "actual_category": "...",
  "is_different": true
}
``` 
# 🧪 Vérifier Supabase
```text
bash
python verif_supabase.py
```
# 🏁 Conclusion
```text
SentiCraft est un pipeline MLOps complet :

modèle entraîné automatiquement

API FastAPI dockerisée

image GHCR

déploiement Render

feedback loop Supabase

CI/CD GitHub Actions

Le projet est scalable, automatisé, et prêt pour la production.
```
