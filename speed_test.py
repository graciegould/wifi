import speedtest
import logging
from database import WiFiSpeedDB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WiFiSpeedTester:
    def __init__(self):
        self.db = WiFiSpeedDB()
    
    def run_speed_test(self):
        try:
            logging.info("Starting speed test...")
            
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
            
            self.db.insert_speed_test(
                download_speed=download_speed,
                upload_speed=upload_speed,
                ping=ping,
                server_name=server_name,
                server_location=server_location
            )
            
            logging.info("Results saved to database")
            return True
            
        except Exception as e:
            logging.error(f"Speed test failed: {e}")
            return False

if __name__ == "__main__":
    tester = WiFiSpeedTester()
    tester.run_speed_test()