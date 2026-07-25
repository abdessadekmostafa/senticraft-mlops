import pytest
from fastapi.testclient import TestClient
from src.app import app
from src.data_prep import generate_synthetic_reviews
from unittest.mock import patch
import psycopg2

client = TestClient(app)

@patch("psycopg2.connect")
def test_api_feedback(mock_connect):
    """Vérifie que l'enregistrement de feedback fonctionne sans vraie base."""
    mock_connect.return_value = True
    with TestClient(app) as client:
        payload = {
            "text": "Le prix est trop élevé.",
            "predicted_sentiment": "Neutre",
            "actual_sentiment": "Négatif",
            "predicted_category": "Produit",
            "actual_category": "Prix"
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Feedback enregistré pour le réapprentissage."
        }


def test_dataset_generation():
    """Vérifie que la génération du dataset synthétique produit un DataFrame correct."""
    df = generate_synthetic_reviews(n_samples=50)
    assert len(df) == 50
    assert list(df.columns) == ["review_id", "text", "sentiment", "category"]
    assert df["sentiment"].isin(["Positif", "Neutre", "Négatif"]).all()
    assert df["category"].isin(["Produit", "Livraison", "Service Client", "Prix"]).all()


def test_api_health():
    """Vérifie l'endpoint /health de l'API avec le démarrage complet (chargement du modèle)."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True


def test_api_predict():
    """Vérifie que l'endpoint /predict retourne des prédictions formatées correctement."""
    with TestClient(app) as client:
        payload = {"text": "Le colis est arrivé très vite, emballage superbe."}
        response = client.post("/predict", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "text" in data
        assert data["text"] == payload["text"]
        assert "sentiment" in data
        assert data["sentiment"] in ["Positif", "Neutre", "Négatif"]
        assert "category" in data
        assert data["category"] == "Livraison"
        assert "sentiment_confidence" in data
        assert "category_confidence" in data
        assert "latency_ms" in data
