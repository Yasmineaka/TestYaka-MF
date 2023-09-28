import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète'

# ma base de données SQLite3
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# ma création de la table Utilisateur
cursor.execute('''
    CREATE TABLE IF NOT EXISTS utilisateur (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        email TEXT UNIQUE,
        contact TEXT UNIQUE,
        mot_de_passe TEXT,
        solde REAL DEFAULT 3000
    )
''')
conn.commit()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS historique_operation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        utilisateur_id INTEGER,
        description TEXT,
        contact_destinataire TEXT,
        montant REAL,
        date DATETIME DEFAULT CURRENT_TIMES
    )
''')
conn.commit()
# Création de la table HistoriqueOperation
cursor.execute('''
    CREATE TABLE IF NOT EXISTS historique_operation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        utilisateur_id INTEGER,
        description TEXT,
        montant REAL,
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur (id)
    )
''')
conn.commit()

login_manager = LoginManager(app)
login_manager.login_view = 'connexion'

class Utilisateur(UserMixin):
    def __init__(self, id, nom, email, contact, mot_de_passe, solde=0.0):
        self.id = id
        self.nom = nom
        self.email = email
        self.contact = contact
        self.mot_de_passe = mot_de_passe
        self.solde = solde

    def get_id(self):
        return str(self.id)
class HistoriqueOperation:
    def __init__(self, utilisateur_id, description, montant):
        self.utilisateur_id = utilisateur_id
        self.description = description
        self.montant = montant

    def save(self):
        cursor.execute('INSERT INTO historique_operation (utilisateur_id, description, montant) VALUES (?, ?, ?)', (self.utilisateur_id, self.description, self.montant))
        conn.commit()
@login_manager.user_loader
def load_user(user_id):
    cursor.execute('SELECT * FROM utilisateur WHERE id = ?', (user_id,))
    utilisateur_data = cursor.fetchone()
    if utilisateur_data:
        return Utilisateur(*utilisateur_data)
    return None
# accueil generale
@app.route('/')
def accueil():
    return render_template("accueil.html")
# accueil après inscription
@app.route('/accueil_inscrip')
@login_required
def accueil_inscrip():
    return render_template("accueil_inscrip.html")

@app.route('/inscription_info')
def inscription_info():
    return render_template("inscription_info.html")

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email = request.form.get('email')
        contact = request.form.get('contact')
        mot_de_passe = request.form.get('mot_de_passe')

        cursor.execute('SELECT * FROM utilisateur WHERE email = ? OR contact = ?', (email, contact))
        existe_utilisateur = cursor.fetchone()

        if existe_utilisateur:
            flash('Cet e-mail ou contact est déjà enregistré.', 'danger')
            return redirect('/inscription')

        mot_de_passe_hash = generate_password_hash(mot_de_passe, method='sha256')

        cursor.execute('INSERT INTO utilisateur (nom, email, contact, mot_de_passe) VALUES (?, ?, ?, ?)', (nom, email, contact, mot_de_passe_hash))
        conn.commit()

        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect('/connexion')

    return render_template('inscription.html')

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')

        cursor.execute('SELECT * FROM utilisateur WHERE email = ?', (email,))
        utilisateur_data = cursor.fetchone()

        if utilisateur_data and check_password_hash(utilisateur_data[4], mot_de_passe):
            utilisateur = Utilisateur(*utilisateur_data)
            login_user(utilisateur)
            flash('Connexion réussie !', 'success')
            return redirect('/dashboard')
        else:
            flash('Identifiants incorrects. Veuillez réessayer.', 'danger')

    return render_template('connexion.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor.execute('SELECT * FROM historique_operation WHERE utilisateur_id = ?', (current_user.id,))
    historique_operations = cursor.fetchall()
    return render_template('dashboard.html', utilisateur=current_user, historique_operations=historique_operations)

@app.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    flash('Déconnexion réussie.', 'success')
    return redirect('/')

@app.route('/solde')
@login_required
def solde():
    return render_template('solde.html', solde=current_user.solde)

@app.route('/transfert', methods=['GET', 'POST'])
@login_required
def transfert():
    if request.method == 'POST':
        montant = float(request.form.get('montant'))
        contact_destinataire = request.form.get('contact_destinataire') 

        if montant <= 0:
            flash('Le montant doit être positif.', 'danger')
            return redirect('/transfert')

        # Rechercher l'utilisateur qui  correspond au contact de celui qui recois
        cursor.execute('SELECT * FROM utilisateur WHERE contact = ?', (contact_destinataire,))
        destinataire_data = cursor.fetchone()

        if not destinataire_data:
            flash("Destinataire introuvable ou non inscrit sur la plateforme.", 'danger')
            return redirect('/transfert')

        if current_user.solde < montant:
            flash('Solde insuffisant.', 'danger')
            return redirect('/transfert')

        # Effectuez la transaction
        cursor.execute('UPDATE utilisateur SET solde = solde + ? WHERE id = ?', (montant, destinataire_data[0]))
        cursor.execute('UPDATE utilisateur SET solde = solde - ? WHERE id = ?', (montant, current_user.id))
        conn.commit()

        # Enregistrer le transfert dans l'historique avec le montant
        description = f"Transfert de F{montant} vers {destinataire_data[1]}"
        nouvelle_operation = HistoriqueOperation(utilisateur_id=current_user.id, description=description, montant=montant)
        nouvelle_operation.save()

        # Enregistrer la réception dans l'historique du destinataire
        description_destinataire = f"Transfert de F{montant} par {current_user.nom}"
        nouvelle_operation_destinataire = HistoriqueOperation(utilisateur_id=destinataire_data[0], description=description_destinataire, montant=montant)
        nouvelle_operation_destinataire.save()

        flash('Transfert réussi !', 'success')
        return redirect('/dashboard') 

    return render_template('transfert.html')

@app.route('/recharge', methods=['GET', 'POST'])
@login_required
def recharge():
    if request.method == 'POST':
        montant = float(request.form.get('montant'))
        contact = request.form.get('contact') 
        
        if montant <= 0:
            flash('Le montant doit être positif.', 'danger')
        else:
            # pour mettre à jour le solde de l'utilisateur
            current_user.solde += montant
            cursor.execute('UPDATE utilisateur SET solde = ? WHERE id = ?', (current_user.solde, current_user.id))
            conn.commit()

            # pour enregistrez la recharge dans l'historique avec le contact
            description = f"Rechargement de F{montant} via le contact : {contact}"
            date_heure = datetime.datetime.now()
            cursor.execute('INSERT INTO historique_operation (utilisateur_id, description, montant, date, contact_destinataire) VALUES (?, ?, ?, ?, ?)', 
                           (current_user.id, description, montant, date_heure, contact))
            conn.commit()

            flash('Rechargement réussi !', 'success')

    return redirect('/dashboard')




# -----------------------------------Administrateur----------------------------------
# @app.route('/admin', methods=['GET', 'POST'])
# @login_required
# def admin():
#     return render_template('admin.html')



if __name__ == '__main__':
    app.run(debug=True)
