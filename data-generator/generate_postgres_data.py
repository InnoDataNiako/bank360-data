#!/usr/bin/env python3

"""
Bank360 Data Platform - Générateur de données
Script pour générer des données bancaires réalistes dans PostgreSQL
"""
# Documentation du script (docstring). Elle décrit l'objectif général du programme.

# ======================================================
# IMPORTATION DES BIBLIOTHÈQUES
# ======================================================

import os

import sys

import random

import uuid

from datetime import datetime, timedelta, date


from decimal import Decimal

import psycopg2

from psycopg2 import sql, extras

from faker import Faker

import logging

# ======================================================
# CONFIGURATION DU LOGGING
# ======================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
 
)


logger = logging.getLogger(__name__)
# Création d'un objet logger utilisé dans tout le programme.

# ======================================================
# INITIALISATION DE FAKER
# ======================================================

fake = Faker('fr_FR')
# Configure Faker pour générer des données françaises

# ============================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ============================================
DB_CONFIG = {
    # Dictionnaire contenant les paramètres de connexion à PostgreSQL.
    'host': '172.18.0.2', 
    # Hôte de la base, lu depuis la variable d'environnement, sinon 'localhost' par défaut.
    'port': os.getenv('POSTGRES_PORT', '5432'),
    # Port de la base, lu depuis la variable d'environnement, sinon '5432' par défaut.
    'database': os.getenv('POSTGRES_DB', 'bank360'),
    # Nom de la base de données, sinon 'bank360' par défaut.
    'user': os.getenv('POSTGRES_USER', 'bank360'),
    # Utilisateur PostgreSQL, sinon 'bank360' par défaut.
    'password': os.getenv('POSTGRES_PASSWORD', 'bank360')
    # Mot de passe PostgreSQL, sinon 'bank360' par défaut.
}
# Fin du dictionnaire de configuration.

# ============================================
# CONSTANTES
# ============================================
NB_CLIENTS = 5000
# Nombre de clients à générer.
NB_COMPTES_PAR_CLIENT = 2  # En moyenne
# Nombre moyen de comptes par client (indicatif, non utilisé strictement dans le code).
NB_TRANSACTIONS = 50000
# Nombre total de transactions à générer.
NB_CREDITS = 1000
# Nombre total de crédits à générer.
NB_CARTES = 3000
# Nombre indicatif de cartes à générer (non utilisé directement, dépend du taux de possession de carte).
NB_VIREMENTS = 10000
# Nombre total de virements à générer.
NB_PAIEMENTS = 15000
# Nombre total de paiements à générer.
NB_OPERATIONS_ATM = 8000
# Nombre total d'opérations ATM à générer.
NB_MOBILE_BANKING = 12000
# Nombre total d'opérations de mobile banking à générer.
NB_BENEFICIAIRES = 2000
# Nombre total de bénéficiaires à générer.
NB_ALERTES_FRAUDE = 500
# Nombre total d'alertes de fraude à générer.

TYPES_COMPTE = ['COURANT', 'EPARGNE', 'JOINT', 'PROFESSIONNEL']
# Liste des types de comptes possibles.
TYPES_CARTE = ['DEBIT', 'CREDIT', 'PREPAID']
# Liste des types de cartes possibles.
TYPES_TRANSACTION = ['CREDIT', 'DEBIT', 'TRANSFERT', 'PAIEMENT', 'RETRAIT']
# Liste des types de transactions possibles.
CANAUX = ['ATM', 'MOBILE', 'WEB', 'AGENCE', 'VIREMENT']
# Liste des canaux possibles pour une opération.
STATUTS = ['EN_ATTENTE', 'COMPLETEE', 'ECHOUE', 'ANNULEE']
# Liste des statuts possibles d'une transaction.
TYPES_CREDIT = ['PERSONNEL', 'IMMOBILIER', 'AUTO', 'SCOLAIRE']
# Liste des types de crédits possibles.
STATUTS_CREDIT = ['ACTIF', 'REMBOURSE', 'IMPAYE']
# Liste des statuts possibles d'un crédit.
NIVEAUX_RISQUE = ['FAIBLE', 'MOYEN', 'ELEVE', 'CRITIQUE']
# Liste des niveaux de risque possibles pour une alerte de fraude.
STATUTS_ALERTE = ['OUVERTE', 'EN_COURS', 'RESOLUE', 'IGNOREE']
# Liste des statuts possibles d'une alerte de fraude.

VILLES_SENEGAL = ['Dakar', 'Rufisque', 'Thiès', 'Mbour', 'Saint-Louis', 
                  'Touba', 'Ziguinchor', 'Kaolack', 'Kolda', 'Tambacounda']
# Liste des villes du Sénégal utilisées pour générer les adresses des clients.

# Agences avec leurs IDs (chargées depuis la base)
AGENCES_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
# Liste des identifiants d'agences bancaires disponibles.


# ============================================
# CONNEXION À LA BASE DE DONNÉES
# ============================================
def get_connection():
    # Déclaration de la fonction qui établit la connexion à PostgreSQL.
    """Établir la connexion à PostgreSQL"""
    # Docstring décrivant le rôle de la fonction.
    try:
        # Début du bloc try pour capturer les erreurs de connexion.
        conn = psycopg2.connect(**DB_CONFIG)
        # Ouvre la connexion à PostgreSQL avec les paramètres définis dans DB_CONFIG.
        conn.autocommit = False
        # Désactive l'autocommit pour gérer les transactions manuellement.
        logger.info("Connexion à PostgreSQL établie")
        # Journalise un message confirmant la connexion réussie.
        return conn
        # Retourne l'objet de connexion.
    except Exception as e:
        # Capture toute exception survenue lors de la connexion.
        logger.error(f" Erreur de connexion: {e}")
        # Journalise l'erreur rencontrée.
        sys.exit(1)
        # Arrête le programme avec un code d'erreur.


# ============================================
# GÉNÉRATION DE DONNÉES
# ============================================

