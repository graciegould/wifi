#!/usr/bin/env python3
import argparse
import sys
from database import WiFiSpeedDB

class DataCleanup:
    def __init__(self):
        self.db = WiFiSpeedDB()
    
    def show_storage_stats(self):
        """Display current database storage statistics"""
        stats = self.db.get_database_stats()
        speed_tests_days, summaries_days = self.db.get_retention_policy()
        
        print("📊 Database Storage Statistics")
        print("=" * 50)
        print(f"💾 Database size: {stats['db_size_kb']} KB")
        print(f"🔢 Speed tests: {stats['speed_tests_count']:,} records")
        print(f"📅 Daily summaries: {stats['daily_summaries_count']} records")
        
        if stats['date_range'][0]:
            print(f"📆 Data range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        else:
            print("📆 No data found")
        
        print(f"\n⚙️ Retention Policy:")
        print(f"   Speed tests: {speed_tests_days} days")
        print(f"   Daily summaries: {summaries_days} days")
        
        # Estimate data growth
        if stats['speed_tests_count'] > 0:
            # Get monitoring interval
            interval_minutes = int(self.db.get_config('monitoring_interval', '10'))
            tests_per_day = 1440 / interval_minutes
            estimated_growth_per_day = tests_per_day
            
            print(f"\n📈 Growth Estimation:")
            print(f"   Current interval: {interval_minutes} minutes")
            print(f"   New records/day: ~{estimated_growth_per_day:.0f}")
            
            # Warning if database is growing too fast
            if estimated_growth_per_day > 144:  # More than 10 minutes
                print(f"   ⚠️ High growth rate due to frequent monitoring")
    
    def cleanup_old_data(self, days_to_keep=None, dry_run=False):
        """Clean up old speed test data"""
        if days_to_keep is None:
            days_to_keep, _ = self.db.get_retention_policy()
        
        print(f"🧹 Cleaning up speed tests older than {days_to_keep} days")
        
        if dry_run:
            print("🔍 DRY RUN - No data will be deleted")
            # Count what would be deleted
            from datetime import date, timedelta
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM speed_tests WHERE DATE(timestamp) < ?', 
                          (cutoff_date.isoformat(),))
            would_delete = cursor.fetchone()[0]
            conn.close()
            
            print(f"📋 Would delete: {would_delete:,} speed test records")
            return would_delete
        else:
            deleted_count, kb_freed = self.db.cleanup_old_data(days_to_keep)
            print(f"✅ Deleted: {deleted_count:,} records")
            print(f"💾 Space freed: ~{kb_freed} KB")
            return deleted_count
    
    def archive_old_data(self, days_to_keep=90, dry_run=False):
        """Archive old data to summaries before deletion"""
        print(f"📦 Archiving speed tests older than {days_to_keep} days")
        
        if dry_run:
            print("🔍 DRY RUN - No data will be archived")
            # Count what would be archived
            from datetime import date, timedelta
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM speed_tests 
                WHERE DATE(timestamp) < ?
                AND DATE(timestamp) NOT IN (SELECT day FROM daily_summary)
            ''', (cutoff_date.isoformat(),))
            would_archive = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT DATE(timestamp)) FROM speed_tests WHERE DATE(timestamp) < ?', 
                          (cutoff_date.isoformat(),))
            days_affected = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"📋 Would archive: {would_archive:,} records")
            print(f"📅 Days affected: {days_affected}")
            return would_archive
        else:
            deleted_count, summaries_created = self.db.archive_old_data(days_to_keep)
            print(f"✅ Archived: {deleted_count:,} records")
            print(f"📝 Created: {summaries_created} daily summaries")
            return deleted_count
    
    def set_retention_policy(self, speed_tests_days, summaries_days, weekly_weeks=52):
        """Set data retention policies"""
        self.db.set_retention_policy(speed_tests_days, summaries_days)
        self.db.set_config('retention_weekly_weeks', str(weekly_weeks))
        print(f"⚙️ Retention policy updated:")
        print(f"   Speed tests: {speed_tests_days} days")
        print(f"   Daily summaries: {summaries_days} days")
        print(f"   Weekly summaries: {weekly_weeks} weeks")
    
    def auto_cleanup(self):
        """Perform automatic 3-tier cleanup: Speed tests -> Daily -> Weekly"""
        speed_tests_days, summaries_days = self.db.get_retention_policy()
        weekly_weeks = int(self.db.get_config('retention_weekly_weeks', '52'))
        
        print("🤖 3-Tier automatic cleanup starting...")
        
        # Tier 1: Archive speed tests to daily summaries
        print(f"📊 Tier 1: Archiving speed tests older than {speed_tests_days} days")
        archived_tests = self.archive_old_data(speed_tests_days)
        
        # Tier 2: Archive daily summaries to weekly summaries
        print(f"📅 Tier 2: Archiving daily summaries older than 4 weeks")
        archived_weeks = self.db.archive_daily_to_weekly(weeks_to_keep=4)
        if archived_weeks[0] > 0:
            print(f"✅ Archived: {archived_weeks[1]} daily summaries into {archived_weeks[0]} weekly summaries")
        
        # Tier 3: Cleanup very old weekly summaries
        if weekly_weeks < 999:  # If not "keep forever"
            print(f"\n🗑️ Tier 3: Cleaning weekly summaries older than {weekly_weeks} weeks")
            from datetime import date, timedelta
            cutoff_date = date.today() - timedelta(weeks=weekly_weeks)
            
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM weekly_summary WHERE week_start < ?', (cutoff_date.isoformat(),))
            deleted_weekly = cursor.rowcount
            
            # Also cleanup any remaining old daily summaries beyond policy
            if summaries_days < 9999:
                cutoff_date = date.today() - timedelta(days=summaries_days)
                cursor.execute('DELETE FROM daily_summary WHERE day < ?', (cutoff_date.isoformat(),))
                deleted_daily = cursor.rowcount
            else:
                deleted_daily = 0
            
            conn.commit()
            conn.close()
            
            if deleted_weekly > 0:
                print(f"✅ Deleted: {deleted_weekly} old weekly summaries")
            if deleted_daily > 0:
                print(f"✅ Deleted: {deleted_daily} old daily summaries")
        
        # Vacuum database to reclaim space
        print("\n🗜️ Optimizing database...")
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        conn.execute('VACUUM')
        conn.close()
        
        print("✅ 3-tier automatic cleanup completed")

def main():
    parser = argparse.ArgumentParser(description='Manage WiFi monitoring data cleanup')
    parser.add_argument('--stats', action='store_true', help='Show storage statistics')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', 
                        help='Delete speed tests older than N days')
    parser.add_argument('--archive', type=int, metavar='DAYS',
                        help='Archive speed tests older than N days to summaries') 
    parser.add_argument('--auto', action='store_true', 
                        help='Run automatic cleanup based on retention policy')
    parser.add_argument('--set-retention', nargs=2, type=int, metavar=('SPEED_DAYS', 'SUMMARY_DAYS'),
                        help='Set retention policy (speed_tests_days summary_days)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    cleanup = DataCleanup()
    
    if args.stats:
        cleanup.show_storage_stats()
    elif args.cleanup:
        cleanup.cleanup_old_data(args.cleanup, args.dry_run)
    elif args.archive:
        cleanup.archive_old_data(args.archive, args.dry_run)
    elif args.auto:
        if args.dry_run:
            print("🔍 DRY RUN - Auto cleanup preview:")
            speed_tests_days, summaries_days = cleanup.db.get_retention_policy()
            cleanup.archive_old_data(speed_tests_days, dry_run=True)
        else:
            cleanup.auto_cleanup()
    elif args.set_retention:
        cleanup.set_retention_policy(args.set_retention[0], args.set_retention[1])
    else:
        # Default: show stats
        cleanup.show_storage_stats()
        print(f"\n💡 Usage examples:")
        print(f"   python3 cleanup.py --cleanup 30        # Delete tests > 30 days old")
        print(f"   python3 cleanup.py --archive 90        # Archive tests > 90 days old")
        print(f"   python3 cleanup.py --auto              # Automatic cleanup")
        print(f"   python3 cleanup.py --set-retention 30 365  # Keep tests 30d, summaries 1y")

if __name__ == "__main__":
    main()