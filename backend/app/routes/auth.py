"""
auth.py — Authentication & User Profile API
JWT-based auth with SQLite for lightweight persistence.
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List

import jwt
import bcrypt

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# ── Configuration ─────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", "dermai-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BACKEND_DIR, "dermai.db")


# ── Database Setup ────────────────────────────────────
def get_db():
    """Get SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            skin_type TEXT DEFAULT 'normal',
            age INTEGER DEFAULT 25,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analysis_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            condition TEXT NOT NULL,
            confidence REAL NOT NULL,
            risk_level TEXT NOT NULL,
            category TEXT DEFAULT '',
            top3_json TEXT DEFAULT '[]',
            gradcam_available INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS progress_entries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            condition TEXT DEFAULT '',
            confidence REAL DEFAULT 0,
            risk_level TEXT DEFAULT '',
            image_hash TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_analysis_user ON analysis_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_progress_user ON progress_entries(user_id);
    """)
    conn.commit()
    conn.close()


# Initialize DB on module import
try:
    init_db()
    print("[OK] SQLite database initialized")
except Exception as e:
    print(f"[WARN] Database initialization failed: {e}")


# ── Models ────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = ""
    skin_type: Optional[str] = "normal"
    age: Optional[int] = 25


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    skin_type: Optional[str] = None
    age: Optional[int] = None


class ProgressEntry(BaseModel):
    title: str = ""
    notes: str = ""
    condition: str = ""
    confidence: float = 0
    risk_level: str = ""


# ── Token Helpers ─────────────────────────────────────
def create_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Auth Routes ───────────────────────────────────────
@router.post("/register")
async def register(data: RegisterRequest):
    """Register a new user."""
    conn = get_db()
    try:
        # Check if email already exists
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (data.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        existing_user = conn.execute("SELECT id FROM users WHERE username = ?", (data.username,)).fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")

        # Hash password
        password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "INSERT INTO users (id, email, username, password_hash, full_name, skin_type, age, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, data.email, data.username, password_hash, data.full_name, data.skin_type, data.age, now, now)
        )
        conn.commit()

        token = create_token(user_id, data.username)

        return {
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user_id,
                "email": data.email,
                "username": data.username,
                "full_name": data.full_name,
                "skin_type": data.skin_type,
                "age": data.age,
            }
        }
    finally:
        conn.close()


@router.post("/login")
async def login(data: LoginRequest):
    """Login with email and password."""
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (data.email,)
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not bcrypt.checkpw(data.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_token(user['id'], user['username'])

        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user['username'],
                "full_name": user['full_name'],
                "skin_type": user['skin_type'],
                "age": user['age'],
            }
        }
    finally:
        conn.close()


@router.get("/profile")
async def get_profile(payload: dict = Depends(verify_token)):
    """Get current user profile."""
    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (payload['sub'],)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user['id'],
            "email": user['email'],
            "username": user['username'],
            "full_name": user['full_name'],
            "skin_type": user['skin_type'],
            "age": user['age'],
            "created_at": user['created_at'],
        }
    finally:
        conn.close()


@router.put("/profile")
async def update_profile(data: ProfileUpdate, payload: dict = Depends(verify_token)):
    """Update user profile."""
    conn = get_db()
    try:
        updates = []
        params = []
        if data.full_name is not None:
            updates.append("full_name = ?")
            params.append(data.full_name)
        if data.skin_type is not None:
            updates.append("skin_type = ?")
            params.append(data.skin_type)
        if data.age is not None:
            updates.append("age = ?")
            params.append(data.age)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(payload['sub'])

        conn.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

        return {"message": "Profile updated successfully"}
    finally:
        conn.close()


# ── Progress Tracker Routes ───────────────────────────
@router.post("/progress")
async def add_progress_entry(entry: ProgressEntry, payload: dict = Depends(verify_token)):
    """Add a progress tracking entry."""
    conn = get_db()
    try:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "INSERT INTO progress_entries (id, user_id, title, notes, condition, confidence, risk_level, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry_id, payload['sub'], entry.title, entry.notes, entry.condition, entry.confidence, entry.risk_level, now)
        )
        conn.commit()

        return {"message": "Progress entry added", "id": entry_id}
    finally:
        conn.close()


@router.get("/progress")
async def get_progress(payload: dict = Depends(verify_token)):
    """Get all progress entries for the authenticated user."""
    conn = get_db()
    try:
        entries = conn.execute(
            "SELECT * FROM progress_entries WHERE user_id = ? ORDER BY created_at DESC",
            (payload['sub'],)
        ).fetchall()

        return {
            "entries": [dict(e) for e in entries],
            "total": len(entries),
        }
    finally:
        conn.close()


@router.delete("/progress/{entry_id}")
async def delete_progress_entry(entry_id: str, payload: dict = Depends(verify_token)):
    """Delete a progress entry."""
    conn = get_db()
    try:
        result = conn.execute(
            "DELETE FROM progress_entries WHERE id = ? AND user_id = ?",
            (entry_id, payload['sub'])
        )
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")

        return {"message": "Entry deleted"}
    finally:
        conn.close()
