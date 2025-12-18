import subprocess
import socket
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class DeviceScanner:
    def __init__(self):
        self.gateway_ip = self.get_default_gateway()
        self.network_prefix = self.get_network_prefix()
    
    def get_default_gateway(self):
        try:
            result = subprocess.run(['route', '-n', 'get', 'default'], 
                                  capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'gateway:' in line:
                    return line.split(':')[1].strip()
        except:
            pass
        return "192.168.1.1"
    
    def get_network_prefix(self):
        gateway_parts = self.gateway_ip.split('.')
        return f"{gateway_parts[0]}.{gateway_parts[1]}.{gateway_parts[2]}"
    
    def ping_host(self, ip):
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1000', ip], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def scan_arp_table(self):
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            active_devices = []
            
            for line in result.stdout.split('\n'):
                ip_match = re.search(r'\(([\d.]+)\)', line)
                if ip_match and 'incomplete' not in line.lower():
                    ip = ip_match.group(1)
                    if ip.startswith(self.network_prefix):
                        active_devices.append(ip)
            
            return list(set(active_devices))
        except:
            return []
    
    def scan_network_range(self, max_workers=20):
        active_devices = []
        ip_range = [f"{self.network_prefix}.{i}" for i in range(1, 255)]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {executor.submit(self.ping_host, ip): ip for ip in ip_range}
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        active_devices.append(ip)
                except:
                    pass
        
        return active_devices
    
    def get_router_device_count(self):
        try:
            result = subprocess.run(['nmap', '-sn', f"{self.network_prefix}.0/24"], 
                                  capture_output=True, text=True, timeout=30)
            
            host_count = len(re.findall(r'Nmap scan report for', result.stdout))
            return host_count if host_count > 0 else None
        except:
            return None
    
    def count_active_devices(self):
        logging.info("Scanning for active devices on network...")
        start_time = time.time()
        
        arp_devices = self.scan_arp_table()
        logging.info(f"Found {len(arp_devices)} devices in ARP table")
        
        if len(arp_devices) >= 3:
            device_count = len(arp_devices)
        else:
            logging.info("ARP table has few entries, performing network scan...")
            ping_devices = self.scan_network_range(max_workers=15)
            device_count = len(ping_devices)
            logging.info(f"Found {device_count} devices via ping scan")
        
        scan_time = time.time() - start_time
        logging.info(f"Device scan completed in {scan_time:.1f} seconds")
        
        return max(device_count, 1)

if __name__ == "__main__":
    scanner = DeviceScanner()
    count = scanner.count_active_devices()
    print(f"Active devices on network: {count}")