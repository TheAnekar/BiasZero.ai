from flask import *
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('Login.html')

@app.route('/home')
def home():
    return render_template('profile_create.html')

@app.route("/login", methods=["POST","GET"])
def login():
    email = request.form["email"]
    password = request.form["password"]
    conn = get_db_connection()
    conn.execute("INSERT into users(email,password) VALUES (?,?)",(email,password))
    conn.commit()
    conn.close()
    return redirect('/home')

if __name__ == "__main__":
    app.run(debug=True)