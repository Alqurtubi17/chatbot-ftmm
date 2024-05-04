from flask import Flask, render_template, request, jsonify
from fix import get_response
import psycopg2
from psycopg2 import Error
from datetime import datetime

app = Flask(__name__)

# Konfigurasi koneksi ke PostgreSQL
app.config['POSTGRESQL_DATABASE_USER'] = 'chatbot_ftmm_user'
app.config['POSTGRESQL_DATABASE_PASSWORD'] = 'Ifj4AKodZrrBNeoH7fUizTwGpNtMr51a'
app.config['POSTGRESQL_DATABASE_DB'] = 'chatbot_ftmm'
app.config['POSTGRESQL_DATABASE_HOST'] = 'dpg-cor0emq0si5c7399uel0-a.oregon-postgres.render.com'

# Fungsi untuk membuat koneksi ke PostgreSQL
def create_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            user=app.config['POSTGRESQL_DATABASE_USER'],
            password=app.config['POSTGRESQL_DATABASE_PASSWORD'],
            database=app.config['POSTGRESQL_DATABASE_DB'],
            host=app.config['POSTGRESQL_DATABASE_HOST']
        )
        print("Connection to PostgreSQL successful")
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    return connection

# Fungsi untuk mengeksekusi kueri SQL
def execute_query(connection, query, args=None):
    cursor = connection.cursor()
    try:
        cursor.execute(query, args)
        connection.commit()
        print("Query executed successfully")
    except (Exception, Error) as error:
        print("Error executing query:", error)
    finally:
        cursor.close()

# Route untuk halaman utama
@app.route("/")
def index():
    return render_template("base.html")

# Route untuk prediksi
@app.route("/predict", methods=["POST"])
def predict():
    # Buat koneksi
    connection = create_connection()
    # Inisialisasi cursor setelah koneksi dibuat
    cursor = connection.cursor()
    text = request.get_json().get("message")
    response, label = get_response(text)
    query = 'INSERT INTO history (text, label, date) VALUES (%s, %s, %s)'
    args = (text, label, datetime.now())
    execute_query(connection, query, args)
    cursor.execute("SELECT MAX(id) FROM history")
    message_id = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return jsonify({"answer": response, "message_id": message_id})

# Route untuk umpan balik
@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    message_id = data.get("index")
    feedback = data.get("feedback")
    connection = create_connection()
    query = 'UPDATE history SET feedback=%s WHERE id=%s'
    args = (feedback, message_id)
    execute_query(connection, query, args)
    connection.close()
    return jsonify({"success": True, "message": "Feedback received"})

if __name__ == "__main__":
    app.run(debug=True)
