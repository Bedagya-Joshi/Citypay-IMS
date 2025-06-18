from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from db import get_db_connection

bp = Blueprint('main', __name__)

login_manager = LoginManager()
login_manager.login_view = 'main.login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, role FROM Users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, password, role FROM Users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and password == user[2]:  # Replace with hashed password check in production
            user_obj = User(user[0], user[1], user[3])
            login_user(user_obj)
            return redirect(url_for('main.items'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/items')
@login_required
def items():
    return render_template('items.html')

@bp.route('/item_taken_history')
@login_required
def item_taken_history():
    return render_template('items_taken.html')

@bp.route('/requested_history')
@login_required
def requested_history():
    return render_template('request.html')

@bp.route('/item_update')
@login_required
def item_update():
    return render_template('items_update.html')

@bp.route('/view_users_items')
@login_required
def view_users_items():
    return render_template('users_items.html')

@bp.route('/administrator')
@login_required
def administrator():
    return render_template('admin.html')