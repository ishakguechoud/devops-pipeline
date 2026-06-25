from flask import Flask, jsonify
import psycopg2
import os
import re

app = Flask(__name__)


def get_db_config():
    """
    Charge les credentials DB depuis :
    1. Le fichier Vault injecté (/vault/secrets/db) — en prod
    2. Les variables d'environnement                 — en preprod
    """
    config = {
        "host": os.getenv("DB_HOST", "192.168.74.129"),
        "database": os.getenv("DB_NAME", "workflow"),
        "user": os.getenv("DB_USER", "workflow_app"),
        "password": os.getenv("DB_PASSWORD", ""),
    }

    vault_file = "/vault/secrets/db"
    try:
        with open(vault_file, "r") as f:
            content = f.read()
            print("[INFO] Fichier Vault trouvé, chargement des credentials DB...")

            patterns = {
                "host":     r"DB_HOST=(.+)",
                "database": r"DB_NAME=(.+)",
                "user":     r"DB_USER=(.+)",
                "password": r"DB_PASSWORD=(.+)",
            }
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    config[key] = match.group(1).strip()

            print("[INFO] Credentials DB chargés depuis Vault.")
    except FileNotFoundError:
        print("[INFO] Vault non disponible, utilisation des variables d'environnement.")
    except Exception as e:
        print(f"[WARN] Erreur lecture Vault : {e} — fallback sur env vars.")

    return config


DB_CONFIG = get_db_config()


def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "app-users"})


@app.route("/users")
def get_users():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, email FROM users")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        users = [{"id": r[0], "username": r[1], "email": r[2]} for r in rows]
        return jsonify({"users": users})

    except Exception as e:
        print(f"[ERROR] Connexion DB échouée : {e}")
        return jsonify({"error": "Database connection failed", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)