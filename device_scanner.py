"""
DeviceScanner
=============

Purpose:
--------
This module provides the DeviceScanner class for discovering and counting active devices on a local network. It uses ARP table inspection, ICMP ping sweeps, and nmap to estimate device counts, and is designed for use in WiFi monitoring and automation scripts.

Class:
------
DeviceScanner
    Methods:
    ---------
    __init__(self)
        Initializes the scanner, sets gateway IP and network prefix.

    get_default_gateway(self) -> str
        Returns the default gateway IP address as a string.

    get_network_prefix(self) -> str
        Returns the network prefix (e.g. '192.168.1') as a string.

    ping_host(self, ip: str) -> bool
        Pings a given IP address. Returns True if host is reachable, False otherwise.

    scan_arp_table(self) -> list[str]
        Scans the ARP table for active devices in the local network prefix. Returns a list of IP addresses.

    scan_network_range(self, max_workers: int = 20) -> list[str]
        Pings all IPs in the subnet using threads. Returns a list of reachable IP addresses.

    get_router_device_count(self) -> int | None
        Uses nmap to scan the subnet and count devices. Returns the count or None if scan fails.

    count_active_devices(self) -> int
        Combines ARP and ping scans to estimate the number of active devices. Returns at least 1.

Usage:
------
scanner = DeviceScanner()
count = scanner.count_active_devices()
print(f"Active devices on network: {count}")
"""
import subprocess
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def print_device_scanner_table(scanner):
    """
    Standalone function to output a rich table summary of all device scan info tested by DeviceScanner.
    Includes ARP table count, ping scan count, nmap count, gateway IP, network prefix, and scan time.
    Parameters:
        scanner (DeviceScanner): An instance of DeviceScanner.
    """
    import time
    from utils.format import print_rich_table
    start_time = time.time()
    arp_devices = scanner.scan_arp_table()
    arp_count = len(arp_devices)
    ping_devices = scanner.scan_network_range(max_workers=15)
    ping_count = len(ping_devices)
    nmap_count = scanner.get_router_device_count()
    scan_time = time.time() - start_time
    summary_rows = [
        ["Gateway IP", scanner.gateway_ip],
        ["Network Prefix", scanner.network_prefix],
        ["ARP Table Devices", str(arp_count)],
        ["Ping Scan Devices", str(ping_count)],
        ["Nmap Devices", str(nmap_count) if nmap_count is not None else "N/A"],
        ["Scan Time (s)", f"{scan_time:.1f}"],
    ]
    print_rich_table("Device Scanner Summary", ["Metric", "Value"], summary_rows)
    

class DeviceScanner:
    def __init__(self):
        """
        Initializes the DeviceScanner instance.
        Sets gateway_ip and network_prefix for the local network.
        """
        self.gateway_ip = self.get_default_gateway()
        self.network_prefix = self.get_network_prefix()

    def get_default_gateway(self):
        """
        Returns the default gateway IP address as a string.
        No parameters.
        Returns:
            str: Gateway IP address (e.g. '192.168.1.1')
        """
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
        """
        Returns the network prefix for the local subnet.
        No parameters.
        Returns:
            str: Network prefix (e.g. '192.168.1')
        """
        gateway_parts = self.gateway_ip.split('.')
        return f"{gateway_parts[0]}.{gateway_parts[1]}.{gateway_parts[2]}"

    def ping_host(self, ip):
        """
        Pings a given IP address to check if it is reachable.
        Parameters:
            ip (str): IP address to ping.
        Returns:
            bool: True if host responds, False otherwise.
        """
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1000', ip], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    def scan_arp_table(self):
        """
        Scans the ARP table for active devices in the local network prefix.
        No parameters.
        Returns:
            list[str]: List of IP addresses found in ARP table.
        """
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
        """
        Pings all IPs in the subnet using threads to find active devices.
        Parameters:
            max_workers (int): Number of threads to use (default 20).
        Returns:
            list[str]: List of reachable IP addresses.
        """
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
        """
        Uses nmap to scan the subnet and count devices connected to the router.
        No parameters.
        Returns:
            int or None: Number of devices found, or None if scan fails.
        """
        try:
            result = subprocess.run(['nmap', '-sn', f"{self.network_prefix}.0/24"], 
                                  capture_output=True, text=True, timeout=30)
            host_count = len(re.findall(r'Nmap scan report for', result.stdout))
            return host_count if host_count > 0 else None
        except:
            return None

    def count_active_devices(self):
        """
        Combines ARP and ping scans to estimate the number of active devices on the network.
        No parameters.
        Returns:
            int: Estimated number of active devices (minimum 1).
        """
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
    print_device_scanner_table(scanner)