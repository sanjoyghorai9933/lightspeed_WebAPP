"""
Lightseed Solutions LLP — Flask Backend
Routes: Contact form, Newsletter, Admin dashboard, API
Database: SQLite via Python sqlite3 (built-in)
"""

import os
import sqlite3
import json
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, g, send_from_directory, abort)

# ─── APP CONFIG ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['DATABASE'] = os.path.join(app.instance_path, 'lightseed.db')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

os.makedirs(app.instance_path, exist_ok=True)

ALLOWED_ENQUIRY_STATUSES = {'new', 'contacted', 'converted', 'closed'}
ALLOWED_PROGRAM_CATEGORIES = {'training', 'shuddhi', 'education', 'healing', 'therapy'}
EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# ─── DATABASE HELPERS ──────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            org        TEXT,
            email      TEXT NOT NULL,
            phone      TEXT,
            interest   TEXT,
            message    TEXT,
            status     TEXT DEFAULT 'new',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS newsletter (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT UNIQUE NOT NULL,
            name       TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS testimonials (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            author     TEXT NOT NULL,
            role       TEXT,
            org        TEXT,
            content    TEXT NOT NULL,
            rating     INTEGER DEFAULT 5,
            approved   INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS programs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            category    TEXT NOT NULL,
            description TEXT,
            tag         TEXT,
            icon        TEXT,
            active      INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS admins (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS page_views (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            page       TEXT NOT NULL,
            ip         TEXT,
            ua         TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    # Seed default admin: admin / lightseed2025
    pw = hashlib.sha256("lightseed2025".encode()).hexdigest()
    db.execute("""INSERT OR IGNORE INTO admins (username, password_hash)
                  VALUES ('admin', ?)""", (pw,))

    # Seed sample programs
    programs = [
        ('Lead Smart', 'training', 'Emotionally intelligent leaders navigating complexity with clarity.', 'Leadership', '🎯'),
        ('Building High-Trust Teams', 'training', 'Collaboration, accountability and psychological safety.', 'Team', '🤝'),
        ('Communication & Influence', 'training', 'Clarity, listening, presence and persuasive communication.', 'Communication', '💬'),
        ('NLP Practitioner Certification', 'training', 'Applied behavioural tools for personal and professional growth.', 'NLP', '🧠'),
        ('POSH Awareness & Sensitisation', 'shuddhi', 'Safe, respectful and legally compliant workplaces.', 'POSH', '⚖️'),
        ('POCSO & Child Protection', 'shuddhi', 'Mandatory reporting, recognising vulnerability.', 'POCSO', '🛡️'),
        ('DEI Sensitisation', 'shuddhi', 'Inclusive behaviour and equitable culture-building.', 'DEI', '🌍'),
        ('Faculty Development Programs', 'education', 'Conscious, impactful educators.', 'Faculty', '🎓'),
        ('Plug & Play Freshers', 'education', 'Campus-to-corporate readiness program.', 'Students', '🚀'),
        ('Praankosh', 'healing', 'Breathwork and emotional regulation for sustainable performance.', 'Breathwork', '🌿'),
        ('Meditation & Awareness', 'healing', 'Focus, presence, inner stillness and self-awareness.', 'Mindfulness', '🧘'),
        ('Emotional Reset Circles', 'healing', 'Safe spaces for emotional release and reflection.', 'Group', '💚'),
        ('Saarthi', 'therapy', 'Individual therapy and coaching for clarity and behavioural insight.', 'Flagship', '🕊️'),
        ('Group Counselling', 'therapy', 'Facilitated group environments for shared understanding.', 'Group', '👥'),
        ('Hypnotherapy', 'therapy', 'Evidence-informed interventions for behavioural change.', 'Specialist', '✨'),
    ]
    for p in programs:
        db.execute("""INSERT OR IGNORE INTO programs (title,category,description,tag,icon)
                      SELECT ?,?,?,?,? WHERE NOT EXISTS
                      (SELECT 1 FROM programs WHERE title=?)""",
                   (*p, p[0]))

    # Seed sample testimonials
    testimonials = [
        ('HR Director', 'HR Director', 'Large Manufacturing Firm, North India',
         "The POSH training by Lightseed transformed how our entire organisation approaches workplace safety. It wasn't a checkbox exercise — it was a genuine awakening.", 5),
        ('CEO', 'CEO', 'Technology Company',
         "Mini Gupta's facilitation style is rare — deeply knowledgeable yet profoundly human. Our leadership team left with clarity they hadn't found in years.", 5),
        ('Vice President, Operations', 'VP Operations', 'FMCG Organisation',
         "Praankosh gave our people tools they actually use. The breathwork sessions were a turning point for our team culture.", 5),
        ('Dean of Academics', 'Dean', 'Private University, Uttarakhand',
         "The Faculty Development Program was eye-opening. Lightseed gave us the language and tools to teach with intention.", 5),
        ('Placement Officer', 'Placement Officer', 'Engineering College',
         "Our students came out of the Plug & Play program visibly different — more confident and actually ready for interviews.", 5),
    ]
    for t in testimonials:
        db.execute("""INSERT OR IGNORE INTO testimonials (author,role,org,content,rating,approved)
                      SELECT ?,?,?,?,?,1 WHERE NOT EXISTS
                      (SELECT 1 FROM testimonials WHERE author=? AND org=?)""",
                   (*t, t[0], t[2]))

    db.commit()


def _is_valid_email(email):
    return bool(EMAIL_REGEX.match(email or ''))

# ─── AUTH DECORATOR ────────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── CORS HELPER (no flask-cors needed) ───────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    db = get_db()
    testimonials = db.execute(
        "SELECT * FROM testimonials WHERE approved=1 ORDER BY id LIMIT 6"
    ).fetchall()
    programs = db.execute(
        "SELECT * FROM programs WHERE active=1 ORDER BY id"
    ).fetchall()
    _track(request, 'home')
    return render_template('index.html',
                           testimonials=testimonials,
                           programs=programs)

@app.route('/about')
def about():
    _track(request, 'about')
    return render_template('about.html')

@app.route('/services')
def services():
    db = get_db()
    programs = db.execute("SELECT * FROM programs WHERE active=1 ORDER BY category,id").fetchall()
    _track(request, 'services')
    return render_template('services.html', programs=programs)

@app.route('/healing')
def healing():
    _track(request, 'healing')
    return render_template('healing.html')

@app.route('/training')
def training():
    _track(request, 'training')
    return render_template('training.html')

@app.route('/therapy')
def therapy():
    _track(request, 'therapy')
    return render_template('therapy.html')

@app.route('/shuddhi')
def shuddhi():
    _track(request, 'shuddhi')
    return render_template('shuddhi.html')

@app.route('/education')
def education():
    _track(request, 'education')
    return render_template('education.html')

@app.route('/testimonials')
def testimonials_page():
    db = get_db()
    testimonials = db.execute(
        "SELECT * FROM testimonials WHERE approved=1 ORDER BY id"
    ).fetchall()
    _track(request, 'testimonials')
    return render_template('testimonials.html', testimonials=testimonials)

@app.route('/contact')
def contact():
    _track(request, 'contact')
    return render_template('contact.html')

# ─── STATIC LOGO ──────────────────────────────────────────────────────────────
@app.route('/logo')
def logo():
    return send_from_directory('static/images', 'logo.png')

# ══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/enquiry', methods=['POST', 'OPTIONS'])
def api_enquiry():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    data = request.get_json(silent=True) or request.form
    name    = (data.get('name') or '').strip()
    email   = (data.get('email') or '').strip()
    org     = (data.get('org') or '').strip()
    phone   = (data.get('phone') or '').strip()
    interest= (data.get('interest') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email:
        return jsonify({'success': False, 'error': 'Name and email are required'}), 400
    if not _is_valid_email(email):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400

    db = get_db()
    db.execute("""INSERT INTO enquiries (name,org,email,phone,interest,message)
                  VALUES (?,?,?,?,?,?)""",
               (name, org, email, phone, interest, message))
    db.commit()
    return jsonify({'success': True, 'message': 'Thank you! We will reach out to you shortly.'})


@app.route('/api/newsletter', methods=['POST', 'OPTIONS'])
def api_newsletter():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    data  = request.get_json(silent=True) or request.form
    email = (data.get('email') or '').strip()
    name  = (data.get('name') or '').strip()

    if not _is_valid_email(email):
        return jsonify({'success': False, 'error': 'Valid email is required'}), 400

    db = get_db()
    try:
        db.execute("INSERT INTO newsletter (email,name) VALUES (?,?)", (email, name))
        db.commit()
        return jsonify({'success': True, 'message': 'You have been subscribed!'})
    except sqlite3.IntegrityError:
        return jsonify({'success': True, 'message': 'You are already subscribed.'})


@app.route('/api/programs')
def api_programs():
    category = request.args.get('category', '').strip().lower()
    db = get_db()
    if category:
        if category not in ALLOWED_PROGRAM_CATEGORIES:
            return jsonify({
                'success': False,
                'error': f"Invalid category. Use one of: {', '.join(sorted(ALLOWED_PROGRAM_CATEGORIES))}"
            }), 400
        rows = db.execute(
            "SELECT * FROM programs WHERE active=1 AND category=? ORDER BY id",
            (category,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM programs WHERE active=1 ORDER BY category,id"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/testimonials')
def api_testimonials():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM testimonials WHERE approved=1 ORDER BY id"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/stats')
def api_stats():
    db = get_db()
    enquiries = db.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]
    newsletter = db.execute("SELECT COUNT(*) FROM newsletter").fetchone()[0]
    views = db.execute("SELECT COUNT(*) FROM page_views").fetchone()[0]
    programs = db.execute("SELECT COUNT(*) FROM programs WHERE active=1").fetchone()[0]
    return jsonify({
        'enquiries': enquiries,
        'newsletter': newsletter,
        'page_views': views,
        'active_programs': programs,
        'years_experience': 10,
        'cities_served': 8,
    })

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        pw_hash  = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE username=? AND password_hash=?",
            (username, pw_hash)
        ).fetchone()
        if admin:
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_username']  = username
            return redirect(url_for('admin_dashboard'))
        error = 'Invalid credentials. Please try again.'
    return render_template('admin/login.html', error=error)


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'enquiries':  db.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0],
        'new_enquiries': db.execute("SELECT COUNT(*) FROM enquiries WHERE status='new'").fetchone()[0],
        'newsletter': db.execute("SELECT COUNT(*) FROM newsletter").fetchone()[0],
        'testimonials_pending': db.execute("SELECT COUNT(*) FROM testimonials WHERE approved=0").fetchone()[0],
        'programs':   db.execute("SELECT COUNT(*) FROM programs WHERE active=1").fetchone()[0],
        'page_views': db.execute("SELECT COUNT(*) FROM page_views").fetchone()[0],
    }
    recent = db.execute(
        "SELECT * FROM enquiries ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    top_pages = db.execute(
        "SELECT page, COUNT(*) as cnt FROM page_views GROUP BY page ORDER BY cnt DESC LIMIT 6"
    ).fetchall()
    return render_template('admin/dashboard.html',
                           stats=stats, recent=recent, top_pages=top_pages)


@app.route('/admin/enquiries')
@admin_required
def admin_enquiries():
    db   = get_db()
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    query  = "SELECT * FROM enquiries"
    params = []
    conditions = []
    if status:
        conditions.append("status=?"); params.append(status)
    if search:
        conditions.append("(name LIKE ? OR email LIKE ? OR org LIKE ?)")
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC"
    enquiries = db.execute(query, params).fetchall()
    return render_template('admin/enquiries.html',
                           enquiries=enquiries, status=status, search=search)


@app.route('/admin/enquiries/<int:eid>/status', methods=['POST'])
@admin_required
def admin_update_enquiry(eid):
    new_status = request.form.get('status', 'new').strip().lower()
    if new_status not in ALLOWED_ENQUIRY_STATUSES:
        abort(400, description='Invalid enquiry status')
    db = get_db()
    db.execute("UPDATE enquiries SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
               (new_status, eid))
    db.commit()
    return redirect(url_for('admin_enquiries'))


@app.route('/admin/testimonials')
@admin_required
def admin_testimonials():
    db = get_db()
    testimonials = db.execute("SELECT * FROM testimonials ORDER BY approved ASC, created_at DESC").fetchall()
    return render_template('admin/testimonials.html', testimonials=testimonials)


@app.route('/admin/testimonials/<int:tid>/approve', methods=['POST'])
@admin_required
def admin_approve_testimonial(tid):
    approved = 1 if request.form.get('approved') == '1' else 0
    db = get_db()
    db.execute("UPDATE testimonials SET approved=? WHERE id=?", (approved, tid))
    db.commit()
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonials/<int:tid>/delete', methods=['POST'])
@admin_required
def admin_delete_testimonial(tid):
    db = get_db()
    db.execute("DELETE FROM testimonials WHERE id=?", (tid,))
    db.commit()
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/programs')
@admin_required
def admin_programs():
    db = get_db()
    programs = db.execute("SELECT * FROM programs ORDER BY category,id").fetchall()
    return render_template('admin/programs.html', programs=programs)


@app.route('/admin/programs/add', methods=['POST'])
@admin_required
def admin_add_program():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip().lower()
    description = request.form.get('description', '').strip()
    tag = request.form.get('tag', '').strip()
    icon = request.form.get('icon', '📌').strip() or '📌'

    if not title or not category:
        abort(400, description='Program title and category are required')
    if category not in ALLOWED_PROGRAM_CATEGORIES:
        abort(400, description='Invalid program category')

    db = get_db()
    db.execute("""INSERT INTO programs (title,category,description,tag,icon)
                  VALUES (?,?,?,?,?)""",
               (title, category, description, tag, icon))
    db.commit()
    return redirect(url_for('admin_programs'))


@app.route('/admin/programs/<int:pid>/toggle', methods=['POST'])
@admin_required
def admin_toggle_program(pid):
    db = get_db()
    db.execute("UPDATE programs SET active = 1 - active WHERE id=?", (pid,))
    db.commit()
    return redirect(url_for('admin_programs'))


@app.route('/admin/newsletter')
@admin_required
def admin_newsletter():
    db = get_db()
    subscribers = db.execute("SELECT * FROM newsletter ORDER BY created_at DESC").fetchall()
    return render_template('admin/newsletter.html', subscribers=subscribers)


@app.route('/admin/newsletter/<int:nid>/delete', methods=['POST'])
@admin_required
def admin_delete_subscriber(nid):
    db = get_db()
    db.execute("DELETE FROM newsletter WHERE id=?", (nid,))
    db.commit()
    return redirect(url_for('admin_newsletter'))


# ─── PRIVATE HELPERS ──────────────────────────────────────────────────────────
def _track(req, page):
    try:
        db = get_db()
        db.execute("INSERT INTO page_views (page,ip,ua) VALUES (?,?,?)",
                   (page, req.remote_addr, req.user_agent.string[:200]))
        db.commit()
    except Exception:
        pass


# ─── INIT & RUN ───────────────────────────────────────────────────────────────
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
