import sqlite3
from datetime import datetime
import pickle

DB_NAME = "coaching_bot.db"

# ------------------------------
# DATABASE INITIALIZATION
# ------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    # Conversations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # RAG context table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rag_context (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        embedding BLOB NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# ------------------------------
# USER OPERATIONS
# ------------------------------
def add_user(username, email, password_hash):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                       (username, email, password_hash))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print("Error:", e)
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


# ------------------------------
# CONVERSATION OPERATIONS
# ------------------------------
def add_conversation(user_id, message, response):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute("INSERT INTO conversations (user_id, message, response, timestamp) VALUES (?, ?, ?, ?)",
                   (user_id, message, response, timestamp))
    conn.commit()
    conn.close()

def get_conversations(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message, response, timestamp FROM conversations WHERE user_id = ? ORDER BY timestamp",
                   (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ------------------------------
# RAG CONTEXT OPERATIONS
# ------------------------------
def add_rag_context(user_id, content, embedding):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    embedding_blob = pickle.dumps(embedding)  # convert embedding to binary
    cursor.execute("INSERT INTO rag_context (user_id, content, embedding, timestamp) VALUES (?, ?, ?, ?)",
                   (user_id, content, embedding_blob, timestamp))
    conn.commit()
    conn.close()

def get_rag_context(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT content, embedding, timestamp FROM rag_context WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    # Unpickle embeddings
    results = [(content, pickle.loads(embedding_blob), timestamp) for content, embedding_blob, timestamp in rows]
    conn.close()
    return results


