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
                server_location TEXT,
                device_count INTEGER
            )
        ''')
        
        cursor.execute("PRAGMA table_info(speed_tests)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'device_count' not in columns:
            cursor.execute('ALTER TABLE speed_tests ADD COLUMN device_count INTEGER')
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                day DATE PRIMARY KEY,
                sample_count INTEGER NOT NULL,
                median_download_mbps REAL NOT NULL,
                median_upload_mbps REAL NOT NULL,
                p95_ping_ms REAL NOT NULL,
                pct_bad REAL NOT NULL,
                avg_device_count REAL,
                status TEXT CHECK(status IN ('good', 'meh', 'bad', 'no_data')),
                created_at DATETIME NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_summary (
                week_start DATE PRIMARY KEY,
                week_end DATE NOT NULL,
                days_with_data INTEGER NOT NULL,
                total_samples INTEGER NOT NULL,
                avg_download_mbps REAL NOT NULL,
                avg_upload_mbps REAL NOT NULL,
                avg_ping_ms REAL NOT NULL,
                weekly_pct_bad REAL NOT NULL,
                good_days INTEGER DEFAULT 0,
                meh_days INTEGER DEFAULT 0,
                bad_days INTEGER DEFAULT 0,
                no_data_days INTEGER DEFAULT 0,
                status TEXT CHECK(status IN ('excellent', 'good', 'poor', 'bad')),
                created_at DATETIME NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_speed_test(self, download_speed, upload_speed, ping, server_name=None, server_location=None, device_count=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO speed_tests (timestamp, download_speed, upload_speed, ping, server_name, server_location, device_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), download_speed, upload_speed, ping, server_name, server_location, device_count))
        
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
    
    def get_daily_data(self, target_date):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                download_speed, 
                upload_speed, 
                ping, 
                device_count
            FROM speed_tests 
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp
        ''', (target_date,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def insert_daily_summary(self, day, sample_count, median_download, median_upload, 
                           p95_ping, pct_bad, avg_device_count, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_summary 
            (day, sample_count, median_download_mbps, median_upload_mbps, 
             p95_ping_ms, pct_bad, avg_device_count, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (day, sample_count, median_download, median_upload, p95_ping, 
              pct_bad, avg_device_count, status, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_daily_summaries(self, limit=30):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_summary 
            ORDER BY day DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def update_today_summary(self):
        """
        Update today's daily summary with current data.
        Called after each speed test to keep running summary current.
        """
        from datetime import date
        today = date.today().isoformat()
        
        # Get today's data
        daily_data = self.get_daily_data(today)
        if not daily_data:
            return False
        
        # Get current plan
        plan = self.get_current_plan()
        plan_download = plan[2] if plan else None
        plan_upload = plan[3] if plan else None
        
        # Calculate metrics
        downloads = [row[0] for row in daily_data if row[0] is not None]
        uploads = [row[1] for row in daily_data if row[1] is not None]
        pings = [row[2] for row in daily_data if row[2] is not None]
        device_counts = [row[3] for row in daily_data if row[3] is not None]
        
        if not downloads or not uploads or not pings:
            return False
        
        # Calculate summary metrics
        import statistics
        median_download = statistics.median(downloads)
        median_upload = statistics.median(uploads)
        p95_ping = self._calculate_percentile(pings, 95)
        avg_device_count = statistics.mean(device_counts) if device_counts else None
        
        # Calculate bad samples percentage
        bad_samples = 0
        ping_threshold = 50  # Default threshold
        
        for download, upload, ping, _ in daily_data:
            if self._is_bad_sample(download, upload, ping, plan_download, plan_upload, ping_threshold):
                bad_samples += 1
        
        pct_bad = (bad_samples / len(daily_data)) * 100
        status = self._get_daily_status(pct_bad)
        
        # Update summary
        self.insert_daily_summary(
            day=today,
            sample_count=len(daily_data),
            median_download=median_download,
            median_upload=median_upload,
            p95_ping=p95_ping,
            pct_bad=pct_bad,
            avg_device_count=avg_device_count,
            status=status
        )
        
        return True
    
    def create_placeholder_entries(self, days_back=3):
        """
        Create placeholder entries for missed days (computer was off).
        Only creates entries for days that are completely missing.
        """
        from datetime import date, timedelta
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing summary days
        cursor.execute('SELECT day FROM daily_summary WHERE day >= ?', 
                      ((date.today() - timedelta(days=days_back)).isoformat(),))
        existing_days = set(row[0] for row in cursor.fetchall())
        
        # Check each day and create placeholder if missing
        for i in range(1, days_back + 1):
            check_date = date.today() - timedelta(days=i)
            date_str = check_date.isoformat()
            
            if date_str not in existing_days:
                # Check if there's any speed test data for this day
                cursor.execute('SELECT COUNT(*) FROM speed_tests WHERE DATE(timestamp) = ?', (date_str,))
                data_count = cursor.fetchone()[0]
                
                if data_count == 0:
                    # No data for this day, create placeholder
                    cursor.execute('''
                        INSERT OR IGNORE INTO daily_summary 
                        (day, sample_count, median_download_mbps, median_upload_mbps, 
                         p95_ping_ms, pct_bad, avg_device_count, status, created_at)
                        VALUES (?, 0, 0, 0, 0, 0, NULL, 'no_data', ?)
                    ''', (date_str, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def _is_bad_sample(self, download, upload, ping, plan_download, plan_upload, ping_threshold=50):
        """Helper method for bad sample detection"""
        if plan_download and download < (plan_download * 0.7):
            return True
        if plan_upload and upload < (plan_upload * 0.7):
            return True
        if ping > ping_threshold:
            return True
        return False
    
    def _get_daily_status(self, pct_bad):
        """Helper method for status calculation"""
        if pct_bad < 10:
            return 'good'
        elif pct_bad <= 30:
            return 'meh'
        else:
            return 'bad'
    
    def _calculate_percentile(self, data, percentile):
        """Helper method for percentile calculation"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        index = (percentile / 100.0) * (n - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def set_config(self, key, value):
        """Store configuration value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create config table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME NOT NULL
            )
        ''')
        
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_config(self, key, default=None):
        """Retrieve configuration value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        except:
            return default
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_to_keep=30):
        """
        Clean up old speed test data to prevent database bloat.
        Keeps daily summaries but removes detailed speed tests older than specified days.
        """
        from datetime import date, timedelta
        
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count records before cleanup
        cursor.execute('SELECT COUNT(*) FROM speed_tests WHERE DATE(timestamp) < ?', (cutoff_date.isoformat(),))
        old_count = cursor.fetchone()[0]
        
        if old_count == 0:
            conn.close()
            return 0, 0
        
        # Delete old speed test records (keep daily summaries)
        cursor.execute('DELETE FROM speed_tests WHERE DATE(timestamp) < ?', (cutoff_date.isoformat(),))
        
        # Get database size before and after
        cursor.execute('PRAGMA page_count')
        page_count = cursor.fetchone()[0]
        cursor.execute('PRAGMA page_size') 
        page_size = cursor.fetchone()[0]
        
        # Vacuum to reclaim space
        cursor.execute('VACUUM')
        
        conn.commit()
        conn.close()
        
        return old_count, (page_count * page_size) // 1024  # KB
    
    def get_database_stats(self):
        """Get database storage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Speed tests count
        cursor.execute('SELECT COUNT(*) FROM speed_tests')
        stats['speed_tests_count'] = cursor.fetchone()[0]
        
        # Daily summaries count  
        cursor.execute('SELECT COUNT(*) FROM daily_summary')
        stats['daily_summaries_count'] = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)) FROM speed_tests')
        result = cursor.fetchone()
        stats['date_range'] = result if result[0] else (None, None)
        
        # Database size
        cursor.execute('PRAGMA page_count')
        page_count = cursor.fetchone()[0]
        cursor.execute('PRAGMA page_size')
        page_size = cursor.fetchone()[0]
        stats['db_size_kb'] = (page_count * page_size) // 1024
        
        conn.close()
        return stats
    
    def archive_old_data(self, days_to_keep=90, archive_to_summaries=True):
        """
        Archive old data by converting detailed records to aggregated summaries.
        More sophisticated than simple deletion.
        """
        from datetime import date, timedelta
        
        archive_cutoff = date.today() - timedelta(days=days_to_keep)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find days with speed tests but no daily summary
        cursor.execute('''
            SELECT DATE(timestamp) as test_date
            FROM speed_tests 
            WHERE DATE(timestamp) < ?
            AND DATE(timestamp) NOT IN (SELECT day FROM daily_summary)
            GROUP BY DATE(timestamp)
        ''', (archive_cutoff.isoformat(),))
        
        missing_summary_dates = [row[0] for row in cursor.fetchall()]
        
        # Create summaries for missing dates before archiving
        archived_count = 0
        for date_str in missing_summary_dates:
            daily_data = self.get_daily_data(date_str)
            if daily_data:
                # Calculate summary metrics quickly
                downloads = [row[0] for row in daily_data if row[0]]
                uploads = [row[1] for row in daily_data if row[1]]
                pings = [row[2] for row in daily_data if row[2]]
                
                if downloads and uploads and pings:
                    import statistics
                    median_download = statistics.median(downloads)
                    median_upload = statistics.median(uploads)
                    p95_ping = self._calculate_percentile(pings, 95)
                    
                    # Simple bad percentage calculation
                    plan = self.get_current_plan()
                    bad_count = 0
                    if plan:
                        for d, u, p, _ in daily_data:
                            if (d < plan[2] * 0.7) or (u < plan[3] * 0.7) or (p > 50):
                                bad_count += 1
                    
                    pct_bad = (bad_count / len(daily_data)) * 100
                    status = 'good' if pct_bad < 10 else 'meh' if pct_bad <= 30 else 'bad'
                    
                    # Insert summary
                    cursor.execute('''
                        INSERT OR IGNORE INTO daily_summary 
                        (day, sample_count, median_download_mbps, median_upload_mbps, 
                         p95_ping_ms, pct_bad, avg_device_count, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    ''', (date_str, len(daily_data), median_download, median_upload, 
                          p95_ping, pct_bad, status, datetime.now()))
                    
                    archived_count += len(daily_data)
        
        # Now delete the archived speed test records
        cursor.execute('DELETE FROM speed_tests WHERE DATE(timestamp) < ?', (archive_cutoff.isoformat(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count, len(missing_summary_dates)
    
    def set_retention_policy(self, speed_tests_days=30, summaries_days=365):
        """Set data retention policies"""
        self.set_config('retention_speed_tests_days', str(speed_tests_days))
        self.set_config('retention_summaries_days', str(summaries_days))
    
    def get_retention_policy(self):
        """Get current retention policies"""
        speed_tests_days = int(self.get_config('retention_speed_tests_days', '30'))
        summaries_days = int(self.get_config('retention_summaries_days', '365'))
        return speed_tests_days, summaries_days
    
    def get_week_start_end(self, date_obj):
        """Get Sunday-to-Sunday week boundaries for a given date"""
        from datetime import timedelta
        
        # Find the Sunday of this week (0=Monday, 6=Sunday)
        days_since_sunday = (date_obj.weekday() + 1) % 7
        week_start = date_obj - timedelta(days=days_since_sunday)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    
    def create_weekly_summary(self, week_start_date):
        """Create weekly summary from daily summaries for a given week"""
        from datetime import timedelta
        
        week_start, week_end = self.get_week_start_end(week_start_date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all daily summaries for this week
        cursor.execute('''
            SELECT day, sample_count, median_download_mbps, median_upload_mbps, 
                   p95_ping_ms, pct_bad, status
            FROM daily_summary 
            WHERE day >= ? AND day <= ?
            ORDER BY day
        ''', (week_start.isoformat(), week_end.isoformat()))
        
        daily_data = cursor.fetchall()
        
        if not daily_data:
            conn.close()
            return False
        
        # Calculate weekly aggregates
        total_samples = sum(row[1] for row in daily_data)
        days_with_data = len([row for row in daily_data if row[1] > 0])
        
        # Weighted averages (by sample count)
        if total_samples > 0:
            weighted_download = sum(row[2] * row[1] for row in daily_data if row[1] > 0) / total_samples
            weighted_upload = sum(row[3] * row[1] for row in daily_data if row[1] > 0) / total_samples
            weighted_ping = sum(row[4] * row[1] for row in daily_data if row[1] > 0) / total_samples
            weighted_pct_bad = sum(row[5] * row[1] for row in daily_data if row[1] > 0) / total_samples
        else:
            weighted_download = weighted_upload = weighted_ping = weighted_pct_bad = 0
        
        # Count days by status
        status_counts = {'good': 0, 'meh': 0, 'bad': 0, 'no_data': 0}
        for row in daily_data:
            status = row[6] if row[6] in status_counts else 'no_data'
            status_counts[status] += 1
        
        # Determine weekly status
        if days_with_data == 0:
            weekly_status = 'bad'
        elif status_counts['good'] >= 5:  # 5+ good days
            weekly_status = 'excellent'
        elif status_counts['good'] + status_counts['meh'] >= 5:  # 5+ okay days
            weekly_status = 'good'
        elif status_counts['good'] + status_counts['meh'] >= 3:  # 3+ okay days
            weekly_status = 'poor'
        else:
            weekly_status = 'bad'
        
        # Insert or replace weekly summary
        cursor.execute('''
            INSERT OR REPLACE INTO weekly_summary 
            (week_start, week_end, days_with_data, total_samples, 
             avg_download_mbps, avg_upload_mbps, avg_ping_ms, weekly_pct_bad,
             good_days, meh_days, bad_days, no_data_days, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (week_start.isoformat(), week_end.isoformat(), days_with_data, total_samples,
              weighted_download, weighted_upload, weighted_ping, weighted_pct_bad,
              status_counts['good'], status_counts['meh'], 
              status_counts['bad'], status_counts['no_data'],
              weekly_status, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return True
    
    def archive_daily_to_weekly(self, weeks_to_keep=4):
        """Archive old daily summaries to weekly summaries"""
        from datetime import date, timedelta
        
        # Find completed weeks (Sunday to Sunday) older than weeks_to_keep
        today = date.today()
        cutoff_date = today - timedelta(weeks=weeks_to_keep)
        
        # Find the Sunday before cutoff_date
        cutoff_week_start, _ = self.get_week_start_end(cutoff_date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all daily summaries older than cutoff that aren't archived to weekly yet
        cursor.execute('''
            SELECT DISTINCT DATE(day, 'weekday 0', '-6 days') as week_start
            FROM daily_summary 
            WHERE day <= ? 
            AND DATE(day, 'weekday 0', '-6 days') NOT IN (SELECT week_start FROM weekly_summary)
            ORDER BY week_start
        ''', (cutoff_week_start.isoformat(),))
        
        weeks_to_archive = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        archived_weeks = 0
        archived_days = 0
        
        # Create weekly summaries for each week
        for week_start_str in weeks_to_archive:
            from datetime import datetime as dt
            week_start = dt.fromisoformat(week_start_str).date()
            
            if self.create_weekly_summary(week_start):
                archived_weeks += 1
                
                # Count how many daily records would be archived
                week_end = week_start + timedelta(days=6)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM daily_summary 
                    WHERE day >= ? AND day <= ?
                ''', (week_start.isoformat(), week_end.isoformat()))
                archived_days += cursor.fetchone()[0]
                conn.close()
        
        # Now delete the daily summaries that have been archived
        if archived_weeks > 0:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM daily_summary 
                WHERE day <= ?
                AND DATE(day, 'weekday 0', '-6 days') IN (SELECT week_start FROM weekly_summary)
            ''', (cutoff_week_start.isoformat(),))
            deleted_days = cursor.rowcount
            conn.commit()
            conn.close()
        else:
            deleted_days = 0
        
        return archived_weeks, deleted_days
    
    def get_weekly_summaries(self, limit=12):
        """Get recent weekly summaries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM weekly_summary 
            ORDER BY week_start DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results