from flask import Flask, request, redirect, url_for, session
import requests
import os
import re

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "une_cle_secrete_super_secure")

KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://172.28.77.160:8086")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "zak-local")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "app-frontend")

def get_keycloak_secret():
    try:
        with open("/vault/secrets/keycloak", "r") as f:
            content = f.read()
            match = re.search(r"keycloak-client-secret:\s*([^\s]+)", content)
            if match:
                return match.group(1)
            match = re.search(r'KEYCLOAK_CLIENT_SECRET="([^"]+)"', content)
            if match:
                return match.group(1)
    except Exception:
        pass
    return os.getenv("KEYCLOAK_CLIENT_SECRET")

KEYCLOAK_CLIENT_SECRET = get_keycloak_secret()
KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://192.168.74.128:30002")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://192.168.74.128:30001")

CSS = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f0f2f5;
    min-height: 100vh;
    color: #1a1a2e;
  }

  /* ── LOGIN ── */
  .login-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #0f3460 0%, #16213e 50%, #0f3460 100%);
  }
  .login-card {
    background: #fff;
    border-radius: 16px;
    padding: 48px 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  }
  .login-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 32px;
  }
  .login-logo-icon {
    width: 40px;
    height: 40px;
    background: #0f3460;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 20px;
    font-weight: 700;
  }
  .login-logo-text {
    font-size: 18px;
    font-weight: 700;
    color: #0f3460;
    line-height: 1.2;
  }
  .login-logo-sub {
    font-size: 11px;
    font-weight: 400;
    color: #6b7280;
    display: block;
  }
  .login-title {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 6px;
  }
  .login-subtitle {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 28px;
  }
  .form-group {
    margin-bottom: 18px;
  }
  .form-group label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
  }
  .form-group input {
    width: 100%;
    padding: 11px 14px;
    border: 1.5px solid #e5e7eb;
    border-radius: 8px;
    font-size: 14px;
    color: #111827;
    background: #f9fafb;
    transition: border-color 0.2s, background 0.2s;
    outline: none;
  }
  .form-group input:focus {
    border-color: #0f3460;
    background: #fff;
  }
  .btn-primary {
    width: 100%;
    padding: 12px;
    background: #0f3460;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    margin-top: 8px;
  }
  .btn-primary:hover { background: #16213e; }
  .error-box {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 20px;
    color: #dc2626;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── DASHBOARD ── */
  .topbar {
    background: #0f3460;
    color: white;
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .topbar-brand {
    font-size: 16px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .topbar-brand span {
    background: white;
    color: #0f3460;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
  }
  .topbar-user {
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 14px;
  }
  .avatar {
    width: 34px;
    height: 34px;
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    text-transform: uppercase;
  }
  .btn-logout {
    background: rgba(255,255,255,0.15);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 7px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.2s;
  }
  .btn-logout:hover { background: rgba(255,255,255,0.25); }

  .main-content {
    max-width: 1100px;
    margin: 0 auto;
    padding: 32px 24px;
  }
  .page-header {
    margin-bottom: 28px;
  }
  .page-title {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 4px;
  }
  .page-subtitle {
    font-size: 14px;
    color: #6b7280;
  }

  .badge-connected {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #d1fae5;
    color: #065f46;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 10px;
    vertical-align: middle;
  }
  .dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; }

  .section-title {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title .count {
    background: #e5e7eb;
    color: #374151;
    border-radius: 20px;
    padding: 1px 8px;
    font-size: 12px;
    font-weight: 600;
  }

  /* ── PRODUITS ── */
  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 36px;
  }
  .product-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e5e7eb;
    transition: box-shadow 0.2s, transform 0.2s;
  }
  .product-card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    transform: translateY(-2px);
  }
  .product-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
  }
  .product-icon.auto   { background: #dbeafe; }
  .product-icon.habita { background: #d1fae5; }
  .product-icon.vie    { background: #ede9fe; }
  .product-name {
    font-size: 15px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 6px;
  }
  .product-id {
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 14px;
  }
  .product-price {
    font-size: 22px;
    font-weight: 800;
    color: #0f3460;
  }
  .product-price span {
    font-size: 13px;
    font-weight: 500;
    color: #9ca3af;
  }

  /* ── USERS TABLE ── */
  .table-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
  }
  .table-card table {
    width: 100%;
    border-collapse: collapse;
  }
  .table-card thead {
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
  }
  .table-card th {
    padding: 12px 20px;
    text-align: left;
    font-size: 12px;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .table-card td {
    padding: 14px 20px;
    font-size: 14px;
    color: #111827;
    border-bottom: 1px solid #f3f4f6;
  }
  .table-card tr:last-child td { border-bottom: none; }
  .table-card tr:hover td { background: #f9fafb; }
  .user-initial {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: #dbeafe;
    color: #1e40af;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    margin-right: 10px;
  }
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #9ca3af;
    font-size: 14px;
  }

  /* ── STATS BAR ── */
  .stats-bar {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 14px;
    margin-bottom: 32px;
  }
  .stat-card {
    background: white;
    border-radius: 10px;
    padding: 16px 18px;
    border: 1px solid #e5e7eb;
  }
  .stat-label {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
  }
  .stat-value {
    font-size: 24px;
    font-weight: 800;
    color: #0f3460;
  }
</style>
"""

ICONS = {"auto": "🚗", "habita": "🏠", "vie": "❤️"}

def product_icon_class(name):
    n = name.lower()
    if "auto" in n: return "auto", ICONS["auto"]
    if "habitation" in n: return "habita", ICONS["habita"]
    return "vie", ICONS["vie"]


@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    try:
        products_data = requests.get(f"{PRODUCTS_SERVICE_URL}/products", timeout=5).json().get("products", [])
    except Exception:
        products_data = []

    try:
        users_data = requests.get(f"{USERS_SERVICE_URL}/users", timeout=5).json().get("users", [])
    except Exception:
        users_data = []

    # Build product cards
    product_cards_html = ""
    for p in products_data:
        css_class, icon = product_icon_class(p.get("name", ""))
        product_cards_html += f"""
        <div class="product-card">
          <div class="product-icon {css_class}">{icon}</div>
          <div class="product-name">{p.get('name', 'N/A')}</div>
          <div class="product-id">Réf. #{p.get('id', '?')}</div>
          <div class="product-price">{p.get('price', 0):,} <span>DZD / an</span></div>
        </div>
        """
    if not product_cards_html:
        product_cards_html = '<div class="empty-state">Aucun produit disponible</div>'

    # Build users rows
    user_rows_html = ""
    for u in users_data:
        initial = u.get("username", "?")[0].upper()
        user_rows_html += f"""
        <tr>
          <td>{u.get('id', '')}</td>
          <td><span class="user-initial">{initial}</span>{u.get('username', '')}</td>
          <td>{u.get('email', '')}</td>
        </tr>
        """
    if not user_rows_html:
        user_rows_html = '<tr><td colspan="3"><div class="empty-state">Aucun utilisateur trouvé</div></td></tr>'

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DevOps Platform</title>
  {CSS}
</head>
<body>

<nav class="topbar">
  <div class="topbar-brand">
    ⚙️ DevOps Platform <span>K8S</span>
  </div>
  <div class="topbar-user">
    <div class="avatar">{username[0].upper()}</div>
    <span>{username}</span>
    <a href="/logout" class="btn-logout">Déconnexion</a>
  </div>
</nav>

<div class="main-content">

  <div class="page-header">
    <h1 class="page-title">
      Tableau de bord
      <span class="badge-connected"><span class="dot"></span> Connecté via Keycloak</span>
    </h1>
    <p class="page-subtitle">Bienvenue, <strong>{username}</strong> — plateforme microservices déployée sur Kubernetes</p>
  </div>

  <div class="stats-bar">
    <div class="stat-card">
      <div class="stat-label">Produits</div>
      <div class="stat-value">{len(products_data)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Utilisateurs</div>
      <div class="stat-value">{len(users_data)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Namespace</div>
      <div class="stat-value" style="font-size:15px; padding-top:4px;">devops-pipeline</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Auth</div>
      <div class="stat-value" style="font-size:15px; padding-top:4px;">Keycloak</div>
    </div>
  </div>

  <div class="section-title">
    🛡️ Catalogue produits <span class="count">{len(products_data)}</span>
  </div>
  <div class="products-grid">
    {product_cards_html}
  </div>

  <div class="section-title">
    👤 Utilisateurs PostgreSQL <span class="count">{len(users_data)}</span>
  </div>
  <div class="table-card">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Utilisateur</th>
          <th>Email</th>
        </tr>
      </thead>
      <tbody>
        {user_rows_html}
      </tbody>
    </table>
  </div>

</div>
</body>
</html>"""


@app.route("/login", methods=["GET", "POST"])
def login():
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
                session["username"] = username
                session["access_token"] = resp.json().get("access_token")
                return redirect(url_for("home"))
            else:
                error = f"Identifiants incorrects — code {resp.status_code}"
        except requests.exceptions.ConnectionError:
            error = "Impossible de contacter Keycloak. Vérifiez votre réseau."
        except Exception as e:
            error = f"Erreur inattendue : {e}"

    error_html = ""
    if error:
        error_html = f'<div class="error-box">⚠️ {error}</div>'

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connexion — DevOps Platform</title>
  {CSS}
</head>
<body>
<div class="login-wrapper">
  <div class="login-card">
    <div class="login-logo">
      <div class="login-logo-icon">⚙</div>
      <div class="login-logo-text">
        DevOps Platform
        <span class="login-logo-sub">Kubernetes · Keycloak · Vault</span>
      </div>
    </div>

    <h2 class="login-title">Connexion</h2>
    <p class="login-subtitle">Authentification via Keycloak SSO</p>

    {error_html}

    <form method="post">
      <div class="form-group">
        <label for="username">Nom d'utilisateur</label>
        <input type="text" id="username" name="username" placeholder="ex: ishak" required>
      </div>
      <div class="form-group">
        <label for="password">Mot de passe</label>
        <input type="password" id="password" name="password" placeholder="••••••••" required>
      </div>
      <button type="submit" class="btn-primary">Se connecter</button>
    </form>
  </div>
</div>
</body>
</html>"""


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    # On garde le debug pour tes tests, mais on désactive le reloader automatique qui binde sur 127.0.0.1
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)