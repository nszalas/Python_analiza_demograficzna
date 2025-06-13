from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "tajny_klucz"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Użytkownik "na sztywno" (można potem rozszerzyć o bazę danych)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)

# Logika użytkownika
USERS = {'admin': {'password': 'admin'}}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dane i wykresy
DATA_DIR = "dane"
IMG_DIR = "static/wykresy"

def prepare_charts():
    print("Generuję wykresy...")
    df_1 = pd.read_excel(os.path.join(DATA_DIR, "tablica_2.xls"), sheet_name="tabl.2_ogółem")
    df_1 = df_1.iloc[66:80, [1, 2, 4, 5, 11, 12]].astype(float)
    df_1.columns = ["Ludność", "Małżeństwa", "Urodzenia", "Zgony", "Imigracja", "Emigracja"]
    df_1.index = list(range(2010, 2024))

    # Wykres: Urodzenia i zgony
    df_1[['Urodzenia', 'Zgony']].plot()
    plt.title("Urodzenia i zgony")
    plt.savefig(os.path.join(IMG_DIR, "urodzenia_zgony.png"))
    plt.clf()

    # Wykres: Przyrost naturalny
    df_1["Przyrost"] = df_1["Urodzenia"] - df_1["Zgony"]
    df_1["Przyrost"].plot(kind='bar')
    plt.title("Przyrost naturalny")
    plt.savefig(os.path.join(IMG_DIR, "przyrost.png"))
    plt.clf()

    print("Wykresy zapisane do:", os.path.abspath(IMG_DIR))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            prepare_charts()
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Nieprawidłowe dane logowania.")
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        password2 = request.form['password2']

        if password != password2:
            return render_template('register.html', error="Hasła nie są takie same.")

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Użytkownik o takim loginie już istnieje.")

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

def init_db():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        hashed_pw = generate_password_hash("admin")
        new_user = User(username="admin", password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

if __name__ == '__main__':
    os.makedirs(IMG_DIR, exist_ok=True)
    with app.app_context():
        init_db()
    app.run(debug=True)
