from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from db import get_db_connection
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import abort

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, password, role, failed_attempts, lockout_until FROM Users WHERE username = %s", (username,))
        user = cur.fetchone()
        now = datetime.now()
        if user:
            user_id, db_username, db_password, role, failed_attempts, lockout_until = user
            if lockout_until and now < lockout_until:
                remaining = (lockout_until - now).seconds // 60 + 1
                message = f"Account locked. Try again in {remaining} minutes."
            elif check_password_hash(db_password, password):
                cur.execute("UPDATE Users SET failed_attempts = 0, lockout_until = NULL WHERE user_id = %s", (user_id,))
                conn.commit()
                cur.close()
                conn.close()
                user_obj = User(user_id, db_username, role)
                login_user(user_obj)
                session.permanent = True
                return redirect(url_for('main.items'))
            else:
                failed_attempts += 1
                if failed_attempts >= 10:
                    lockout_until = now + timedelta(minutes=15)
                    cur.execute("UPDATE Users SET failed_attempts = %s, lockout_until = %s WHERE user_id = %s", (failed_attempts, lockout_until, user_id))
                    message = "Account locked due to too many failed attempts. Try again in 15 minutes."
                else:
                    cur.execute("UPDATE Users SET failed_attempts = %s WHERE user_id = %s", (failed_attempts, user_id))
                    message = f"Incorrect password. {10 - failed_attempts} attempts left."
                conn.commit()
                cur.close()
                conn.close()
        else:
            message = "Incorrect username or password."
        return render_template('login.html', error=message)
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/items', methods=['GET', 'POST'])
@login_required
def items():
    conn = get_db_connection()
    cur = conn.cursor()
    message = None

    # Handle item request (for users)
    if request.method == 'POST' and current_user.role == 'user':
        item_id = request.form['item_id']
        quantity = int(request.form['quantity'])
        reason = request.form['reason']
        user_id = current_user.id
        # Insert into ItemRequested with status 'Pending'
        cur.execute("""
            INSERT INTO ItemRequested (date_of_request, user_id, item_id, reason, status, quantity)
            VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
        """, (user_id, item_id, reason, 'Pending', quantity))
        conn.commit()
        message = "Request submitted successfully."

    # Fetch items with category
    cur.execute("""
        SELECT i.item_id, i.name, c.category_name, i.quantity
        FROM Item i
        JOIN ItemCategory c ON i.category_id = c.category_id
        ORDER BY i.item_id
    """)
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('items.html', items=items, message=message)

@bp.route('/item_taken_history')
@login_required
def item_taken_history():
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch only approved items for the logged-in user
    cur.execute("""
        SELECT h.date_of_approve, i.name, h.quantity
        FROM ItemHistory h
        JOIN Item i ON h.item_id = i.item_id
        WHERE h.user_id = %s AND h.status = 'Approved'
        ORDER BY h.date_of_approve DESC
    """, (current_user.id,))
    taken_items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('items_taken.html', taken_items=taken_items)