def generate_customers(conn, nb_customers):
    """Générer des clients"""
    logger.info(f" Génération de {nb_customers} clients...")
    
    cursor = conn.cursor()
    customers = []
    used_emails = set()  # ← Ajout : ensemble pour suivre les emails déjà utilisés
    
    for _ in range(nb_customers):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # Générer un email unique
        email_base = f"{first_name.lower()}.{last_name.lower()}"
        email = f"{email_base}@{fake.free_email_domain()}"
        
        # Si l'email existe déjà, ajouter un suffixe
        counter = 1
        while email in used_emails:
            email = f"{email_base}{counter}@{fake.free_email_domain()}"
            counter += 1
        
        used_emails.add(email)
        
        customer = {
            'prenom': first_name,
            'nom': last_name,
            'email': email,
            'telephone': fake.phone_number(),
            'adresse': fake.street_address(),
            'ville': random.choice(VILLES_SENEGAL),
            'pays': 'Sénégal',
            'date_naissance': fake.date_of_birth(minimum_age=18, maximum_age=85),
            'date_inscription': fake.date_time_between(start_date='-5y', end_date='now'),
            'est_premium': random.random() < 0.15,
            'est_actif': random.random() < 0.85,
            'dernier_connexion': fake.date_time_between(start_date='-30d', end_date='now') if random.random() < 0.7 else None
        }
        customers.append(customer)
    
    # Insertion en batch
    insert_query = """
        INSERT INTO bank360.clients 
        (prenom, nom, email, telephone, adresse, ville, pays, date_naissance, 
         date_inscription, est_premium, est_actif, dernier_connexion)
        VALUES (%(prenom)s, %(nom)s, %(email)s, %(telephone)s, %(adresse)s, 
                %(ville)s, %(pays)s, %(date_naissance)s, %(date_inscription)s, 
                %(est_premium)s, %(est_actif)s, %(dernier_connexion)s)
        RETURNING client_id
    """
    
    customer_ids = []
    for customer in customers:
        cursor.execute(insert_query, customer)
        customer_id = cursor.fetchone()[0]
        customer_ids.append(customer_id)
    
    conn.commit()
    logger.info(f" {len(customer_ids)} clients créés")
    return customer_ids

def generate_accounts(conn, customer_ids):
    # Déclaration de la fonction de génération des comptes bancaires.
    """Générer des comptes pour les clients"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de comptes pour {len(customer_ids)} clients...")
    # Journalise le début de la génération des comptes.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    accounts = []
    # Liste qui contiendra les dictionnaires représentant chaque compte.
    account_count = 0
    # Compteur du nombre de comptes générés.
    
    for client_id in customer_ids:
        # Parcourt chaque identifiant client.
        nb_comptes = random.randint(1, 3)
        # Détermine aléatoirement le nombre de comptes (entre 1 et 3) pour ce client.
        
        for _ in range(nb_comptes):
            # Boucle pour créer nb_comptes comptes pour ce client.
            account_type = random.choice(TYPES_COMPTE)
            # Choisit aléatoirement un type de compte.
            balance = Decimal(random.uniform(-1000, 50000)).quantize(Decimal('0.01'))
            # Génère un solde aléatoire compris entre -1000 et 50000, arrondi à 2 décimales.
            
            # Générer un IBAN fictif (SN + 28 chiffres)
            iban = f"SN{random.randint(10, 99)}{''.join([str(random.randint(0,9)) for _ in range(28)])}"
            # Construit un IBAN fictif commençant par 'SN' suivi de chiffres aléatoires.
            
            account = {
                # Dictionnaire représentant les données du compte.
                'client_id': client_id,
                # Identifiant du client propriétaire du compte.
                'numero_compte': iban,
                # Numéro de compte (IBAN généré).
                'type_compte': account_type,
                # Type de compte choisi.
                'devise': 'XOF',
                # Devise fixée au Franc CFA (XOF).
                'solde': balance,
                # Solde initial du compte.
                'decouvert_autorise': Decimal(random.uniform(0, 5000)).quantize(Decimal('0.01')),
                # Montant du découvert autorisé, généré aléatoirement.
                'taux_interet': Decimal(random.uniform(0, 5)).quantize(Decimal('0.01')),
                # Taux d'intérêt du compte, généré aléatoirement.
                'est_actif': random.random() < 0.9,
                # Statut actif du compte avec une probabilité de 90%.
                'date_ouverture': fake.date_time_between(start_date='-5y', end_date='now'),
                # Date d'ouverture du compte, générée entre 5 ans avant aujourd'hui et maintenant.
                'date_fermeture': None
                # Date de fermeture, laissée à None (compte non fermé).
            }
            # Fin du dictionnaire compte.
            accounts.append(account)
            # Ajoute le compte généré à la liste des comptes.
            account_count += 1
            # Incrémente le compteur de comptes générés.
    
    # Insertion en batch
    insert_query = """
        INSERT INTO bank360.comptes 
        (client_id, numero_compte, type_compte, devise, solde, decouvert_autorise, 
         taux_interet, est_actif, date_ouverture, date_fermeture)
        VALUES (%(client_id)s, %(numero_compte)s, %(type_compte)s, %(devise)s, 
                %(solde)s, %(decouvert_autorise)s, %(taux_interet)s, 
                %(est_actif)s, %(date_ouverture)s, %(date_fermeture)s)
        RETURNING compte_id
    """
    # Requête SQL paramétrée pour insérer un compte et récupérer son identifiant généré.
    
    account_ids = []
    # Liste qui contiendra les identifiants des comptes insérés.
    for account in accounts:
        # Parcourt chaque compte généré.
        cursor.execute(insert_query, account)
        # Exécute la requête d'insertion avec les données du compte.
        account_id = cursor.fetchone()[0]
        # Récupère l'identifiant du compte nouvellement inséré.
        account_ids.append(account_id)
        # Ajoute l'identifiant à la liste des identifiants comptes.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(account_ids)} comptes créés")
    # Journalise le nombre de comptes créés.
    return account_ids
    # Retourne la liste des identifiants des comptes créés.


def generate_cards(conn, account_ids, customer_ids):
    # Déclaration de la fonction de génération des cartes bancaires.
    """Générer des cartes bancaires"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {len(account_ids)} cartes...")
    # Journalise le début de la génération des cartes.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    cards = []
    # Liste qui contiendra les dictionnaires représentant chaque carte.
    card_count = 0
    # Compteur du nombre de cartes générées.
    
    # Récupérer les clients pour les noms des porteurs
    cursor.execute("SELECT client_id, prenom, nom FROM bank360.clients")
    # Exécute une requête pour récupérer tous les clients (id, prénom, nom).
    clients_map = {row[0]: f"{row[1]} {row[2]}" for row in cursor.fetchall()}
    # Construit un dictionnaire associant chaque client_id à son nom complet.
    
    for account_id in account_ids:
        # Parcourt chaque identifiant de compte.
        # 60% des comptes ont une carte
        if random.random() < 0.6:
            # Condition : 60% de chance qu'un compte ait une carte associée.
            card_type = random.choice(TYPES_CARTE)
            # Choisit aléatoirement un type de carte.
            card_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
            # Génère un numéro de carte à 16 chiffres aléatoires.
            
            # Récupérer le client_id du compte
            cursor.execute("SELECT client_id FROM bank360.comptes WHERE compte_id = %s", (account_id,))
            # Requête pour récupérer le client_id associé à ce compte.
            client_id = cursor.fetchone()[0]
            # Récupère le client_id retourné par la requête.
            card_holder = clients_map.get(client_id, fake.name())
            # Récupère le nom du porteur depuis le dictionnaire, sinon génère un nom aléatoire.
            
            card = {
                # Dictionnaire représentant les données de la carte.
                'compte_id': account_id,
                # Identifiant du compte associé à la carte.
                'numero_carte': card_number,
                # Numéro de carte généré.
                'type_carte': card_type,
                # Type de carte choisi.
                'nom_porteur': card_holder,
                # Nom du porteur de la carte.
                'date_expiration': fake.date_between(start_date='+1y', end_date='+5y'),
                # Date d'expiration générée entre 1 et 5 ans dans le futur.
                'cvv': ''.join([str(random.randint(0, 9)) for _ in range(3)]),
                # CVV généré aléatoirement (3 chiffres).
                'code_pin': ''.join([str(random.randint(0, 9)) for _ in range(4)]),
                # Code PIN généré aléatoirement (4 chiffres).
                'est_active': random.random() < 0.85,
                # Statut actif de la carte avec une probabilité de 85%.
                'limite_quotidienne': Decimal(random.uniform(50000, 2000000)).quantize(Decimal('0.01')),
                # Limite de retrait/dépense quotidienne générée aléatoirement.
                'limite_mensuelle': Decimal(random.uniform(500000, 10000000)).quantize(Decimal('0.01')),
                # Limite de dépense mensuelle générée aléatoirement.
                'est_internationale': random.random() < 0.3
                # Statut international de la carte avec une probabilité de 30%.
            }
            # Fin du dictionnaire carte.
            cards.append(card)
            # Ajoute la carte générée à la liste des cartes.
            card_count += 1
            # Incrémente le compteur de cartes générées.
    
    # Insertion en batch
    insert_query = """
        INSERT INTO bank360.cartes 
        (compte_id, numero_carte, type_carte, nom_porteur, date_expiration, cvv, 
         code_pin, est_active, limite_quotidienne, limite_mensuelle, est_internationale)
        VALUES (%(compte_id)s, %(numero_carte)s, %(type_carte)s, %(nom_porteur)s, 
                %(date_expiration)s, %(cvv)s, %(code_pin)s, %(est_active)s, 
                %(limite_quotidienne)s, %(limite_mensuelle)s, %(est_internationale)s)
        RETURNING carte_id
    """
    # Requête SQL paramétrée pour insérer une carte et récupérer son identifiant généré.
    
    card_ids = []
    # Liste qui contiendra les identifiants des cartes insérées.
    for card in cards:
        # Parcourt chaque carte générée.
        cursor.execute(insert_query, card)
        # Exécute la requête d'insertion avec les données de la carte.
        card_id = cursor.fetchone()[0]
        # Récupère l'identifiant de la carte nouvellement insérée.
        card_ids.append(card_id)
        # Ajoute l'identifiant à la liste des identifiants cartes.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(card_ids)} cartes créées")
    # Journalise le nombre de cartes créées.
    return card_ids
    # Retourne la liste des identifiants des cartes créées.


