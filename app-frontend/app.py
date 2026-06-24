from flask import Flask, request, redirect, url_for, session
import requests
import os
import re

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_super_secure'

# Configuration Keycloak
KEYCLOAK_BASE_URL = 'http://172.28.77.160:8086'  # pas de slash à la fin
KEYCLOAK_REALM = 'zak-local'
KEYCLOAK_CLIENT_ID = 'app-frontend'

# Fonction pour récupérer le secret depuis Vault
def get_keycloak_secret():
    # Essayer de lire depuis le fichier Vault
    try:
        with open('/vault/secrets/keycloak', 'r') as f:
            content = f.read()
            print(f"[DEBUG] Contenu du fichier Vault: {content}")
            
            # Chercher le pattern: keycloak-client-secret: valeur
            match = re.search(r'keycloak-client-secret:\s*([^\s]+)', content)
            if match:
                secret = match.group(1)
                print(f"[DEBUG] Secret trouvé dans le fichier Vault: {secret[:10]}...")
                return secret
            
            # Si le fichier contient export KEYCLOAK_CLIENT_SECRET="valeur"
            match = re.search(r'KEYCLOAK_CLIENT_SECRET="([^"]+)"', content)
            if match:
                secret = match.group(1)
                print(f"[DEBUG] Secret trouvé dans export: {secret[:10]}...")
                return secret
                
    except FileNotFoundError:
        print("[DEBUG] Fichier Vault non trouvé, utilisation de la variable d'environnement")
    except Exception as e:
        print(f"[DEBUG] Erreur lors de la lecture du fichier Vault: {e}")
    
    # Fallback sur variable d'environnement
    secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
    if secret:
        print(f"[DEBUG] Secret trouvé dans les variables d'environnement: {secret[:10]}...")
    else:
        print("[DEBUG] Aucun secret trouvé !")
    
    return secret

# Récupérer le secret
KEYCLOAK_CLIENT_SECRET = get_keycloak_secret()

# Vérifier que le secret est bien chargé
if not KEYCLOAK_CLIENT_SECRET:
    print("[ERREUR] KEYCLOAK_CLIENT_SECRET n'est pas défini !")
else:
    print(f"[INFO] KEYCLOAK_CLIENT_SECRET chargé avec succès (longueur: {len(KEYCLOAK_CLIENT_SECRET)})")

# URL Token Endpoint
KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

# URL app-products via NodePort exposé sur la VM
PRODUCTS_SERVICE_URL = "http://192.168.74.128:30002"

USERS_SERVICE_URL = "http://192.168.74.128:30001"


@app.route('/')
def home():

    if 'username' in session:

        try:
            products_response = requests.get(
                f"{PRODUCTS_SERVICE_URL}/products"
            )

            products_data = products_response.json().get(
                'products',
                []
            )

        except Exception:
            products_data = []

        try:
            users_response = requests.get(
                f"{USERS_SERVICE_URL}/users"
            )

            users_data = users_response.json().get(
                'users',
                []
            )

        except Exception:
            users_data = []

        users_html = ""

        for user in users_data:
            users_html += f"""
            <li>
                {user['username']} - {user['email']}
            </li>
            """

        return f"""
            <h1>Bienvenue sur ton interface, {session['username']} !</h1>

            <p>
                <strong>Statut :</strong>
                Connecté via Keycloak (Direct Grant)
            </p>

            <p>
                <strong>Produits disponibles :</strong>
                {products_data}
            </p>

            <h2>Utilisateurs PostgreSQL</h2>

            <ul>
                {users_html}
            </ul>

            <br>

            <a href='/logout'>Se déconnecter</a>
        """

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        payload = {
            'grant_type': 'password',
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'username': username,
            'password': password,
            'scope': 'openid'
        }

        try:
            print(f"[DEBUG] Tentative de connexion pour: {username}")
            print(f"[DEBUG] KEYCLOAK_TOKEN_URL: {KEYCLOAK_TOKEN_URL}")
            print(f"[DEBUG] client_id: {KEYCLOAK_CLIENT_ID}")
            print(f"[DEBUG] client_secret: {KEYCLOAK_CLIENT_SECRET[:10]}...")
            
            response = requests.post(KEYCLOAK_TOKEN_URL, data=payload)
            
            print(f"[DEBUG] Status code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text[:200]}")
            
            if response.status_code == 200:
                token_data = response.json()
                session['username'] = username
                session['access_token'] = token_data.get('access_token')
                return redirect(url_for('home'))
            else:
                error = f"Identifiants incorrects (refusés par Keycloak). Status: {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            error = f"Impossible de contacter le serveur d'authentification Keycloak: {e}"
        except Exception as e:
            error = f"Erreur inattendue: {e}"

    return f'''
        <div style="max-width: 300px; margin: 50px auto; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
            <h2>Connexion Mon Application</h2>
            {f'<p style="color: red;">{error}</p>' if error else ''}
            <form method="post">
                <label>Utilisateur :</label><br>
                <input type="text" name="username" style="width: 100%; margin-bottom: 10px;"><br>
                <label>Mot de passe :</label><br>
                <input type="password" name="password" style="width: 100%; margin-bottom: 20px;"><br>
                <input type="submit" value="Se connecter" style="width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">
            </form>
        </div>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)