from flask import Flask, jsonify

app = Flask(__name__)

users = [
    {"id": 1, "name": "Izak", "email": "izak@amana.dz"},
    {"id": 2, "name": "Belakcem", "email": "belkacem@gmail.com"},
    {"id": 3, "name": "Athman", "email": "athman@gmail.com"}
]

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "app-users"})

@app.route('/users')
def get_users():
    return jsonify({"users": users})

@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