def generate_transactions(conn, account_ids, nb_transactions):
    # Déclaration de la fonction de génération des transactions.
    """Générer des transactions"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_transactions} transactions...")
    # Journalise le début de la génération des transactions.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    transactions = []
    # Liste qui contiendra les dictionnaires représentant chaque transaction.
    
    for _ in range(nb_transactions):
        # Boucle pour générer nb_transactions transactions.
        account_id = random.choice(account_ids)
        # Choisit aléatoirement un compte parmi les comptes existants.
        transaction_type = random.choice(TYPES_TRANSACTION)
        # Choisit aléatoirement un type de transaction.
        amount = Decimal(random.uniform(100, 500000)).quantize(Decimal('0.01'))
        # Génère un montant aléatoire par défaut entre 100 et 500000.
        
        # Les crédits sont souvent des montants plus petits
        if transaction_type == 'CREDIT':
            # Si la transaction est de type CREDIT.
            amount = Decimal(random.uniform(1000, 50000)).quantize(Decimal('0.01'))
            # Remplace le montant par une valeur plus petite, typique d'un crédit.
        
        transaction = {
            # Dictionnaire représentant les données de la transaction.
            'compte_id': account_id,
            # Identifiant du compte concerné.
            'type_transaction': transaction_type,
            # Type de la transaction.
            'montant': amount,
            # Montant de la transaction.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'date_transaction': fake.date_time_between(start_date='-180d', end_date='now'),
            # Date de la transaction générée dans les 180 derniers jours.
            'description': fake.sentence(nb_words=6),
            # Description générée automatiquement (phrase de 6 mots).
            'canal': random.choice(CANAUX),
            # Canal utilisé pour la transaction, choisi aléatoirement.
            'statut': random.choices(STATUTS, weights=[0.05, 0.85, 0.05, 0.05])[0],
            # Statut de la transaction, tiré aléatoirement selon des probabilités pondérées.
            'reference': str(uuid.uuid4())[:20].replace('-', '').upper(),
            # Référence unique générée à partir d'un UUID.
            'est_suspecte': random.random() < 0.02,  # 2% de transactions suspectes
            # Marque la transaction comme suspecte avec une probabilité de 2%.
            'frais': Decimal(random.uniform(0, 500)).quantize(Decimal('0.01'))
            # Frais associés à la transaction, générés aléatoirement.
        }
        # Fin du dictionnaire transaction.
        transactions.append(transaction)
        # Ajoute la transaction générée à la liste des transactions.
    
    # Insertion en batch
    insert_query = """
        INSERT INTO bank360.transactions 
        (compte_id, type_transaction, montant, devise, date_transaction, description, 
         canal, statut, reference, est_suspecte, frais)
        VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                %(reference)s, %(est_suspecte)s, %(frais)s)
        RETURNING transaction_id
    """
    # Requête SQL paramétrée pour insérer une transaction et récupérer son identifiant généré.
    
    transaction_ids = []
    # Liste qui contiendra les identifiants des transactions insérées.
    for transaction in transactions:
        # Parcourt chaque transaction générée.
        cursor.execute(insert_query, transaction)
        # Exécute la requête d'insertion avec les données de la transaction.
        transaction_id = cursor.fetchone()[0]
        # Récupère l'identifiant de la transaction nouvellement insérée.
        transaction_ids.append(transaction_id)
        # Ajoute l'identifiant à la liste des identifiants transactions.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(transaction_ids)} transactions créées")
    # Journalise le nombre de transactions créées.
    return transaction_ids
    # Retourne la liste des identifiants des transactions créées.


def generate_loans(conn, customer_ids, nb_loans):
    # Déclaration de la fonction de génération des crédits.
    """Générer des crédits"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_loans} crédits...")
    # Journalise le début de la génération des crédits.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    loans = []
    # Liste qui contiendra les dictionnaires représentant chaque crédit.
    
    for _ in range(nb_loans):
        # Boucle pour générer nb_loans crédits.
        client_id = random.choice(customer_ids)
        # Choisit aléatoirement un client parmi les clients existants.
        loan_type = random.choice(TYPES_CREDIT)
        # Choisit aléatoirement un type de crédit.
        amount = Decimal(random.uniform(100000, 50000000)).quantize(Decimal('0.01'))
        # Génère un montant de crédit aléatoire.
        interest_rate = Decimal(random.uniform(3, 15)).quantize(Decimal('0.01'))
        # Génère un taux d'intérêt aléatoire entre 3% et 15%.
        duration = random.choice([12, 24, 36, 48, 60, 72, 84, 96, 120])
        # Choisit aléatoirement une durée de crédit (en mois) parmi une liste de valeurs typiques.
        
        monthly_payment = (amount * (interest_rate/100/12) * (1 + interest_rate/100/12)**duration) / ((1 + interest_rate/100/12)**duration - 1)
        # Calcule la mensualité selon la formule standard d'amortissement d'un prêt.
        monthly_payment = Decimal(monthly_payment).quantize(Decimal('0.01'))
        # Arrondit la mensualité à 2 décimales.
        
        start_date = fake.date_between(start_date='-3y', end_date='now')
        # Génère une date de début de crédit dans les 3 dernières années.
        end_date = start_date + timedelta(days=30*duration)
        # Calcule la date de fin approximative en ajoutant la durée (en jours) à la date de début.
        
        status = random.choices(STATUTS_CREDIT, weights=[0.7, 0.2, 0.1])[0]
        # Tire aléatoirement le statut du crédit selon des probabilités pondérées.
        
        if status == 'REMBOURSE':
            # Si le crédit est totalement remboursé.
            outstanding_balance = Decimal(0)
            # Le solde restant est nul.
            amount_paid = amount
            # Le montant payé est égal au montant total du crédit.
        elif status == 'IMPAYE':
            # Si le crédit est en situation d'impayé.
            outstanding_balance = amount * Decimal(random.uniform(0.4, 0.9))
            # Le solde restant représente entre 40% et 90% du montant initial.
            amount_paid = amount - outstanding_balance
            # Le montant payé est la différence entre le montant total et le solde restant.
        else:  # ACTIF
            # Sinon, le crédit est actif (en cours de remboursement).
            outstanding_balance = amount * Decimal(random.uniform(0.3, 0.95))
            # Le solde restant représente entre 30% et 95% du montant initial.
            amount_paid = amount - outstanding_balance
            # Le montant payé est la différence entre le montant total et le solde restant.
        
        loan = {
            # Dictionnaire représentant les données du crédit.
            'client_id': client_id,
            # Identifiant du client emprunteur.
            'type_credit': loan_type,
            # Type de crédit.
            'montant': amount,
            # Montant total du crédit.
            'taux_interet': interest_rate,
            # Taux d'intérêt appliqué.
            'duree_mois': duration,
            # Durée du crédit en mois.
            'mensualite': monthly_payment,
            # Montant de la mensualité calculée.
            'solde_restant': outstanding_balance,
            # Solde restant à rembourser.
            'statut': status,
            # Statut du crédit.
            'date_debut': start_date,
            # Date de début du crédit.
            'date_fin': end_date,
            # Date de fin prévue du crédit.
            'date_prochain_paiement': fake.date_between(start_date='now', end_date='+3m') if status == 'ACTIF' else None,
            # Date du prochain paiement, définie uniquement si le crédit est actif.
            'montant_paye': amount_paid
            # Montant déjà payé sur le crédit.
        }
        # Fin du dictionnaire crédit.
        loans.append(loan)
        # Ajoute le crédit généré à la liste des crédits.
    
    # Insertion en batch
    insert_query = """
        INSERT INTO bank360.credits 
        (client_id, type_credit, montant, taux_interet, duree_mois, mensualite, 
         solde_restant, statut, date_debut, date_fin, date_prochain_paiement, montant_paye)
        VALUES (%(client_id)s, %(type_credit)s, %(montant)s, %(taux_interet)s, 
                %(duree_mois)s, %(mensualite)s, %(solde_restant)s, %(statut)s, 
                %(date_debut)s, %(date_fin)s, %(date_prochain_paiement)s, %(montant_paye)s)
    """
    # Requête SQL paramétrée pour insérer un crédit.
    
    for loan in loans:
        # Parcourt chaque crédit généré.
        cursor.execute(insert_query, loan)
        # Exécute la requête d'insertion avec les données du crédit.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(loans)} crédits créés")
    # Journalise le nombre de crédits créés.


