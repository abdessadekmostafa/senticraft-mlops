import os
import json
import pickle
import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score

def train_pipeline():
    print("--- Étape 2 : Entraînement du Modèle ---")
    
    # Chemins
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "raw_reviews.csv")
    registry_dir = os.path.join(base_dir, "models", "registry")
    runs_dir = os.path.join(base_dir, "models", "training_runs")
    
    os.makedirs(registry_dir, exist_ok=True)
    os.makedirs(runs_dir, exist_ok=True)
    
    # 1. Chargement des données
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Le jeu de données {data_path} n'existe pas. Veuillez exécuter data_prep.py d'abord.")
        
    df = pd.read_csv(data_path)
    X = df["text"]
    y_sentiment = df["sentiment"]
    y_category = df["category"]
    
    # Split train/test (80% train, 20% test)
    # Stratification sur sentiment + catégorie pour avoir des ensembles équilibrés
    df['stratify_col'] = df['sentiment'] + "_" + df['category']
    
    X_train, X_test, y_train_sent, y_test_sent, y_train_cat, y_test_cat = train_test_split(
        X, y_sentiment, y_category, test_size=0.2, random_state=42, stratify=df['stratify_col']
    )
    
    print(f"Jeu d'entraînement : {len(X_train)} échantillons")
    print(f"Jeu de test : {len(X_test)} échantillons")
    
    # 2. Vectorisation TF-IDF
    print("Vectorisation du texte avec TF-IDF...")
    # ngram_range=(1,2) pour capturer les négations ou bi-grammes ("pas bon", "très bien")
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2), min_df=2)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # 3. Entraînement des modèles
    print("Entraînement du classifieur de sentiment...")
    model_sentiment = LogisticRegression(C=1.5, max_iter=1000, random_state=42)
    model_sentiment.fit(X_train_vec, y_train_sent)
    
    print("Entraînement du classifieur de catégorie...")
    model_category = LogisticRegression(C=1.5, max_iter=1000, random_state=42)
    model_category.fit(X_train_vec, y_train_cat)
    
    # 4. Évaluation
    # Sentiment
    preds_sent = model_sentiment.predict(X_test_vec)
    acc_sent = accuracy_score(y_test_sent, preds_sent)
    f1_sent = f1_score(y_test_sent, preds_sent, average="macro")
    
    # Catégorie
    preds_cat = model_category.predict(X_test_vec)
    acc_cat = accuracy_score(y_test_cat, preds_cat)
    f1_cat = f1_score(y_test_cat, preds_cat, average="macro")
    
    print("\n=== ÉVALUATION DU SENTIMENT ===")
    print(f"Accuracy : {acc_sent:.4f}")
    print(f"F1-Score Macro : {f1_sent:.4f}")
    print(classification_report(y_test_sent, preds_sent))
    
    print("=== ÉVALUATION DE LA CATÉGORIE ===")
    print(f"Accuracy : {acc_cat:.4f}")
    print(f"F1-Score Macro : {f1_cat:.4f}")
    print(classification_report(y_test_cat, preds_cat))
    
    # 5. Sauvegarde des artefacts (Model Registry)
    model_path = os.path.join(registry_dir, "model.pkl")
    print(f"Sauvegarde des modèles et du vectorizer dans le registre : {model_path}")
    artifacts = {
        "vectorizer": vectorizer,
        "model_sentiment": model_sentiment,
        "model_category": model_category,
        "classes_sentiment": list(model_sentiment.classes_),
        "classes_category": list(model_category.classes_)
    }
    with open(model_path, "wb") as f:
        pickle.dump(artifacts, f)
        
    # 6. Enregistrement de la Run d'entraînement (Experiment Tracking)
    run_metadata = {
        "timestamp": datetime.datetime.now().isoformat(),
        "dataset_info": {
            "path": data_path,
            "total_records": len(df),
            "train_records": len(X_train),
            "test_records": len(X_test)
        },
        "hyperparameters": {
            "tfidf_max_features": 2500,
            "tfidf_ngram_range": [1, 2],
            "logistic_regression_C": 1.5
        },
        "metrics": {
            "sentiment": {
                "accuracy": acc_sent,
                "f1_score_macro": f1_sent
            },
            "category": {
                "accuracy": acc_cat,
                "f1_score_macro": f1_cat
            }
        }
    }
    
    run_file = os.path.join(runs_dir, "run_latest.json")
    print(f"Enregistrement des métadonnées de l'entraînement dans : {run_file}")
    with open(run_file, "w", encoding="utf-8") as f:
        json.dump(run_metadata, f, indent=4, ensure_ascii=False)
        
    print("\nÉtape 2 terminée avec succès !")

if __name__ == "__main__":
    train_pipeline()
