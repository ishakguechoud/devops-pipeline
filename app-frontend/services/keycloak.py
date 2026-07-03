"""
Service de récupération du secret Keycloak.
Le secret peut venir de :
  1. Le fichier Vault injecté (/vault/secrets/keycloak) — en prod/preprod avec Vault Agent
  2. Une variable d'environnement KEYCLOAK_CLIENT_SECRET — en fallback
"""
import os
import re


def get_keycloak_secret():
    """Lit le secret Keycloak depuis Vault ou les variables d'environnement."""

    # 1. Essayer le fichier Vault (injecté par Vault Agent Injector)
    try:
        with open("/vault/secrets/keycloak", "r") as f:
            content = f.read()

            # Format: keycloak-client-secret: <valeur>
            match = re.search(r"keycloak-client-secret:\s*([^\s]+)", content)
            if match:
                print("[INFO] Secret Keycloak chargé depuis Vault.")
                return match.group(1)

            # Format alternatif: export KEYCLOAK_CLIENT_SECRET="<valeur>"
            match = re.search(r'KEYCLOAK_CLIENT_SECRET="([^"]+)"', content)
            if match:
                print("[INFO] Secret Keycloak chargé depuis Vault (format export).")
                return match.group(1)

    except FileNotFoundError:
        print("[INFO] Vault non disponible, fallback sur variable d'environnement.")
    except Exception as e:
        print(f"[WARN] Erreur lecture Vault : {e}")

    # 2. Fallback sur variable d'environnement
    secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
    if secret:
        print("[INFO] Secret Keycloak chargé depuis variable d'environnement.")
    else:
        print("[ERREUR] Aucun secret Keycloak trouvé !")

    return secret


# Chargé une seule fois au démarrage de l'application
KEYCLOAK_CLIENT_SECRET = get_keycloak_secret()
