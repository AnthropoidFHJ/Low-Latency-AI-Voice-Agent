import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

class UserDatabase:
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_data TEXT,
                    UNIQUE(phone)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    form_data TEXT,
                    status TEXT DEFAULT 'in_progress',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    def save_user_data(self, name: str, phone: str, job_title: str, session_data: Optional[Dict] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
            existing_user = cursor.fetchone()
            
            session_data_json = json.dumps(session_data) if session_data else None
            
            if existing_user:
                user_id = existing_user[0]
                cursor.execute('''
                    UPDATE users 
                    SET name = ?, job_title = ?, updated_at = CURRENT_TIMESTAMP, session_data = ?
                    WHERE id = ?
                ''', (name, job_title, session_data_json, user_id))
            else:
                cursor.execute('''
                    INSERT INTO users (name, phone, job_title, session_data)
                    VALUES (?, ?, ?, ?)
                ''', (name, phone, job_title, session_data_json))
                user_id = cursor.lastrowid
            
            conn.commit()
            return user_id
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, job_title, created_at, updated_at, session_data
                FROM users WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'job_title': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'session_data': json.loads(row[6]) if row[6] else None
                }
            return None
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, job_title, created_at, updated_at, session_data
                FROM users WHERE phone = ?
            ''', (phone,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'job_title': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'session_data': json.loads(row[6]) if row[6] else None
                }
            return None
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, job_title, created_at, updated_at, session_data
                FROM users 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'job_title': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'session_data': json.loads(row[6]) if row[6] else None
                })
            return users
    
    def search_users(self, search_term: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            search_pattern = f"%{search_term}%"
            cursor.execute('''
                SELECT id, name, phone, job_title, created_at, updated_at, session_data
                FROM users 
                WHERE name LIKE ? OR job_title LIKE ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern))
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'job_title': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'session_data': json.loads(row[6]) if row[6] else None
                })
            return users
    
    def save_form_session(self, session_id: str, form_data: Dict[str, Any], status: str = "in_progress") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            form_data_json = json.dumps(form_data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO form_sessions (session_id, form_data, status)
                VALUES (?, ?, ?)
            ''', (session_id, form_data_json, status))
            
            session_db_id = cursor.lastrowid
            conn.commit()
            return session_db_id
    
    def complete_form_session(self, session_id: str, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE form_sessions 
                SET status = 'completed', user_id = ?, completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (user_id, session_id))
            conn.commit()
    
    def get_user_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    
    def delete_user(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            affected_rows = cursor.rowcount
            conn.commit()
            return affected_rows > 0
    
    def get_recent_users(self, days: int = 7) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, job_title, created_at, updated_at, session_data
                FROM users 
                WHERE created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
            '''.format(days))
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'job_title': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'session_data': json.loads(row[6]) if row[6] else None
                })
            return users

db = UserDatabase()