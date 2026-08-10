#!/usr/bin/env python3
"""
Bank360 Data Platform - Générateur de données
Script pour générer des données bancaires réalistes dans PostgreSQL
"""

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

fake = Faker('fr_FR')

# ============================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ============================================
DB_CONFIG = {
    'host': 'localhost',
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'bank360'),
    'user': os.getenv('POSTGRES_USER', 'bank360'),
    'password': os.getenv('POSTGRES_PASSWORD', 'bank360')
}

# ============================================
# CONSTANTES
# ============================================
NB_CLIENTS = 5000
NB_COMPTES_PAR_CLIENT = 2  # indicatif, non utilisé directement (voir randint dans generate_accounts)
NB_TRANSACTIONS = 50000
NB_CREDITS = 1000
NB_CARTES = 3000  # indicatif, dépend en réalité du taux de possession de carte (60%)
NB_VIREMENTS = 10000
NB_PAIEMENTS = 15000
NB_OPERATIONS_ATM = 8000
NB_MOBILE_BANKING = 12000
NB_BENEFICIAIRES = 2000
NB_ALERTES_FRAUDE = 500

TYPES_COMPTE = ['COURANT', 'EPARGNE', 'JOINT', 'PROFESSIONNEL']
TYPES_CARTE = ['DEBIT', 'CREDIT', 'PREPAID']
TYPES_TRANSACTION = ['CREDIT', 'DEBIT', 'TRANSFERT', 'PAIEMENT', 'RETRAIT']
CANAUX = ['ATM', 'MOBILE', 'WEB', 'AGENCE', 'VIREMENT']
STATUTS = ['EN_ATTENTE', 'COMPLETEE', 'ECHOUE', 'ANNULEE']
TYPES_CREDIT = ['PERSONNEL', 'IMMOBILIER', 'AUTO', 'SCOLAIRE']
STATUTS_CREDIT = ['ACTIF', 'REMBOURSE', 'IMPAYE']
NIVEAUX_RISQUE = ['FAIBLE', 'MOYEN', 'ELEVE', 'CRITIQUE']
STATUTS_ALERTE = ['OUVERTE', 'EN_COURS', 'RESOLUE', 'IGNOREE']

VILLES_SENEGAL = ['Dakar', 'Rufisque', 'Thiès', 'Mbour', 'Saint-Louis',
                  'Touba', 'Ziguinchor', 'Kaolack', 'Kolda', 'Tambacounda']

AGENCES_IDS = [1, 2, 3, 4, 5, 6, 7, 8]


