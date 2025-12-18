#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def setup_cron_job():
    script_dir = Path(__file__).parent.absolute()
    python_path = sys.executable
    script_path = script_dir / "wifi_monitor.py"
    log_path = script_dir / "wifi_monitor.log"
    
    cron_command = f"*/10 * * * * cd {script_dir} && {python_path} {script_path} >> {log_path} 2>&1"
    
    print("Setting up cron job for wifi monitoring...")
    print(f"Script location: {script_path}")
    print(f"Python path: {python_path}")
    print(f"Log file: {log_path}")
    print(f"Cron command: {cron_command}")
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing_crontab = result.stdout if result.returncode == 0 else ""
        
        if "wifi_monitor.py" in existing_crontab:
            print("WiFi monitor cron job already exists!")
            return
        
        new_crontab = existing_crontab + cron_command + "\n"
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron job successfully added!")
            print("WiFi speed will be monitored every 10 minutes")
            print(f"Check logs at: {log_path}")
        else:
            print("❌ Failed to add cron job")
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")

def remove_cron_job():
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("No existing crontab found")
            return
        
        existing_crontab = result.stdout
        lines = existing_crontab.split('\n')
        new_lines = [line for line in lines if "wifi_monitor.py" not in line]
        new_crontab = '\n'.join(new_lines)
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ WiFi monitor cron job removed")
        else:
            print("❌ Failed to remove cron job")
            
    except Exception as e:
        print(f"❌ Error removing cron job: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "remove":
        remove_cron_job()
    else:
        setup_cron_job()