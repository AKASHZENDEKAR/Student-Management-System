from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("students_database.db")

# ---------------- INIT DATABASE (RUN ONCE) ----------------
@app.route("/init")
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            course TEXT NOT NULL,
            marks INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    return "Database initialized successfully"

# ---------------- SIGN UP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            error = "Username already exists"

    return render_template("signup.html", error=error)


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["admin"] = True
            session["username"] = username
            return redirect("/")
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# ---------------- READ (PROTECTED) ----------------
@app.route("/")
def students():
    if not session.get("admin"):
        return redirect("/login")

    search = request.args.get("search", "")
    conn = get_db()
    cur = conn.cursor()

    if search:
        cur.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR email LIKE ? OR course LIKE ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM students")

    data = cur.fetchall()
    conn.close()
    return render_template("students.html", students=data, search=search)

# ---------------- ADD STUDENT ----------------
@app.route("/add", methods=["GET", "POST"])
def add_student():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]
        marks = request.form["marks"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO students (name, email, course, marks) VALUES (?,?,?,?)",
            (name, email, course, marks)
        )
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_student.html")

# ---------------- EDIT STUDENT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]
        marks = request.form["marks"]

        cur.execute(
            "UPDATE students SET name=?, email=?, course=?, marks=? WHERE id=?",
            (name, email, course, marks, id)
        )
        conn.commit()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cur.fetchone()
    conn.close()
    return render_template("edit_student.html", student=student)

# ---------------- DELETE STUDENT ----------------
@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete_student(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("DELETE FROM students WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cur.fetchone()
    conn.close()
    return render_template("delete.html", student=student)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
