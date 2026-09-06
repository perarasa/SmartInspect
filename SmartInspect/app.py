from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder automatically
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- DATABASE ----------------
def ai_suggest_issue(description):
    text = description.lower()

    if "road" in text or "pothole" in text or "damage" in text:
        return "Road Damage"

    elif "garbage" in text or "waste" in text or "trash" in text:
        return "Garbage"

    elif "streetlight" in text or "street light" in text or "lamp" in text:
        return "Broken Streetlight"

    elif "water" in text or "leakage" in text or "pipe" in text:
        return "Water Leakage"

    else:
        return "Other"
        
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_type TEXT,
            severity TEXT,
            location TEXT,
            description TEXT,
            photo TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():

    username = request.form["username"]
    password = request.form["password"]

    # Inspector login
    if username == "inspector" and password == "1234":
        return redirect(url_for("inspector"))

    # Admin login
    elif username == "admin" and password == "admin123":
        return redirect(url_for("admin"))

    else:
        return "<h2>Invalid Username or Password ❌</h2><a href='/'>Go Back</a>"


# ---------------- INSPECTOR ----------------

@app.route("/inspector")
def inspector():
    return render_template("inspector.html")


# ---------------- SUBMIT INSPECTION ----------------

@app.route("/submit-inspection", methods=["POST"])
def submit_inspection():

    issue_type = request.form["issue_type"]
    severity = request.form["severity"]
    location = request.form["location"]
    description = request.form["description"]

    # Get uploaded photo
    photo = request.files.get("photo")
    photo_filename = ""

    if photo and photo.filename:

        photo_filename = secure_filename(photo.filename)

        photo.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                photo_filename
            )
        )

    # Save inspection into database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO inspections
        (issue_type, severity, location, description, photo, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        issue_type,
        severity,
        location,
        description,
        photo_filename,
        "Pending"
    ))

    conn.commit()
    conn.close()

    return """
        <h2>Inspection Submitted Successfully! ✅</h2>
        <br>
        <a href="/inspector">Back to Inspector Dashboard</a>
        <br><br>
        <a href="/admin">Open Admin Dashboard</a>
    """


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
def admin():

    conn = sqlite3.connect("database.db")

    # Allows item["id"], item["status"], etc.
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM inspections
        ORDER BY id DESC
    """)

    inspections = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        inspections=inspections
    )


# ---------------- DISPLAY UPLOADED PHOTOS ----------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ---------------- UPDATE STATUS ----------------

@app.route("/update-status/<int:inspection_id>", methods=["POST"])
def update_status(inspection_id):

    new_status = request.form["status"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE inspections
        SET status = ?
        WHERE id = ?
    """, (
        new_status,
        inspection_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)