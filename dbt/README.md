
# README : SILVER → GOLD AVEC DBT

# DBT — Transformation Silver → Gold

## 1. Pourquoi cette étape ?

Les données présentes dans **Silver** sont propres, nettoyées et dédoublonnées grâce à Spark. Elles sont cependant encore organisées principalement sous forme de tables opérationnelles.

Elles ne sont pas encore directement adaptées aux besoins analytiques et métier.

L'objectif de cette étape est donc de transformer les données Silver en **modèles analytiques Gold** à l'aide de **dbt exécuté sur Spark**.

---

## 2. Architecture globale

```text
                    PostgreSQL
                 Données sources
                       │
                       │ Spark
                       ▼
              ┌─────────────────┐
              │     BRONZE      │
              │ MinIO + Iceberg │
              │ Données brutes  │
              └────────┬────────┘
                       │
                       │ Spark
                       │ Nettoyage
                       ▼
              ┌─────────────────┐
              │     SILVER      │
              │ MinIO + Iceberg │
              │ Données propres │
              └────────┬────────┘
                       │
                       │ dbt
                       │
                       ▼
              ┌─────────────────┐
              │    STAGING      │
              │    stg_*.sql    │
              │ Préparation     │
              └────────┬────────┘
                       │
                       │ dbt + Spark SQL
                       │ Jointures
                       │ Agrégations
                       │ Modélisation
                       ▼
              ┌─────────────────┐
              │      GOLD       │
              │ MinIO + Iceberg │
              │                 │
              │ Dimensions      │
              │ Facts           │
              │ KPIs            │
              └────────┬────────┘
                       │
                       ▼
              Power BI / Streamlit
              Analyse & Reporting
```

---

# 3. Pourquoi utiliser dbt ?

**dbt (Data Build Tool)** permet de construire la couche analytique à partir de SQL tout en conservant une architecture modulaire et maintenable.

Dans notre architecture, dbt ne remplace pas Spark.

### Spark est responsable de :

* l'ingestion ;
* la lecture des données ;
* la transformation Bronze → Silver ;
* le nettoyage ;
* la déduplication ;
* l'écriture des tables Iceberg.

### dbt est responsable de :

* la préparation des données Silver ;
* la modélisation analytique ;
* les jointures ;
* les agrégations ;
* la construction des dimensions ;
* la construction des tables de faits ;
* la construction des KPI ;
* les tests et la documentation des modèles.

---

# 4. Comment dbt récupère les données Silver ?

Les données Silver sont stockées dans **MinIO au format Iceberg**.

dbt ne va donc pas utiliser PostgreSQL pour récupérer ces données.

dbt utilise **Spark SQL via Spark Thrift Server**.

```text
                MinIO
                  │
                  │ Iceberg
                  ▼
              Silver
                  │
                  │
                  ▼
          Spark Thrift Server
              port 10000
                  │
                  │ SQL
                  ▼
                 dbt
```

Le profil dbt contient notamment :

```yaml
bank360:
  target: dev

  outputs:
    dev:
      type: spark
      method: thrift
      host: spark-master
      port: 10000
      schema: gold
      threads: 4
```

Ainsi, lorsqu'on exécute :

```bash
dbt run
```

dbt génère du SQL et le transmet à Spark.

**Spark exécute alors les requêtes sur les données Iceberg présentes dans MinIO.**

---

# 5. Pourquoi avons-nous une couche Staging ?

La couche Staging constitue une **couche intermédiaire entre Silver et les modèles analytiques Gold**.

Elle expose proprement les données Silver à dbt.

Par exemple :

```text
Silver
   │
   ▼
silver.clients
   │
   ▼
stg_clients
   │
   ▼
dim_clients
```

Le modèle :

```text
models/staging/stg_clients.sql
```

contient par exemple :

```sql
SELECT
    client_id,
    prenom,
    nom,
    email,
    telephone,
    adresse,
    ville,
    pays,
    date_naissance,
    date_inscription,
    est_premium,
    est_actif
FROM {{ ref('silver_clients') }}
```

