-- ============================================
-- BANK360 DATA PLATFORM
-- Script d'initialisation PostgreSQL
-- ============================================

-- Création du schéma
CREATE SCHEMA IF NOT EXISTS bank360;

-- ============================================
-- 1. TABLE CLIENTS
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.clients (
    client_id SERIAL PRIMARY KEY,
    prenom VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    adresse TEXT,
    ville VARCHAR(100),
    pays VARCHAR(100) DEFAULT 'Sénégal',
    date_naissance DATE,
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    est_premium BOOLEAN DEFAULT FALSE,
    est_actif BOOLEAN DEFAULT TRUE,
    dernier_connexion TIMESTAMP,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.clients IS 'Informations sur les clients de la banque';
COMMENT ON COLUMN bank360.clients.est_premium IS 'Indique si le client est premium (True) ou standard (False)';
COMMENT ON COLUMN bank360.clients.est_actif IS 'Indique si le client est actif dans le système';

-- ============================================
-- 2. TABLE COMPTES
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.comptes (
    compte_id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES bank360.clients(client_id) ON DELETE CASCADE,
    numero_compte VARCHAR(34) UNIQUE NOT NULL, -- IBAN
    type_compte VARCHAR(50) NOT NULL, -- Courant, Epargne, Joint, etc.
    devise VARCHAR(3) DEFAULT 'XOF',
    solde DECIMAL(15,2) DEFAULT 0,
    decouvert_autorise DECIMAL(15,2) DEFAULT 0,
    taux_interet DECIMAL(5,2) DEFAULT 0,
    est_actif BOOLEAN DEFAULT TRUE,
    date_ouverture TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_fermeture TIMESTAMP,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.comptes IS 'Comptes bancaires des clients';
COMMENT ON COLUMN bank360.comptes.type_compte IS 'Type de compte : Courant, Epargne, Joint, Professionnel';
COMMENT ON COLUMN bank360.comptes.decouvert_autorise IS 'Montant maximal de découvert autorisé';

-- ============================================
-- 3. TABLE CARTES BANCAIRES
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.cartes (
    carte_id SERIAL PRIMARY KEY,
    compte_id INTEGER REFERENCES bank360.comptes(compte_id) ON DELETE CASCADE,
    numero_carte VARCHAR(16) UNIQUE NOT NULL,
    type_carte VARCHAR(50) NOT NULL, -- DEBIT, CREDIT, PREPAID
    nom_porteur VARCHAR(255) NOT NULL,
    date_expiration DATE NOT NULL,
    cvv VARCHAR(4) NOT NULL,
    code_pin VARCHAR(4),
    est_active BOOLEAN DEFAULT TRUE,
    limite_quotidienne DECIMAL(15,2) DEFAULT 1000000,
    limite_mensuelle DECIMAL(15,2) DEFAULT 5000000,
    est_internationale BOOLEAN DEFAULT FALSE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.cartes IS 'Cartes bancaires liées aux comptes';
COMMENT ON COLUMN bank360.cartes.type_carte IS 'Type de carte : DEBIT, CREDIT, PREPAID';
COMMENT ON COLUMN bank360.cartes.est_internationale IS 'Indique si la carte permet les paiements à l''international';

-- ============================================
-- 4. TABLE TRANSACTIONS
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.transactions (
    transaction_id SERIAL PRIMARY KEY,
    compte_id INTEGER REFERENCES bank360.comptes(compte_id) ON DELETE CASCADE,
    type_transaction VARCHAR(50) NOT NULL, -- CREDIT, DEBIT, TRANSFERT, PAIEMENT, RETRAIT
    montant DECIMAL(15,2) NOT NULL,
    devise VARCHAR(3) DEFAULT 'XOF',
    date_transaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    canal VARCHAR(50), -- ATM, MOBILE, WEB, AGENCE, VIREMENT
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE', -- EN_ATTENTE, COMPLETEE, ECHOUE, ANNULEE
    reference VARCHAR(100) UNIQUE,
    est_suspecte BOOLEAN DEFAULT FALSE,
    frais DECIMAL(10,2) DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.transactions IS 'Toutes les transactions bancaires effectuées';
COMMENT ON COLUMN bank360.transactions.canal IS 'Canal par lequel la transaction a été effectuée';
COMMENT ON COLUMN bank360.transactions.est_suspecte IS 'Indique si la transaction a été flaggée comme suspecte pour fraude';

-- ============================================
-- 5. TABLE PAIEMENTS
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.paiements (
    paiement_id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES bank360.transactions(transaction_id) ON DELETE CASCADE,
    carte_id INTEGER REFERENCES bank360.cartes(carte_id) ON DELETE CASCADE,
    beneficiaire VARCHAR(255) NOT NULL,
    montant DECIMAL(15,2) NOT NULL,
    devise VARCHAR(3) DEFAULT 'XOF',
    reference_paiement VARCHAR(100) UNIQUE,
    date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE', -- EN_ATTENTE, COMPLETE, ECHOUE
    type_paiement VARCHAR(50), -- COMMERCE, FACTURE, EN LIGNE, AUTRE
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. TABLE VIREMENTS
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.virements (
    virement_id SERIAL PRIMARY KEY,
    compte_source_id INTEGER REFERENCES bank360.comptes(compte_id) ON DELETE CASCADE,
    compte_destinataire_id INTEGER REFERENCES bank360.comptes(compte_id) ON DELETE CASCADE,
    transaction_id INTEGER REFERENCES bank360.transactions(transaction_id) ON DELETE CASCADE,
    montant DECIMAL(15,2) NOT NULL,
    devise VARCHAR(3) DEFAULT 'XOF',
    reference_virement VARCHAR(100) UNIQUE,
    motif TEXT,
    date_virement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_execution TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE', -- EN_ATTENTE, EXECUTE, ECHOUE, ANNULE
    frais DECIMAL(10,2) DEFAULT 0,
    est_international BOOLEAN DEFAULT FALSE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.virements IS 'Virements entre comptes bancaires';

-- ============================================
-- 7. TABLE CREDITS
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.credits (
    credit_id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES bank360.clients(client_id) ON DELETE CASCADE,
    type_credit VARCHAR(50) NOT NULL, -- PERSONNEL, IMMOBILIER, AUTO, SCOLAIRE
    montant DECIMAL(15,2) NOT NULL,
    taux_interet DECIMAL(5,2) NOT NULL,
    duree_mois INTEGER NOT NULL,
    mensualite DECIMAL(15,2),
    solde_restant DECIMAL(15,2),
    statut VARCHAR(20) DEFAULT 'ACTIF', -- ACTIF, REMBOURSE, IMPAYE
    date_debut DATE NOT NULL,
    date_fin DATE,
    date_prochain_paiement DATE,
    montant_paye DECIMAL(15,2) DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.credits IS 'Crédits accordés aux clients';
COMMENT ON COLUMN bank360.credits.type_credit IS 'Type de crédit : PERSONNEL, IMMOBILIER, AUTO, SCOLAIRE';

-- ============================================
-- 8. TABLE AGENCES
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.agences (
    agence_id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    adresse TEXT NOT NULL,
    ville VARCHAR(100) NOT NULL,
    pays VARCHAR(100) DEFAULT 'Sénégal',
    code_agence VARCHAR(10) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    email VARCHAR(255),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    date_ouverture DATE,
    est_active BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 9. TABLE EMPLOYES
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.employes (
    employe_id SERIAL PRIMARY KEY,
    agence_id INTEGER REFERENCES bank360.agences(agence_id) ON DELETE CASCADE,
    prenom VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    poste VARCHAR(100) NOT NULL, -- DIRECTEUR, CONSEILLER, CAISSIER
    date_embauche DATE NOT NULL,
    date_naissance DATE,
    est_actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 10. TABLE OPERATIONS_ATM
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.operations_atm (
    operation_atm_id SERIAL PRIMARY KEY,
    carte_id INTEGER REFERENCES bank360.cartes(carte_id) ON DELETE CASCADE,
    transaction_id INTEGER REFERENCES bank360.transactions(transaction_id) ON DELETE CASCADE,
    code_atm VARCHAR(20) NOT NULL,
    type_operation VARCHAR(50) NOT NULL, -- RETRAIT, DEPOT, CONSULTATION
    montant DECIMAL(15,2),
    devise VARCHAR(3) DEFAULT 'XOF',
    date_operation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE',
    frais DECIMAL(10,2) DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 11. TABLE MOBILE_BANKING
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.mobile_banking (
    mobile_id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES bank360.clients(client_id) ON DELETE CASCADE,
    compte_id INTEGER REFERENCES bank360.comptes(compte_id) ON DELETE CASCADE,
    transaction_id INTEGER REFERENCES bank360.transactions(transaction_id) ON DELETE CASCADE,
    num_telephone VARCHAR(20) NOT NULL,
    type_operation VARCHAR(50) NOT NULL, -- PAYEMENT, VIREMENT, RECHARGE, CONSULTATION
    montant DECIMAL(15,2),
    devise VARCHAR(3) DEFAULT 'XOF',
    reference_operation VARCHAR(100) UNIQUE,
    date_operation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'EN_ATTENTE',
    frais DECIMAL(10,2) DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 12. TABLE DEVISES
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.devises (
    devise_id SERIAL PRIMARY KEY,
    code_devise VARCHAR(3) UNIQUE NOT NULL, -- XOF, EUR, USD
    nom_devise VARCHAR(50) NOT NULL,
    symbole VARCHAR(5),
    est_active BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 13. TABLE TAUX_CHANGE
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.taux_change (
    taux_change_id SERIAL PRIMARY KEY,
    devise_source VARCHAR(3) NOT NULL,
    devise_cible VARCHAR(3) NOT NULL,
    taux DECIMAL(15,6) NOT NULL,
    date_taux DATE DEFAULT CURRENT_DATE,
    source VARCHAR(50) DEFAULT 'BCEAO',
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(devise_source, devise_cible, date_taux)
);

-- ============================================
-- 14. TABLE BENEFICIAIRES
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.beneficiaires (
    beneficiaire_id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES bank360.clients(client_id) ON DELETE CASCADE,
    prenom VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    numero_compte VARCHAR(34) NOT NULL,
    banque VARCHAR(100),
    code_banque VARCHAR(50),
    pays VARCHAR(100),
    email VARCHAR(255),
    telephone VARCHAR(20),
    est_actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 15. TABLE ALERTES_FRAUDE
-- ============================================
CREATE TABLE IF NOT EXISTS bank360.alertes_fraude (
    alerte_id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES bank360.transactions(transaction_id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES bank360.clients(client_id) ON DELETE CASCADE,
    type_alerte VARCHAR(50) NOT NULL, -- MONTANT_ELEVE, PAYS_ANORMAL, CONNEXION_SUSPECTE
    niveau_risque VARCHAR(20) NOT NULL, -- FAIBLE, MOYEN, ELEVE, CRITIQUE
    description TEXT,
    score_risque DECIMAL(5,2),
    date_alerte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'OUVERTE', -- OUVERTE, EN_COURS, RESOLUE, IGNOREE
    date_resolution TIMESTAMP,
    commentaire_resolution TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bank360.alertes_fraude IS 'Alertes générées pour la détection de fraude';
COMMENT ON COLUMN bank360.alertes_fraude.type_alerte IS 'Type d''alerte : MONTANT_ELEVE, PAYS_ANORMAL, CONNEXION_SUSPECTE';
COMMENT ON COLUMN bank360.alertes_fraude.niveau_risque IS 'Niveau de risque : FAIBLE, MOYEN, ELEVE, CRITIQUE';

-- ============================================
-- INDEX POUR LES PERFORMANCES
-- ============================================

-- Index sur les clés étrangères
CREATE INDEX idx_comptes_client ON bank360.comptes(client_id);
CREATE INDEX idx_transactions_compte ON bank360.transactions(compte_id);
CREATE INDEX idx_transactions_date ON bank360.transactions(date_transaction);
CREATE INDEX idx_transactions_canal ON bank360.transactions(canal);
CREATE INDEX idx_cartes_compte ON bank360.cartes(compte_id);
CREATE INDEX idx_credits_client ON bank360.credits(client_id);
CREATE INDEX idx_virements_source ON bank360.virements(compte_source_id);
CREATE INDEX idx_virements_destinataire ON bank360.virements(compte_destinataire_id);
CREATE INDEX idx_beneficiaires_client ON bank360.beneficiaires(client_id);
CREATE INDEX idx_alertes_fraude_client ON bank360.alertes_fraude(client_id);
CREATE INDEX idx_alertes_fraude_transaction ON bank360.alertes_fraude(transaction_id);
CREATE INDEX idx_alertes_fraude_date ON bank360.alertes_fraude(date_alerte);
CREATE INDEX idx_mobile_banking_client ON bank360.mobile_banking(client_id);
CREATE INDEX idx_operations_atm_carte ON bank360.operations_atm(carte_id);
CREATE INDEX idx_employes_agence ON bank360.employes(agence_id);

-- Index pour les recherches
CREATE INDEX idx_clients_nom ON bank360.clients(nom);
CREATE INDEX idx_clients_email ON bank360.clients(email);
CREATE INDEX idx_clients_ville ON bank360.clients(ville);
CREATE INDEX idx_comptes_numero ON bank360.comptes(numero_compte);
CREATE INDEX idx_transactions_reference ON bank360.transactions(reference);

-- ============================================
-- FONCTION POUR MISE À JOUR AUTO DATE_MODIFICATION
-- ============================================

CREATE OR REPLACE FUNCTION bank360.update_date_modification()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_modification = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- TRIGGERS POUR MISE À JOUR AUTO
-- ============================================

CREATE TRIGGER trigger_clients_date_modification 
    BEFORE UPDATE ON bank360.clients 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_comptes_date_modification 
    BEFORE UPDATE ON bank360.comptes 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_cartes_date_modification 
    BEFORE UPDATE ON bank360.cartes 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_credits_date_modification 
    BEFORE UPDATE ON bank360.credits 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_agences_date_modification 
    BEFORE UPDATE ON bank360.agences 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_employes_date_modification 
    BEFORE UPDATE ON bank360.employes 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_beneficiaires_date_modification 
    BEFORE UPDATE ON bank360.beneficiaires 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

CREATE TRIGGER trigger_alertes_fraude_date_modification 
    BEFORE UPDATE ON bank360.alertes_fraude 
    FOR EACH ROW 
    EXECUTE FUNCTION bank360.update_date_modification();

-- ============================================
-- DONNÉES DE BASE (INSERTIONS INITIALES)
-- ============================================

-- Insertion des devises de base
INSERT INTO bank360.devises (code_devise, nom_devise, symbole) VALUES
('XOF', 'Franc CFA', 'CFA'),
('EUR', 'Euro', '€'),
('USD', 'Dollar Américain', '$'),
('GBP', 'Livre Sterling', '£'),
('CAD', 'Dollar Canadien', 'C$');

-- Insertion des agences
INSERT INTO bank360.agences (nom, adresse, ville, pays, code_agence, telephone, email) VALUES
('Agence Dakar Plateau', 'Avenue du Président, Dakar', 'Dakar', 'Sénégal', 'AG001', '+221 33 123 45 67', 'dakar.plateau@bank360.sn'),
('Agence Dakar Fann', 'Rue de Fann, Dakar', 'Dakar', 'Sénégal', 'AG002', '+221 33 123 45 68', 'dakar.fann@bank360.sn'),
('Agence Rufisque', 'Boulevard de la République, Rufisque', 'Rufisque', 'Sénégal', 'AG003', '+221 33 123 45 69', 'rufisque@bank360.sn'),
('Agence Thiès', 'Avenue Léopold Sédar Senghor, Thiès', 'Thiès', 'Sénégal', 'AG004', '+221 33 123 45 70', 'thies@bank360.sn'),
('Agence Mbour', 'Route de la Corniche, Mbour', 'Mbour', 'Sénégal', 'AG005', '+221 33 123 45 71', 'mbour@bank360.sn'),
('Agence Saint-Louis', 'Rue du Faidherbe, Saint-Louis', 'Saint-Louis', 'Sénégal', 'AG006', '+221 33 123 45 72', 'saintlouis@bank360.sn'),
('Agence Touba', 'Avenue du Grand Magal, Touba', 'Touba', 'Sénégal', 'AG007', '+221 33 123 45 73', 'touba@bank360.sn'),
('Agence Ziguinchor', 'Avenue de l''Indépendance, Ziguinchor', 'Ziguinchor', 'Sénégal', 'AG008', '+221 33 123 45 74', 'ziguinchor@bank360.sn');

-- Insertion des employés pour l'agence Dakar Plateau
INSERT INTO bank360.employes (agence_id, prenom, nom, email, telephone, poste, date_embauche) VALUES
(1, 'Jean', 'Diouf', 'jean.diouf@bank360.sn', '+221 77 123 45 01', 'DIRECTEUR', '2020-01-15'),
(1, 'Marie', 'Fall', 'marie.fall@bank360.sn', '+221 77 123 45 02', 'CONSEILLER', '2021-03-20'),
(1, 'Ousmane', 'Ndiaye', 'ousmane.ndiaye@bank360.sn', '+221 77 123 45 03', 'CAISSIER', '2022-06-10');

-- Insertion des taux de change initiaux (source: BCEAO)
INSERT INTO bank360.taux_change (devise_source, devise_cible, taux, date_taux, source) VALUES
('XOF', 'EUR', 0.00152, CURRENT_DATE, 'BCEAO'),
('XOF', 'USD', 0.00166, CURRENT_DATE, 'BCEAO'),
('EUR', 'XOF', 655.96, CURRENT_DATE, 'BCEAO'),
('USD', 'XOF', 602.25, CURRENT_DATE, 'BCEAO');

-- ============================================
-- MESSAGE DE SUCCÈS
-- ============================================
DO $$
BEGIN
    RAISE NOTICE ' Bank360 : Base de données initialisée avec succès !';
    RAISE NOTICE ' Tables créées : 15';
    RAISE NOTICE ' Agences créées : 8';
    RAISE NOTICE ' Devises créées : 5';
END $$;