from flask import Flask, request, redirect, url_for, session, render_template_string
import requests

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_super_secure'

# Configuration Keycloak
KEYCLOAK_BASE_URL = 'http://localhost:8086'
KEYCLOAK_REALM = 'zak-local'
KEYCLOAK_CLIENT_ID = 'app-frontend'
KEYCLOAK_CLIENT_SECRET = '5jrP3rYCpuv3UWJWEjLQ11RvP6Din5y3'  # <--- METS TON CODE SECRET ICI !

# URL de Keycloak pour demander un Jeton (Token Endpoint)
KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

# URL de ton microservice existant pour les produits
PRODUCTS_SERVICE_URL = "http://localhost:5002"

@app.route('/')
def home():
    if 'username' in session:
        # L'utilisateur est connecté ! On récupère les produits
        try:
            response = requests.get(f"{PRODUCTS_SERVICE_URL}/products")
            products_data = response.json().get('products', [])
        except requests.exceptions.ConnectionError:
            products_data = []

        return f"""
            <h1>Bienvenue sur ton interface, {session['username']} !</h1>
            <p><strong>Statut :</strong> Connecté via Keycloak (Direct Grant)</p>
            <p><strong>Produits disponibles :</strong> {products_data}</p>
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
        
        # On prépare les données à envoyer en arrière-plan à Keycloak
        payload = {
            'grant_type': 'password',
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'username': username,
            'password': password,
            'scope': 'openid'
        }
        
        try:
            # Requete POST vers Keycloak
            response = requests.post(KEYCLOAK_TOKEN_URL, data=payload)
            
            if response.status_code == 200:
                # Si Keycloak répond 200, le mot de passe est BON !
                token_data = response.json()
                session['username'] = username
                session['access_token'] = token_data.get('access_token') # Ton badge d'accès
                return redirect(url_for('home'))
            else:
                error = "Identifiants incorrects (refusés par Keycloak)."
        except requests.exceptions.ConnectionError:
            error = "Impossible de contacter le serveur d'authentification Keycloak."

    # Ton propre formulaire HTML personnalisé
    return f'''
        <div style="max-width: 300px; margin: 50px auto; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
            <h2>Connexion Assurance</h2>
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
