"""
Client API Gateway.
Toutes les communications avec les microservices passent par ici.
Le Gateway valide le token JWT et forwarde aux bons services.
"""
import requests
from flask import session
from config import GATEWAY_URL


def _auth_headers():
    """Construit les headers avec le token JWT pour appeler le Gateway."""
    token = session.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def get_products():
    """Récupère la liste des produits via le Gateway."""
    try:
        resp = requests.get(
            f"{GATEWAY_URL}/api/products",
            headers=_auth_headers(),
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("products", [])
        print(f"[WARN] Gateway /api/products retourné {resp.status_code}")
        return []
    except Exception as e:
        print(f"[ERROR] Impossible de contacter le Gateway (products): {e}")
        return []


def get_users():
    """Récupère la liste des utilisateurs via le Gateway."""
    try:
        resp = requests.get(
            f"{GATEWAY_URL}/api/users",
            headers=_auth_headers(),
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("users", [])
        print(f"[WARN] Gateway /api/users retourné {resp.status_code}")
        return []
    except Exception as e:
        print(f"[ERROR] Impossible de contacter le Gateway (users): {e}")
        return []


def add_product(name, price):
    """Ajoute un nouveau produit via le Gateway."""
    try:
        resp = requests.post(
            f"{GATEWAY_URL}/api/products",
            headers={**_auth_headers(), "Content-Type": "application/json"},
            json={"name": name, "price": price},
            timeout=5,
        )
        return resp.status_code == 201, resp.json()
    except Exception as e:
        print(f"[ERROR] Impossible d'ajouter un produit: {e}")
        return False, {"error": str(e)}


def get_health():
    """Récupère le health check agrégé de tous les services."""
    try:
        resp = requests.get(f"{GATEWAY_URL}/api/health", timeout=5)
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Health check échoué: {e}")
        return {"status": "error", "detail": str(e)}
