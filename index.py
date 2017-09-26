# coding: utf8

import re
from flask import Flask, render_template
from flask import g
from flask import request
from flask import redirect
from flask import session
from flask import Response
from database import Database
import sys
import hashlib
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import uuid
from functools import wraps

reload(sys)
sys.setdefaultencoding('utf-8')
app = Flask(__name__, static_url_path="", static_folder="static")
app.config.from_pyfile('default_settings.py')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        g._database = Database()
    return g._database

def authentication_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated(session):
            return send_unauthorized()
        return f(*args, **kwargs)
    return decorated
    
def authentication_required_without_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated(session):
            return send_unauthorized_without_login()
        return f(*args, **kwargs)
    return decorated

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.disconnect()


@app.route('/')
def page_accueil():
    source_address = "aerts.julien.101@gmail.com"
    destination_address = "ja.inf3005@gmail.com"
    body = "Please note that I'm writing a script to send emails."
    subject = "I send mails!"

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = source_address
    msg['To'] = destination_address

    msg.attach(MIMEText(body, 'plain'))


    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(source_address, "Jupass110")
    text = msg.as_string()
    server.sendmail(source_address, destination_address, text)
    server.quit()
    username = None
    if "id" in session:
        username = get_db().get_session(session["id"])
    articles = get_db().get_last_articles()
    return render_template('accueil.html', articles=articles , username=username)
    
@app.route('/connexion')
def page_connexion():
    return render_template('login.html')


@app.route('/admin')
@authentication_required
def page_admin():
    articles = get_db().get_articles()
    return render_template('admin.html', articles=articles)


@app.route('/admin-nouveau')
@authentication_required_without_login
def page_admin_nouveau():
    return render_template('admin-nouveau.html')


@app.route('/article/<identifier>')
def article_page(identifier):
    article = get_db().get_article(identifier)
    if article is None:
        return render_template('404.html'), 404
    else:
        return render_template('article.html', article=article)


@app.route('/article/<identifier>/edit')
@authentication_required_without_login
def article_edit_page(identifier):
    article = get_db().get_article(identifier)
    if article is None:
        return render_template('404.html'), 404
    else:
        return render_template('article-edit.html', article=article)


@app.route('/articles', methods=['POST'])
def article_recherche_page():
    mot = request.form['search']
    if not mot:
        articles = get_db().get_articles()
    else:
        articles = get_db().get_article_rechercher(mot)
        if articles is None:
            return render_template('404.html'), 404
    return render_template('article-recherche.html', articles=articles)


@app.route('/ajout-article', methods=['POST'])
@authentication_required_without_login
def article_formulaire():
    erreurs = ''
    titre = request.form['title']
    identifiant = request.form['identifier']
    auteur = request.form['autor']
    date_publication = request.form['publication_date']
    paragraphe = request.form['paragraph']
    data = {
        'titre': titre,
        'identifiant': identifiant,
        'auteur': auteur,
        'date_publication': date_publication,
        'paragraphe': paragraphe,
    }

    if not titre or not identifiant or not auteur or not date_publication or not paragraphe:
        erreurs = "Tous les champs sont obligatoire."

    if not re.match("^[A-Za-z0-9_-]*$", identifiant):
        erreurs = erreurs + "\n"
        + "Le champ Identifiant ne doit pas être composé de caractères spéciale"

    if not erreurs:
        get_db().insert_article(
            titre, identifiant, auteur, date_publication, paragraphe)
        return redirect('/admin')
    else:
        erreurs = erreurs.split('\n')
        return render_template(
            'admin-nouveau.html', erreurs=erreurs, data=data)


@app.route('/update-article', methods=['POST'])
@authentication_required_without_login
def update_article():
    erreurs = ''
    titre = request.form['title']
    identifiant = request.form['identifier']
    paragraphe = request.form['paragraph']
    # Check if all the fields are non-empty and raise an error otherwise
    if not titre or not paragraphe:
        erreurs = "Tous les champs sont obligatoire."
    if not erreurs:
        get_db().update_article(titre, identifiant, paragraphe)
        return redirect('/admin')
    else:
        article = get_db().get_article(identifiant)
        erreurs = erreurs.split('\n')
        return render_template(
            'article-edit.html', erreurs=erreurs, article=article)

@app.route('/confirmation')
def confirmation_page():
    return render_template('confirmation.html')


@app.route('/formulaire', methods=["GET", "POST"])
def formulaire_creation():
    if request.method == "GET":
        return render_template("formulaire.html")
    else:
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        # Vérifier que les champs ne sont pas vides
        if username == "" or password == "" or email == "":
            return render_template("formulaire.html",
                                   error="Tous les champs sont obligatoires.")
        user = get_db().get_user_login_info(username)
        if user is not None:
            return render_template("formulaire.html",
                                   error="Utilisateur déja existant.")
        # TODO Faire la validation du formulaire
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(password + salt).hexdigest()
        db = get_db()
        db.create_user(username, email, salt, hashed_password)

        return redirect("/confirmation")


@app.route('/login', methods=["POST"])
def log_user():
    username = request.form["username"]
    password = request.form["password"]
    # Vérifier que les champs ne sont pas vides
    if username == "" or password == "":
        return redirect("/")

    user = get_db().get_user_login_info(username)
    if user is None:
        return redirect("/")

    salt = user[0]
    hashed_password = hashlib.sha512(password + salt).hexdigest()
    if hashed_password == user[1]:
        # Accès autorisé
        id_session = uuid.uuid4().hex
        get_db().save_session(id_session, username)
        session["id"] = id_session
        return redirect("/")
    else:
        return redirect("/")

@app.route('/logout')
@authentication_required
def logout():
    if "id" in session:
        id_session = session["id"]
        session.pop('id', None)
        get_db().delete_session(id_session)
    return redirect("/")


def is_authenticated(session):
    return "id" in session


def send_unauthorized():
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
                    
def send_unauthorized_without_login():
    return Response('Accès interdit!.\n', 401)


app.secret_key = "(*&*&322387he738220)(*(*22347657"
