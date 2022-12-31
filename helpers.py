from phonenumbers import (
    parse,
    PhoneNumberFormat,
    is_valid_number,
    format_number,
    NumberParseException,
)

from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def error_messege(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("error_messege.html", top=code, bottom=escape(message))


def check_phone(phone_no):
    if not phone_no:
        return error_messege("Insert phone number", 400)
    try:
        phone_number = parse(phone_no)
    except NumberParseException:
        return False
    if not is_valid_number(phone_number):
        return False
    return format_number(phone_number, PhoneNumberFormat.E164).strip("+")
