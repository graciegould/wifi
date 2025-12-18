import speedtest
import logging
from database import WiFiSpeedDB
from device_scanner import DeviceScanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WiFiSpeedTester:
    def __init__(self):
        self.db = WiFiSpeedDB()
        self.device_scanner = DeviceScanner()
    
    def run_speed_test(self):
        try:
            logging.info("Starting speed test...")
            
            device_count = self.device_scanner.count_active_devices()
            logging.info(f"Found {device_count} active devices on network")
            
            st = speedtest.Speedtest()
            st.get_best_server()
            
            logging.info("Testing download speed...")
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            
            logging.info("Testing upload speed...")
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            
            ping = st.results.ping
            
            server_info = st.get_best_server()
            server_name = server_info.get('sponsor', 'Unknown')
            server_location = f"{server_info.get('name', '')}, {server_info.get('country', '')}"
            
            logging.info(f"Speed test completed:")
            logging.info(f"  Download: {download_speed:.2f} Mbps")
            logging.info(f"  Upload: {upload_speed:.2f} Mbps")
            logging.info(f"  Ping: {ping:.2f} ms")
            logging.info(f"  Server: {server_name} ({server_location})")
            logging.info(f"  Devices: {device_count}")
            
            self.db.insert_speed_test(
                download_speed=download_speed,
                upload_speed=upload_speed,
                ping=ping,
                server_name=server_name,
                server_location=server_location,
                device_count=device_count
            )
            
            logging.info("Results saved to database")
            
            # Update today's daily summary with latest data
            if self.db.update_today_summary():
                logging.info("Daily summary updated")
            
            # Create placeholder entries for any missed days (computer was off)
            self.db.create_placeholder_entries(days_back=3)
            
            # Automatic cleanup every 100 tests (roughly daily with 10min intervals)
            # This prevents database from growing indefinitely
            import random
            if random.randint(1, 100) == 1:  # 1% chance per test = ~daily cleanup
                logging.info("Running automatic data cleanup...")
                try:
                    speed_tests_days, _ = self.db.get_retention_policy()
                    deleted_count = self.db.archive_old_data(speed_tests_days)
                    if deleted_count[0] > 0:
                        logging.info(f"Archived {deleted_count[0]} old records to summaries")
                    
                    # Weekly rollup (every Sunday, roughly)
                    from datetime import date
                    if date.today().weekday() == 6:  # Sunday
                        archived_weeks = self.db.archive_daily_to_weekly(weeks_to_keep=4)
                        if archived_weeks[0] > 0:
                            logging.info(f"Archived {archived_weeks[1]} daily summaries to {archived_weeks[0]} weekly summaries")
                            
                except Exception as e:
                    logging.warning(f"Automatic cleanup failed: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Speed test failed: {e}")
            return False

if __name__ == "__main__":
    tester = WiFiSpeedTester()
    tester.run_speed_test()