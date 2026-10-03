"""
Student Subject Selection System
--------------------------------
A beginner-friendly Flask + SQLite project for a DAA hackathon.

Run:  python app.py   then open http://127.0.0.1:5000
Demo student : S101 / pass123
Demo admin   : admin / admin123   (log in from the same login page)
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g
)

app = Flask(__name__)
app.secret_key = "daa-hackathon-secret-key"  # needed for sessions + flash messages

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ----------------------------------------------------------------------
# Database helpers
# ----------------------------------------------------------------------
def get_db():
    """Open one SQLite connection per request and reuse it."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row          # rows behave like dictionaries
        g.db.execute("PRAGMA foreign_keys = ON")  # enforce foreign keys
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close the connection at the end of every request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and insert sample data if the database is empty."""
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            password    TEXT NOT NULL,
            department  TEXT NOT NULL,
            semester    INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code    TEXT UNIQUE NOT NULL,
            subject_name    TEXT NOT NULL,
            department      TEXT NOT NULL,
            credits         INTEGER NOT NULL,
            total_seats     INTEGER NOT NULL,
            available_seats INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS selections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            subject_id  INTEGER NOT NULL,
            selected_at TEXT NOT NULL,
            UNIQUE (student_id, subject_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
    """)

    if db.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO students (student_id, name, password, department, semester) VALUES (?, ?, ?, ?, ?)",
            [
                ("S101", "Nithya Koppolu", "pass123", "CSE", 5),
                ("S102", "Rahul Sharma", "pass123", "CSE", 5),
                ("S103", "Ananya Reddy", "pass123", "ECE", 5),
                ("S104", "Arjun Kumar", "pass123", "IT", 5),
                ("S105", "Priya Nair", "pass123", "MECH", 5),
            ],
        )

    if db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO subjects (subject_code, subject_name, department, credits, total_seats, available_seats) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("CS501", "Machine Learning", "CSE", 4, 30, 30),
                ("CS502", "Cloud Computing", "CSE", 3, 25, 25),
                ("CS503", "Cyber Security", "CSE", 3, 20, 20),
                ("IT501", "Web Technologies", "IT", 3, 30, 30),
                ("IT502", "Data Mining", "IT", 4, 2, 2),
                ("EC501", "Internet of Things", "ECE", 3, 25, 25),
                ("EC502", "VLSI Design", "ECE", 4, 15, 15),
                ("ME501", "Robotics", "MECH", 3, 20, 20),
                ("MA501", "Operations Research", "MATHS", 2, 40, 40),
                ("HS501", "Professional Ethics", "HSS", 2, 1, 1),
            ],
        )
    db.commit()
    db.close()


