"""
create_admin.py

Run this script from the terminal to create an administrator account
for the Room Rental System.

Usage:
python create_admin.py
"""

import getpass
import re
from app import create_app
from extensions import db
from models import User

GMAIL_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@gmail\.com$")


def main():
    app = create_app()

    with app.app_context():

        print("=== Create Admin Account ===")

        full_name = input("Full name: ").strip()

        email = input("Email (must be a Gmail address): ").strip()
        while not GMAIL_REGEX.match(email):
            print("Invalid email. Please enter a valid Gmail address (e.g. admin@gmail.com).")
            email = input("Email (must be a Gmail address): ").strip()

        username = input("Username: ").strip()

        while User.query.filter_by(username=username).first():
            print("That username is already taken.")
            username = input("Username: ").strip()

        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")

        while password != confirm or len(password) < 6:
            if password != confirm:
                print("Passwords do not match. Try again.")
            else:
                print("Password must be at least 6 characters.")

            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm password: ")

        admin = User(
            role="admin",
            full_name=full_name,
            email=email,
            username=username,
            status="approved",
        )

        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print(f"\nAdmin account '{username}' created successfully.")
        print("You can now log in from the website's login page.")


if __name__ == "__main__":
    main()