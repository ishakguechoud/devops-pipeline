from flask import Flask
from config import FLASK_SECRET_KEY
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Enregistrement des Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
