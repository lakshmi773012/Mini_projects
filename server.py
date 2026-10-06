# ---------------------------------------------------------
# SMART COLLEGE COMPLAINT & PRIORITY MANAGEMENT SYSTEM
# ---------------------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


# ---------------------------------------------------------
# FLASK APPLICATION
# ---------------------------------------------------------

app = Flask(__name__)

app.secret_key = "smart_complaint_secret_key"


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db_connection():

    connection = sqlite3.connect("complaints.db")

    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------------
# CREATE DATABASE TABLES
# ---------------------------------------------------------

def create_database():

    connection = get_db_connection()

    cursor = connection.cursor()


    # Student table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL
        )
    """)


    # Complaint table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)


    # Staff table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            category TEXT UNIQUE NOT NULL
        )
    """)


    # -----------------------------------------------------
    # DEFAULT RESPONSIBLE STAFF
    # -----------------------------------------------------

    staff_data = [

        (
            "Ravi Kumar",
            "Plumber",
            "9876543210",
            "plumber@ists.ac.in",
            "Water"
        ),

        (
            "Suresh Kumar",
            "Electrician",
            "9876543211",
            "electrician@ists.ac.in",
            "Electricity"
        ),

        (
            "Network Support Team",
            "Network Technician",
            "9876543212",
            "network@ists.ac.in",
            "Internet"
        ),

        (
            "Cleaning Supervisor",
            "Cleaning Supervisor",
            "9876543213",
            "cleaning@ists.ac.in",
            "Cleanliness"
        ),

        (
            "Security Officer",
            "Security Officer",
            "9876543214",
            "security@ists.ac.in",
            "Security"
        ),

        (
            "Transport Coordinator",
            "Transport Coordinator",
            "9876543215",
            "transport@ists.ac.in",
            "Transport"
        ),

        (
            "Hostel Warden",
            "Hostel Warden",
            "9876543216",
            "hostel@ists.ac.in",
            "Hostel"
        ),

        (
            "Canteen Supervisor",
            "Canteen Supervisor",
            "9876543217",
            "canteen@ists.ac.in",
            "Canteen"
        ),

        (
            "Maintenance Technician",
            "Maintenance Technician",
            "9876543218",
            "maintenance@ists.ac.in",
            "Classroom"
        ),

        (
            "Academic Coordinator",
            "Academic Coordinator",
            "9876543219",
            "academic@ists.ac.in",
            "Academic"
        ),

        (
            "Administration Office",
            "Administrative Staff",
            "9876543220",
            "adminoffice@ists.ac.in",
            "Other"
        )
    ]


    # Add staff only if category does not already exist
    for staff in staff_data:

        cursor.execute("""
            INSERT OR IGNORE INTO staff
            (name, role, phone, email, category)
            VALUES (?, ?, ?, ?, ?)
        """, staff)


    connection.commit()

    connection.close()


# ---------------------------------------------------------
# AUTOMATIC PRIORITY DETECTION
# ---------------------------------------------------------

def detect_priority(title, description):

    text = (title + " " + description).lower()


    critical_words = [
        "fire",
        "accident",
        "emergency",
        "danger",
        "electric shock",
        "short circuit",
        "gas leak",
        "serious injury",
        "life threatening"
    ]


    for word in critical_words:

        if word in text:

            return "Critical"


    high_words = [
        "no water",
        "water problem",
        "no electricity",
        "power cut",
        "security problem",
        "unsafe",
        "broken",
        "leakage",
        "not working",
        "urgent"
    ]


    for word in high_words:

        if word in text:

            return "High"


    medium_words = [
        "cleaning",
        "cleanliness",
        "maintenance",
        "wifi",
        "internet",
        "fan",
        "light",
        "classroom",
        "bench",
        "desk"
    ]


    for word in medium_words:

        if word in text:

            return "Medium"


    return "Low"


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# ---------------------------------------------------------
# STUDENT REGISTRATION
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        department = request.form["department"]


        if not name or not email or not password or not department:

            flash("Please fill all the fields.")

            return redirect(url_for("register"))


        connection = get_db_connection()


        existing_student = connection.execute(
            "SELECT * FROM students WHERE email = ?",
            (email,)
        ).fetchone()


        if existing_student:

            connection.close()

            flash("Email already registered. Please use another email.")

            return redirect(url_for("register"))


        hashed_password = generate_password_hash(password)


        connection.execute("""
            INSERT INTO students
            (name, email, password, department)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            department
        ))


        connection.commit()

        connection.close()


        flash("Registration successful! You can now login.")

        return redirect(url_for("login"))


    return render_template("register.html")


# ---------------------------------------------------------
# STUDENT LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        connection = get_db_connection()


        student = connection.execute(
            "SELECT * FROM students WHERE email = ?",
            (email,)
        ).fetchone()


        connection.close()


        if student:

            if check_password_hash(student["password"], password):

                session["student_id"] = student["id"]

                session["student_name"] = student["name"]

                session["student_email"] = student["email"]

                return redirect(url_for("dashboard"))


        flash("Invalid email or password.")

        return redirect(url_for("login"))


    return render_template("login.html")


# ---------------------------------------------------------
# STUDENT DASHBOARD
# ---------------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        flash("Please login first.")

        return redirect(url_for("login"))


    student_id = session["student_id"]


    connection = get_db_connection()


    complaints = connection.execute("""
        SELECT *
        FROM complaints
        WHERE student_id = ?
        ORDER BY created_at DESC
    """, (student_id,)).fetchall()


    total_complaints = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
    """, (student_id,)).fetchone()[0]


    critical_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND priority = 'Critical'
    """, (student_id,)).fetchone()[0]


    high_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND priority = 'High'
    """, (student_id,)).fetchone()[0]


    medium_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND priority = 'Medium'
    """, (student_id,)).fetchone()[0]


    low_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND priority = 'Low'
    """, (student_id,)).fetchone()[0]


    connection.close()


    return render_template(
        "dashboard.html",
        complaints=complaints,
        total_complaints=total_complaints,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count
    )


