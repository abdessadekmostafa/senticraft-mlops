import os
import time
import pickle
import datetime
import pandas as pd
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import psycopg2
# Connexion Supabase
DB_URL = os.getenv("DATABASE_URL")

def save_feedback_db(feedback):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO feedback (timestamp, text, predicted_sentiment, actual_sentiment,
                              predicted_category, actual_category, is_different)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        feedback["timestamp"],
        feedback["text"],
        feedback["predicted_sentiment"],
        feedback["actual_sentiment"],
        feedback["predicted_category"],
        feedback["actual_category"],
        feedback["is_different"]
    ))
    conn.commit()
    cur.close()
    conn.close()

app = FastAPI(
    title="SentiCraft MLOps API",
    description="API de production pour la classification de sentiment et thématique des reviews clients.",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes locales facilement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour le modèle et le suivi
MODEL_ARTIFACTS = None
API_METRICS = {
    "total_requests": 0,
    "total_errors": 0,
    "latencies_ms": [],
    "sentiment_counts": {"Positif": 0, "Neutre": 0, "Négatif": 0},
    "category_counts": {"Produit": 0, "Livraison": 0, "Service Client": 0, "Prix": 0},
    "feedback_count": 0,
    "start_time": time.time()
}

# Historique glissant des dernières prédictions pour le calcul du drift
PREDICTION_HISTORY: List[Dict] = []
MAX_HISTORY_LEN = 100

# Base de données de feedback client (CSV)
FEEDBACK_CSV_PATH = None

# Pydantic Schemas
class PredictionRequest(BaseModel):
    text: str = Field(..., example="La livraison est en retard de 3 jours, c'est intolérable.")

class PredictionResponse(BaseModel):
    text: str
    sentiment: str
    sentiment_confidence: float
    category: str
    category_confidence: float
    latency_ms: float
    timestamp: str

class FeedbackRequest(BaseModel):
    text: str
    predicted_sentiment: str
    actual_sentiment: str
    predicted_category: str
    actual_category: str

@app.on_event("startup")
def load_model():
    global MODEL_ARTIFACTS, FEEDBACK_CSV_PATH
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "models", "registry", "model.pkl")
    FEEDBACK_CSV_PATH = os.path.join(base_dir, "data", "feedback_store.csv")
    
    print(f"Chargement du modèle de production depuis : {model_path}")
    try:
        with open(model_path, "rb") as f:
            MODEL_ARTIFACTS = pickle.load(f)
        print("Modèle chargé avec succès.")
    except Exception as e:
        print(f"ERREUR : Impossible de charger le modèle : {e}")
        MODEL_ARTIFACTS = None

@app.get("/health")
def health_check():
    """Vérifie l'état de l'API (Liveness/Readiness probe)."""
    if MODEL_ARTIFACTS is None:
        raise HTTPException(status_code=503, detail="Le modèle n'est pas chargé.")
    return {
        "status": "healthy",
        "model_loaded": True,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """Effectue une prédiction en temps réel du sentiment et de la catégorie."""
    global MODEL_ARTIFACTS
    start_time = time.perf_counter()
    
    if MODEL_ARTIFACTS is None:
        API_METRICS["total_errors"] += 1
        raise HTTPException(status_code=503, detail="Le modèle de classification n'est pas prêt.")
        
    try:
        text = request.text
        vectorizer = MODEL_ARTIFACTS["vectorizer"]
        model_sent = MODEL_ARTIFACTS["model_sentiment"]
        model_cat = MODEL_ARTIFACTS["model_category"]
        
        # Inférence
        features = vectorizer.transform([text])
        
        # Prédiction Sentiment
        pred_sent = model_sent.predict(features)[0]
        probs_sent = model_sent.predict_proba(features)[0]
        conf_sent = float(max(probs_sent))
        
        # Prédiction Catégorie
        pred_cat = model_cat.predict(features)[0]
        probs_cat = model_cat.predict_proba(features)[0]
        conf_cat = float(max(probs_cat))
        
        latency = (time.perf_counter() - start_time) * 1000
        
        # Enregistrement des métriques
        API_METRICS["total_requests"] += 1
        API_METRICS["sentiment_counts"][pred_sent] += 1
        API_METRICS["category_counts"][pred_cat] += 1
        
        # Garder en mémoire les 100 dernières latences pour la moyenne glissante
        API_METRICS["latencies_ms"].append(latency)
        if len(API_METRICS["latencies_ms"]) > 100:
            API_METRICS["latencies_ms"].pop(0)
            
        # Mise à jour de l'historique glissant
        prediction_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "sentiment": pred_sent,
            "category": pred_cat
        }
        PREDICTION_HISTORY.append(prediction_record)
        if len(PREDICTION_HISTORY) > MAX_HISTORY_LEN:
            PREDICTION_HISTORY.pop(0)
            
        return PredictionResponse(
            text=text,
            sentiment=pred_sent,
            sentiment_confidence=conf_sent,
            category=pred_cat,
            category_confidence=conf_cat,
            latency_ms=round(latency, 2),
            timestamp=datetime.datetime.now().isoformat()
        )
        
    except Exception as e:
        API_METRICS["total_errors"] += 1
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de l'inférence : {str(e)}")

