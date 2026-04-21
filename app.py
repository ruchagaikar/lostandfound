from flask import Flask, render_template, request, redirect, session, flash, abort
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-in-production')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit


# ─── Helpers ─────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Please login to continue.', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def init_db():
    conn = sqlite3.connect('database.db')

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        description TEXT,
        location    TEXT,
        type        TEXT,
        category    TEXT,
        image       TEXT,
        user        TEXT,
        status      TEXT DEFAULT 'Active'
    )''')

    # Safe migration: add status column if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE items ADD COLUMN status TEXT DEFAULT 'Active'")
        conn.commit()
    except Exception:
        pass  # Column already exists — safe to ignore

    conn.commit()
    conn.close()


init_db()


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        conn = sqlite3.connect('database.db')
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = username
            return redirect('/dashboard')
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not username or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        hashed = generate_password_hash(password)

        try:
            conn = sqlite3.connect('database.db')
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hashed)
            )
            conn.commit()
            conn.close()
            flash('Account created! Please login.', 'success')
            return redirect('/')
        except sqlite3.IntegrityError:
            flash('Username already taken. Please choose another.', 'error')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    search          = request.args.get('search', '').strip()
    filter_type     = request.args.get('type', '')
    filter_category = request.args.get('category', '')
    filter_location = request.args.get('location', '').strip()

    query  = "SELECT * FROM items WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend(['%' + search + '%', '%' + search + '%'])
    if filter_type:
        query += " AND type = ?"
        params.append(filter_type)
    if filter_category:
        query += " AND category = ?"
        params.append(filter_category)
    if filter_location:
        query += " AND location LIKE ?"
        params.append('%' + filter_location + '%')

    query += " ORDER BY id DESC"

    conn  = sqlite3.connect('database.db')
    items = conn.execute(query, params).fetchall()
    # Stats
    total_lost  = conn.execute("SELECT COUNT(*) FROM items WHERE type='Lost'").fetchone()[0]
    total_found = conn.execute("SELECT COUNT(*) FROM items WHERE type='Found'").fetchone()[0]
    resolved    = conn.execute("SELECT COUNT(*) FROM items WHERE status='Resolved'").fetchone()[0]
    conn.close()

    return render_template(
        'dashboard.html',
        items=items,
        search=search,
        filter_type=filter_type,
        filter_category=filter_category,
        filter_location=filter_location,
        total_lost=total_lost,
        total_found=total_found,
        resolved=resolved
    )


# ─── Report Item ─────────────────────────────────────────────────────────────

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        location    = request.form.get('location', '').strip()
        type_       = request.form.get('type', '')
        category    = request.form.get('category', '')

        if not name or not location or not type_:
            flash('Item name, location, and type are required.', 'error')
            return render_template('report.html')

        filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                if allowed_file(image.filename):
                    ext      = image.filename.rsplit('.', 1)[1].lower()
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'error')
                    return render_template('report.html')

        conn = sqlite3.connect('database.db')
        conn.execute(
            '''INSERT INTO items (name, description, location, type, category, image, user, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')''',
            (name, description, location, type_, category, filename, session['user'])
        )
        conn.commit()
        conn.close()

        flash('Item reported successfully!', 'success')
        return redirect('/dashboard')

    return render_template('report.html')


# ─── View Item ───────────────────────────────────────────────────────────────

@app.route('/view/<int:id>')
@login_required
def view(id):
    conn = sqlite3.connect('database.db')
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not item:
        abort(404)

    return render_template('view.html', item=item)


# ─── Edit Item ───────────────────────────────────────────────────────────────

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    conn = sqlite3.connect('database.db')
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not item:
        abort(404)
    if item[7] != session['user']:
        abort(403)

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        location    = request.form.get('location', '').strip()
        type_       = request.form.get('type', '')
        category    = request.form.get('category', '')

        if not name or not location:
            flash('Item name and location are required.', 'error')
            return render_template('edit.html', item=item)

        filename = item[6]  # Keep existing image by default
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                if allowed_file(image.filename):
                    ext         = image.filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{uuid.uuid4().hex}.{ext}"
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    filename = new_filename
                else:
                    flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP.', 'error')
                    return render_template('edit.html', item=item)

        conn = sqlite3.connect('database.db')
        conn.execute(
            '''UPDATE items
               SET name=?, description=?, location=?, type=?, category=?, image=?
               WHERE id=?''',
            (name, description, location, type_, category, filename, id)
        )
        conn.commit()
        conn.close()

        flash('Item updated successfully!', 'success')
        return redirect(f'/view/{id}')

    return render_template('edit.html', item=item)


# ─── Delete Item ─────────────────────────────────────────────────────────────

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    conn = sqlite3.connect('database.db')
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if not item:
        conn.close()
        abort(404)
    if item[7] != session['user']:
        conn.close()
        abort(403)

    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Item deleted successfully.', 'success')
    return redirect('/dashboard')


# ─── Resolve/Reopen Item ─────────────────────────────────────────────────────

@app.route('/resolve/<int:id>', methods=['POST'])
@login_required
def resolve(id):
    conn = sqlite3.connect('database.db')
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if not item:
        conn.close()
        abort(404)
    if item[7] != session['user']:
        conn.close()
        abort(403)

    new_status = 'Resolved' if item[8] == 'Active' else 'Active'
    conn.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, id))
    conn.commit()
    conn.close()

    flash(f'Item marked as {new_status}.', 'success')
    return redirect(f'/view/{id}')


# ─── My Items ────────────────────────────────────────────────────────────────

@app.route('/my-items')
@login_required
def my_items():
    conn  = sqlite3.connect('database.db')
    items = conn.execute(
        'SELECT * FROM items WHERE user = ? ORDER BY id DESC',
        (session['user'],)
    ).fetchall()
    conn.close()

    return render_template('my_items.html', items=items)


# ─── Error Handlers ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 5MB.', 'error')
    return redirect(request.referrer or '/dashboard')


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)