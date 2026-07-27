#!/usr/bin/env python3
"""Add a subscriber for testing. Run from the project root: python scripts/seed_user.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db.session import get_session, init_db
from src.db.models import User


def seed(email: str, name: str, visa_categories: list[str]) -> None:
    init_db()
    db = get_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.visa_categories = visa_categories
            existing.name = name
            db.commit()
            print(f"Updated existing user: {email}")
        else:
            db.add(User(email=email, name=name, visa_categories=visa_categories))
            db.commit()
            print(f"Created user: {email} | visas: {visa_categories}")
    finally:
        db.close()


if __name__ == "__main__":
    # Edit these values before running
    seed(
        email="you@example.com",
        name="Your Name",
        visa_categories=["H-1B", "H-4"],
    )
