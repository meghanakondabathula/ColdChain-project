
import sqlite3
from pathlib import Path
from functools import wraps

from flask import abort
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

AUTH_DB = Path(__file__).resolve().parent / "auth.sqlite"

ROLES = ("ADMIN", "QUALITY_MANAGER", "QUALITY_ANALYST", "VIEWER")


def connect_auth():
    conn = sqlite3.connect(AUTH_DB, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    with connect_auth() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('ADMIN', 'QUALITY_MANAGER',
                             'QUALITY_ANALYST', 'VIEWER')
                ),
                active INTEGER NOT NULL DEFAULT 1
            )
        """)


class User(UserMixin):
    def __init__(self, row):
        self.id = row["user_id"]
        self.username = row["username"]
        self.role = row["role"]
        self.active = bool(row["active"])

    @property
    def is_active(self):
        return self.active


def get_user(user_id):
    with connect_auth() as conn:
        row = conn.execute(
            "SELECT * FROM User WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    return User(row) if row else None


def authenticate(username, password):
    with connect_auth() as conn:
        row = conn.execute(
            "SELECT * FROM User WHERE username = ?",
            (username,)
        ).fetchone()

    if row and row["active"] and check_password_hash(
        row["password_hash"], password
    ):
        return User(row)

    return None


def create_user(username, password, role):
    username = username.strip()

    if not username or len(username) > 50:
        raise ValueError("Username must be 1-50 characters")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters")

    if role not in ROLES:
        raise ValueError("Invalid role")

    with connect_auth() as conn:
        try:
            cursor = conn.execute("""
                INSERT INTO User (username, password_hash, role)
                VALUES (?, ?, ?)
            """, (
                username,
                generate_password_hash(password),
                role
            ))
        except sqlite3.IntegrityError:
            raise ValueError("Username already exists")

        return cursor.lastrowid


def list_users():
    with connect_auth() as conn:
        rows = conn.execute("""
            SELECT user_id, username, role, active
            FROM User
            ORDER BY user_id
        """).fetchall()

    return [dict(row) for row in rows]


def roles_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            if current_user.role not in allowed_roles:
                abort(403)

            return func(*args, **kwargs)

        return wrapper
    return decorator