def generate_transfers(conn, account_ids, nb_transfers):
    # Déclaration de la fonction de génération des virements.
    """Générer des virements"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_transfers} virements...")
    # Journalise le début de la génération des virements.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    transfers = []
    # Liste qui contiendra les dictionnaires représentant chaque virement.
    transfer_count = 0
    # Compteur du nombre de virements générés.
    
    for _ in range(nb_transfers):
        # Boucle pour générer nb_transfers virements.
        source_id = random.choice(account_ids)
        # Choisit aléatoirement le compte source du virement.
        # Éviter le même compte comme source et destination
        destination_id = random.choice([aid for aid in account_ids if aid != source_id])
        # Choisit aléatoirement un compte destination différent du compte source.
        
        amount = Decimal(random.uniform(1000, 1000000)).quantize(Decimal('0.01'))
        # Génère un montant aléatoire pour le virement.
        
        # Créer une transaction associée
        transaction = {
            # Dictionnaire représentant la transaction liée au virement (côté compte source).
            'compte_id': source_id,
            # Identifiant du compte source.
            'type_transaction': 'TRANSFERT',
            # Type de transaction fixé à TRANSFERT.
            'montant': -amount,  # Négatif pour le compte source
            # Montant négatif car il s'agit d'un débit sur le compte source.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'date_transaction': fake.date_time_between(start_date='-90d', end_date='now'),
            # Date de la transaction générée dans les 90 derniers jours.
            'description': f"Virement vers compte {destination_id}",
            # Description mentionnant le compte destinataire.
            'canal': random.choices(['MOBILE', 'WEB', 'AGENCE'], weights=[0.3, 0.4, 0.3])[0],
            # Canal utilisé pour le virement, tiré aléatoirement selon des probabilités pondérées.
            'statut': random.choices(STATUTS, weights=[0.03, 0.90, 0.04, 0.03])[0],
            # Statut de la transaction, tiré aléatoirement selon des probabilités pondérées.
            'reference': f"VIR{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique générée pour le virement.
            'est_suspecte': random.random() < 0.01,
            # Marque la transaction comme suspecte avec une probabilité de 1%.
            'frais': Decimal(random.uniform(0, 200)).quantize(Decimal('0.01'))
            # Frais associés à la transaction, générés aléatoirement.
        }
        # Fin du dictionnaire transaction.
        
        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        # Insère la transaction associée au virement et demande le retour de son identifiant.
        transaction_id = cursor.fetchone()[0]
        # Récupère l'identifiant de la transaction créée.
        
        transfer = {
            # Dictionnaire représentant les données du virement.
            'compte_source_id': source_id,
            # Identifiant du compte source.
            'compte_destinataire_id': destination_id,
            # Identifiant du compte destinataire.
            'transaction_id': transaction_id,
            # Identifiant de la transaction associée.
            'montant': amount,
            # Montant du virement (positif).
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'reference_virement': f"VIR{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique du virement.
            'motif': fake.sentence(nb_words=4),
            # Motif du virement généré automatiquement.
            'date_virement': transaction['date_transaction'],
            # Date du virement, identique à la date de la transaction associée.
            'date_execution': transaction['date_transaction'] + timedelta(hours=random.randint(1, 48)),
            # Date d'exécution, calculée en ajoutant un délai aléatoire (1 à 48h) à la date du virement.
            'statut': transaction['statut'],
            # Statut du virement, identique à celui de la transaction associée.
            'frais': Decimal(random.uniform(0, 200)).quantize(Decimal('0.01')),
            # Frais associés au virement, générés aléatoirement.
            'est_international': random.random() < 0.05
            # Marque le virement comme international avec une probabilité de 5%.
        }
        # Fin du dictionnaire virement.
        transfers.append(transfer)
        # Ajoute le virement généré à la liste des virements.
        transfer_count += 1
        # Incrémente le compteur de virements générés.
    
    # Insertion des virements
    insert_query = """
        INSERT INTO bank360.virements 
        (compte_source_id, compte_destinataire_id, transaction_id, montant, devise, 
         reference_virement, motif, date_virement, date_execution, statut, frais, est_international)
        VALUES (%(compte_source_id)s, %(compte_destinataire_id)s, %(transaction_id)s, 
                %(montant)s, %(devise)s, %(reference_virement)s, %(motif)s, 
                %(date_virement)s, %(date_execution)s, %(statut)s, %(frais)s, %(est_international)s)
    """
    # Requête SQL paramétrée pour insérer un virement.
    
    for transfer in transfers:
        # Parcourt chaque virement généré.
        cursor.execute(insert_query, transfer)
        # Exécute la requête d'insertion avec les données du virement.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {transfer_count} virements créés")
    # Journalise le nombre de virements créés.


def generate_payments(conn, card_ids, nb_payments):
    # Déclaration de la fonction de génération des paiements.
    """Générer des paiements"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_payments} paiements...")
    # Journalise le début de la génération des paiements.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    payments = []
    # Liste qui contiendra les dictionnaires représentant chaque paiement.
    
    for _ in range(nb_payments):
        # Boucle pour générer nb_payments paiements.
        card_id = random.choice(card_ids)
        # Choisit aléatoirement une carte parmi les cartes existantes.
        
        # Récupérer le compte associé à la carte
        cursor.execute("SELECT compte_id FROM bank360.cartes WHERE carte_id = %s", (card_id,))
        # Requête pour récupérer le compte associé à cette carte.
        account_id = cursor.fetchone()[0]
        # Récupère l'identifiant du compte retourné par la requête.
        
        amount = Decimal(random.uniform(100, 200000)).quantize(Decimal('0.01'))
        # Génère un montant aléatoire pour le paiement.
        
        # Créer une transaction associée
        transaction = {
            # Dictionnaire représentant la transaction liée au paiement.
            'compte_id': account_id,
            # Identifiant du compte débité.
            'type_transaction': 'PAIEMENT',
            # Type de transaction fixé à PAIEMENT.
            'montant': -amount,
            # Montant négatif car il s'agit d'un débit.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'date_transaction': fake.date_time_between(start_date='-60d', end_date='now'),
            # Date de la transaction générée dans les 60 derniers jours.
            'description': f"Paiement par carte {card_id}",
            # Description mentionnant l'identifiant de la carte utilisée.
            'canal': random.choices(['MOBILE', 'WEB', 'ATM'], weights=[0.4, 0.4, 0.2])[0],
            # Canal utilisé pour le paiement, tiré aléatoirement selon des probabilités pondérées.
            'statut': random.choices(STATUTS, weights=[0.02, 0.92, 0.03, 0.03])[0],
            # Statut de la transaction, tiré aléatoirement selon des probabilités pondérées.
            'reference': f"PAY{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique générée pour le paiement.
            'est_suspecte': random.random() < 0.015,
            # Marque la transaction comme suspecte avec une probabilité de 1,5%.
            'frais': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01'))
            # Frais associés à la transaction, générés aléatoirement.
        }
        # Fin du dictionnaire transaction.
        
        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        # Insère la transaction associée au paiement et demande le retour de son identifiant.
        transaction_id = cursor.fetchone()[0]
        # Récupère l'identifiant de la transaction créée.
        
        payment = {
            # Dictionnaire représentant les données du paiement.
            'transaction_id': transaction_id,
            # Identifiant de la transaction associée.
            'carte_id': card_id,
            # Identifiant de la carte utilisée.
            'beneficiaire': fake.company(),
            # Nom du bénéficiaire (commerçant) généré aléatoirement.
            'montant': amount,
            # Montant du paiement (positif).
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'reference_paiement': f"PAY{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique du paiement.
            'date_paiement': transaction['date_transaction'],
            # Date du paiement, identique à la date de la transaction associée.
            'statut': transaction['statut'],
            # Statut du paiement, identique à celui de la transaction associée.
            'type_paiement': random.choice(['COMMERCE', 'FACTURE', 'EN LIGNE', 'AUTRE'])
            # Type de paiement, choisi aléatoirement.
        }
        # Fin du dictionnaire paiement.
        payments.append(payment)
        # Ajoute le paiement généré à la liste des paiements.
    
    # Insertion des paiements
    insert_query = """
        INSERT INTO bank360.paiements 
        (transaction_id, carte_id, beneficiaire, montant, devise, reference_paiement, 
         date_paiement, statut, type_paiement)
        VALUES (%(transaction_id)s, %(carte_id)s, %(beneficiaire)s, %(montant)s, 
                %(devise)s, %(reference_paiement)s, %(date_paiement)s, %(statut)s, %(type_paiement)s)
    """
    # Requête SQL paramétrée pour insérer un paiement.
    
    for payment in payments:
        # Parcourt chaque paiement généré.
        cursor.execute(insert_query, payment)
        # Exécute la requête d'insertion avec les données du paiement.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(payments)} paiements créés")
    # Journalise le nombre de paiements créés.