# ============================================
# CONNEXION À LA BASE DE DONNÉES
# ============================================
def get_connection():
    """Établir la connexion à PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # gestion manuelle des transactions (commit/rollback explicites)
        logger.info("Connexion à PostgreSQL établie")
        return conn
    except Exception as e:
        logger.error(f"Erreur de connexion: {e}")
        sys.exit(1)


# ============================================
# GÉNÉRATION DE DONNÉES
# ============================================

def generate_customers(conn, nb_customers):
    """Générer des clients"""
    logger.info(f"Génération de {nb_customers} clients...")

    cursor = conn.cursor()
    customers = []
    used_emails = set()  # évite les doublons d'email entre clients générés

    for _ in range(nb_customers):
        first_name = fake.first_name()
        last_name = fake.last_name()

        email_base = f"{first_name.lower()}.{last_name.lower()}"
        email = f"{email_base}@{fake.free_email_domain()}"

        # ajoute un suffixe numérique tant que l'email généré existe déjà
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
    logger.info(f"{len(customer_ids)} clients créés")
    return customer_ids


def generate_accounts(conn, customer_ids):
    """Générer des comptes pour les clients"""
    logger.info(f"Génération de comptes pour {len(customer_ids)} clients...")

    cursor = conn.cursor()
    accounts = []
    account_count = 0

    for client_id in customer_ids:
        nb_comptes = random.randint(1, 3)  # 1 à 3 comptes par client

        for _ in range(nb_comptes):
            account_type = random.choice(TYPES_COMPTE)
            balance = Decimal(random.uniform(-1000, 50000)).quantize(Decimal('0.01'))

            # IBAN fictif: préfixe SN + 28 chiffres aléatoires
            iban = f"SN{random.randint(10, 99)}{''.join([str(random.randint(0,9)) for _ in range(28)])}"

            account = {
                'client_id': client_id,
                'numero_compte': iban,
                'type_compte': account_type,
                'devise': 'XOF',
                'solde': balance,
                'decouvert_autorise': Decimal(random.uniform(0, 5000)).quantize(Decimal('0.01')),
                'taux_interet': Decimal(random.uniform(0, 5)).quantize(Decimal('0.01')),
                'est_actif': random.random() < 0.9,
                'date_ouverture': fake.date_time_between(start_date='-5y', end_date='now'),
                'date_fermeture': None
            }
            accounts.append(account)
            account_count += 1

    insert_query = """
        INSERT INTO bank360.comptes 
        (client_id, numero_compte, type_compte, devise, solde, decouvert_autorise, 
         taux_interet, est_actif, date_ouverture, date_fermeture)
        VALUES (%(client_id)s, %(numero_compte)s, %(type_compte)s, %(devise)s, 
                %(solde)s, %(decouvert_autorise)s, %(taux_interet)s, 
                %(est_actif)s, %(date_ouverture)s, %(date_fermeture)s)
        RETURNING compte_id
    """

    account_ids = []
    for account in accounts:
        cursor.execute(insert_query, account)
        account_id = cursor.fetchone()[0]
        account_ids.append(account_id)

    conn.commit()
    logger.info(f"{len(account_ids)} comptes créés")
    return account_ids


def generate_cards(conn, account_ids, customer_ids):
    """Générer des cartes bancaires"""
    logger.info(f"Génération de {len(account_ids)} cartes...")

    cursor = conn.cursor()
    cards = []
    card_count = 0

    # pré-charge les noms clients pour éviter une requête répétée par carte
    cursor.execute("SELECT client_id, prenom, nom FROM bank360.clients")
    clients_map = {row[0]: f"{row[1]} {row[2]}" for row in cursor.fetchall()}

    for account_id in account_ids:
        if random.random() < 0.6:  # 60% des comptes ont une carte
            card_type = random.choice(TYPES_CARTE)
            card_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])

            cursor.execute("SELECT client_id FROM bank360.comptes WHERE compte_id = %s", (account_id,))
            client_id = cursor.fetchone()[0]
            card_holder = clients_map.get(client_id, fake.name())

            card = {
                'compte_id': account_id,
                'numero_carte': card_number,
                'type_carte': card_type,
                'nom_porteur': card_holder,
                'date_expiration': fake.date_between(start_date='+1y', end_date='+5y'),
                'cvv': ''.join([str(random.randint(0, 9)) for _ in range(3)]),
                'code_pin': ''.join([str(random.randint(0, 9)) for _ in range(4)]),
                'est_active': random.random() < 0.85,
                'limite_quotidienne': Decimal(random.uniform(50000, 2000000)).quantize(Decimal('0.01')),
                'limite_mensuelle': Decimal(random.uniform(500000, 10000000)).quantize(Decimal('0.01')),
                'est_internationale': random.random() < 0.3
            }
            cards.append(card)
            card_count += 1

    insert_query = """
        INSERT INTO bank360.cartes 
        (compte_id, numero_carte, type_carte, nom_porteur, date_expiration, cvv, 
         code_pin, est_active, limite_quotidienne, limite_mensuelle, est_internationale)
        VALUES (%(compte_id)s, %(numero_carte)s, %(type_carte)s, %(nom_porteur)s, 
                %(date_expiration)s, %(cvv)s, %(code_pin)s, %(est_active)s, 
                %(limite_quotidienne)s, %(limite_mensuelle)s, %(est_internationale)s)
        RETURNING carte_id
    """

    card_ids = []
    for card in cards:
        cursor.execute(insert_query, card)
        card_id = cursor.fetchone()[0]
        card_ids.append(card_id)

    conn.commit()
    logger.info(f"{len(card_ids)} cartes créées")
    return card_ids


def generate_transactions(conn, account_ids, nb_transactions):
    """Générer des transactions"""
    logger.info(f"Génération de {nb_transactions} transactions...")

    cursor = conn.cursor()
    transactions = []

    for _ in range(nb_transactions):
        account_id = random.choice(account_ids)
        transaction_type = random.choice(TYPES_TRANSACTION)
        amount = Decimal(random.uniform(100, 500000)).quantize(Decimal('0.01'))

        if transaction_type == 'CREDIT':
            amount = Decimal(random.uniform(1000, 50000)).quantize(Decimal('0.01'))  # crédits: montants plus petits

        transaction = {
            'compte_id': account_id,
            'type_transaction': transaction_type,
            'montant': amount,
            'devise': 'XOF',
            'date_transaction': fake.date_time_between(start_date='-180d', end_date='now'),
            'description': fake.sentence(nb_words=6),
            'canal': random.choice(CANAUX),
            'statut': random.choices(STATUTS, weights=[0.05, 0.85, 0.05, 0.05])[0],  # 85% de transactions complétées
            'reference': str(uuid.uuid4())[:20].replace('-', '').upper(),
            'est_suspecte': random.random() < 0.02,  # 2% de transactions suspectes
            'frais': Decimal(random.uniform(0, 500)).quantize(Decimal('0.01'))
        }
        transactions.append(transaction)

    insert_query = """
        INSERT INTO bank360.transactions 
        (compte_id, type_transaction, montant, devise, date_transaction, description, 
         canal, statut, reference, est_suspecte, frais)
        VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                %(reference)s, %(est_suspecte)s, %(frais)s)
        RETURNING transaction_id
    """

    transaction_ids = []
    for transaction in transactions:
        cursor.execute(insert_query, transaction)
        transaction_id = cursor.fetchone()[0]
        transaction_ids.append(transaction_id)

    conn.commit()
    logger.info(f"{len(transaction_ids)} transactions créées")
    return transaction_ids


def generate_loans(conn, customer_ids, nb_loans):
    """Générer des crédits"""
    logger.info(f"Génération de {nb_loans} crédits...")

    cursor = conn.cursor()
    loans = []

    for _ in range(nb_loans):
        client_id = random.choice(customer_ids)
        loan_type = random.choice(TYPES_CREDIT)
        amount = Decimal(random.uniform(100000, 50000000)).quantize(Decimal('0.01'))
        interest_rate = Decimal(random.uniform(3, 15)).quantize(Decimal('0.01'))
        duration = random.choice([12, 24, 36, 48, 60, 72, 84, 96, 120])

        # formule d'amortissement standard (mensualité constante)
        monthly_payment = (amount * (interest_rate/100/12) * (1 + interest_rate/100/12)**duration) / ((1 + interest_rate/100/12)**duration - 1)
        monthly_payment = Decimal(monthly_payment).quantize(Decimal('0.01'))

        start_date = fake.date_between(start_date='-3y', end_date='now')
        end_date = start_date + timedelta(days=30*duration)

        status = random.choices(STATUTS_CREDIT, weights=[0.7, 0.2, 0.1])[0]

        # solde restant / montant payé cohérents avec le statut du crédit
        if status == 'REMBOURSE':
            outstanding_balance = Decimal(0)
            amount_paid = amount
        elif status == 'IMPAYE':
            outstanding_balance = amount * Decimal(random.uniform(0.4, 0.9))
            amount_paid = amount - outstanding_balance
        else:  # ACTIF
            outstanding_balance = amount * Decimal(random.uniform(0.3, 0.95))
            amount_paid = amount - outstanding_balance

        loan = {
            'client_id': client_id,
            'type_credit': loan_type,
            'montant': amount,
            'taux_interet': interest_rate,
            'duree_mois': duration,
            'mensualite': monthly_payment,
            'solde_restant': outstanding_balance,
            'statut': status,
            'date_debut': start_date,
            'date_fin': end_date,
            'date_prochain_paiement': fake.date_between(start_date='now', end_date='+3m') if status == 'ACTIF' else None,
            'montant_paye': amount_paid
        }
        loans.append(loan)

    insert_query = """
        INSERT INTO bank360.credits 
        (client_id, type_credit, montant, taux_interet, duree_mois, mensualite, 
         solde_restant, statut, date_debut, date_fin, date_prochain_paiement, montant_paye)
        VALUES (%(client_id)s, %(type_credit)s, %(montant)s, %(taux_interet)s, 
                %(duree_mois)s, %(mensualite)s, %(solde_restant)s, %(statut)s, 
                %(date_debut)s, %(date_fin)s, %(date_prochain_paiement)s, %(montant_paye)s)
    """

    for loan in loans:
        cursor.execute(insert_query, loan)

    conn.commit()
    logger.info(f"{len(loans)} crédits créés")


def generate_transfers(conn, account_ids, nb_transfers):
    """Générer des virements"""
    logger.info(f"Génération de {nb_transfers} virements...")

    cursor = conn.cursor()
    transfers = []
    transfer_count = 0

    for _ in range(nb_transfers):
        source_id = random.choice(account_ids)
        destination_id = random.choice([aid for aid in account_ids if aid != source_id])  # évite source == destination

        amount = Decimal(random.uniform(1000, 1000000)).quantize(Decimal('0.01'))

        transaction = {
            'compte_id': source_id,
            'type_transaction': 'TRANSFERT',
            'montant': -amount,  # négatif: débit côté compte source
            'devise': 'XOF',
            'date_transaction': fake.date_time_between(start_date='-90d', end_date='now'),
            'description': f"Virement vers compte {destination_id}",
            'canal': random.choices(['MOBILE', 'WEB', 'AGENCE'], weights=[0.3, 0.4, 0.3])[0],
            'statut': random.choices(STATUTS, weights=[0.03, 0.90, 0.04, 0.03])[0],
            'reference': f"VIR{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'est_suspecte': random.random() < 0.01,
            'frais': Decimal(random.uniform(0, 200)).quantize(Decimal('0.01'))
        }

        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        transaction_id = cursor.fetchone()[0]

        transfer = {
            'compte_source_id': source_id,
            'compte_destinataire_id': destination_id,
            'transaction_id': transaction_id,
            'montant': amount,
            'devise': 'XOF',
            'reference_virement': f"VIR{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'motif': fake.sentence(nb_words=4),
            'date_virement': transaction['date_transaction'],
            'date_execution': transaction['date_transaction'] + timedelta(hours=random.randint(1, 48)),
            'statut': transaction['statut'],
            'frais': Decimal(random.uniform(0, 200)).quantize(Decimal('0.01')),
            'est_international': random.random() < 0.05
        }
        transfers.append(transfer)
        transfer_count += 1

    insert_query = """
        INSERT INTO bank360.virements 
        (compte_source_id, compte_destinataire_id, transaction_id, montant, devise, 
         reference_virement, motif, date_virement, date_execution, statut, frais, est_international)
        VALUES (%(compte_source_id)s, %(compte_destinataire_id)s, %(transaction_id)s, 
                %(montant)s, %(devise)s, %(reference_virement)s, %(motif)s, 
                %(date_virement)s, %(date_execution)s, %(statut)s, %(frais)s, %(est_international)s)
    """

    for transfer in transfers:
        cursor.execute(insert_query, transfer)

    conn.commit()
    logger.info(f"{transfer_count} virements créés")


def generate_payments(conn, card_ids, nb_payments):
    """Générer des paiements"""
    logger.info(f"Génération de {nb_payments} paiements...")

    cursor = conn.cursor()
    payments = []

    for _ in range(nb_payments):
        card_id = random.choice(card_ids)

        cursor.execute("SELECT compte_id FROM bank360.cartes WHERE carte_id = %s", (card_id,))
        account_id = cursor.fetchone()[0]

        amount = Decimal(random.uniform(100, 200000)).quantize(Decimal('0.01'))

        transaction = {
            'compte_id': account_id,
            'type_transaction': 'PAIEMENT',
            'montant': -amount,  # débit
            'devise': 'XOF',
            'date_transaction': fake.date_time_between(start_date='-60d', end_date='now'),
            'description': f"Paiement par carte {card_id}",
            'canal': random.choices(['MOBILE', 'WEB', 'ATM'], weights=[0.4, 0.4, 0.2])[0],
            'statut': random.choices(STATUTS, weights=[0.02, 0.92, 0.03, 0.03])[0],
            'reference': f"PAY{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'est_suspecte': random.random() < 0.015,
            'frais': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01'))
        }

        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        transaction_id = cursor.fetchone()[0]

        payment = {
            'transaction_id': transaction_id,
            'carte_id': card_id,
            'beneficiaire': fake.company(),
            'montant': amount,
            'devise': 'XOF',
            'reference_paiement': f"PAY{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'date_paiement': transaction['date_transaction'],
            'statut': transaction['statut'],
            'type_paiement': random.choice(['COMMERCE', 'FACTURE', 'EN LIGNE', 'AUTRE'])
        }
        payments.append(payment)

    insert_query = """
        INSERT INTO bank360.paiements 
        (transaction_id, carte_id, beneficiaire, montant, devise, reference_paiement, 
         date_paiement, statut, type_paiement)
        VALUES (%(transaction_id)s, %(carte_id)s, %(beneficiaire)s, %(montant)s, 
                %(devise)s, %(reference_paiement)s, %(date_paiement)s, %(statut)s, %(type_paiement)s)
    """

    for payment in payments:
        cursor.execute(insert_query, payment)

    conn.commit()
    logger.info(f"{len(payments)} paiements créés")


def generate_atm_operations(conn, card_ids, nb_operations):
    """Générer des opérations ATM"""
    logger.info(f"Génération de {nb_operations} opérations ATM...")

    cursor = conn.cursor()
    operations = []
    op_count = 0

    for _ in range(nb_operations):
        card_id = random.choice(card_ids)

        cursor.execute("SELECT compte_id FROM bank360.cartes WHERE carte_id = %s", (card_id,))
        account_id = cursor.fetchone()[0]

        operation_type = random.choice(['RETRAIT', 'DEPOT', 'CONSULTATION'])

        # montant et type de transaction dépendent du type d'opération
        if operation_type == 'RETRAIT':
            amount = Decimal(random.uniform(1000, 500000)).quantize(Decimal('0.01'))
            transaction_type = 'RETRAIT'
        elif operation_type == 'DEPOT':
            amount = Decimal(random.uniform(1000, 1000000)).quantize(Decimal('0.01'))
            transaction_type = 'CREDIT'
        else:  # CONSULTATION
            amount = Decimal(0)
            transaction_type = 'CONSULTATION'

        transaction = {
            'compte_id': account_id,
            'type_transaction': transaction_type,
            'montant': -amount if operation_type == 'RETRAIT' else amount,
            'devise': 'XOF',
            'date_transaction': fake.date_time_between(start_date='-60d', end_date='now'),
            'description': f"Opération ATM: {operation_type}",
            'canal': 'ATM',
            'statut': random.choices(STATUTS, weights=[0.02, 0.93, 0.03, 0.02])[0],
            'reference': f"ATM{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'est_suspecte': random.random() < 0.01,
            'frais': Decimal(random.uniform(0, 500)).quantize(Decimal('0.01'))
        }

        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        transaction_id = cursor.fetchone()[0]

        operation = {
            'carte_id': card_id,
            'transaction_id': transaction_id,
            'code_atm': f"ATM{random.randint(1000, 9999)}",
            'type_operation': operation_type,
            'montant': amount,
            'devise': 'XOF',
            'date_operation': transaction['date_transaction'],
            'statut': transaction['statut'],
            'frais': Decimal(random.uniform(0, 200)).quantize(Decimal('0.01'))
        }
        operations.append(operation)
        op_count += 1

    insert_query = """
        INSERT INTO bank360.operations_atm 
        (carte_id, transaction_id, code_atm, type_operation, montant, devise, 
         date_operation, statut, frais)
        VALUES (%(carte_id)s, %(transaction_id)s, %(code_atm)s, %(type_operation)s, 
                %(montant)s, %(devise)s, %(date_operation)s, %(statut)s, %(frais)s)
    """

    for operation in operations:
        cursor.execute(insert_query, operation)

    conn.commit()
    logger.info(f"{op_count} opérations ATM créées")


def generate_mobile_banking(conn, customer_ids, account_ids, nb_operations):
    """Générer des opérations Mobile Banking"""
    logger.info(f"Génération de {nb_operations} opérations Mobile Banking...")

    cursor = conn.cursor()
    operations = []

    for _ in range(nb_operations):
        client_id = random.choice(customer_ids)
        account_id = random.choice(account_ids)
        operation_type = random.choice(['PAIEMENT', 'VIREMENT', 'RECHARGE', 'CONSULTATION'])

        amount = Decimal(random.uniform(100, 200000)).quantize(Decimal('0.01'))

        transaction_type = 'DEBIT' if operation_type in ['PAIEMENT', 'VIREMENT'] else 'CREDIT'
        transaction = {
            'compte_id': account_id,
            'type_transaction': transaction_type,
            'montant': -amount if transaction_type == 'DEBIT' else amount,
            'devise': 'XOF',
            'date_transaction': fake.date_time_between(start_date='-30d', end_date='now'),
            'description': f"Mobile Banking: {operation_type}",
            'canal': 'MOBILE',
            'statut': random.choices(STATUTS, weights=[0.03, 0.88, 0.05, 0.04])[0],
            'reference': f"MB{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'est_suspecte': random.random() < 0.01,
            'frais': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01'))
        }

        cursor.execute("""
            INSERT INTO bank360.transactions 
            (compte_id, type_transaction, montant, devise, date_transaction, description, 
             canal, statut, reference, est_suspecte, frais)
            VALUES (%(compte_id)s, %(type_transaction)s, %(montant)s, %(devise)s, 
                    %(date_transaction)s, %(description)s, %(canal)s, %(statut)s, 
                    %(reference)s, %(est_suspecte)s, %(frais)s)
            RETURNING transaction_id
        """, transaction)
        transaction_id = cursor.fetchone()[0]

        operation = {
            'client_id': client_id,
            'compte_id': account_id,
            'transaction_id': transaction_id,
            'num_telephone': fake.phone_number(),
            'type_operation': operation_type,
            'montant': amount,
            'devise': 'XOF',
            'reference_operation': f"MB{''.join([str(random.randint(0,9)) for _ in range(12)])}",
            'date_operation': transaction['date_transaction'],
            'statut': transaction['statut'],
            'frais': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01'))
        }
        operations.append(operation)

    insert_query = """
        INSERT INTO bank360.mobile_banking 
        (client_id, compte_id, transaction_id, num_telephone, type_operation, montant, 
         devise, reference_operation, date_operation, statut, frais)
        VALUES (%(client_id)s, %(compte_id)s, %(transaction_id)s, %(num_telephone)s, 
                %(type_operation)s, %(montant)s, %(devise)s, %(reference_operation)s, 
                %(date_operation)s, %(statut)s, %(frais)s)
    """

    for operation in operations:
        cursor.execute(insert_query, operation)

    conn.commit()
    logger.info(f"{len(operations)} opérations Mobile Banking créées")


def generate_beneficiaries(conn, customer_ids, nb_beneficiaries):
    """Générer des bénéficiaires"""
    logger.info(f"Génération de {nb_beneficiaries} bénéficiaires...")

    cursor = conn.cursor()
    beneficiaries = []

    for _ in range(nb_beneficiaries):
        client_id = random.choice(customer_ids)  # un client peut avoir plusieurs bénéficiaires

        beneficiary = {
            'client_id': client_id,
            'prenom': fake.first_name(),
            'nom': fake.last_name(),
            'numero_compte': f"SN{random.randint(10, 99)}{''.join([str(random.randint(0,9)) for _ in range(28)])}",
            'banque': fake.company() + ' Bank',
            'code_banque': f"BANK{random.randint(100, 999)}",
            'pays': random.choice(['Sénégal', 'France', 'Canada', 'Mali', 'Côte d\'Ivoire']),
            'email': fake.email(),
            'telephone': fake.phone_number(),
            'est_actif': random.random() < 0.85
        }
        beneficiaries.append(beneficiary)

    insert_query = """
        INSERT INTO bank360.beneficiaires 
        (client_id, prenom, nom, numero_compte, banque, code_banque, pays, email, telephone, est_actif)
        VALUES (%(client_id)s, %(prenom)s, %(nom)s, %(numero_compte)s, %(banque)s, 
                %(code_banque)s, %(pays)s, %(email)s, %(telephone)s, %(est_actif)s)
    """

    for beneficiary in beneficiaries:
        cursor.execute(insert_query, beneficiary)

    conn.commit()
    logger.info(f"{len(beneficiaries)} bénéficiaires créés")


def generate_fraud_alerts(conn, transaction_ids, customer_ids, nb_alerts):
    """Générer des alertes de fraude"""
    logger.info(f"Génération de {nb_alerts} alertes de fraude...")

    cursor = conn.cursor()
    alerts = []

    for _ in range(nb_alerts):
        transaction_id = random.choice(transaction_ids)
        client_id = random.choice(customer_ids)

        alert_type = random.choice(['MONTANT_ELEVE', 'PAYS_ANORMAL', 'CONNEXION_SUSPECTE'])
        risk_level = random.choices(NIVEAUX_RISQUE, weights=[0.3, 0.4, 0.2, 0.1])[0]

        descriptions = {
            'MONTANT_ELEVE': 'Transaction de montant anormalement élevé',
            'PAYS_ANORMAL': 'Transaction effectuée depuis un pays inhabituel',
            'CONNEXION_SUSPECTE': 'Connexion détectée à partir d\'un appareil inconnu'
        }

        alert = {
            'transaction_id': transaction_id,
            'client_id': client_id,
            'type_alerte': alert_type,
            'niveau_risque': risk_level,
            'description': descriptions.get(alert_type, 'Alerte de fraude détectée'),
            'score_risque': Decimal(random.uniform(0, 100)).quantize(Decimal('0.01')),
            'date_alerte': fake.date_time_between(start_date='-30d', end_date='now'),
            'statut': random.choices(STATUTS_ALERTE, weights=[0.4, 0.2, 0.2, 0.2])[0],
            'date_resolution': None,
            'commentaire_resolution': None
        }
        alerts.append(alert)

    insert_query = """
        INSERT INTO bank360.alertes_fraude 
        (transaction_id, client_id, type_alerte, niveau_risque, description, score_risque, 
         date_alerte, statut, date_resolution, commentaire_resolution)
        VALUES (%(transaction_id)s, %(client_id)s, %(type_alerte)s, %(niveau_risque)s, 
                %(description)s, %(score_risque)s, %(date_alerte)s, %(statut)s, 
                %(date_resolution)s, %(commentaire_resolution)s)
    """

    for alert in alerts:
        cursor.execute(insert_query, alert)

    conn.commit()
    logger.info(f"{len(alerts)} alertes de fraude créées")


# ============================================
# FONCTION PRINCIPALE
# ============================================
def main():
    """Fonction principale de génération de données"""
    logger.info("=" * 60)
    logger.info("Bank360 - GÉNÉRATION DE DONNÉES")
    logger.info("=" * 60)

    conn = get_connection()

    try:
        customer_ids = generate_customers(conn, NB_CLIENTS)
        account_ids = generate_accounts(conn, customer_ids)
        card_ids = generate_cards(conn, account_ids, customer_ids)
        transaction_ids = generate_transactions(conn, account_ids, NB_TRANSACTIONS)
        generate_loans(conn, customer_ids, NB_CREDITS)
        generate_transfers(conn, account_ids, NB_VIREMENTS)

        if card_ids:
            generate_payments(conn, card_ids, NB_PAIEMENTS)
            generate_atm_operations(conn, card_ids, NB_OPERATIONS_ATM)

        generate_mobile_banking(conn, customer_ids, account_ids, NB_MOBILE_BANKING)
        generate_beneficiaries(conn, customer_ids, NB_BENEFICIAIRES)

        if transaction_ids:
            generate_fraud_alerts(conn, transaction_ids, customer_ids, NB_ALERTES_FRAUDE)

        logger.info("=" * 60)
        logger.info("GÉNÉRATION DE DONNÉES TERMINÉE AVEC SUCCÈS !")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Erreur lors de la génération des données: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()