# ----------------------------------------------------------------------
# Login decorators
# ----------------------------------------------------------------------
def student_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "student_db_id" not in session:
            flash("Please log in as a student first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access only. Please log in as admin.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


# ----------------------------------------------------------------------
# Public pages
# ----------------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    stats = {
        "subjects": db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0],
        "students": db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "seats": db.execute("SELECT COALESCE(SUM(available_seats),0) FROM subjects").fetchone()[0],
    }
    return render_template("index.html", stats=stats)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "").strip()

        # Admin login uses the same form
        if user_id == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["is_admin"] = True
            flash("Welcome, Administrator!", "success")
            return redirect(url_for("admin"))

        student = get_db().execute(
            "SELECT * FROM students WHERE student_id = ? AND password = ?",
            (user_id, password),
        ).fetchone()
        if student:
            session.clear()
            session["student_db_id"] = student["id"]
            session["student_name"] = student["name"]
            flash(f"Welcome back, {student['name']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid ID or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Student pages
# ----------------------------------------------------------------------
@app.route("/dashboard")
@student_required
def dashboard():
    db = get_db()
    sid = session["student_db_id"]
    student = db.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    selections = db.execute("""
        SELECT sel.id, sub.subject_code, sub.subject_name, sub.credits, sel.selected_at
        FROM selections sel JOIN subjects sub ON sel.subject_id = sub.id
        WHERE sel.student_id = ? ORDER BY sel.selected_at DESC
    """, (sid,)).fetchall()
    available = db.execute(
        "SELECT COUNT(*) FROM subjects WHERE available_seats > 0").fetchone()[0]
    total_credits = sum(s["credits"] for s in selections)
    return render_template("dashboard.html", student=student, selections=selections,
                           available=available, total_credits=total_credits)


@app.route("/subjects")
def subjects():
    """List subjects with search + department + credit filters."""
    db = get_db()
    q = request.args.get("q", "").strip()
    dept = request.args.get("department", "")
    credits = request.args.get("credits", "")

    sql = "SELECT * FROM subjects WHERE 1=1"
    params = []
    if q:
        sql += " AND (subject_name LIKE ? OR subject_code LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if dept:
        sql += " AND department = ?"
        params.append(dept)
    if credits:
        sql += " AND credits = ?"
        params.append(int(credits))
    sql += " ORDER BY subject_code"

    rows = db.execute(sql, params).fetchall()
    departments = [r[0] for r in db.execute("SELECT DISTINCT department FROM subjects ORDER BY department")]
    credit_options = [r[0] for r in db.execute("SELECT DISTINCT credits FROM subjects ORDER BY credits")]

    selected_ids = set()
    if "student_db_id" in session:
        selected_ids = {r[0] for r in db.execute(
            "SELECT subject_id FROM selections WHERE student_id = ?", (session["student_db_id"],))}

    return render_template("subjects.html", subjects=rows, departments=departments,
                           credit_options=credit_options, selected_ids=selected_ids,
                           q=q, dept=dept, credits=credits)


@app.route("/select/<int:subject_id>", methods=["GET", "POST"])
@student_required
def select_subject(subject_id):
    db = get_db()
    sid = session["student_db_id"]
    subject = db.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()

    if subject is None:
        flash("Subject not found.", "danger")
    elif db.execute("SELECT 1 FROM selections WHERE student_id = ? AND subject_id = ?",
                    (sid, subject_id)).fetchone():
        flash(f"You already selected {subject['subject_name']}.", "warning")
    elif subject["available_seats"] <= 0:
        flash(f"Sorry, no seats left in {subject['subject_name']}.", "danger")
    else:
        # Decrease seat only if still available (safe against double clicks)
        cur = db.execute(
            "UPDATE subjects SET available_seats = available_seats - 1 WHERE id = ? AND available_seats > 0",
            (subject_id,))
        if cur.rowcount == 1:
            db.execute("INSERT INTO selections (student_id, subject_id, selected_at) VALUES (?, ?, ?)",
                       (sid, subject_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.commit()
            flash(f"Successfully selected {subject['subject_name']}!", "success")
        else:
            flash("Seat was just taken. Try another subject.", "danger")
    return redirect(request.referrer or url_for("subjects"))


@app.route("/selections")
@student_required
def selections():
    rows = get_db().execute("""
        SELECT sel.id, sub.subject_code, sub.subject_name, sub.credits, sel.selected_at
        FROM selections sel JOIN subjects sub ON sel.subject_id = sub.id
        WHERE sel.student_id = ? ORDER BY sel.selected_at DESC
    """, (session["student_db_id"],)).fetchall()
    return render_template("selections.html", selections=rows,
                           total_credits=sum(r["credits"] for r in rows))


@app.route("/remove/<int:selection_id>", methods=["GET", "POST"])
@student_required
def remove_selection(selection_id):
    db = get_db()
    sel = db.execute("SELECT * FROM selections WHERE id = ? AND student_id = ?",
                     (selection_id, session["student_db_id"])).fetchone()
    if sel:
        db.execute("DELETE FROM selections WHERE id = ?", (selection_id,))
        db.execute("UPDATE subjects SET available_seats = available_seats + 1 WHERE id = ?",
                   (sel["subject_id"],))
        db.commit()
        flash("Subject removed and seat released.", "info")
    else:
        flash("Selection not found.", "danger")
    return redirect(url_for("selections"))


# ----------------------------------------------------------------------
# Admin pages
# ----------------------------------------------------------------------
@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    stats = {
        "students": db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "selections": db.execute("SELECT COUNT(*) FROM selections").fetchone()[0],
        "available": db.execute("SELECT COALESCE(SUM(available_seats),0) FROM subjects").fetchone()[0],
        "total": db.execute("SELECT COALESCE(SUM(total_seats),0) FROM subjects").fetchone()[0],
    }
    rows = db.execute("SELECT * FROM subjects ORDER BY subject_code").fetchall()
    return render_template("admin.html", stats=stats, subjects=rows)


def read_subject_form():
    """Read and validate the add/edit subject form. Returns (data, error)."""
    f = request.form
    try:
        data = {
            "code": f["subject_code"].strip().upper(),
            "name": f["subject_name"].strip(),
            "dept": f["department"].strip().upper(),
            "credits": int(f["credits"]),
            "total": int(f["total_seats"]),
        }
    except (KeyError, ValueError):
        return None, "Please fill all fields with valid values."
    if not data["code"] or not data["name"] or not data["dept"]:
        return None, "All fields are required."
    if data["credits"] < 1 or data["total"] < 1:
        return None, "Credits and seats must be at least 1."
    return data, None


@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def add_subject():
    if request.method == "POST":
        data, error = read_subject_form()
        if error:
            flash(error, "danger")
        else:
            try:
                db = get_db()
                db.execute("""INSERT INTO subjects (subject_code, subject_name, department, credits, total_seats, available_seats)
                              VALUES (?, ?, ?, ?, ?, ?)""",
                           (data["code"], data["name"], data["dept"], data["credits"], data["total"], data["total"]))
                db.commit()
                flash("Subject added successfully.", "success")
                return redirect(url_for("admin"))
            except sqlite3.IntegrityError:
                flash("A subject with this code already exists.", "danger")
    return render_template("add_subject.html")


@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_subject(id):
    db = get_db()
    subject = db.execute("SELECT * FROM subjects WHERE id = ?", (id,)).fetchone()
    if subject is None:
        flash("Subject not found.", "danger")
        return redirect(url_for("admin"))

    if request.method == "POST":
        data, error = read_subject_form()
        taken = subject["total_seats"] - subject["available_seats"]
        if error:
            flash(error, "danger")
        elif data["total"] < taken:
            flash(f"Total seats cannot be less than {taken} (already selected).", "danger")
        else:
            try:
                db.execute("""UPDATE subjects SET subject_code=?, subject_name=?, department=?,
                              credits=?, total_seats=?, available_seats=? WHERE id=?""",
                           (data["code"], data["name"], data["dept"], data["credits"],
                            data["total"], data["total"] - taken, id))
                db.commit()
                flash("Subject updated.", "success")
                return redirect(url_for("admin"))
            except sqlite3.IntegrityError:
                flash("A subject with this code already exists.", "danger")
    return render_template("edit_subject.html", subject=subject)


@app.route("/admin/delete/<int:id>", methods=["POST", "GET"])
@admin_required
def delete_subject(id):
    db = get_db()
    db.execute("DELETE FROM subjects WHERE id = ?", (id,))  # selections removed by CASCADE
    db.commit()
    flash("Subject deleted.", "info")
    return redirect(url_for("admin"))


# ----------------------------------------------------------------------
# DAA component: Greedy Subject Allocation
# ----------------------------------------------------------------------
def greedy_allocation(students, seats, max_per_student):
    """
    students: list of (name, [pref1, pref2, ...]) already in priority order
    seats:    dict subject -> seats available
    For each student (by priority), walk their preferences in order and
    allocate a subject if a seat is free; otherwise skip it.
    Time  : O(S * P)  (S students, P preferences each)
    Space : O(S + M)  (M subjects)
    """
    seats = dict(seats)  # copy so the original is unchanged
    result, steps = [], []
    for name, prefs in students:
        got = []
        for subj in prefs:
            if len(got) >= max_per_student:
                break
            if seats.get(subj, 0) > 0:
                seats[subj] -= 1
                got.append(subj)
                steps.append(f"{name}: '{subj}' allocated (seats left {seats[subj]})")
            else:
                steps.append(f"{name}: '{subj}' FULL - skipped")
        result.append({"name": name, "prefs": prefs, "allocated": got})
    return result, steps, seats


@app.route("/algorithm", methods=["GET", "POST"])
def algorithm():
    # Default demo input (students listed in priority order, e.g. by CGPA)
    default_students = "Nithya: ML, Cloud, IoT\nRahul: ML, Security, Cloud\nAnanya: ML, IoT, Cloud\nArjun: Cloud, ML, Security"
    default_seats = "ML: 2\nCloud: 2\nSecurity: 1\nIoT: 1"
    students_text = request.form.get("students", default_students)
    seats_text = request.form.get("seats", default_seats)
    max_per = int(request.form.get("max_per", 1) or 1)

    students, seats, error = [], {}, None
    try:
        for line in students_text.strip().splitlines():
            if line.strip():
                name, prefs = line.split(":", 1)
                students.append((name.strip(), [p.strip() for p in prefs.split(",") if p.strip()]))
        for line in seats_text.strip().splitlines():
            if line.strip():
                subj, n = line.split(":", 1)
                seats[subj.strip()] = int(n)
    except ValueError:
        error = "Use the format  Name: pref1, pref2   and   Subject: seats"

    result, steps, remaining = ([], [], {}) if error else greedy_allocation(students, seats, max_per)
    return render_template("algorithm.html", students_text=students_text, seats_text=seats_text,
                           max_per=max_per, result=result, steps=steps, remaining=remaining, error=error)


if __name__ == "__main__":
    init_db()  # create database.db + sample data on first run
    app.run(debug=True)