def generate_atm_operations(conn, card_ids, nb_operations):
    # Déclaration de la fonction de génération des opérations ATM.
    """Générer des opérations ATM"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_operations} opérations ATM...")
    # Journalise le début de la génération des opérations ATM.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    operations = []
    # Liste qui contiendra les dictionnaires représentant chaque opération ATM.
    op_count = 0
    # Compteur du nombre d'opérations ATM générées.
    
    for _ in range(nb_operations):
        # Boucle pour générer nb_operations opérations ATM.
        card_id = random.choice(card_ids)
        # Choisit aléatoirement une carte parmi les cartes existantes.
        
        # Récupérer le compte associé à la carte
        cursor.execute("SELECT compte_id FROM bank360.cartes WHERE carte_id = %s", (card_id,))
        # Requête pour récupérer le compte associé à cette carte.
        account_id = cursor.fetchone()[0]
        # Récupère l'identifiant du compte retourné par la requête.
        
        operation_type = random.choice(['RETRAIT', 'DEPOT', 'CONSULTATION'])
        # Choisit aléatoirement le type d'opération ATM.
        
        if operation_type == 'RETRAIT':
            # Si l'opération est un retrait.
            amount = Decimal(random.uniform(1000, 500000)).quantize(Decimal('0.01'))
            # Génère un montant de retrait aléatoire.
            transaction_type = 'RETRAIT'
            # Le type de transaction associé est RETRAIT.
        elif operation_type == 'DEPOT':
            # Si l'opération est un dépôt.
            amount = Decimal(random.uniform(1000, 1000000)).quantize(Decimal('0.01'))
            # Génère un montant de dépôt aléatoire.
            transaction_type = 'CREDIT'
            # Le type de transaction associé est CREDIT.
        else:  # CONSULTATION
            # Sinon, il s'agit d'une consultation de solde.
            amount = Decimal(0)
            # Le montant est nul pour une consultation.
            transaction_type = 'CONSULTATION'
            # Le type de transaction associé est CONSULTATION.
        
        # Créer une transaction associée
        transaction = {
            # Dictionnaire représentant la transaction liée à l'opération ATM.
            'compte_id': account_id,
            # Identifiant du compte concerné.
            'type_transaction': transaction_type,
            # Type de transaction déterminé selon l'opération.
            'montant': -amount if operation_type == 'RETRAIT' else amount,
            # Montant négatif pour un retrait, positif sinon.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'date_transaction': fake.date_time_between(start_date='-60d', end_date='now'),
            # Date de la transaction générée dans les 60 derniers jours.
            'description': f"Opération ATM: {operation_type}",
            # Description mentionnant le type d'opération.
            'canal': 'ATM',
            # Canal fixé à ATM.
            'statut': random.choices(STATUTS, weights=[0.02, 0.93, 0.03, 0.02])[0],
            # Statut de la transaction, tiré aléatoirement selon des probabilités pondérées.
            'reference': f"ATM{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique générée pour l'opération.
            'est_suspecte': random.random() < 0.01,
            # Marque la transaction comme suspecte avec une probabilité de 1%.
            'frais': Decimal(random.uniform(0, 500)).quantize(Decimal('0.01'))
            # Frais associés à la transaction, générés aléatoirement.
        }
        # Fin du dictionnaire transaction.
        
        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        # Insère la transaction associée à l'opération ATM et demande le retour de son identifiant.
        transaction_id = cursor.fetchone()[0]
        # Récupère l'identifiant de la transaction créée.
        
        operation = {
            # Dictionnaire représentant les données de l'opération ATM.
            'carte_id': card_id,
            # Identifiant de la carte utilisée.
            'transaction_id': transaction_id,
            # Identifiant de la transaction associée.
            'code_atm': f"ATM{random.randint(1000, 9999)}",
            # Code identifiant le distributeur ATM utilisé.
            'type_operation': operation_type,
            # Type d'opération effectuée.
            'montant': amount,
            # Montant de l'opération.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'date_operation': transaction['date_transaction'],
            # Date de l'opération, identique à la date de la transaction associée.
            'statut': transaction['statut'],
            # Statut de l'opération, identique à celui de la transaction associée.
            'frais': Decimal(random.uniform(0, 200)).quantize(Decimal('0.01'))
            # Frais associés à l'opération, générés aléatoirement.
        }
        # Fin du dictionnaire opération.
        operations.append(operation)
        # Ajoute l'opération générée à la liste des opérations.
        op_count += 1
        # Incrémente le compteur d'opérations générées.
    
    # Insertion des opérations ATM
    insert_query = """
        INSERT INTO bank360.operations_atm 
        (carte_id, transaction_id, code_atm, type_operation, montant, devise, 
         date_operation, statut, frais)
        VALUES (%(carte_id)s, %(transaction_id)s, %(code_atm)s, %(type_operation)s, 
                %(montant)s, %(devise)s, %(date_operation)s, %(statut)s, %(frais)s)
    """
    # Requête SQL paramétrée pour insérer une opération ATM.
    
    for operation in operations:
        # Parcourt chaque opération générée.
        cursor.execute(insert_query, operation)
        # Exécute la requête d'insertion avec les données de l'opération.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {op_count} opérations ATM créées")
    # Journalise le nombre d'opérations ATM créées.


def generate_mobile_banking(conn, customer_ids, account_ids, nb_operations):
    # Déclaration de la fonction de génération des opérations Mobile Banking.
    """Générer des opérations Mobile Banking"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f"📱 Génération de {nb_operations} opérations Mobile Banking...")
    # Journalise le début de la génération des opérations Mobile Banking.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    operations = []
    # Liste qui contiendra les dictionnaires représentant chaque opération.
    
    for _ in range(nb_operations):
        # Boucle pour générer nb_operations opérations Mobile Banking.
        client_id = random.choice(customer_ids)
        # Choisit aléatoirement un client parmi les clients existants.
        account_id = random.choice(account_ids)
        # Choisit aléatoirement un compte parmi les comptes existants.
        operation_type = random.choice(['PAIEMENT', 'VIREMENT', 'RECHARGE', 'CONSULTATION'])
        # Choisit aléatoirement le type d'opération mobile.
        
        amount = Decimal(random.uniform(100, 200000)).quantize(Decimal('0.01'))
        # Génère un montant aléatoire pour l'opération.
        
        # Créer une transaction associée
        transaction_type = 'DEBIT' if operation_type in ['PAIEMENT', 'VIREMENT'] else 'CREDIT'
        # Détermine le type de transaction : DEBIT pour paiement/virement, CREDIT sinon.
        transaction = {
            # Dictionnaire représentant la transaction liée à l'opération mobile.
            'compte_id': account_id,
            # Identifiant du compte concerné.
            'type_transaction': transaction_type,
            # Type de transaction déterminé ci-dessus.
            'montant': -amount if transaction_type == 'DEBIT' else amount,
            # Montant négatif pour un débit, positif pour un crédit.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'date_transaction': fake.date_time_between(start_date='-30d', end_date='now'),
            # Date de la transaction générée dans les 30 derniers jours.
            'description': f"Mobile Banking: {operation_type}",
            # Description mentionnant le type d'opération.
            'canal': 'MOBILE',
            # Canal fixé à MOBILE.
            'statut': random.choices(STATUTS, weights=[0.03, 0.88, 0.05, 0.04])[0],
            # Statut de la transaction, tiré aléatoirement selon des probabilités pondérées.
            'reference': f"MB{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique générée pour l'opération.
            'est_suspecte': random.random() < 0.01,
            # Marque la transaction comme suspecte avec une probabilité de 1%.
            'frais': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01'))
            # Frais associés à la transaction, générés aléatoirement.
        }
        # Fin du dictionnaire transaction.
        
        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        # Insère la transaction associée à l'opération mobile et demande le retour de son identifiant.
        transaction_id = cursor.fetchone()[0]
        # Récupère l'identifiant de la transaction créée.
        
        operation = {
            # Dictionnaire représentant les données de l'opération mobile.
            'client_id': client_id,
            # Identifiant du client concerné.
            'compte_id': account_id,
            # Identifiant du compte concerné.
            'transaction_id': transaction_id,
            # Identifiant de la transaction associée.
            'num_telephone': fake.phone_number(),
            # Numéro de téléphone utilisé pour l'opération, généré aléatoirement.
            'type_operation': operation_type,
            # Type d'opération effectuée.
            'montant': amount,
            # Montant de l'opération.
            'devise': 'XOF',
            # Devise fixée au Franc CFA.
            'reference_operation': f"MB{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            # Référence unique de l'opération.
            'date_operation': transaction['date_transaction'],
            # Date de l'opération, identique à la date de la transaction associée.
            'statut': transaction['statut'],
            # Statut de l'opération, identique à celui de la transaction associée.
            'frais': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01'))
            # Frais associés à l'opération, générés aléatoirement.
        }
        # Fin du dictionnaire opération.
        operations.append(operation)
        # Ajoute l'opération générée à la liste des opérations.
    
    # Insertion des opérations mobile
    insert_query = """
        INSERT INTO bank360.mobile_banking 
        (client_id, compte_id, transaction_id, num_telephone, type_operation, montant, 
         devise, reference_operation, date_operation, statut, frais)
        VALUES (%(client_id)s, %(compte_id)s, %(transaction_id)s, %(num_telephone)s, 
                %(type_operation)s, %(montant)s, %(devise)s, %(reference_operation)s, 
                %(date_operation)s, %(statut)s, %(frais)s)
    """
    # Requête SQL paramétrée pour insérer une opération Mobile Banking.
    
    for operation in operations:
        # Parcourt chaque opération générée.
        cursor.execute(insert_query, operation)
        # Exécute la requête d'insertion avec les données de l'opération.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(operations)} opérations Mobile Banking créées")
    # Journalise le nombre d'opérations Mobile Banking créées.


