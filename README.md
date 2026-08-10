# Data Generator

## Pourquoi ?

Bank360 est un projet académique. Les données réelles d'une banque ne sont pas accessibles.

Nous générons donc des données fictives permettant de simuler le fonctionnement d'un système bancaire.

## Objectif

Le générateur produit des données représentant :
- clients
- comptes
- cartes
- transactions
- crédits
- agences
- retraits ATM
- paiements
- virements
- bénéficiaires
- alertes fraude

## Architecture

```text
Python (Faker)
    ↓
PostgreSQL (OLTP Source)
    ↓
Base de données simulée