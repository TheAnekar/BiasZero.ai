from flask import *
from Database.connection import *
from Database.CRUD import *

app = Flask(__name__)


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
    
    return redirect('/home')

if __name__ == "__main__":
    app.run(debug=True)