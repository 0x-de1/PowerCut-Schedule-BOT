from flask import Flask, redirect, render_template, request, session, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from cs50 import SQL

import os
from helpers import error_messege, login_required, check_phone

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///powercut_bot.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        session.clear()
        email = request.form.get("email")
        password = request.form.get("password")
        # Ensure email was submitted
        if not email:
            return error_messege("must provide email", 403)

        # Ensure password was submitted
        elif not password:
            return error_messege("must provide password", 403)

        # Query database for email
        rows = db.execute("SELECT * FROM users WHERE email = ?", email.strip().lower())
        print(rows, email)
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password.strip()):
            return render_template("login.html", invalid_login=True, before_login=True)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        return redirect("/")
    return render_template("login.html", before_login=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    field_answers = {
        "invalid_phone": False,
        "invalid_ceb": False,
        "invalid_email": False,
        "invalid_password": False,
        "invalid_confirmation": False,
    }
    if request.method == "POST":
        phone = check_phone(request.form.get("phone"))
        ceb = request.form.get("ceb_account")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not phone:
            return error_messege(
                "Insert a valid phone number with '+ country code'. eg: +94 333 542 432",
                400,
            )
        elif not ceb:
            return error_messege("Insert CEB account number", 400)
        elif not email:
            return error_messege("Insert email", 400)
        elif not password:
            return error_messege("Insert user password", 400)
        elif not confirmation:
            return error_messege("Insert Confirmation", 400)
        elif password != confirmation:
            # return error_messege("Password confrmation does not match", 400)
            field_answers["invalid_confirmation"] = True
        email_exists = db.execute("SELECT * FROM users WHERE email = ? ", email)

        phone_exists = db.execute("SELECT * FROM users WHERE phone = ? ", phone)

        if email_exists:
            field_answers["invalid_email"] = True
        elif phone_exists:
            field_answers["invalid_phone"] = True
        else:
            db.execute(
                "INSERT INTO users (phone,ceb_account,email,hash) VALUES (?,?,?,?)",
                phone,
                ceb.lower(),
                email.lower(),
                generate_password_hash(password),
            )
            # Add account to account list if it is a unique account
            if not db.execute("SELECT * FROM users WHERE ceb_account = ? ", ceb):
                db.execute("INSERT INTO accounts (ceb_account) VALUES (?)", ceb)
            session["account created"] = True
            flash(f"Account was successfully created for {email}")
            return redirect("/login")

    return render_template(
        "register.html", field_answers=field_answers, before_login=True
    )


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/help")
def help():
    return render_template("help.html")


# if not logged in, @login_required will redirect to login page
@app.route("/")
@login_required
def index():
    # Query database for email
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    return render_template(
        "index.html",
        email=rows[0]["email"],
        ceb=rows[0]["ceb_account"],
        phone=rows[0]["phone"],
    )


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    field_answers = {
        "invalid_phone": False,
        "invalid_ceb": False,
        "invalid_email": False,
        "invalid_password": False,
        "invalid_confirmation": False,
    }
    if request.method == "POST":
        # get updated fields
        edited = request.form.getlist("edited")
        inputs = {}
        #  Validate entered inputs
        for item in edited:
            input = request.form.get(item)
            if not input:
                return error_messege(f"Insert {item}", 400)
            elif item == "phone":
                input = check_phone(input)
                if not input:
                    return error_messege(
                        "Insert a valid phone number with '+ country code'. eg: +94 333 542 432",
                        400,
                    )
                phone_exists = db.execute(
                    "SELECT * FROM users WHERE ? = ? ", item, input
                )
                if phone_exists:
                    return error_messege(f"Entered {item} already exists", 400)

            elif item == "password":
                confirmation = request.form.get("confirmation")
                if not confirmation:
                    return error_messege("Insert password confirmation", 400)
                elif input != confirmation:
                    return error_messege("Password confrmation does not match", 400)
                item = "hash"
                input = generate_password_hash(input)

            elif item == "email":
                input_exists = db.execute(
                    "SELECT * FROM users WHERE ? = ? ", item, input
                )
                if input_exists:
                    return error_messege(
                        f"Entered email already exists. Enter another email", 400
                    )

            inputs.update({item: input.strip()})
        # Update all new fields
        for item in inputs.keys():
            db.execute(
                f"UPDATE users SET ? = ? WHERE id = ?",
                item,
                inputs[item],
                session["user_id"],
            )

            session["account created"] = True
            flash(f"Account details was successfully updated!")
            return redirect("/")
    # Query database for email
    rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    return render_template(
        "settings.html",
        email=rows[0]["email"],
        ceb=rows[0]["ceb_account"],
        phone=rows[0]["phone"],
        field_answers=field_answers,
    )


if __name__ == "__main__":
    # If you are debugging you can do that in the browser:
    app.run(debug=True)