def generate_beneficiaries(conn, customer_ids, nb_beneficiaries):
    # Déclaration de la fonction de génération des bénéficiaires.
    """Générer des bénéficiaires"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_beneficiaries} bénéficiaires...")
    # Journalise le début de la génération des bénéficiaires.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    beneficiaries = []
    # Liste qui contiendra les dictionnaires représentant chaque bénéficiaire.
    
    for _ in range(nb_beneficiaries):
        # Boucle pour générer nb_beneficiaries bénéficiaires.
        client_id = random.choice(customer_ids)
        # Choisit aléatoirement un client parmi les clients existants.
        
        # Un client peut avoir plusieurs bénéficiaires
        beneficiary = {
            # Dictionnaire représentant les données du bénéficiaire.
            'client_id': client_id,
            # Identifiant du client propriétaire du bénéficiaire.
            'prenom': fake.first_name(),
            # Prénom du bénéficiaire généré aléatoirement.
            'nom': fake.last_name(),
            # Nom du bénéficiaire généré aléatoirement.
            'numero_compte': f"SN{random.randint(10, 99)}{''.join([str(random.randint(0,9)) for _ in range(28)])}",
            # Numéro de compte (IBAN fictif) du bénéficiaire.
            'banque': fake.company() + ' Bank',
            # Nom de la banque du bénéficiaire, généré aléatoirement.
            'code_banque': f"BANK{random.randint(100, 999)}",
            # Code identifiant la banque du bénéficiaire.
            'pays': random.choice(['Sénégal', 'France', 'Canada', 'Mali', 'Côte d\'Ivoire']),
            # Pays du bénéficiaire, choisi aléatoirement.
            'email': fake.email(),
            # Email du bénéficiaire généré aléatoirement.
            'telephone': fake.phone_number(),
            # Numéro de téléphone du bénéficiaire généré aléatoirement.
            'est_actif': random.random() < 0.85
            # Statut actif du bénéficiaire avec une probabilité de 85%.
        }
        # Fin du dictionnaire bénéficiaire.
        beneficiaries.append(beneficiary)
        # Ajoute le bénéficiaire généré à la liste des bénéficiaires.
    
    # Insertion des bénéficiaires
    insert_query = """
        INSERT INTO bank360.beneficiaires 
        (client_id, prenom, nom, numero_compte, banque, code_banque, pays, email, telephone, est_actif)
        VALUES (%(client_id)s, %(prenom)s, %(nom)s, %(numero_compte)s, %(banque)s, 
                %(code_banque)s, %(pays)s, %(email)s, %(telephone)s, %(est_actif)s)
    """
    # Requête SQL paramétrée pour insérer un bénéficiaire.
    
    for beneficiary in beneficiaries:
        # Parcourt chaque bénéficiaire généré.
        cursor.execute(insert_query, beneficiary)
        # Exécute la requête d'insertion avec les données du bénéficiaire.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(beneficiaries)} bénéficiaires créés")
    # Journalise le nombre de bénéficiaires créés.


def generate_fraud_alerts(conn, transaction_ids, customer_ids, nb_alerts):
    # Déclaration de la fonction de génération des alertes de fraude.
    """Générer des alertes de fraude"""
    # Docstring décrivant le rôle de la fonction.
    logger.info(f" Génération de {nb_alerts} alertes de fraude...")
    # Journalise le début de la génération des alertes de fraude.
    
    cursor = conn.cursor()
    # Crée un curseur pour exécuter des requêtes SQL.
    alerts = []
    # Liste qui contiendra les dictionnaires représentant chaque alerte.
    
    for _ in range(nb_alerts):
        # Boucle pour générer nb_alerts alertes de fraude.
        transaction_id = random.choice(transaction_ids)
        # Choisit aléatoirement une transaction parmi les transactions existantes.
        client_id = random.choice(customer_ids)
        # Choisit aléatoirement un client parmi les clients existants.
        
        alert_type = random.choice(['MONTANT_ELEVE', 'PAYS_ANORMAL', 'CONNEXION_SUSPECTE'])
        # Choisit aléatoirement le type d'alerte.
        risk_level = random.choices(NIVEAUX_RISQUE, weights=[0.3, 0.4, 0.2, 0.1])[0]
        # Tire aléatoirement le niveau de risque selon des probabilités pondérées.
        
        descriptions = {
            # Dictionnaire associant chaque type d'alerte à une description textuelle.
            'MONTANT_ELEVE': 'Transaction de montant anormalement élevé',
            # Description pour une alerte de type montant élevé.
            'PAYS_ANORMAL': 'Transaction effectuée depuis un pays inhabituel',
            # Description pour une alerte de type pays anormal.
            'CONNEXION_SUSPECTE': 'Connexion détectée à partir d\'un appareil inconnu'
            # Description pour une alerte de type connexion suspecte.
        }
        # Fin du dictionnaire des descriptions.
        
        alert = {
            # Dictionnaire représentant les données de l'alerte de fraude.
            'transaction_id': transaction_id,
            # Identifiant de la transaction concernée.
            'client_id': client_id,
            # Identifiant du client concerné.
            'type_alerte': alert_type,
            # Type de l'alerte.
            'niveau_risque': risk_level,
            # Niveau de risque associé à l'alerte.
            'description': descriptions.get(alert_type, 'Alerte de fraude détectée'),
            # Description correspondant au type d'alerte, ou message par défaut.
            'score_risque': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01')),
            # Score de risque généré aléatoirement entre 0 et 100.
            'date_alerte': fake.date_time_between(start_date='-30d', end_date='now'),
            # Date de déclenchement de l'alerte, générée dans les 30 derniers jours.
            'statut': random.choices(STATUTS_ALERTE, weights=[0.4, 0.2, 0.2, 0.2])[0],
            # Statut de l'alerte, tiré aléatoirement selon des probabilités pondérées.
            'date_resolution': None,
            # Date de résolution, laissée à None (non résolue par défaut).
            'commentaire_resolution': None
            # Commentaire de résolution, laissé à None.
        }
        # Fin du dictionnaire alerte.
        alerts.append(alert)
        # Ajoute l'alerte générée à la liste des alertes.
    
    # Insertion des alertes
    insert_query = """
        INSERT INTO bank360.alertes_fraude 
        (transaction_id, client_id, type_alerte, niveau_risque, description, score_risque, 
         date_alerte, statut, date_resolution, commentaire_resolution)
        VALUES (%(transaction_id)s, %(client_id)s, %(type_alerte)s, %(niveau_risque)s, 
                %(description)s, %(score_risque)s, %(date_alerte)s, %(statut)s, 
                %(date_resolution)s, %(commentaire_resolution)s)
    """
    # Requête SQL paramétrée pour insérer une alerte de fraude.
    
    for alert in alerts:
        # Parcourt chaque alerte générée.
        cursor.execute(insert_query, alert)
        # Exécute la requête d'insertion avec les données de l'alerte.
    
    conn.commit()
    # Valide (commit) toutes les insertions effectuées.
    logger.info(f" {len(alerts)} alertes de fraude créées")
    # Journalise le nombre d'alertes de fraude créées.


# ============================================
# FONCTION PRINCIPALE
# ============================================
def main():
    # Déclaration de la fonction principale du script.
    """Fonction principale de génération de données"""
    # Docstring décrivant le rôle de la fonction.
    logger.info("=" * 60)
    # Journalise une ligne de séparation.
    logger.info(" Bank360 - GÉNÉRATION DE DONNÉES")
    # Journalise le titre du programme.
    logger.info("=" * 60)
    # Journalise une seconde ligne de séparation.
    
    conn = get_connection()
    # Établit la connexion à la base de données.
    
    try:
        # Début du bloc try englobant toute la génération de données.
        # 1. Générer les clients
        customer_ids = generate_customers(conn, NB_CLIENTS)
        # Génère les clients et récupère leurs identifiants.
        
        # 2. Générer les comptes
        account_ids = generate_accounts(conn, customer_ids)
        # Génère les comptes associés aux clients et récupère leurs identifiants.
        
        # 3. Générer les cartes
        card_ids = generate_cards(conn, account_ids, customer_ids)
        # Génère les cartes associées aux comptes et récupère leurs identifiants.
        
        # 4. Générer les transactions
        transaction_ids = generate_transactions(conn, account_ids, NB_TRANSACTIONS)
        # Génère les transactions et récupère leurs identifiants.
        
        # 5. Générer les crédits
        generate_loans(conn, customer_ids, NB_CREDITS)
        # Génère les crédits pour les clients.
        
        # 6. Générer les virements
        generate_transfers(conn, account_ids, NB_VIREMENTS)
        # Génère les virements entre comptes.
        
        # 7. Générer les paiements
        if card_ids:
            # Vérifie qu'il existe des cartes avant de générer les paiements.
            generate_payments(conn, card_ids, NB_PAIEMENTS)
            # Génère les paiements par carte.
        
        # 8. Générer les opérations ATM
        if card_ids:
            # Vérifie qu'il existe des cartes avant de générer les opérations ATM.
            generate_atm_operations(conn, card_ids, NB_OPERATIONS_ATM)
            # Génère les opérations ATM.
        
        # 9. Générer les opérations Mobile Banking
        generate_mobile_banking(conn, customer_ids, account_ids, NB_MOBILE_BANKING)
        # Génère les opérations de mobile banking.
        
        # 10. Générer les bénéficiaires
        generate_beneficiaries(conn, customer_ids, NB_BENEFICIAIRES)
        # Génère les bénéficiaires des clients.
        
        # 11. Générer les alertes de fraude
        if transaction_ids:
            # Vérifie qu'il existe des transactions avant de générer les alertes.
            generate_fraud_alerts(conn, transaction_ids, customer_ids, NB_ALERTES_FRAUDE)
            # Génère les alertes de fraude.
        
        logger.info("=" * 60)
        # Journalise une ligne de séparation finale.
        logger.info(" GÉNÉRATION DE DONNÉES TERMINÉE AVEC SUCCÈS !")
        # Journalise le message de succès.
        logger.info("=" * 60)
        # Journalise une dernière ligne de séparation.
        
    except Exception as e:
        # Capture toute exception survenue pendant la génération des données.
        logger.error(f" Erreur lors de la génération des données: {e}")
        # Journalise le message d'erreur.
        conn.rollback()
        # Annule (rollback) toutes les modifications non validées en cas d'erreur.
        raise
        # Relance l'exception pour ne pas la masquer.
    finally:
        # Bloc exécuté systématiquement, qu'il y ait eu une erreur ou non.
        conn.close()
        # Ferme la connexion à la base de données.


if __name__ == "__main__":
    # Vérifie que le script est exécuté directement (et non importé comme module).
    main()
    # Appelle la fonction principale pour lancer la génération de données.