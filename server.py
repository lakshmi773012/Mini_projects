from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "online_exam_secret_key"


def get_db():
    conn = sqlite3.connect("exam.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    count = conn.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    if count == 0:

        questions = [

            (
                "Which language is used for web development?",
                "Python",
                "HTML",
                "C",
                "Java",
                "HTML"
            ),

            (
                "Which keyword is used to define a function in Python?",
                "function",
                "define",
                "def",
                "fun",
                "def"
            ),

            (
                "Which database is used in this project?",
                "MySQL",
                "MongoDB",
                "SQLite",
                "Oracle",
                "SQLite"
            ),

            (
                "Which symbol is used for comments in Python?",
                "//",
                "#",
                "/*",
                "<!--",
                "#"
            ),

            (
                "What does CPU stand for?",
                "Central Processing Unit",
                "Computer Personal Unit",
                "Central Program Unit",
                "Control Processing Unit",
                "Central Processing Unit"
            ),

            (
                "Which language is mainly used for styling web pages?",
                "Python",
                "CSS",
                "Java",
                "SQL",
                "CSS"
            ),

            (
                "Which HTML tag is used to create a paragraph?",
                "<p>",
                "<h1>",
                "<div>",
                "<br>",
                "<p>"
            ),

            (
                "What does SQL stand for?",
                "Structured Query Language",
                "Simple Query Language",
                "System Query Language",
                "Structured Question Language",
                "Structured Query Language"
            ),

            (
                "Which one is a Python framework?",
                "Flask",
                "HTML",
                "CSS",
                "SQL",
                "Flask"
            ),

            (
                "Which keyword is used for a loop in Python?",
                "loop",
                "repeat",
                "for",
                "iterate",
                "for"
            )
        ]

        conn.executemany("""
            INSERT INTO questions
            (question, option1, option2, option3, option4, answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, questions)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():

    if "username" not in session:
        return redirect("/login")

    return render_template(
        "home.html",
        username=session["username"]
    )


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO students
                (name, username, password)
                VALUES (?, ?, ?)
            """, (name, username, password))

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()

            return "Username already exists"

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Admin login
        if username == "admin" and password == "admin123":

            session["admin"] = True

            return redirect("/admin")

        conn = get_db()

        student = conn.execute("""
            SELECT * FROM students
            WHERE username=? AND password=?
        """, (username, password)).fetchone()

        conn.close()

        if student:

            session["username"] = username

            return redirect("/")

        return "Invalid username or password"

    return render_template("login.html")


# ---------------- INSTRUCTIONS ----------------

@app.route("/instructions")
def instructions():

    if "username" not in session:
        return redirect("/login")

    return render_template("instructions.html")


# ---------------- EXAM ----------------

@app.route("/exam", methods=["GET", "POST"])
def exam():

    if "username" not in session:
        return redirect("/login")

    conn = get_db()

    questions = conn.execute(
        "SELECT * FROM questions"
    ).fetchall()

    if request.method == "POST":

        score = 0

        for question in questions:

            selected_answer = request.form.get(
                str(question["id"])
            )

            if selected_answer == question["answer"]:
                score += 1

        total = len(questions)

        percentage = (score / total) * 100

        if percentage >= 50:
            status = "PASS"
        else:
            status = "FAIL"

        conn.execute("""
            INSERT INTO results
            (username, score, total, percentage, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["username"],
            score,
            total,
            percentage,
            status
        ))

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            score=score,
            total=total,
            percentage=round(percentage, 2),
            status=status
        )

    conn.close()

    return render_template(
        "exam.html",
        questions=questions
    )


# ---------------- RESULT HISTORY ----------------

@app.route("/history")
def history():

    if "username" not in session:
        return redirect("/login")

    conn = get_db()

    results = conn.execute("""
        SELECT *
        FROM results
        WHERE username=?
        ORDER BY id DESC
    """, (session["username"],)).fetchall()

    conn.close()

    return render_template(
        "history.html",
        results=results
    )


# ---------------- PERFORMANCE ----------------

@app.route("/performance")
def performance():

    if "username" not in session:
        return redirect("/login")

    conn = get_db()

    results = conn.execute("""
        SELECT *
        FROM results
        WHERE username=?
        ORDER BY id
    """, (session["username"],)).fetchall()

    conn.close()

    if results:

        total_exams = len(results)

        average = sum(
            result["percentage"]
            for result in results
        ) / total_exams

        best = max(
            result["percentage"]
            for result in results
        )

        passed = sum(
            1 for result in results
            if result["status"] == "PASS"
        )

        first_score = results[0]["percentage"]
        latest_score = results[-1]["percentage"]

        improvement = latest_score - first_score

    else:

        total_exams = 0
        average = 0
        best = 0
        passed = 0
        improvement = 0

    return render_template(
        "performance.html",
        total_exams=total_exams,
        average=round(average, 2),
        best=round(best, 2),
        passed=passed,
        improvement=round(improvement, 2)
    )


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    conn = get_db()

    students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    questions = conn.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    results = conn.execute(
        "SELECT COUNT(*) FROM results"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        students=students,
        questions=questions,
        results=results
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":

    create_database()

    app.run(debug=True)