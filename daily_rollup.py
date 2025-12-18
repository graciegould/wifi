#!/usr/bin/env python3
import statistics
import argparse
from datetime import datetime, date, timedelta
from database import WiFiSpeedDB
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DailyRollup:
    def __init__(self, ping_threshold=50):
        self.db = WiFiSpeedDB()
        self.ping_threshold = ping_threshold
    
    def is_bad_sample(self, download, upload, ping, plan_download, plan_upload):
        """
        A sample is "bad" if ANY of these conditions are true:
        - Download < 70% of plan download
        - Upload < 70% of plan upload  
        - Ping > threshold (default 50ms)
        """
        if plan_download and download < (plan_download * 0.7):
            return True
        if plan_upload and upload < (plan_upload * 0.7):
            return True
        if ping > self.ping_threshold:
            return True
        return False
    
    def get_daily_status(self, pct_bad):
        """
        Derive daily status from percentage of bad samples:
        - good: <10% bad
        - meh: 10-30% bad  
        - bad: >30% bad
        """
        if pct_bad < 10:
            return 'good'
        elif pct_bad <= 30:
            return 'meh'
        else:
            return 'bad'
    
    def calculate_percentile(self, data, percentile):
        """Calculate nth percentile of a list"""
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
    
    def compute_daily_summary(self, target_date):
        """
        Compute daily summary for a specific date.
        Idempotent - safe to re-run.
        """
        logging.info(f"Computing daily summary for {target_date}")
        
        # Get current plan speeds
        plan = self.db.get_current_plan()
        if not plan:
            logging.warning("No active plan found - cannot determine 'bad' samples accurately")
            plan_download = plan_upload = None
        else:
            plan_download = plan[2]  # download_mbps
            plan_upload = plan[3]    # upload_mbps
            logging.info(f"Using plan: {plan[1]} ({plan_download} down, {plan_upload} up)")
        
        # Get all samples for the target date
        daily_data = self.db.get_daily_data(target_date)
        
        if not daily_data:
            logging.warning(f"No speed test data found for {target_date}")
            return False
        
        sample_count = len(daily_data)
        logging.info(f"Found {sample_count} samples for {target_date}")
        
        # Extract metrics
        downloads = [row[0] for row in daily_data if row[0] is not None]
        uploads = [row[1] for row in daily_data if row[1] is not None]
        pings = [row[2] for row in daily_data if row[2] is not None]
        device_counts = [row[3] for row in daily_data if row[3] is not None]
        
        if not downloads or not uploads or not pings:
            logging.warning(f"Missing critical data for {target_date}")
            return False
        
        # Calculate summary metrics
        median_download = statistics.median(downloads)
        median_upload = statistics.median(uploads)
        p95_ping = self.calculate_percentile(pings, 95)
        avg_device_count = statistics.mean(device_counts) if device_counts else None
        
        # Calculate percentage of "bad" samples
        bad_samples = 0
        for download, upload, ping, _ in daily_data:
            if self.is_bad_sample(download, upload, ping, plan_download, plan_upload):
                bad_samples += 1
        
        pct_bad = (bad_samples / sample_count) * 100
        status = self.get_daily_status(pct_bad)
        
        # Log summary
        logging.info(f"Daily summary for {target_date}:")
        logging.info(f"  Samples: {sample_count}")
        logging.info(f"  Median download: {median_download:.1f} Mbps")
        logging.info(f"  Median upload: {median_upload:.1f} Mbps")
        logging.info(f"  95th percentile ping: {p95_ping:.1f} ms")
        logging.info(f"  Bad samples: {bad_samples}/{sample_count} ({pct_bad:.1f}%)")
        logging.info(f"  Status: {status}")
        logging.info(f"  Avg devices: {avg_device_count:.1f}" if avg_device_count else "  Avg devices: N/A")
        
        # Insert/update summary (idempotent)
        self.db.insert_daily_summary(
            day=target_date,
            sample_count=sample_count,
            median_download=median_download,
            median_upload=median_upload,
            p95_ping=p95_ping,
            pct_bad=pct_bad,
            avg_device_count=avg_device_count,
            status=status
        )
        
        logging.info(f"Daily summary saved for {target_date}")
        return True
    
    def rollup_yesterday(self):
        """Compute summary for yesterday (most common use case)"""
        yesterday = date.today() - timedelta(days=1)
        return self.compute_daily_summary(yesterday.isoformat())
    
    def rollup_missing_days(self, days_back=7):
        """Backfill any missing daily summaries for the last N days"""
        existing_summaries = set()
        
        # Get existing summaries
        summaries = self.db.get_daily_summaries(days_back)
        for summary in summaries:
            existing_summaries.add(summary[0])  # day column
        
        # Check each day and compute if missing
        for i in range(1, days_back + 1):
            check_date = date.today() - timedelta(days=i)
            date_str = check_date.isoformat()
            
            if date_str not in existing_summaries:
                logging.info(f"Missing summary for {date_str}, computing...")
                self.compute_daily_summary(date_str)
            else:
                logging.info(f"Summary already exists for {date_str}")

def main():
    parser = argparse.ArgumentParser(description='Compute daily WiFi performance summaries')
    parser.add_argument('--date', help='Specific date to process (YYYY-MM-DD)')
    parser.add_argument('--yesterday', action='store_true', help='Process yesterday')
    parser.add_argument('--backfill', type=int, default=7, 
                        help='Backfill missing summaries for last N days (default: 7)')
    parser.add_argument('--ping-threshold', type=int, default=50,
                        help='Ping threshold for "bad" samples in ms (default: 50)')
    
    args = parser.parse_args()
    
    rollup = DailyRollup(ping_threshold=args.ping_threshold)
    
    if args.date:
        rollup.compute_daily_summary(args.date)
    elif args.yesterday:
        rollup.rollup_yesterday()
    else:
        # Default: backfill any missing days
        rollup.rollup_missing_days(args.backfill)

if __name__ == "__main__":
    main()