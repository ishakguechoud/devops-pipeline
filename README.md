# DevOps Pipeline — Plateforme Microservices sur Kubernetes

> Stack complète : CI/CD Jenkins · Docker · Kubernetes (k3s) · Helm · Keycloak · HashiCorp Vault · Nexus · PostgreSQL

![GitHub](https://img.shields.io/badge/GitHub-devops--pipeline-181717?logo=github)
![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s-326CE5?logo=kubernetes)
![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins-D24939?logo=jenkins)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker)
![Helm](https://img.shields.io/badge/Package-Helm-0F1689?logo=helm)
![Vault](https://img.shields.io/badge/Secrets-HashiCorp%20Vault-000000?logo=vault)
![Keycloak](https://img.shields.io/badge/Auth-Keycloak-4D4D4D?logo=keycloak)

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [GitFlow & Environnements](#gitflow--environnements)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Composants](#composants)
- [Helm Charts](#helm-charts)
- [Pipeline CI/CD](#pipeline-cicd)
- [Flux d'authentification](#flux-dauthentification)
- [Déploiement](#déploiement)
- [Lancement local](#lancement-local)
- [Améliorations prévues](#améliorations-prévues)

---

## Vue d'ensemble

Ce projet est une plateforme applicative microservices déployée sur Kubernetes, conçue comme un projet DevOps end-to-end.

L'objectif est de couvrir l'ensemble du cycle de vie d'une application en production :

- **Développement** → code versionné sur GitHub (branches `develop` / `main`)
- **Build** → images Docker buildées automatiquement par Jenkins (Poll SCM)
- **Registry** → images stockées dans Nexus Repository Manager
- **Déploiement** → géré par **Helm** sur un cluster k3s (multi-environnement)
- **Authentification** → centralisée via Keycloak (OAuth2 / OpenID Connect)
- **Gestion des secrets** → HashiCorp Vault avec injection via Vault Agent Injector

---

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │         GitHub (source)             │
                        │   branch develop │ branch main      │
                        └────────┬─────────────────┬──────────┘
                                 │ Poll SCM        │ Poll SCM
                                 ▼                 ▼
                        ┌─────────────────────────────────────┐
                        │           Jenkins (CI/CD)           │
                        │  devops-pipeline-develop            │
                        │  devops-pipeline-main               │
                        │   Build → Push Nexus → Helm Deploy  │
                        └────────┬─────────────────┬──────────┘
                                 │                 │
                          preprod-platform    prod-platform
                                 ▼                 ▼
              ┌──────────────────────────────────────────────┐
              │           Kubernetes k3s                      │
              │                                              │
              │  ┌────────────┐   ┌──────────────────────┐  │
              │  │  Keycloak  │◄─►│    app-frontend       │  │
              │  │  (Auth)    │   │    Flask  :5000       │  │
              │  └────────────┘   └───────┬──────┬────────┘  │
              │                          │      │            │
              │           ┌──────────────┘      └─────────┐  │
              │           ▼                               ▼  │
              │  ┌─────────────────┐      ┌─────────────────┐│
              │  │   app-users     │      │  app-products   ││
              │  │   Flask :5001   │      │  Flask :5002    ││
              │  └────────┬────────┘      └─────────────────┘│
              └───────────┼──────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │   PostgreSQL (VM Linux) │
              │   Base : workflow       │
              │   Table : users         │
              └─────────────────────────┘
```

**HashiCorp Vault** injecte les secrets dans les pods via le Vault Agent Injector :
- `app-frontend` → `KEYCLOAK_CLIENT_SECRET` depuis `secret/data/frontend`
- `app-users` → credentials DB depuis `secret/data/users` (prod uniquement)

---

## GitFlow & Environnements

Ce projet suit un workflow **GitFlow** avec deux environnements distincts :

```
develop ──── push ──► Jenkins ──► preprod-platform  (tests)
                                         │
                               Pull Request + merge
                                         │
main    ──── push ──► Jenkins ──► prod-platform     (production)
```

**Ports par environnement :**

| Service | Preprod (NodePort) | Prod (NodePort) |
|---|---|---|
| app-frontend | 30010 | 31000 |
| app-users | 30011 | 30001 |
| app-products | 30012 | 30002 |

**Jenkins Poll SCM** vérifie GitHub toutes les 2 minutes et déclenche automatiquement le bon pipeline selon la branche détectée.

---

## Stack technique

| Catégorie | Technologie |
|---|---|
| Langage applicatif | Python 3.12 / Flask |
| Conteneurisation | Docker |
| Orchestration | Kubernetes k3s |
| Package Manager K8s | Helm |
| CI/CD | Jenkins (Poll SCM) |
| Registry | Sonatype Nexus |
| Authentification | Keycloak (OAuth2 / OIDC) |
| Gestion des secrets | HashiCorp Vault + Agent Injector |
| Base de données | PostgreSQL |
| Réseau K8s | Calico CNI |
| OS cible | Rocky Linux / Ubuntu |

---

## Structure du projet

```
devops-pipeline/
│
├── app-frontend/
│   ├── app.py                      # Interface utilisateur Flask (UI moderne)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── chart/                      # Helm Chart
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-preprod.yaml
│       ├── values-prod.yaml        # Vault activé (frontend-sa)
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           └── service.yaml
│
├── app-products/
│   ├── app.py                      # Microservice catalogue produits
│   ├── Dockerfile
│   ├── requirements.txt
│   └── chart/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-preprod.yaml
│       ├── values-prod.yaml        # 2 replicas en prod
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           └── service.yaml
│
├── app-users/
│   ├── app.py                      # Microservice users → PostgreSQL
│   ├── Dockerfile
│   ├── requirements.txt
│   └── chart/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-preprod.yaml     # Credentials DB via env vars
│       ├── values-prod.yaml        # Credentials DB via Vault (users-sa)
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml     # readiness + liveness probes
│           └── service.yaml
│
├── keycloak/                       # Configuration Keycloak
├── nexus/                          # Configuration Nexus
├── Jenkinsfile                     # Pipeline CI/CD (Poll SCM + GitFlow)
└── README.md
```

---

## Composants

### app-frontend

Application Flask faisant office de portail utilisateur.

- Authentification via Keycloak (OAuth2 Direct Grant)
- Session Flask après validation du token JWT
- `KEYCLOAK_CLIENT_SECRET` injecté depuis Vault (`/vault/secrets/keycloak`)
- Configuration externalisée via variables d'environnement

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard (authentification requise) |
| `GET /login` | Page de connexion |
| `GET /logout` | Déconnexion |

---

### app-products

Microservice REST exposant un catalogue de produits d'assurance.

| Endpoint | Description |
|---|---|
| `GET /health` | Healthcheck du service |
| `GET /products` | Liste de tous les produits |
| `GET /products/<id>` | Détail d'un produit |

---

### app-users

Microservice REST connecté à PostgreSQL.

| Endpoint | Description |
|---|---|
| `GET /health` | Healthcheck du service |
| `GET /users` | Liste des utilisateurs depuis la base |

**Gestion des secrets DB :**
- **Preprod** : credentials via variables d'environnement Helm
- **Prod** : credentials injectés depuis Vault (`/vault/secrets/db`)

---

### HashiCorp Vault

| Secret | Path Vault | Service | Env |
|---|---|---|---|
| `keycloak-client-secret` | `secret/data/frontend` | app-frontend | preprod + prod |
| `db-host/name/user/password` | `secret/data/users` | app-users | prod |

- `frontend-sa` → rôle `frontend-role` → policy `frontend-policy`
- `users-sa` → rôle `users-role` → policy `users-policy`

---

### Keycloak

- **Realm :** `zak-local`
- **Client :** `app-frontend` (flux Direct Grant)
- Génère les tokens OAuth2 / OpenID Connect

---

## Helm Charts

Chaque microservice a son propre Helm Chart avec séparation preprod/prod.

```
chart/
├── _helpers.tpl         # svc.name, svc.fullname, svc.labels
├── deployment.yaml      # readiness + liveness probes inclus
└── service.yaml         # NodePort ou ClusterIP selon l'env
```

**Vérifier sans déployer :**

```bash
helm template app-users ./app-users/chart \
  -f ./app-users/chart/values-prod.yaml \
  --namespace prod-platform

helm lint ./app-users/chart -f ./app-users/chart/values-prod.yaml
```

---

## Pipeline CI/CD

Deux jobs Jenkins avec **Poll SCM** (toutes les 2 minutes) :

```
GitHub push develop                    GitHub push/merge main
       │                                       │
       ▼                                       ▼
devops-pipeline-develop            devops-pipeline-main
       │                                       │
  ┌────┴────┐                            ┌─────┴────┐
  │ Clone   │                            │  Clone   │
  │ Build   │                            │  Build   │
  │ Push    │                            │  Push    │
  │ Nexus   │                            │  Nexus   │
  │ Helm ──►│ preprod-platform           │  Helm ──►│ prod-platform
  └─────────┘                            └──────────┘
  ✅ PREPROD                             ✅ PROD
```

---

## Flux d'authentification

```
Utilisateur → http://<NODE_IP>:31000
    │
    ▼
app-frontend (formulaire login)
    │
    ▼
Keycloak Direct Grant
    │ access_token JWT
    ▼
app-frontend (session Flask)
    ├──► app-products GET /products
    └──► app-users    GET /users
    │
    ▼
Dashboard (produits + utilisateurs PostgreSQL)
```

---

## Déploiement

### Via Helm

```bash
# Preprod (branche develop)
helm upgrade --install app-users ./app-users/chart \
  --namespace preprod-platform --create-namespace \
  -f ./app-users/chart/values-preprod.yaml \
  --set image.tag=v1

# Prod (branche main)
helm upgrade --install app-users ./app-users/chart \
  --namespace prod-platform --create-namespace \
  -f ./app-users/chart/values-prod.yaml \
  --set image.tag=v1
```

### Vérifier les pods

```bash
kubectl get pods -n preprod-platform
kubectl get pods -n prod-platform
```

### Configurer Vault pour un nouveau service

```bash
# 1. ServiceAccount
kubectl create serviceaccount <sa-name> -n prod-platform

# 2. Policy
kubectl exec -n vault vault-0 -- sh -c \
  'echo "path \"secret/data/<svc>\" { capabilities = [\"read\"] }" \
  > /tmp/p.hcl && vault policy write <svc>-policy /tmp/p.hcl'

# 3. Role
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/<svc>-role \
  bound_service_account_names=<sa-name> \
  bound_service_account_namespaces=prod-platform \
  policies=<svc>-policy ttl=24h

# 4. Secret
kubectl exec -n vault vault-0 -- vault kv put secret/<svc> key="value"
```

---

## Lancement local (sans Kubernetes)

```bash
git clone https://github.com/ishakguechoud/devops-pipeline.git
cd devops-pipeline

# app-products
cd app-products && pip install -r requirements.txt && python app.py

# app-users
cd ../app-users
export DB_HOST=localhost DB_NAME=workflow DB_USER=... DB_PASSWORD=...
pip install -r requirements.txt && python app.py

# app-frontend
cd ../app-frontend
export KEYCLOAK_CLIENT_SECRET=<secret>
export KEYCLOAK_BASE_URL=http://<keycloak-ip>:8086
pip install -r requirements.txt && python app.py
```

---

## Améliorations prévues

- [ ] **Webhook GitHub → Jenkins** — remplacer le Poll SCM par un webhook via ngrok ou reverse proxy
- [ ] **Ingress Controller** — remplacer les NodePort par un Ingress NGINX avec nom de domaine
- [ ] **Observabilité** — Prometheus + Grafana pour la supervision des pods
- [ ] **Dockerfiles multi-stage** — réduire la taille des images de production
- [ ] **Communication interne K8s** — appels inter-services via ClusterIP (`http://app-users:5001`)
- [ ] **Tests automatisés** — stage de tests dans le pipeline avant déploiement

---

## Auteur

**Ishak GUECHOUD** — DevOps Engineer  
[GitHub](https://github.com/ishakguechoud) · [LinkedIn](#)

> Projet portfolio DevOps — stack complète déployée sur homelab.  
> Architecture transposable en environnement d'entreprise (Helm, Vault, GitFlow, multi-namespace).