@bp.route('/requested_history', methods=['GET', 'POST'])
@login_required
@admin_required
def requested_history():
    conn = get_db_connection()
    cur = conn.cursor()
    message = None

    # Handle approve/reject
    if request.method == 'POST':
        action = request.form.get('action')
        req_id = request.form.get('req_id')
        reason = request.form.get('reason')
        now = datetime.now()
        # Get request info (including quantity)
        cur.execute("""
            SELECT date_of_request, user_id, item_id, reason, status
            FROM ItemRequested WHERE id = %s
        """, (req_id,))
        req = cur.fetchone()
        if req:
            date_of_request, user_id, item_id, req_reason, current_status = req
            if current_status == 'Pending':
                status = 'Approved' if action == 'approve' else 'Rejected'
                # Get requested quantity
                cur.execute("SELECT quantity FROM ItemRequested WHERE id = %s", (req_id,))
                qty = cur.fetchone()[0]
                cur.execute("UPDATE ItemRequested SET status = %s WHERE id = %s", (status, req_id))
                if status == 'Approved':
                    cur.execute("UPDATE Item SET quantity = quantity - %s WHERE item_id = %s", (qty, item_id))
                # Insert into ItemHistory with quantity
                cur.execute("""
                    INSERT INTO ItemHistory (date_of_request, date_of_approve, user_id, item_id, status, reason, quantity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (date_of_request, now, user_id, item_id, status, reason, qty))
                conn.commit()
                message = f"Request {status.lower()}."
            else:
                message = "Request already processed."

    # Filtering
    filter_status = request.args.get('status', 'All')
    filter_query = ""
    params = []
    if filter_status and filter_status != 'All':
        filter_query = "AND r.status = %s"
        params.append(filter_status)

    # Fetch requests with user and item info (include quantity)
    cur.execute(f"""
        SELECT r.id, r.date_of_request, u.username, i.name, r.reason, r.status, r.quantity
        FROM ItemRequested r
        JOIN Users u ON r.user_id = u.user_id
        JOIN Item i ON r.item_id = i.item_id
        WHERE 1=1 {filter_query}
        ORDER BY r.date_of_request DESC
    """, params)
    requests = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('request.html', requests=requests, message=message, filter_status=filter_status)

@bp.route('/item_update', methods=['GET', 'POST'])
@login_required
@admin_required
def item_update():
    conn = get_db_connection()
    cur = conn.cursor()
    message = None

    # Handle add/remove quantity
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_quantity':
            item_id = request.form['item_id']
            qty = int(request.form['quantity'])
            cur.execute("UPDATE Item SET quantity = quantity + %s WHERE item_id = %s", (qty, item_id))
            conn.commit()
            message = "Quantity added successfully."
        elif action == 'remove_quantity':
            item_id = request.form['item_id']
            qty = int(request.form['quantity'])
            # Ensure quantity doesn't go below zero
            cur.execute("SELECT quantity FROM Item WHERE item_id = %s", (item_id,))
            current_qty = cur.fetchone()[0]
            if current_qty >= qty:
                cur.execute("UPDATE Item SET quantity = quantity - %s WHERE item_id = %s", (qty, item_id))
                conn.commit()
                message = "Quantity removed successfully."
            else:
                message = "Cannot remove more than available quantity."
        elif action == 'add_item':
            name = request.form['item_name']
            category_id = request.form['category_id']
            quantity = int(request.form['quantity'])
            user_id = current_user.id
            cur.execute("INSERT INTO Item (name, quantity, category_id, user_id) VALUES (%s, %s, %s, %s)",
                        (name, quantity, category_id, user_id))
            conn.commit()
            message = "Item added successfully."
        elif action == 'add_category':
            category_name = request.form['category_name']
            cur.execute("INSERT INTO ItemCategory (category_name) VALUES (%s)", (category_name,))
            conn.commit()
            message = "Category added successfully."

    # Fetch items and categories for display
    cur.execute("""
        SELECT i.item_id, i.name, c.category_name, i.quantity
        FROM Item i
        JOIN ItemCategory c ON i.category_id = c.category_id
        ORDER BY i.item_id
    """)
    items = cur.fetchall()
    cur.execute("SELECT category_id, category_name FROM ItemCategory ORDER BY category_name")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('items_update.html', items=items, categories=categories, message=message)

@bp.route('/view_users_items', methods=['GET', 'POST'])
@login_required
@admin_required
def view_users_items():
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch all users for dropdown
    cur.execute("SELECT user_id, username FROM Users ORDER BY username")
    users = cur.fetchall()

    selected_user_id = request.form.get('user_id') if request.method == 'POST' else None
    items_history = []

    if selected_user_id:
        cur.execute("""
            SELECT h.date_of_approve, i.name, i.item_id, h.quantity
            FROM ItemHistory h
            JOIN Item i ON h.item_id = i.item_id
            WHERE h.user_id = %s AND h.status = 'Approved'
            ORDER BY h.date_of_approve DESC
        """, (selected_user_id,))
        items_history = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('users_items.html', users=users, items_history=items_history, selected_user_id=selected_user_id)

@bp.route('/administrator', methods=['GET', 'POST'])
@login_required
@admin_required
def administrator():
    conn = get_db_connection()
    cur = conn.cursor()
    message = None

    # Handle add user
    if request.method == 'POST' and request.form.get('action') == 'add_user':
        username = request.form['username']
        password = request.form['password']
        is_admin = request.form.get('is_admin') == 'on'
        role = 'admin' if is_admin else 'user'
        hashed_password = generate_password_hash(password)
        try:
            cur.execute("INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)", (username, hashed_password, role))
            conn.commit()
            message = "User added successfully."
        except Exception as e:
            conn.rollback()
            message = f"Error: {str(e)}"

    # Handle password update
    if request.method == 'POST' and request.form.get('action') == 'update_password':
        user_id = request.form['user_id']
        new_password = request.form['new_password']
        hashed_password = generate_password_hash(new_password)
        try:
            cur.execute("UPDATE Users SET password = %s WHERE user_id = %s", (hashed_password, user_id))
            conn.commit()
            message = "Password updated successfully."
        except Exception as e:
            conn.rollback()
            message = f"Error: {str(e)}"

    # Handle user deletion
    if request.method == 'POST' and request.form.get('action') == 'delete_user':
        user_id = request.form['user_id']
        admin_password = request.form['admin_password']
        # Get the current admin's hashed password from DB
        cur.execute("SELECT password FROM Users WHERE user_id = %s", (current_user.id,))
        admin_hashed_pw = cur.fetchone()
        if admin_hashed_pw and check_password_hash(admin_hashed_pw[0], admin_password):
            try:
                cur.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
                conn.commit()
                message = "User deleted successfully."
            except Exception as e:
                conn.rollback()
                message = f"Error: {str(e)}"
        else:
            message = "Incorrect admin password. User not deleted."

    # Fetch users for display
    cur.execute("SELECT user_id, username, role FROM Users ORDER BY user_id")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', users=users, message=message)

@bp.route('/my_requests')
@login_required
def my_requests():
    conn = get_db_connection()
    cur = conn.cursor()
    # Get all requests for the user
    cur.execute("""
        SELECT r.id, r.date_of_request, i.name, r.quantity, r.status
        FROM ItemRequested r
        JOIN Item i ON r.item_id = i.item_id
        WHERE r.user_id = %s
        ORDER BY r.date_of_request DESC
    """, (current_user.id,))
    requests = cur.fetchall()

    # For each request, get the reason from ItemHistory if not pending
    results = []
    for req in requests:
        req_id, date_of_request, item_name, quantity, status = req
        reason = ""
        if status in ('Approved', 'Rejected'):
            cur.execute("""
                SELECT reason FROM ItemHistory
                WHERE user_id = %s AND item_id = (
                    SELECT item_id FROM ItemRequested WHERE id = %s
                ) AND date_of_request = (
                    SELECT date_of_request FROM ItemRequested WHERE id = %s
                ) AND status = %s
                ORDER BY id DESC LIMIT 1
            """, (current_user.id, req_id, req_id, status))
            row = cur.fetchone()
            if row:
                reason = row[0]
        results.append((date_of_request, item_name, quantity, status, reason))
    cur.close()
    conn.close()
    return render_template('my_requests.html', my_requests=results)