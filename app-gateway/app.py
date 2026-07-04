from flask import Flask, request, jsonify
import requests
import os
import jwt
from functools import wraps

app = Flask(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://app-products-preprod-service:5002")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://app-users-preprod-service:5001")

KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://172.28.77.160:8086")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "zak-local")
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

# Cache pour les clés publiques Keycloak
_jwks_client = None


def get_jwks_client():
    """Récupère le client JWKS pour valider les tokens JWT Keycloak."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(KEYCLOAK_JWKS_URL)
    return _jwks_client


# ──────────────────────────────────────────────
# Middleware : Vérification du token JWT
# ──────────────────────────────────────────────
def require_token(f):
    """
    Décorateur qui vérifie le token JWT Bearer dans le header Authorization.
    En entreprise, c'est le Gateway qui valide le token AVANT de forwarder
    aux microservices — les microservices n'ont pas à gérer l'auth eux-mêmes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Missing or invalid Authorization header",
                "detail": "Expected: Bearer <token>"
            }), 401

        token = auth_header.split(" ", 1)[1]

        try:
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="account",
                options={"verify_exp": True},
            )

            # Ajouter les infos utilisateur au contexte de la requête
            request.user = {
                "sub": payload.get("sub"),
                "username": payload.get("preferred_username"),
                "email": payload.get("email"),
                "roles": payload.get("realm_access", {}).get("roles", []),
            }

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": "Invalid token", "detail": str(e)}), 401
        except Exception as e:
            print(f"[GATEWAY] JWT validation error: {e}")
            return jsonify({"error": "Authentication failed", "detail": str(e)}), 401

        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────
# Helper : Proxy vers un microservice
# ──────────────────────────────────────────────
def proxy_request(service_url, path):
    """
    Forwarde la requête vers un microservice backend.
    Transmet les headers et la méthode HTTP d'origine.
    """
    url = f"{service_url}/{path}"
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={
                "Content-Type": request.content_type or "application/json",
                "X-Forwarded-For": request.remote_addr,
                "X-Gateway-User": request.user.get("username", "unknown") if hasattr(request, "user") else "anonymous",
            },
            data=request.get_data(),
            params=request.args,
            timeout=10,
        )
        return jsonify(resp.json()), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Service unavailable",
            "service": service_url,
            "path": path,
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Service timeout",
            "service": service_url,
            "path": path,
        }), 504
    except Exception as e:
        return jsonify({
            "error": "Gateway error",
            "detail": str(e),
        }), 502


# ──────────────────────────────────────────────
# Routes : API Gateway
# ──────────────────────────────────────────────

# --- Health Check (pas de token requis) ---
@app.route("/health")
def gateway_health():
    """Health check du gateway lui-même."""
    return jsonify({"status": "ok", "service": "api-gateway"})


@app.route("/api/health")
def aggregated_health():
    """
    Health check agrégé de tous les microservices.
    C'est une fonctionnalité clé d'un API Gateway :
    vérifier l'état de tous les backends en un seul appel.
    """
    services = {
        "gateway": {"status": "ok"},
        "products": {"status": "unknown"},
        "users": {"status": "unknown"},
    }

    try:
        resp = requests.get(f"{PRODUCTS_SERVICE_URL}/health", timeout=3)
        services["products"] = resp.json()
    except Exception as e:
        services["products"] = {"status": "error", "detail": str(e)}

    try:
        resp = requests.get(f"{USERS_SERVICE_URL}/health", timeout=3)
        services["users"] = resp.json()
    except Exception as e:
        services["users"] = {"status": "error", "detail": str(e)}

    all_ok = all(s.get("status") == "ok" for s in services.values())

    return jsonify({
        "status": "ok" if all_ok else "degraded",
        "services": services,
    }), 200 if all_ok else 207


# --- Routes Produits (protégées par JWT) ---
@app.route("/api/products", methods=["GET"])
@require_token
def get_products():
    """Liste tous les produits via app-products."""
    return proxy_request(PRODUCTS_SERVICE_URL, "products")


@app.route("/api/products/<int:product_id>", methods=["GET"])
@require_token
def get_product(product_id):
    """Détail d'un produit via app-products."""
    return proxy_request(PRODUCTS_SERVICE_URL, f"products/{product_id}")


# --- Routes Utilisateurs (protégées par JWT) ---
@app.route("/api/users", methods=["GET"])
@require_token
def get_users():
    """Liste tous les utilisateurs via app-users."""
    return proxy_request(USERS_SERVICE_URL, "users")


# --- Info Gateway (protégée) ---
@app.route("/api/whoami", methods=["GET"])
@require_token
def whoami():
    """
    Retourne les infos de l'utilisateur authentifié.
    Utile pour vérifier que le token est valide et voir
    quelles informations Keycloak transmet.
    """
    return jsonify({
        "user": request.user,
        "gateway": "api-gateway",
        "message": f"Hello {request.user.get('username', 'unknown')}!",
    })


# ──────────────────────────────────────────────
# Error handlers globaux
# ──────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Route not found",
        "detail": "Check the API documentation for available endpoints",
        "available_routes": [
            "GET /health",
            "GET /api/health",
            "GET /api/products",
            "GET /api/products/<id>",
            "GET /api/users",
            "GET /api/whoami",
        ],
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal gateway error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)