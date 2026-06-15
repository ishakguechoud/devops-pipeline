# 🚀 DevOps Pipeline — CI/CD Complet

Pipeline CI/CD complet simulant un environnement de production avec microservices, authentification, registry Docker et déploiement Kubernetes.

## 🧱 Architecture

```
GitHub (code source)
    ↓ webhook
Jenkins (CI/CD)
    ↓ build
Docker Images
    ↓ push
Nexus Registry
    ↓ deploy
Minikube (Kubernetes)
    +
Keycloak (IAM / Auth)
```

## 🛠️ Stack technique

| Outil | Rôle |
|---|---|
| Flask (Python) | Microservices REST |
| Jenkins | Pipeline CI/CD |
| Nexus | Registry Docker |
| Minikube | Cluster Kubernetes local |
| Keycloak | Authentification IAM (OIDC) |
| Docker | Conteneurisation |

## 📦 Microservices

| Service | Port | Description |
|---|---|---|
| app-users | 5001 | API REST — gestion des utilisateurs |
| app-products | 5002 | API REST — gestion des produits |
| app-frontend | 5000 | Interface web avec authentification Keycloak |

## 🔄 Pipeline Jenkins

Le pipeline est défini dans le `Jenkinsfile` avec 4 étapes :

1. **Clone** — récupération du code depuis GitHub
2. **Build Images** — construction des images Docker
3. **Push to Nexus** — push vers le registry Nexus
4. **Deploy to Minikube** — déploiement sur Kubernetes

## 🚀 Démarrage rapide

### Prérequis

- Docker Desktop
- Minikube
- kubectl
- Jenkins (via Docker)
- Nexus (via Docker)

### Lancer les services

```bash
# Keycloak
cd keycloak && docker compose up -d

# Nexus
cd nexus && docker compose up -d

# Jenkins
cd ~/jenkins-lab/jenkins-lab && docker compose up -d

# Minikube
minikube start

# Déployer les services
kubectl create namespace devops-pipeline
kubectl apply -f k8s/app-users.yml -n devops-pipeline
kubectl apply -f k8s/app-products.yml -n devops-pipeline
```

### Accès aux interfaces

| Interface | URL | Credentials |
|---|---|---|
| Jenkins | http://localhost:8080 | admin |
| Nexus | http://localhost:8081 | admin |
| Keycloak | http://localhost:8086 | admin / adminpassword |
| app-frontend | http://localhost:5000 | izak / zak56 |

## 📈 Endpoints API

```bash
# app-users
GET /health
GET /users
GET /users/{id}

# app-products
GET /health
GET /products
GET /products/{id}
```

## 🗂️ Structure du projet

```
devops-pipeline/
├── Jenkinsfile              # Pipeline CI/CD
├── app-users/               # Microservice utilisateurs
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── app-products/            # Microservice produits
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── app-frontend/            # Interface web
│   ├── app.py
│   └── requirements.txt
├── keycloak/                # Config IAM
│   └── docker-compose.yml
├── nexus/                   # Registry Docker
│   └── docker-compose.yml
└── k8s/                     # Manifests Kubernetes
    ├── app-users.yml
    └── app-products.yml
```

## 🔐 Authentification Keycloak

L'application utilise Keycloak 24 avec le flux **Direct Grant (OIDC)** :

1. L'utilisateur saisit ses credentials sur le formulaire Flask
2. Flask envoie une requête POST vers le Token Endpoint Keycloak
3. Keycloak vérifie et retourne un `access_token` JWT
4. Flask stocke le token en session et affiche les données

### Configuration utilisateur Keycloak

Pour créer un utilisateur fonctionnel :
- Realm : `zak-local`
- Remplir `firstName`, `lastName`, `email`
- `Email verified` → `On`
- Mot de passe → `Temporary: Off`

## ⚠️ Note environnement WSL

En environnement WSL + Docker Desktop, le pull depuis Nexus vers Minikube utilise `minikube image load` en raison des limitations réseau HTTP/HTTPS entre Docker Desktop et Minikube.

En production sur serveur Linux, Kubernetes pullera directement depuis Nexus :
```yaml
image: nexus.company.com:8082/app-users:v1
```

## 📚 Contexte

Projet réalisé dans le cadre d'un portfolio DevOps personnel. Simule un workflow CI/CD complet tel qu'utilisé en environnement professionnel avec Jenkins, Nexus, Kubernetes et Keycloak.