def save_feedback_bg(feedback_data: Dict):
    """Enregistre le feedback utilisateur de manière asynchrone (Background Task)."""
    global FEEDBACK_CSV_PATH
    try:
        df = pd.DataFrame([feedback_data])
        # Si le fichier n'existe pas, écrire les en-têtes
        write_header = not os.path.exists(FEEDBACK_CSV_PATH)
        df.to_csv(FEEDBACK_CSV_PATH, mode='a', header=write_header, index=False, encoding='utf-8')
    except Exception as e:
        print(f"Erreur lors de l'écriture du feedback : {e}")

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Enregistre une correction de prédiction pour le réapprentissage futur (Feedback Loop)."""
    global FEEDBACK_CSV_PATH
    
    feedback_record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "text": request.text,
        "predicted_sentiment": request.predicted_sentiment,
        "actual_sentiment": request.actual_sentiment,
        "predicted_category": request.predicted_category,
        "actual_category": request.actual_category,
        "is_different": (request.predicted_sentiment != request.actual_sentiment) or (request.predicted_category != request.actual_category)
    }
    
    API_METRICS["feedback_count"] += 1
    
    # Exécuter l'écriture fichier en tâche de fond pour ne pas bloquer l'appelant
    background_tasks.add_task(save_feedback_db, feedback_record)
    
    return {"status": "success", "message": "Feedback enregistré pour le réapprentissage."}

@app.get("/metrics")
def get_metrics():
    """Retourne les métriques de monitoring de l'API et de santé du modèle (Drift)."""
    uptime = time.time() - API_METRICS["start_time"]
    avg_latency = sum(API_METRICS["latencies_ms"]) / len(API_METRICS["latencies_ms"]) if API_METRICS["latencies_ms"] else 0.0
    
    # Calcul du drift de données (Drift de concept ou de distribution)
    # Référence de la distribution d'entraînement :
    # Sentiment : 34% Positif, 33% Neutre, 33% Négatif
    # Catégorie : 25% partout
    drift_alert = False
    drift_score = 0.0
    
    if len(PREDICTION_HISTORY) >= 30:
        # Analyser la proportion de "Négatif" dans les 30 derniers feedbacks.
        # Si la proportion de négatif dépasse 55%, on alerte sur une dérive potentielle (ex: bug système)
        last_reviews = PREDICTION_HISTORY[-30:]
        neg_count = sum(1 for r in last_reviews if r["sentiment"] == "Négatif")
        neg_ratio = neg_count / len(last_reviews)
        
        # Drift score normalisé par rapport à la référence (0.33)
        # Si neg_ratio passe de 33% à 60%, drift_score augmente
        drift_score = max(0.0, (neg_ratio - 0.33) / (1.0 - 0.33))
        if neg_ratio > 0.55:
            drift_alert = True
            
    # Récupérer les feedbacks récents de correction si disponibles
    recent_feedbacks = []
    if FEEDBACK_CSV_PATH and os.path.exists(FEEDBACK_CSV_PATH):
        try:
            df = pd.read_csv(FEEDBACK_CSV_PATH)
            # Prendre les 5 derniers
            recent_feedbacks = df.tail(5).to_dict(orient="records")
        except:
            pass
            
    return {
        "uptime_seconds": int(uptime),
        "total_requests": API_METRICS["total_requests"],
        "total_errors": API_METRICS["total_errors"],
        "average_latency_ms": round(avg_latency, 2),
        "sentiment_distribution": API_METRICS["sentiment_counts"],
        "category_distribution": API_METRICS["category_counts"],
        "feedback_loop": {
            "total_submitted": API_METRICS["feedback_count"],
            "recent_corrections": recent_feedbacks
        },
        "model_monitoring": {
            "drift_detected": drift_alert,
            "drift_score": round(drift_score, 4),
            "analyzed_window_size": len(PREDICTION_HISTORY)
        }
    }

# Servir les fichiers statiques (Dashboard de monitoring et Playground)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "src", "static")
os.makedirs(static_dir, exist_ok=True)

# Monter le dossier static pour y accéder directement sur http://localhost:8000/
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
