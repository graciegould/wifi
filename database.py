import sqlite3
from datetime import datetime

class WiFiSpeedDB:
    def __init__(self, db_path="wifi_speed.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS speed_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                download_speed REAL NOT NULL,
                upload_speed REAL NOT NULL,
                ping REAL NOT NULL,
                server_name TEXT,
                server_location TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plan_speeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_name TEXT NOT NULL,
                download_mbps REAL NOT NULL,
                upload_mbps REAL NOT NULL,
                created_date DATETIME NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_speed_test(self, download_speed, upload_speed, ping, server_name=None, server_location=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO speed_tests (timestamp, download_speed, upload_speed, ping, server_name, server_location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), download_speed, upload_speed, ping, server_name, server_location))
        
        conn.commit()
        conn.close()
    
    def get_recent_tests(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM speed_tests 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def set_plan_speed(self, plan_name, download_mbps, upload_mbps):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE plan_speeds SET is_active = 0')
        
        cursor.execute('''
            INSERT INTO plan_speeds (plan_name, download_mbps, upload_mbps, created_date, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (plan_name, download_mbps, upload_mbps, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_current_plan(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM plan_speeds 
            WHERE is_active = 1 
            ORDER BY created_date DESC 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_speed_test_with_plan_comparison(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                st.*,
                ps.plan_name,
                ps.download_mbps as plan_download,
                ps.upload_mbps as plan_upload,
                ROUND((st.download_speed / ps.download_mbps) * 100, 1) as download_percentage,
                ROUND((st.upload_speed / ps.upload_mbps) * 100, 1) as upload_percentage
            FROM speed_tests st
            LEFT JOIN plan_speeds ps ON ps.is_active = 1
            ORDER BY st.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results