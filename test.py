from cs50 import SQL
from helpers import check_phone

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///powercut_bot.db")
input = check_phone("+94777777777")

phone_exists = db.execute("SELECT * FROM users WHERE phone = ?", input)
print(phone_exists)
