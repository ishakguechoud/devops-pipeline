# DevOps Pipeline — Plateforme Microservices sur Kubernetes

> Stack complète : CI/CD Jenkins · Docker · Kubernetes (k3s) · Helm · API Gateway · Keycloak · HashiCorp Vault · Nexus · PostgreSQL

![GitHub](https://img.shields.io/badge/GitHub-devops--pipeline-181717?logo=github)
![Kubernetes](https://img.shields.io/badge/Kubernetes-k3s-326CE5?logo=kubernetes)
![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins-D24939?logo=jenkins)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker)
![Helm](https://img.shields.io/badge/Package-Helm-0F1689?logo=helm)
![Vault](https://img.shields.io/badge/Secrets-HashiCorp%20Vault-000000?logo=vault)
![Keycloak](https://img.shields.io/badge/Auth-Keycloak-4D4D4D?logo=keycloak)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [GitFlow & Environnements](#gitflow--environnements)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Composants](#composants)
- [API Gateway](#api-gateway)
- [Helm Charts](#helm-charts)
- [Pipeline CI/CD](#pipeline-cicd)
- [Gestion des secrets (Vault)](#gestion-des-secrets-vault)
- [Flux d'authentification](#flux-dauthentification)
- [Déploiement](#déploiement)
- [Troubleshooting](#troubleshooting)
- [Améliorations prévues](#améliorations-prévues)

---

## Vue d'ensemble

Ce projet est une plateforme applicative microservices déployée sur Kubernetes, conçue comme un projet DevOps end-to-end couvrant l'ensemble du cycle de vie d'une application en production.

- **Développement** → code versionné sur GitHub (branches `develop` / `main`)
- **Build** → images Docker buildées automatiquement par Jenkins (Poll SCM)
- **Registry** → images stockées dans Nexus Repository Manager
- **Déploiement** → géré par **Helm** sur un cluster k3s (multi-environnement)
- **Routage API** → centralisé via un **API Gateway** Flask avec validation JWT
- **Authentification** → centralisée via Keycloak (OAuth2 / OpenID Connect)
- **Gestion des secrets** → HashiCorp Vault avec injection via Vault Agent Injector

---

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │         GitHub (source)              │
                        │   branch develop │ branch main       │
                        └────────┬─────────────────┬───────────┘
                                 │ Poll SCM        │ Poll SCM
                                 ▼                 ▼
                        ┌─────────────────────────────────────┐
                        │           Jenkins (CI/CD)            │
                        │  devops-pipeline-develop             │
                        │  devops-pipeline-main                │
                        │  Build → Push Nexus → Helm Deploy    │
                        └────────┬─────────────────┬───────────┘
                                 │                 │
                          preprod-platform    prod-platform
                                 ▼                 ▼
              ┌──────────────────────────────────────────────────┐
              │             Kubernetes k3s (2 nodes)              │
              │          master (192.168.74.128) + worker          │
              │                                                    │
              │  ┌────────────┐   ┌───────────────────────┐       │
              │  │  Keycloak  │◄─►│    app-frontend        │       │
              │  │  (Auth)    │   │    Flask :5000          │       │
              │  └────────────┘   │    Blueprints + Jinja2  │       │
              │                   └───────────┬────────────┘       │
              │                               │ Bearer JWT         │
              │                   ┌───────────▼────────────┐       │
              │                   │    API Gateway          │       │
              │                   │    Flask :5003           │       │
              │                   │    JWT validation        │       │
              │                   └─────┬───────────┬───────┘       │
              │                        │           │               │
              │            ┌───────────┘           └────────────┐  │
              │            ▼                                    ▼  │
              │  ┌──────────────────┐        ┌──────────────────┐ │
              │  │   app-users      │        │  app-products    │ │
              │  │   Flask :5001    │        │  Flask :5002     │ │
              │  └────────┬─────────┘        └──────────────────┘ │
              │           │                                        │
              └───────────┼────────────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────────┐     ┌──────────────────┐
              │   PostgreSQL (VM Linux) │     │ HashiCorp Vault  │
              │   Base : workflow       │     │ Secrets Injection│
              │   Table : users         │     │ Agent Injector   │
              └─────────────────────────┘     └──────────────────┘
```

---

## GitFlow & Environnements

Ce projet suit un workflow **GitFlow** avec deux environnements complètement isolés :

```
develop ──── push ──► Jenkins ──► preprod-platform  (tests)
                                       │
                             Pull Request + merge
                                       │
main    ──── merge ──► Jenkins ──► prod-platform    (production)
```

**Ports par environnement :**

| Service | Preprod (NodePort) | Prod (NodePort) |
|---|---|---|
| app-frontend | 30010 | 31000 |
| app-gateway | 30013 | 30003 |
| app-users | 30011 | 30001 |
| app-products | 30012 | 30002 |

**Jenkins Poll SCM** vérifie GitHub toutes les 2 minutes et déclenche automatiquement le pipeline correspondant à la branche modifiée.

---

## Stack technique

| Catégorie | Technologie |
|---|---|
| Langage applicatif | Python 3.12 / Flask |
| Architecture | Microservices + API Gateway |
| Conteneurisation | Docker |
| Orchestration | Kubernetes k3s (2 nodes) |
| Package Manager K8s | Helm |
| CI/CD | Jenkins (Poll SCM, GitFlow) |
| Registry | Sonatype Nexus |
| Authentification | Keycloak (OAuth2 / OIDC) |
| Gestion des secrets | HashiCorp Vault + Agent Injector |
| Base de données | PostgreSQL |
| Ingress | NGINX Ingress Controller |
| OS | AlmaLinux 9.6 (VMware) |

---

## Structure du projet

```
devops-pipeline/
│
├── app-frontend/                    # Interface utilisateur Flask
│   ├── app.py                       # Point d'entrée (12 lignes)
│   ├── config.py                    # Configuration centralisée
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── routes/                      # Flask Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py                  # /login, /logout
│   │   └── dashboard.py            # / (dashboard principal)
│   ├── services/                    # Logique métier
│   │   ├── __init__.py
│   │   ├── keycloak.py             # Lecture secret Vault
│   │   └── gateway.py              # Client API Gateway
│   ├── templates/                   # Templates Jinja2
│   │   ├── base.html               # Layout commun
│   │   ├── login.html              # Page de connexion
│   │   └── dashboard.html          # Dashboard produits + users
│   ├── static/
│   │   └── style.css               # CSS séparé
│   └── chart/                       # Helm Chart
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-preprod.yaml
│       ├── values-prod.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           ├── service.yaml
│           └── ingress.yaml
│
├── app-gateway/                     # API Gateway (JWT + routing)
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── chart/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-preprod.yaml
│       └── values-prod.yaml
│
├── app-products/                    # Microservice catalogue
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── chart/
│
├── app-users/                       # Microservice users → PostgreSQL
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── chart/
│
├── keycloak/                        # Configuration Keycloak
├── nexus/                           # Configuration Nexus
├── Jenkinsfile                      # Pipeline CI/CD
└── README.md
```

---

## Composants

### app-frontend

Interface utilisateur Flask structurée avec **Blueprints** (séparation des responsabilités).

- Authentification via Keycloak (OAuth2 Direct Grant)
- Appels API via l'**API Gateway** (plus d'appels directs aux microservices)
- Token JWT transmis automatiquement au Gateway
- `KEYCLOAK_CLIENT_SECRET` injecté depuis Vault

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard (produits + utilisateurs) |
| `GET /login` | Page de connexion Keycloak |
| `GET /logout` | Déconnexion |

---

### app-gateway

**API Gateway** central — point d'entrée unique pour tous les microservices.

- Validation du token JWT Keycloak avant forwarding
- Routing vers les microservices via URLs internes K8s (ClusterIP)
- Health check agrégé de tous les services
- Headers `X-Gateway-User` transmis aux backends

| Endpoint | Auth | Description |
|---|---|---|
| `GET /health` | Non | Healthcheck du gateway |
| `GET /api/health` | Non | Health agrégé (gateway + products + users) |
| `GET /api/products` | JWT | Liste des produits via app-products |
| `GET /api/products/<id>` | JWT | Détail d'un produit |
| `GET /api/users` | JWT | Liste des utilisateurs via app-users |
| `GET /api/whoami` | JWT | Infos du token JWT décodé |

**Communication interne (Gateway → microservices) :**

```
Gateway  ──►  http://app-products-preprod-service:5002  (ClusterIP)
Gateway  ──►  http://app-users-preprod-service:5001     (ClusterIP)
```

---

### app-products

Microservice REST — catalogue de produits d'assurance (données en mémoire).

| Endpoint | Description |
|---|---|
| `GET /health` | Healthcheck |
| `GET /products` | Liste des produits |
| `GET /products/<id>` | Détail d'un produit |

---

### app-users

Microservice REST connecté à PostgreSQL (lecture des utilisateurs).

| Endpoint | Description |
|---|---|
| `GET /health` | Healthcheck |
| `GET /users` | Utilisateurs depuis la base |

**Credentials DB :**
- **Preprod** : variables d'environnement via Helm values
- **Prod** : injection depuis Vault (`/vault/secrets/db`) via Vault Agent

---

## API Gateway

Le Gateway est le composant central de l'architecture. Voici le flux complet :

```
Utilisateur → Navigateur → Frontend (login)
                              │
                              │ Token JWT Keycloak
                              ▼
                         API Gateway (:5003)
                              │
                   ┌──────────┼──────────┐
                   │          │          │
                   ▼          ▼          ▼
              /api/products  /api/users  /api/whoami
                   │          │
                   ▼          ▼
            app-products  app-users → PostgreSQL
```

**Pourquoi un API Gateway ?**
- Un seul point d'entrée pour toutes les APIs
- Validation JWT centralisée (les microservices n'ont pas à gérer l'auth)
- Communication interne K8s (ClusterIP, pas de NodePort inter-services)
- Monitoring et logging centralisé
- Possibilité d'ajouter rate limiting, caching, circuit breaker

---

## Helm Charts

Chaque microservice possède son propre Helm Chart avec séparation preprod/prod via les fichiers `values-*.yaml`.

```
chart/
├── Chart.yaml
├── values.yaml              # Valeurs par défaut (dev)
├── values-preprod.yaml      # Surcharge preprod
├── values-prod.yaml         # Surcharge prod (Vault, replicas)
└── templates/
    ├── _helpers.tpl          # svc.name, svc.fullname, svc.labels
    ├── deployment.yaml       # readiness + liveness probes
    ├── service.yaml          # NodePort ou ClusterIP
    └── ingress.yaml          # (frontend uniquement)
```

**Vérifier les templates sans déployer :**

```bash
# Générer le YAML final
helm template app-users ./app-users/chart \
  -f ./app-users/chart/values-prod.yaml \
  --namespace prod-platform

# Valider la syntaxe
helm lint ./app-users/chart -f ./app-users/chart/values-prod.yaml
```

---

## Pipeline CI/CD

Deux jobs Jenkins avec **Poll SCM** (toutes les 2 minutes), déploiement dynamique selon la branche :

```
GitHub push (develop)                   GitHub merge (main)
       │                                       │
       ▼                                       ▼
devops-pipeline-develop             devops-pipeline-main
       │                                       │
  ┌────┴──────────┐                      ┌─────┴──────────┐
  │ Initialize    │                      │ Initialize     │
  │ ENV=preprod   │                      │ ENV=prod       │
  │ Build 4 imgs  │                      │ Build 4 imgs   │
  │ Push Nexus    │                      │ Push Nexus     │
  │ Configure     │                      │ Configure      │
  │ Vault         │                      │ Vault          │
  │ Helm Deploy ──┤► preprod-platform    │ Helm Deploy ──┤► prod-platform
  └───────────────┘                      └────────────────┘
```

**Images Docker taguées automatiquement** : `Application{BUILD_NUMBER}-{TIMESTAMP}` (ex: `Application52-20260702-1902`)

**Images stockées dans Nexus** par environnement : `workflow-devops/preprod/` et `workflow-devops/prod/`

---

## Gestion des secrets (Vault)

HashiCorp Vault gère tous les secrets applicatifs via le **Vault Agent Injector** (sidecar automatique dans les pods Kubernetes).

**Secrets stockés :**

| Secret | Path Vault | Service | Env |
|---|---|---|---|
| `keycloak-client-secret` | `secret/data/frontend` | app-frontend | preprod + prod |
| `db-host`, `db-name`, `db-user`, `db-password` | `secret/data/users` | app-users | prod |

**ServiceAccounts & Rôles :**

| ServiceAccount | Namespace | Rôle Vault | Policy |
|---|---|---|---|
| `frontend-sa` | preprod + prod | `frontend-role` | `frontend-policy` |
| `users-sa` | preprod + prod | `users-role` | `users-policy` |

**Configurer Vault pour un nouveau service :**

```bash
# 1. ServiceAccount
kubectl create serviceaccount <sa-name> -n prod-platform

# 2. Policy
kubectl exec -n vault vault-0 -- sh -c \
  'echo "path \"secret/data/<svc>\" { capabilities = [\"read\"] }" \
  > /tmp/p.hcl && VAULT_TOKEN=<root-token> vault policy write <svc>-policy /tmp/p.hcl'

# 3. Rôle
kubectl exec -n vault vault-0 -- sh -c 'VAULT_TOKEN=<root-token> vault write \
  auth/kubernetes/role/<svc>-role \
  bound_service_account_names=<sa-name> \
  bound_service_account_namespaces=prod-platform \
  policies=<svc>-policy ttl=24h'

# 4. Secret
kubectl exec -n vault vault-0 -- sh -c 'VAULT_TOKEN=<root-token> \
  vault kv put secret/<svc> key1="value1" key2="value2"'
```

---

## Flux d'authentification

```
Utilisateur
    │
    │  1. Accède à http://<IP>:31000 (prod) ou :30010 (preprod)
    ▼
app-frontend (/login)
    │
    │  2. POST username + password → Keycloak
    ▼
Keycloak (Direct Grant)
    │
    │  3. Retourne access_token JWT
    ▼
app-frontend (session Flask)
    │
    │  4. Appelle Gateway avec Bearer token
    ▼
API Gateway (:5003)
    │
    │  5. Valide le JWT, forwarde aux microservices
    ├──► GET /api/products → app-products → données produits
    └──► GET /api/users → app-users → PostgreSQL → données users
    │
    ▼
Dashboard (produits assurance + utilisateurs PostgreSQL)
```

---

## Déploiement

### Via Helm (automatique par Jenkins)

```bash
# Preprod
helm upgrade --install app-frontend ./app-frontend/chart \
  --namespace preprod-platform --create-namespace \
  -f ./app-frontend/chart/values-preprod.yaml \
  --set image.tag=<TAG>

# Prod
helm upgrade --install app-frontend ./app-frontend/chart \
  --namespace prod-platform --create-namespace \
  -f ./app-frontend/chart/values-prod.yaml \
  --set image.tag=<TAG>
```

### Vérifier l'état

```bash
# Pods
kubectl get pods -n preprod-platform
kubectl get pods -n prod-platform

# Health check global via Gateway
curl http://192.168.74.128:30013/api/health   # preprod
curl http://192.168.74.128:30003/api/health   # prod

# Test JWT Gateway
TOKEN=$(curl -s -X POST http://<KEYCLOAK_IP>:8086/realms/zak-local/protocol/openid-connect/token \
  -d "grant_type=password&client_id=app-frontend&client_secret=<SECRET>&username=<USER>&password=<PASS>&scope=openid" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" http://192.168.74.128:30013/api/products
curl -H "Authorization: Bearer $TOKEN" http://192.168.74.128:30013/api/whoami
```

---

## Troubleshooting

Problèmes rencontrés et solutions documentées durant le développement de ce projet :

| Problème | Cause | Solution |
|---|---|---|
| `nbf: token not yet valid` | Horloge VMware désynchronisée | `vmware-toolbox-cmd timesync enable` + power-cycle VM |
| `403 permission denied` (Vault Agent) | `token_reviewer_jwt` absent | `vault write auth/kubernetes/config` avec CA cert + JWT |
| `403 permission denied` (audience) | Champ `audience` dans le rôle Vault | Supprimer et recréer le rôle sans `audience` |
| `invalid role name` | Rôle/policy manquant dans Vault | Créer policy + rôle + secret manuellement |
| `1/1` au lieu de `2/2` (pas de sidecar) | Certificat TLS du webhook expiré | `kubectl rollout restart deployment/vault-agent-injector -n vault` |
| Vault sealed après reboot | Comportement normal (sécurité) | Unseal avec 3 des 5 clés shamir |
| Pipeline déploie en preprod au lieu de prod | `ENV_NAME` dans bloc `environment` Jenkins | Déplacer dans bloc `script` avec condition `if GIT_BRANCH` |
| Secret Keycloak écrasé à chaque pipeline | Jenkinsfile injectait un placeholder | Retirer l'injection du secret du pipeline |

---

## Améliorations prévues

- [ ] **CRUD complet** — ajouter/modifier/supprimer des produits et utilisateurs via le Gateway
- [ ] **Webhook GitHub → Jenkins** — remplacer le Poll SCM par un vrai webhook
- [ ] **Observabilité** — Prometheus + Grafana pour la supervision des pods
- [ ] **Dockerfiles multi-stage** — réduire la taille des images
- [ ] **Tests automatisés** — stage de tests unitaires dans le pipeline avant déploiement
- [ ] **Auto-unseal Vault** — configurer l'auto-unseal pour éviter l'intervention manuelle après reboot

---

## Auteur

**Ishak GUECHOUD** — DevOps Engineer
[GitHub](https://github.com/ishakguechoud) · [LinkedIn](#)

> Projet portfolio DevOps — stack complète déployée sur homelab (VMware, 2 VMs AlmaLinux 9.6).
> Architecture microservices transposable en environnement d'entreprise :
> Helm, Vault, GitFlow, API Gateway, multi-namespace, CI/CD automatisé.