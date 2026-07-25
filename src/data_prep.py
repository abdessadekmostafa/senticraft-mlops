import os
import random
import pandas as pd

def generate_synthetic_reviews(n_samples=800):
    """
    Génère un jeu de données synthétique réaliste de commentaires clients en français,
    avec des sentiments (Positif, Neutre, Négatif) et des catégories (Produit, Livraison, Service Client, Prix).
    """
    
    templates = {
        ("Livraison", "Positif"): [
            "Livraison ultra rapide, colis reçu en parfait état !",
            "Reçu très rapidement, emballage soigné et sécurisé.",
            "Livré le lendemain de ma commande, service impeccable.",
            "Super service de livraison, livreur très courtois et ponctuel.",
            "Expédition rapide et colis très bien protégé, merci !",
            "Arrivé pile à l'heure, rien à redire sur le transport.",
            "Livraison en 24h chrono, impressionnant !"
        ],
        ("Livraison", "Négatif"): [
            "Le colis est arrivé avec trois jours de retard et carton écrasé.",
            "Livreur désagréable qui a laissé le colis sur le trottoir.",
            "Livraison catastrophique, le colis a été perdu par le transporteur.",
            "Retard de livraison inadmissible, aucun suivi disponible.",
            "Le colis est arrivé ouvert et abîmé. Très mécontent.",
            "Suivi de livraison mensonger, soit-disant livré mais rien reçu.",
            "Délai d'attente interminable pour la livraison, plus d'une semaine de retard."
        ],
        ("Produit", "Positif"): [
            "Le produit est de super qualité, je recommande vivement !",
            "Très satisfait de cet achat, fonctionne parfaitement bien.",
            "Conforme à la description, les finitions sont magnifiques.",
            "Un excellent produit, robuste et conforme à mes attentes.",
            "Matériel de qualité professionnelle, très simple à utiliser.",
            "Fonctionne à merveille, le design est superbe.",
            "Je l'utilise tous les jours, c'est un produit génial !"
        ],
        ("Produit", "Négatif"): [
            "La qualité est médiocre, le produit s'est cassé après deux jours d'utilisation.",
            "Déçu par cet article, il ne fonctionne pas du tout.",
            "Plastique de mauvaise qualité, très fragile, je ne recommande pas.",
            "Ne correspond pas du tout à la photo ni à la description.",
            "Produit défectueux à l'arrivée, impossible de l'allumer.",
            "Les fonctionnalités promises ne sont pas là. Très décevant.",
            "Passez votre chemin, c'est du bas de gamme."
        ],
        ("Service Client", "Positif"): [
            "Support client réactif et très professionnel. Problème résolu !",
            "Le SAV a traité ma demande de remboursement en quelques minutes.",
            "Très bonne écoute de la part du conseiller au téléphone.",
            "Service client au top, aimable et très efficace.",
            "Le support a été d'une grande aide pour configurer l'appareil.",
            "Remplacement du produit défectueux fait sans aucun frais ni discussion.",
            "Une équipe de support client très humaine et attentionnée."
        ],
        ("Service Client", "Négatif"): [
            "Impossible de joindre le service client, le téléphone sonne dans le vide.",
            "Le SAV refuse de me rembourser malgré le défaut. Service lamentable.",
            "Conseiller au téléphone impoli, agressif et d'aucune aide.",
            "J'attends une réponse du support par mail depuis deux semaines.",
            "Service après-vente incompétent qui n'a pas compris mon problème.",
            "On me ballade de service en service sans résoudre mon problème.",
            "Aucune considération pour le client, SAV inexistant."
        ],
        ("Prix", "Positif"): [
            "Excellent rapport qualité prix, je rachèterai sans hésiter.",
            "Un prix très compétitif pour une telle qualité de service.",
            "Bonne affaire, beaucoup moins cher qu'en magasin physique.",
            "Tarif tout à fait raisonnable et accessible.",
            "Rapport qualité-prix imbattable sur le marché actuel.",
            "Très bon prix avec la promotion en cours.",
            "Je suis surpris de la qualité pour un prix aussi bas."
        ],
        ("Prix", "Négatif"): [
            "Beaucoup trop cher pour ce que c'est réellement.",
            "Le tarif a augmenté de 20% sans explication, c'est abusé.",
            "On trouve exactement le même produit deux fois moins cher ailleurs.",
            "Le prix est prohibitif par rapport aux performances du produit.",
            "Rapport qualité-prix très défavorable, je regrette cet achat coûteux.",
            "Des frais cachés s'ajoutent à la fin, ce n'est pas honnête.",
            "Trop cher pour une qualité aussi basique."
        ],
        ("Livraison", "Neutre"): [
            "Livraison correcte, dans les délais annoncés.",
            "Colis reçu. Rien à signaler de particulier.",
            "Livré avec un jour de retard mais carton intact.",
            "Temps de livraison moyen, emballage standard."
        ],
        ("Produit", "Neutre"): [
            "Produit moyen, fait le job mais sans plus.",
            "Qualité standard, conforme au prix payé.",
            "Fonctionne comme prévu, mais n'a rien d'exceptionnel.",
            "Correct dans l'ensemble, mais quelques détails à améliorer."
        ],
        ("Service Client", "Neutre"): [
            "Temps d'attente correct pour joindre le support.",
            "Réponse reçue en 48 heures, standard.",
            "SAV poli mais procédure d'échange un peu longue.",
            "Le conseiller a fait ce qu'il pouvait sans plus."
        ],
        ("Prix", "Neutre"): [
            "Le prix est dans la moyenne du marché.",
            "Ni cher ni bon marché, tarif normal.",
            "Prix correct pour les prestations fournies.",
            "Tarif standard sans réduction particulière."
        ]
    }

    data = []
    keys = list(templates.keys())
    
    # Remplissage pour atteindre le nombre de samples souhaité
    for i in range(n_samples):
        cat, sent = random.choice(keys)
        text_template = random.choice(templates[(cat, sent)])
        
        # Ajout de légères variations aléatoires pour simuler la diversité naturelle
        variations_prefix = ["", "Bonjour, ", "Honnêtement, ", "Mon avis : ", "Pour ma part, "]
        variations_suffix = ["", ".", "...", " !", " à voir dans le temps.", " Je conseille.", " Déçu."]
        
        prefix = random.choice(variations_prefix) if random.random() > 0.7 else ""
        suffix = random.choice(variations_suffix) if random.random() > 0.7 else ""
        
        text = f"{prefix}{text_template}{suffix}"
        # Remplacement de doublons de ponctuation si nécessaire
        text = text.replace("!.", "!").replace("..", ".").replace("! !", "!")
        
        data.append({
            "review_id": i + 1,
            "text": text,
            "sentiment": sent,
            "category": cat
        })
        
    return pd.DataFrame(data)

def main():
    print("--- Étape 1 : Préparation et Génération des Données ---")
    
    # Définition des chemins
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, "raw_reviews.csv")
    
    print(f"Génération de 1000 commentaires synthétiques...")
    df = generate_synthetic_reviews(n_samples=1000)
    
    print(f"Sauvegarde du dataset dans {output_file}...")
    df.to_csv(output_file, index=False, encoding="utf-8")
    
    print("\nStatistiques du dataset généré :")
    print(f"Nombre de lignes : {len(df)}")
    print("\nDistribution des sentiments :")
    print(df["sentiment"].value_counts())
    print("\nDistribution des catégories :")
    print(df["category"].value_counts())
    
    print("\nExemple de données :")
    print(df.head(3))
    print("\nÉtape 1 terminée avec succès !")

if __name__ == "__main__":
    main()
