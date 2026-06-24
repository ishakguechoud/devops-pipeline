from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

DB_HOST = "192.168.74.129"
DB_NAME = "workflow"
DB_USER = "workflow_app"
DB_PASSWORD = "Guizak-56"

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "app-users"
    })

@app.route('/users')
def get_users():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, email
        FROM users
    """)

    rows = cur.fetchall()

    users = []

    for row in rows:
        users.append({
            "id": row[0],
            "username": row[1],
            "email": row[2]
        })

    cur.close()
    conn.close()

    return jsonify({"users": users})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)