# ---------------------------------------------------------
# SUBMIT COMPLAINT
# ---------------------------------------------------------

@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if "student_id" not in session:

        flash("Please login first.")

        return redirect(url_for("login"))


    if request.method == "POST":

        title = request.form["title"]

        description = request.form["description"]

        category = request.form["category"]

        location = request.form["location"]


        if not title or not description or not category or not location:

            flash("Please fill all complaint fields.")

            return redirect(url_for("complaint"))


        # Automatically detect priority
        priority = detect_priority(title, description)


        # New complaint starts as Pending
        status = "Pending"


        connection = get_db_connection()


        connection.execute("""
            INSERT INTO complaints
            (
                student_id,
                title,
                description,
                category,
                location,
                priority,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["student_id"],
            title,
            description,
            category,
            location,
            priority,
            status
        ))


        connection.commit()

        connection.close()


        flash(
            f"Complaint submitted successfully! Priority detected: {priority}"
        )


        return redirect(url_for("dashboard"))


    return render_template("complaint.html")


# ---------------------------------------------------------
# ADMIN LOGIN
# ---------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        admin_email = "admin@ists.ac.in"

        admin_password = "admin123"


        if email == admin_email and password == admin_password:

            session["admin_logged_in"] = True

            return redirect(url_for("admin_dashboard"))


        flash("Invalid admin email or password.")

        return redirect(url_for("admin_login"))


    return render_template("admin_login.html")


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_logged_in" not in session:

        flash("Please login as admin.")

        return redirect(url_for("admin_login"))


    connection = get_db_connection()


    # Get all complaints and responsible staff
    complaints = connection.execute("""
        SELECT
            complaints.id,
            complaints.title,
            complaints.description,
            complaints.category,
            complaints.location,
            complaints.priority,
            complaints.status,
            complaints.created_at,

            students.name,
            students.email,
            students.department,

            staff.name AS staff_name,
            staff.role AS staff_role,
            staff.phone AS staff_phone,
            staff.email AS staff_email

        FROM complaints

        JOIN students
        ON complaints.student_id = students.id

        LEFT JOIN staff
        ON complaints.category = staff.category

        ORDER BY
            CASE complaints.priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
            END,

            complaints.created_at DESC

    """).fetchall()


    # -----------------------------------------------------
    # COMPLAINT STATISTICS
    # -----------------------------------------------------

    total_complaints = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
    """).fetchone()[0]


    critical_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority = 'Critical'
    """).fetchone()[0]


    high_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority = 'High'
    """).fetchone()[0]


    medium_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority = 'Medium'
    """).fetchone()[0]


    low_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE priority = 'Low'
    """).fetchone()[0]


    pending_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Pending'
    """).fetchone()[0]


    progress_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'In Progress'
    """).fetchone()[0]


    resolved_count = connection.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'Resolved'
    """).fetchone()[0]


    connection.close()


    return render_template(
        "admin_dashboard.html",

        complaints=complaints,

        total_complaints=total_complaints,

        critical_count=critical_count,

        high_count=high_count,

        medium_count=medium_count,

        low_count=low_count,

        pending_count=pending_count,

        progress_count=progress_count,

        resolved_count=resolved_count
    )


# ---------------------------------------------------------
# UPDATE COMPLAINT STATUS
# ---------------------------------------------------------

@app.route("/admin/update_status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):

    if "admin_logged_in" not in session:

        flash("Please login as admin.")

        return redirect(url_for("admin_login"))


    status = request.form["status"]


    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]


    if status not in allowed_statuses:

        flash("Invalid status.")

        return redirect(url_for("admin_dashboard"))


    connection = get_db_connection()


    connection.execute("""
        UPDATE complaints

        SET status = ?

        WHERE id = ?
    """, (
        status,
        complaint_id
    ))


    connection.commit()

    connection.close()


    flash("Complaint status updated successfully.")

    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------
# STUDENT LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.pop("student_id", None)

    session.pop("student_name", None)

    session.pop("student_email", None)


    flash("You have been logged out.")

    return redirect(url_for("login"))


# ---------------------------------------------------------
# ADMIN LOGOUT
# ---------------------------------------------------------

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)


    flash("Admin logged out successfully.")

    return redirect(url_for("admin_login"))


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)