"""
WiFiSpeedTester
===============

Purpose:
--------
This module provides the WiFiSpeedTester class for running internet speed tests, saving results to a database, and outputting results in a formatted table. It separates data collection from presentation for better maintainability.

Class:
------
WiFiSpeedTester
    Methods:
    ---------
    __init__(self)
        Initializes the tester, sets up database and device scanner.

    run_speed_test(self) -> dict | None
        Runs a speed test, saves results to the database, and returns a dictionary of results. Returns None on failure.

    print_speed_test_table(self, results: dict)
        Outputs the speed test results in a pretty table format. Accepts a results dictionary.

Usage:
------
tester = WiFiSpeedTester()
results = tester.run_speed_test()
if results:
    tester.print_speed_test_table(results)
"""
import speedtest
import logging
from database import WiFiSpeedDB
from device_scanner import DeviceScanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WiFiSpeedTester:
    def __init__(self):
        """
        Initializes the WiFiSpeedTester instance.
        Sets up database and device scanner.
        """
        self.db = WiFiSpeedDB()
        self.device_scanner = DeviceScanner()
    
    def run_speed_test(self):
        """
        Runs a speed test, saves results to the database, and returns a dictionary of results.
        Returns:
            dict: Speed test results (download, upload, ping, server, location, devices)
            None: If the test fails
        """
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
            # Save to DB
            self.db.insert_speed_test(
                download_speed=download_speed,
                upload_speed=upload_speed,
                ping=ping,
                server_name=server_name,
                server_location=server_location,
                device_count=device_count
            )
            if self.db.update_today_summary():
                logging.info("Daily summary updated")
            self.db.create_placeholder_entries(days_back=3)
            import random
            if random.randint(1, 100) == 1:
                try:
                    speed_tests_days, _ = self.db.get_retention_policy()
                    deleted_count = self.db.archive_old_data(speed_tests_days)
                    if deleted_count[0] > 0:
                        logging.info(f"Archived {deleted_count[0]} old records to summaries")
                    from datetime import date
                    if date.today().weekday() == 6:
                        archived_weeks = self.db.archive_daily_to_weekly(weeks_to_keep=4)
                        if archived_weeks[0] > 0:
                            logging.info(f"Archived {archived_weeks[1]} daily summaries to {archived_weeks[0]} weekly summaries")
                except Exception as e:
                    logging.warning(f"Automatic cleanup failed: {e}")
            # Return results as a dictionary
            return {
                "download_speed": download_speed,
                "upload_speed": upload_speed,
                "ping": ping,
                "server_name": server_name,
                "server_location": server_location,
                "device_count": device_count
            }
        except Exception as e:
            logging.error(f"Speed test failed: {e}")
            return None

    def print_speed_test_table(self, results):
        """
        Outputs the speed test results in a rich table format.
        Parameters:
            results (dict): Dictionary of speed test results.
        Returns:
            None
        """
        from utils.format import print_rich_table
        columns = ["Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "Server", "Devices"]
        row = self._format_speed_test_row(results)
        print_rich_table("Speed Test Results", columns, [row])

    def _format_speed_test_row(self, results):
        """
        Helper to format a speed test result row for table output.
        Parameters:
            results (dict): Dictionary of speed test results.
        Returns:
            list: Formatted row for table output.
        """
        return [
            f"{results['download_speed']:.2f}",
            f"{results['upload_speed']:.2f}",
            f"{results['ping']:.2f}",
            f"{results['server_name']} ({results['server_location']})",
            results['device_count']
        ]

if __name__ == "__main__":
    tester = WiFiSpeedTester()
    results = tester.run_speed_test()
    if results:
        tester.print_speed_test_table(results)