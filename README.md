# DevOps Pipeline — Plateforme Microservices sur Kubernetes

> Stack complète : CI/CD Jenkins · Docker · Kubernetes (k3s) · Keycloak · HashiCorp Vault · Nexus · PostgreSQL

![GitHub](https://img.shields.io/badge/GitHub-devops--pipeline-181717?logo=github)
![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s-326CE5?logo=kubernetes)
![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins-D24939?logo=jenkins)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker)
![Vault](https://img.shields.io/badge/Secrets-HashiCorp%20Vault-000000?logo=vault)
![Keycloak](https://img.shields.io/badge/Auth-Keycloak-4D4D4D?logo=keycloak)

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Composants](#composants)
- [Pipeline CI/CD](#pipeline-cicd)
- [Flux d'authentification](#flux-dauthentification)
- [Déploiement Kubernetes](#déploiement-kubernetes)
- [Lancement local](#lancement-local)
- [Améliorations prévues](#améliorations-prévues)

---

## Vue d'ensemble

Ce projet est une plateforme applicative microservices déployée sur Kubernetes, conçue comme un projet DevOps end-to-end.

L'objectif est de couvrir l'ensemble du cycle de vie d'une application en production :

- **Développement** → code versionné sur GitHub
- **Build** → images Docker buildées automatiquement par Jenkins
- **Registry** → images stockées dans Nexus Repository Manager
- **Déploiement** → manifests Kubernetes appliqués sur un cluster k3s
- **Authentification** → centralisée via Keycloak (OAuth2 / OpenID Connect)
- **Gestion des secrets** → HashiCorp Vault avec injection via Vault Agent Injector

---

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │         GitHub (source)             │
                        └────────────────┬────────────────────┘
                                         │ push / webhook
                                         ▼
                        ┌─────────────────────────────────────┐
                        │           Jenkins (CI/CD)           │
                        │   Build → Push Nexus → Deploy k3s  │
                        └────────────────┬────────────────────┘
                                         │
                                         ▼
              ┌──────────────────────────────────────────────────┐
              │                 Kubernetes (k3s)                  │
              │  Namespace : devops-pipeline                      │
              │                                                   │
              │   ┌────────────┐      ┌────────────────────┐     │
              │   │  Keycloak  │◄────►│   app-frontend     │     │
              │   │  (Auth)    │      │   Flask  :5000     │     │
              │   └────────────┘      └──────┬──────┬──────┘     │
              │                             │      │             │
              │               ┌─────────────┘      └──────────┐  │
              │               ▼                               ▼  │
              │   ┌───────────────────┐      ┌───────────────────┐│
              │   │   app-users       │      │   app-products    ││
              │   │   Flask  :5001    │      │   Flask  :5002    ││
              │   └────────┬──────────┘      └───────────────────┘│
              │            │                                      │
              └────────────┼──────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   PostgreSQL (VM Linux) │
              │   Base : workflow       │
              │   Table : users         │
              └─────────────────────────┘
```

**HashiCorp Vault** injecte les secrets dans les pods via le Vault Agent Injector (annotations Kubernetes).

---

## Stack technique

| Catégorie | Technologie |
|---|---|
| Langage applicatif | Python 3.12 / Flask |
| Conteneurisation | Docker |
| Orchestration | Kubernetes k3s |
| CI/CD | Jenkins |
| Registry | Sonatype Nexus |
| Authentification | Keycloak (OAuth2 / OIDC) |
| Gestion des secrets | HashiCorp Vault |
| Base de données | PostgreSQL |
| Réseau K8s | Calico CNI |
| OS cible | Rocky Linux / Ubuntu |

---

## Structure du projet

```
devops-pipeline/
│
├── app-frontend/          # Interface utilisateur Flask
│   ├── app.py             # Application principale
│   ├── Dockerfile
│   └── requirements.txt
│
├── app-products/          # Microservice catalogue produits
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── app-users/             # Microservice utilisateurs → PostgreSQL
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s/                   # Manifests Kubernetes
│   ├── app-frontend.yml   # Deployment + Service + annotations Vault
│   ├── app-products.yml   # Deployment + Service
│   └── app-users.yml      # Deployment + Service
│
├── keycloak/              # Configuration Keycloak (realm, client)
├── nexus/                 # Configuration Nexus Repository
│
├── Jenkinsfile            # Pipeline CI/CD complet
└── README.md
```

---

## Composants

### app-frontend

Application Flask faisant office de portail utilisateur.

- Authentification via Keycloak (OAuth2 Direct Grant)
- Session Flask après validation du token
- Consommation des APIs `app-products` et `app-users`
- Secret Keycloak (`KEYCLOAK_CLIENT_SECRET`) injecté depuis **Vault** via le fichier `/vault/secrets/keycloak`

**Port exposé :** `5000` → NodePort `30000`

---

### app-products

Microservice REST exposant un catalogue de produits d'assurance.

| Endpoint | Description |
|---|---|
| `GET /health` | Healthcheck du service |
| `GET /products` | Liste de tous les produits |
| `GET /products/<id>` | Détail d'un produit |

**Port exposé :** `5002` → NodePort `30002`

---

### app-users

Microservice REST connecté à **PostgreSQL**.

| Endpoint | Description |
|---|---|
| `GET /health` | Healthcheck du service |
| `GET /users` | Liste des utilisateurs depuis la base |

Connexion à la base `workflow`, table `users` (colonnes : `id`, `username`, `email`).

**Port exposé :** `5001` → NodePort `30001`

---

### HashiCorp Vault

Gestion centralisée des secrets.

- Secret stocké : `secret/frontend` → clé `keycloak-client-secret`
- Injection via **Vault Agent Injector** (annotations sur le pod `app-frontend`)
- ServiceAccount K8s dédié : `frontend-sa` avec le rôle Vault `frontend-role`
- Le secret est monté dans le pod à `/vault/secrets/keycloak`

---

### Keycloak

Fournisseur d'identité centralisé.

- **Realm :** `zak-local`
- **Client :** `app-frontend` (flux Direct Grant activé)
- Génère les tokens OAuth2 / OpenID Connect consommés par le frontend

---

## Pipeline CI/CD

Le pipeline Jenkins orchestre 5 étapes automatiques déclenchées sur chaque push GitHub :

```
GitHub Push
    │
    ▼
┌─────────────┐
│ 1. Clone    │  Récupération du code source
└──────┬──────┘
       ▼
┌─────────────────┐
│ 2. Build Images │  docker build des 3 apps (tag : vBUILD_NUMBER)
└──────┬──────────┘
       ▼
┌──────────────────┐
│ 3. Push to Nexus │  docker push vers 192.168.74.128:8082
└──────┬───────────┘
       ▼
┌──────────────────────┐
│ 4. Update Manifests  │  sed -i sur les YAMLs k8s (mise à jour du tag image)
└──────┬───────────────┘
       ▼
┌─────────────────┐
│ 5. Deploy k3s   │  kubectl apply -f k8s/*.yml
└─────────────────┘
```

Les credentials Nexus sont stockés dans **Jenkins Credentials Store** (id : `nexus-credentials`), jamais dans le code.

Le tag de l'image est automatiquement versionné via `v${BUILD_NUMBER}`.

---

## Flux d'authentification

```
Utilisateur
    │
    │  1. Accède à http://<NODE_IP>:30000
    ▼
app-frontend
    │
    │  2. Affiche le formulaire de login
    │
    │  3. Envoie username + password à Keycloak
    ▼
Keycloak (Direct Grant)
    │
    │  4. Valide les credentials
    │  5. Retourne un access_token JWT
    ▼
app-frontend
    │
    │  6. Crée une session Flask
    │  7. Appelle app-products → GET /products
    │  8. Appelle app-users → GET /users
    ▼
Dashboard utilisateur (produits + utilisateurs PostgreSQL)
```

---

## Déploiement Kubernetes

Tous les composants applicatifs sont déployés dans le namespace `devops-pipeline`.

```bash
# Créer le namespace
kubectl create namespace devops-pipeline

# Appliquer les manifests
kubectl apply -f k8s/app-users.yml -n devops-pipeline
kubectl apply -f k8s/app-products.yml -n devops-pipeline
kubectl apply -f k8s/app-frontend.yml -n devops-pipeline

# Vérifier les pods
kubectl get pods -n devops-pipeline

# Vérifier les services
kubectl get svc -n devops-pipeline
```

**Ports exposés (NodePort) :**

| Service | Port interne | NodePort |
|---|---|---|
| app-frontend | 5000 | 30000 |
| app-users | 5001 | 30001 |
| app-products | 5002 | 30002 |

---

## Lancement local (sans Kubernetes)

```bash
# Cloner le repo
git clone https://github.com/Guizak-5621/devops-pipeline.git
cd devops-pipeline

# Lancer app-products
cd app-products
pip install -r requirements.txt
python app.py

# Lancer app-users (nécessite PostgreSQL accessible)
cd ../app-users
pip install -r requirements.txt
python app.py

# Lancer le frontend
cd ../app-frontend
export KEYCLOAK_CLIENT_SECRET=<votre_secret>
pip install -r requirements.txt
python app.py
```

---

## Améliorations prévues

- [ ] **Communication interne K8s** — remplacer les NodePort inter-services par des ClusterIP (`http://app-users:5001`, `http://app-products:5002`)
- [ ] **Secrets DB dans Vault** — externaliser `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` depuis le code source de `app-users`
- [ ] **Observabilité** — intégration Prometheus + Grafana pour la supervision des pods
- [ ] **Pipeline complet** — déclencher automatiquement Jenkins via webhook GitHub sur chaque merge sur `main`
- [ ] **Dockerfiles multi-stage** — réduire la taille des images de production
- [ ] **Ingress Controller** — remplacer les NodePort par un Ingress NGINX avec nom de domaine

---

## Auteur

**Ishak GUECHOUD** — DevOps Engineer  
[GitHub](https://github.com/Guizak-5621) · [LinkedIn](#)

> Projet réalisé dans le cadre d'un portfolio DevOps personnel — stack complète déployée sur infrastructure locale (homelab).
