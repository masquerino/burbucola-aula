import os, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "burbucola.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "burbucola")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn: conn.close()

def init_db():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS announcements(
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS cases(
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, statement TEXT NOT NULL,
      question TEXT NOT NULL, deadline TEXT, published INTEGER DEFAULT 1,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS submissions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL,
      student_name TEXT NOT NULL, answer TEXT NOT NULL, created_at TEXT NOT NULL,
      UNIQUE(case_id, student_name)
    );
    CREATE TABLE IF NOT EXISTS documents(
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
      description TEXT, url TEXT, created_at TEXT NOT NULL
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0] == 0:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn.execute("INSERT INTO announcements(title,body,created_at) VALUES(?,?,?)",
                     ("Bienvenidos a Burbucola", "Trabajadores: esta es vuestra empresa virtual. Consultad periódicamente las comunicaciones de MJA y resolved los casos laborales.", now))
    if conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn.execute("""INSERT INTO cases(title,statement,question,deadline,created_at)
                        VALUES(?,?,?,?,?)""",
                     ("Caso 1 · El nuevo horario",
                      "MJA comunica que, por necesidades de producción, el horario del equipo pasará a ser de 9:00 a 18:00 y que algunos trabajadores deberán acudir dos tardes al mes.",
                      "Como trabajadores de Burbucola, identificad las cuestiones jurídicas relevantes, las facultades empresariales implicadas y los límites que debería respetar la empresa.",
                      "", now))
    conn.commit(); conn.close()

def teacher_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("teacher"):
            return redirect(url_for("teacher_login"))
        return f(*args, **kwargs)
    return wrapper

@app.context_processor
def inject():
    return {"teacher": session.get("teacher", False), "student": session.get("student")}

@app.route("/")
def home():
    announcements = db().execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    cases = db().execute("SELECT * FROM cases WHERE published=1 ORDER BY id DESC").fetchall()
    return render_template("home.html", announcements=announcements, cases=cases)

@app.route("/profesora/login", methods=["GET","POST"])
def teacher_login():
    if request.method == "POST":
        if check_password_hash(generate_password_hash(TEACHER_PASSWORD), request.form.get("password","")):
            session["teacher"] = True
            return redirect(url_for("dashboard"))
        flash("Contraseña incorrecta.", "error")
    return render_template("teacher_login.html")

@app.route("/profesora/logout")
def teacher_logout():
    session.pop("teacher", None); return redirect(url_for("home"))

@app.route("/profesora")
@teacher_required
def dashboard():
    announcements = db().execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    cases = db().execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    docs = db().execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    submissions = db().execute("""SELECT submissions.*, cases.title case_title
                                  FROM submissions JOIN cases ON cases.id=submissions.case_id
                                  ORDER BY submissions.id DESC""").fetchall()
    return render_template("dashboard.html", announcements=announcements, cases=cases, docs=docs, submissions=submissions)

@app.route("/profesora/anuncio", methods=["POST"])
@teacher_required
def add_announcement():
    title=request.form["title"].strip(); body=request.form["body"].strip()
    if title and body:
        db().execute("INSERT INTO announcements(title,body,created_at) VALUES(?,?,?)",
                     (title,body,datetime.now().strftime("%d/%m/%Y %H:%M"))); db().commit()
    return redirect(url_for("dashboard"))

@app.route("/profesora/caso", methods=["POST"])
@teacher_required
def add_case():
    title=request.form["title"].strip(); statement=request.form["statement"].strip()
    question=request.form["question"].strip(); deadline=request.form.get("deadline","").strip()
    if title and statement and question:
        db().execute("""INSERT INTO cases(title,statement,question,deadline,created_at)
                        VALUES(?,?,?,?,?)""",
                     (title,statement,question,deadline,datetime.now().strftime("%d/%m/%Y %H:%M"))); db().commit()
    return redirect(url_for("dashboard"))

@app.route("/profesora/documento", methods=["POST"])
@teacher_required
def add_document():
    title=request.form["title"].strip(); desc=request.form.get("description","").strip()
    url=request.form.get("url","").strip()
    if title:
        db().execute("INSERT INTO documents(title,description,url,created_at) VALUES(?,?,?,?)",
                     (title,desc,url,datetime.now().strftime("%d/%m/%Y %H:%M"))); db().commit()
    return redirect(url_for("dashboard"))

@app.route("/profesora/borrar/<kind>/<int:item_id>", methods=["POST"])
@teacher_required
def delete_item(kind,item_id):
    table={"announcement":"announcements","case":"cases","document":"documents"}.get(kind)
    if not table: abort(404)
    db().execute(f"DELETE FROM {table} WHERE id=?", (item_id,)); db().commit()
    return redirect(url_for("dashboard"))

@app.route("/trabajadores/login", methods=["GET","POST"])
def student_login():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if name:
            session["student"]=name
            return redirect(url_for("home"))
        flash("Introduce tu nombre.", "error")
    return render_template("student_login.html")

@app.route("/trabajadores/logout")
def student_logout():
    session.pop("student",None); return redirect(url_for("home"))

@app.route("/caso/<int:case_id>", methods=["GET","POST"])
def case_detail(case_id):
    case=db().execute("SELECT * FROM cases WHERE id=? AND published=1",(case_id,)).fetchone()
    if not case: abort(404)
    name=session.get("student")
    previous=None
    if name:
        previous=db().execute("SELECT * FROM submissions WHERE case_id=? AND student_name=?",(case_id,name)).fetchone()
    if request.method=="POST":
        if not name: return redirect(url_for("student_login"))
        answer=request.form.get("answer","").strip()
        if answer:
            db().execute("""INSERT INTO submissions(case_id,student_name,answer,created_at)
                           VALUES(?,?,?,?)
                           ON CONFLICT(case_id,student_name) DO UPDATE SET answer=excluded.answer, created_at=excluded.created_at""",
                         (case_id,name,answer,datetime.now().strftime("%d/%m/%Y %H:%M")))
            db().commit()
        return redirect(url_for("case_detail",case_id=case_id))
    return render_template("case.html", case=case, previous=previous)

@app.route("/documentos")
def documents():
    docs=db().execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    return render_template("documents.html",docs=docs)

@app.route("/privacidad")
def privacy():
    return render_template("privacy.html")

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
