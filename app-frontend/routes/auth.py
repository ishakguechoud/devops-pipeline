"""
Routes d'authentification : login et logout.
L'authentification passe par Keycloak via le flux Direct Grant (Resource Owner Password).
"""
from flask import Blueprint, request, redirect, url_for, session, render_template
import requests
from config import KEYCLOAK_CLIENT_ID, KEYCLOAK_TOKEN_URL
from services.keycloak import KEYCLOAK_CLIENT_SECRET

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Page de connexion.
    GET  → affiche le formulaire
    POST → envoie les identifiants à Keycloak, crée la session si OK
    """
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        payload = {
            "grant_type": "password",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "username": username,
            "password": password,
            "scope": "openid",
        }

        try:
            resp = requests.post(KEYCLOAK_TOKEN_URL, data=payload, timeout=5)
            if resp.status_code == 200:
                token_data = resp.json()
                session["username"] = username
                session["access_token"] = token_data.get("access_token")
                return redirect(url_for("dashboard.home"))
            else:
                error = f"Identifiants incorrects — code {resp.status_code}"
        except requests.exceptions.ConnectionError:
            error = "Impossible de contacter Keycloak. Vérifiez votre réseau."
        except Exception as e:
            error = f"Erreur inattendue : {e}"

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    """Déconnexion — vide la session Flask."""
    session.clear()
    return redirect(url_for("auth.login"))
