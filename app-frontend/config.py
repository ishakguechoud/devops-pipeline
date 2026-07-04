"""
Configuration centralisée de l'application.
Toutes les variables d'environnement et constantes sont ici.
"""
import os

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "une_cle_secrete_super_secure")

# Keycloak
KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://172.28.77.160:8086")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "zak-local")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "app-frontend")
KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

# API Gateway — un seul point d'entrée pour tous les microservices
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://app-gateway-preprod-service:5003")