La fonction `ref()` permet à dbt de gérer les **dépendances entre les modèles**.

---

# 6. Staging → Gold

Une fois les données préparées dans Staging, les modèles Gold peuvent les utiliser.

Par exemple :

```text
stg_clients
     │
     ▼
dim_clients
```

```sql
SELECT
    client_id,
    prenom,
    nom,
    email,
    telephone,
    ville,
    pays,
    date_inscription,
    est_premium,
    est_actif
FROM {{ ref('stg_clients') }}
```

Pour une table de faits :

```text
stg_transactions ──────┐
                       │
                       ▼
                 fact_transactions
                       ▲
                       │
stg_comptes ───────────┘
```

On peut alors réaliser une jointure métier :

```sql
SELECT
    t.transaction_id,
    t.compte_id,
    c.client_id,
    t.type_transaction,
    t.montant,
    t.devise,
    t.date_transaction,
    t.canal,
    t.statut
FROM {{ ref('stg_transactions') }} AS t
LEFT JOIN {{ ref('stg_comptes') }} AS c
    ON t.compte_id = c.compte_id
```

C'est **ici** que commence réellement la modélisation analytique.

---

# 7. Objectif de la couche Gold

Gold doit répondre directement aux besoins des analystes, des dashboards et de la direction.

Nous construisons trois catégories de modèles :

| Catégorie      | Rôle                                 |
| -------------- | ------------------------------------ |
| **Dimensions** | Décrire les entités métier           |
| **Facts**      | Stocker les événements mesurables    |
| **KPIs**       | Produire des indicateurs analytiques |

---

# 8. Dimensions

| Modèle        | Description                  | Source dbt            |
| ------------- | ---------------------------- | --------------------- |
| `dim_clients` | Informations sur les clients | `stg_clients`         |
| `dim_comptes` | Informations sur les comptes | `stg_comptes`         |
| `dim_dates`   | Dimension calendrier         | Générée par dbt/Spark |

---

# 9. Tables de faits

| Modèle              | Description             | Sources                            |
| ------------------- | ----------------------- | ---------------------------------- |
| `fact_transactions` | Transactions bancaires  | `stg_transactions` + `stg_comptes` |
| `fact_virements`    | Virements entre comptes | `stg_virements`                    |
| `fact_paiements`    | Paiements par carte     | `stg_paiements`                    |

Les tables de faits contiennent principalement des **événements mesurables** :

* montant ;
* date ;
* frais ;
* statut ;
* canal ;
* identifiants des dimensions.

---

# 10. KPIs

| Modèle                   | Description                          | Source               |
| ------------------------ | ------------------------------------ | -------------------- |
| `kpi_revenus_mensuels`   | Revenus/crédits par mois             | `fact_transactions`  |
| `kpi_croissance_clients` | Nouveaux clients par mois            | `dim_clients`        |
| `kpi_alertes_fraude`     | Alertes par type et niveau de risque | `stg_alertes_fraude` |

Exemple :

```sql
SELECT
    DATE_TRUNC('month', date_transaction) AS mois,
    COUNT(*) AS nb_transactions,
    SUM(montant) AS total_revenus,
    AVG(montant) AS montant_moyen
FROM {{ ref('fact_transactions') }}
WHERE type_transaction = 'CREDIT'
  AND statut = 'COMPLETEE'
GROUP BY DATE_TRUNC('month', date_transaction)
```

Ici, le KPI ne retourne pas directement dans Silver.

Il utilise :

```text
stg_transactions
       ↓
fact_transactions
       ↓
kpi_revenus_mensuels
```

---

# 11. Modèle dimensionnel — Star Schema

