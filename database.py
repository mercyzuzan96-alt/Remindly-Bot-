import sqlite3
import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path="bot_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Reminders table (for scheduled reminders)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_id INTEGER,
                    reminder_time TIMESTAMP,
                    is_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            ''')
            
            conn.commit()
    
    def register_user(self, user_id: int, username: str):
        """Register a new user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, is_active)
                VALUES (?, ?, 1)
            ''', (user_id, username))
            conn.commit()
    
    def add_task(self, user_id: int, description: str) -> int:
        """Add a new task for user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (user_id, description, status)
                VALUES (?, ?, 'pending')
            ''', (user_id, description))
            conn.commit()
            return cursor.lastrowid
    
    def get_pending_tasks(self, user_id: int) -> List[Dict]:
        """Get all pending tasks for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, description, status, created_at
                FROM tasks
                WHERE user_id = ? AND status = 'pending'
                ORDER BY created_at ASC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'description': row[1],
                    'status': row[2],
                    'created_at': row[3]
                }
                for row in rows
            ]
    
    def complete_task(self, task_id: int, user_id: int) -> bool:
        """Mark a task as complete."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND status = 'pending'
            ''', (task_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM tasks
                WHERE id = ? AND user_id = ?
            ''', (task_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_users(self) -> List[Dict]:
        """Get all active users."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username
                FROM users
                WHERE is_active = 1
            ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'user_id': row[0],
                    'username': row[1]
                }
                for row in rows
            ]
    
    def get_all_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """Get all tasks (for admin purposes)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('''
                    SELECT id, user_id, description, status, created_at
                    FROM tasks
                    WHERE status = ?
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT id, user_id, description, status, created_at
                    FROM tasks
                ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'description': row[2],
                    'status': row[3],
                    'created_at': row[4]
                }
                for row in rows
            ]
