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
    os.makedirs(IMG_DIR, exist_ok=True)

    # Wczytaj dane z tablicy 2
    df_1 = pd.read_excel(os.path.join(DATA_DIR, "tablica_2.xls"), sheet_name="tabl.2_ogółem")
    df_1 = df_1.iloc[66:80, [1, 2, 4, 5, 11, 12]].astype(float)
    columns_df1 = ["Ludność", "Małżeństwa", "Urodzenia", "Zgony", "Imigracja", "Emigracja"]
    df_1.columns = columns_df1
    df_1.index = list(range(2010, 2024))

    # Przyrost naturalny
    df_pop_growth = pd.DataFrame({
        "Urodzenia": df_1["Urodzenia"],
        "Zgony": df_1["Zgony"],
        "Przyrost": df_1["Urodzenia"] - df_1["Zgony"]
    })

    # Migracje
    df_migration = pd.DataFrame({
        "Imigracja": df_1["Imigracja"],
        "Emigracja": df_1["Emigracja"],
        "Różnica": df_1["Imigracja"] - df_1["Emigracja"]
    })

    # Wczytaj dane z tablicy 7
    df_2 = pd.read_excel(os.path.join(DATA_DIR, "tablica_7.xls"), sheet_name="tabl.7_ogółem")
    df_2 = df_2.iloc[46:60, [1, 2, 3, 4, 5, 6, 10, 11]].astype(float).round(1)
    columns_df2 = [
        "Wiek 15-19", "Wiek 20-24", "Wiek 25-29", "Wiek 30-34", "Wiek 35-39", "Wiek 40-44",
        "Przeciętny wiek rodzących kobiet", "Przeciętny wiek kobiet rodzących pierwsze dziecko"
    ]
    df_2.columns = columns_df2
    df_2.index = list(range(2010, 2024))

    # Wykres: Urodzenia i zgony
    fig, ax = plt.subplots(figsize=(10, 6))
    df_1[['Urodzenia', 'Zgony']].plot(kind='line', ax=ax)
    ax.set_title("Urodzenia i Zgony (tys.)")
    ax.set_xlabel("Rok")
    ax.set_ylabel("Liczba")
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "urodzenia_zgony.png"))
    plt.close(fig)

    # Przyrost naturalny
    df_1["Przyrost"] = df_1["Urodzenia"] - df_1["Zgony"]
    fig, ax = plt.subplots(figsize=(10, 6))
    df_1["Przyrost"].plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title("Przyrost naturalny (tys.)")
    ax.set_xlabel("Rok")
    ax.set_ylabel("Przyrost")
    ax.grid(axis='y')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "przyrost_naturalny.png"))
    plt.close(fig)

    # Urodzenia wg wieku
    df_birth_age = df_2.iloc[:, 0:6]
    fig, ax = plt.subplots(figsize=(10, 6))
    df_birth_age.plot(kind='line', ax=ax)
    ax.set_title("Urodzenia na 1000 kobiet w grupach wiekowych")
    ax.set_xlabel("Rok")
    ax.set_ylabel("Liczba urodzeń")
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "urodzenia_wg_wieku.png"))
    plt.close(fig)

    # Średni wiek rodzących
    df_average_age = df_2.iloc[:, 6:8]
    fig, ax = plt.subplots(figsize=(10, 6))
    df_average_age.plot(kind='line', ax=ax)
    ax.set_title("Przeciętny wiek kobiet rodzących dziecko")
    ax.set_xlabel("Rok")
    ax.set_ylabel("Wiek")
    ax.legend(["Ogółem", "Pierwsze dziecko"], loc='upper left', bbox_to_anchor=(1, 1))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "sredni_wiek_kobiet.png"))
    plt.close(fig)

    # Małżeństwa i urodzenia
    fig, ax = plt.subplots(figsize=(10, 6))
    df_1[['Małżeństwa', 'Urodzenia']].plot(kind='line', ax=ax)
    ax.set_title("Małżeństwa i Urodzenia (tys.)")
    ax.set_xlabel("Rok")
    ax.set_ylabel("Liczba")
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "malzenstwa_urodzenia.png"))
    plt.close(fig)



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
