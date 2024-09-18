import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from App_chatbot.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# S'inscrire
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        nom = request.form['nom']
        password_ = request.form['password_']
        email = request.form['email']
        adresse = request.form['adresse']
        db = get_db()
        error = None

        if not nom:
            error = 'Nom is required.'
        elif not password_:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO entreprise (nom, email, adresse, password_) VALUES (?, ?, ?, ?)",
                    (nom, email, adresse, generate_password_hash(password_)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"Entreprise {nom} or Email {email} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

# Se connecter
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        nom = request.form['nom']
        password_ = request.form['password']
        db = get_db()
        error = None
        entreprise = db.execute(
            'SELECT * FROM entreprise WHERE nom = ?', (nom,)
        ).fetchone()

        if entreprise is None:
            error = 'Incorrect username.'
        elif not check_password_hash(entreprise['password_'], password_):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['entreprise_id'] = entreprise['id']
            return redirect(url_for('views.index'))

        flash(error)

    return render_template('auth/login.html')


# vérifie si un identifiant utilisateur est stocké dans le sessionet récupère les données de cet utilisateur à partir de la base de données, en les stockant sur g.user
@bp.before_app_request
def load_logged_in_user():
    entreprise_id = session.get('entreprise_id')

    if entreprise_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM entreprise WHERE id = ?', (entreprise_id,)
        ).fetchone()
        
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('views.index'))

# Ce décorateur renvoie une nouvelle fonction de vue qui encapsule la vue d'origine à laquelle elle est appliquée. 
# La nouvelle fonction vérifie si un utilisateur est chargé et redirige vers la page de connexion dans le cas contraire.
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view