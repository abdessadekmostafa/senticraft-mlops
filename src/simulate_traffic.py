import time
import random
import requests

API_URL = "http://127.0.0.1:8000"

NORMAL_REVIEWS = [
    # Positive product
    "Ce téléphone est super, l'écran est magnifique et fluide.",
    "Très bon produit, la batterie tient deux jours sans problème.",
    "Rapport qualité prix excellent pour ces écouteurs.",
    # Positive delivery
    "Reçu très rapidement, emballage impeccable.",
    "Livraison en 24h, livreur poli. Je recommande !",
    # Positive service
    "Service client disponible et très aimable. Merci !",
    "SAV réactif, ils m'ont renvoyé un article neuf en 2 jours.",
    # Neutral
    "Le produit est correct, pas incroyable mais fait le job.",
    "Prix dans la moyenne, livraison sans encombre.",
    "Service client poli mais le temps d'attente est un peu long."
]

DRIFT_REVIEWS = [
    # Critical delivery problems
    "Livraison catastrophique ! Le colis est arrivé complètement déchiré.",
    "Retard inacceptable de 5 jours, aucune nouvelle du livreur.",
    "Le colis a été jeté par-dessus le portail et s'est cassé.",
    "Deuxième retard cette semaine, je change de site.",
    "Suivi de livraison faux, mon colis est perdu dans la nature.",
    "Le transporteur n'est jamais venu, service de livraison nul.",
    "Livreur impoli qui a refusé de monter l'étage."
]

def simulate():
    print("====================================================")
    # Check if server is running
    try:
        res = requests.get(f"{API_URL}/health")
        if res.status_code != 200:
            print("Erreur : L'API n'est pas prête.")
            return
        print("API en ligne détectée. Début de la simulation...")
    except requests.exceptions.ConnectionError:
        print("Erreur : Impossible de se connecter à l'API FastAPI à http://localhost:8000.")
        print("Veuillez d'abord démarrer le serveur de production FastAPI avec la commande :")
        print("  uv run uvicorn src.app:app --reload")
        return
    
    print("====================================================")
    print("Phase 1 : Trafic standard (Production normale)")
    print("Envoi de commentaires normaux...")
    print("Regardez votre dashboard web sur http://localhost:8000/ pour voir les graphiques bouger.")
    print("====================================================")
    
    for i in range(25):
        review = random.choice(NORMAL_REVIEWS)
        try:
            res = requests.post(f"{API_URL}/predict", json={"text": review})
            data = res.json()
            print(f"[Req {i+1}/55] Inférence réussie | Sentiment: {data['sentiment']} | Catégorie: {data['category']} | Latence: {data['latency_ms']}ms")
            
            # Envoyer occasionnellement un feedback utilisateur (correction simulée)
            if random.random() > 0.8:
                feedback_payload = {
                    "text": review,
                    "predicted_sentiment": data['sentiment'],
                    "actual_sentiment": "Neutre" if data['sentiment'] != "Neutre" else "Positif",
                    "predicted_category": data['category'],
                    "actual_category": data['category'] # thématique correcte
                }
                requests.post(f"{API_URL}/feedback", json=feedback_payload)
                print("   ↳ [Feedback Loop] Correction utilisateur soumise et enregistrée dans le CSV !")
                
        except Exception as e:
            print(f"Erreur de requête : {e}")
            
        time.sleep(1.0)
        
    print("\n====================================================")
    print("Phase 2 : Apparition d'une anomalie en production !")
    print("Simulation d'une défaillance du partenaire de livraison.")
    print("Envoi d'un grand nombre de plaintes (sentiment Négatif / catégorie Livraison).")
    print("Le système de monitoring devrait bientôt lever une alerte de DATA DRIFT.")
    print("====================================================")
    
    for i in range(30):
        review = random.choice(DRIFT_REVIEWS)
        try:
            res = requests.post(f"{API_URL}/predict", json={"text": review})
            data = res.json()
            print(f"[Req {i+26}/55] Inférence réussie | Sentiment: {data['sentiment']} | Catégorie: {data['category']} | Latence: {data['latency_ms']}ms")
            
            # Vérifier l'état du drift via l'API metrics
            metrics_res = requests.get(f"{API_URL}/metrics")
            metrics = metrics_res.json()
            drift_info = metrics['model_monitoring']
            
            if drift_info['drift_detected']:
                print(f"   ⚠️  [MONITORING WARNING] ALERTE DRIFT ACTIVÉE ! Score de drift : {drift_info['drift_score']:.3f}")
                print("   ↳ Le dashboard web affiche désormais la bannière rouge d'alerte de dérive !")
                
        except Exception as e:
            print(f"Erreur de requête : {e}")
            
        time.sleep(1.0)
        
    print("\n====================================================")
    print("Simulation terminée !")
    print("Consultez l'onglet 'Real-time Monitor' et 'Feedback Loop' sur le Dashboard.")
    print("Vous verrez les graphiques mis à jour, l'alerte de drift et le fichier data/feedback_store.csv alimenté.")
    print("====================================================")

if __name__ == "__main__":
    simulate()