```text
                       ┌──────────────────┐
                       │   dim_clients    │
                       │                  │
                       │ client_id        │
                       │ nom              │
                       │ prenom           │
                       │ ville            │
                       │ pays             │
                       └────────┬─────────┘
                                │
                                │
┌──────────────────┐            │            ┌──────────────────────┐
│   dim_comptes    │────────────┼────────────│  fact_transactions   │
│                  │            │            │                      │
│ compte_id        │            │            │ transaction_id       │
│ client_id        │            │            │ compte_id             │
│ type_compte      │            │            │ client_id             │
│ solde            │            │            │ montant               │
└──────────────────┘            │            │ date_transaction      │
                                │            │ canal                 │
                                │            │ statut                │
                                │            └──────────┬───────────┘
                                │                       │
                                │                       │
                       ┌────────┴─────────┐             │
                       │    dim_dates     │─────────────┘
                       │                  │
                       │ date_key         │
                       │ jour             │
                       │ mois             │
                       │ trimestre        │
                       │ annee            │
                       └──────────────────┘
```

---

# 12. Dépendances dbt

La chaîne de dépendances est maintenant :

```text
                    SILVER
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
   stg_clients   stg_comptes   stg_transactions
        │             │              │
        ▼             ▼              │
   dim_clients   dim_comptes          │
                                      │
                     ┌────────────────┘
                     ▼
              fact_transactions
                     │
                     ▼
          kpi_revenus_mensuels
```

Et :

```text
stg_alertes_fraude
        │
        ▼
kpi_alertes_fraude
```

---

# 13. Questions métier couvertes

| Question métier                                  | Modèle Gold              |
| ------------------------------------------------ | ------------------------ |
| Combien de nouveaux clients chaque mois ?        | `kpi_croissance_clients` |
| Quel est le montant total des crédits par mois ? | `kpi_revenus_mensuels`   |
| Quels sont les clients Premium ?                 | `dim_clients`            |
| Combien d'alertes de fraude avons-nous ?         | `kpi_alertes_fraude`     |
| Quel est le montant des transactions ?           | `fact_transactions`      |
| Quels sont les types de comptes ?                | `dim_comptes`            |

---

# 14. Organisation du projet dbt

```text
dbt/
│
├── Dockerfile
├── profiles.yml
├── dbt_project.yml
│
├── models/
│   │
│   ├── staging/
│   │   ├── stg_clients.sql
│   │   ├── stg_comptes.sql
│   │   ├── stg_transactions.sql
│   │   ├── stg_paiements.sql
│   │   ├── stg_virements.sql
│   │   └── ...
│   │
│   └── gold/
│       │
│       ├── dimensions/
│       │   ├── dim_clients.sql
│       │   ├── dim_comptes.sql
│       │   └── dim_dates.sql
│       │
│       ├── facts/
│       │   ├── fact_transactions.sql
│       │   ├── fact_virements.sql
│       │   └── fact_paiements.sql
│       │
│       ├── kpis/
│       │   ├── kpi_revenus_mensuels.sql
│       │   ├── kpi_croissance_clients.sql
│       │   └── kpi_alertes_fraude.sql
│       │
│       └── schema.yml
│
├── tests/
├── macros/
└── seeds/
```

---

# 15. Exécution

### Vérifier la configuration

```bash
dbt debug
```

### Construire tous les modèles

```bash
dbt run
```

### Construire uniquement Gold

```bash
dbt run --select gold
```

### Construire un modèle spécifique

```bash
dbt run --select dim_clients
```

### Exécuter les tests

```bash
dbt test
```

### Construire Gold et exécuter les tests

```bash
dbt build --select gold
```

---

## 16. Résumé

La logique de notre pipeline est donc :

```text
PostgreSQL
    │
    ▼
  Bronze
    │
    │ Spark
    ▼
  Silver
    │
    │ dbt + Spark SQL
    ▼
 Staging
    │
    │ dbt + jointures + agrégations
    ▼
  Gold
    │
    ├── Dimensions
    ├── Facts
    └── KPIs
    │
    ▼
Power BI / Streamlit
```

**Point essentiel :**

> **Silver contient les données propres. Staging les prépare pour dbt. Gold les transforme en données analytiques répondant aux besoins métier.**
