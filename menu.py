#!/usr/bin/env python3
import os
import sys
import subprocess
from database import WiFiSpeedDB

try:
    from pyfzf.pyfzf import FzfPrompt
    HAS_FZF = True
except ImportError:
    HAS_FZF = False

class WiFiMonitorMenu:
    def __init__(self):
        self.db = WiFiSpeedDB()
        self.fzf = FzfPrompt() if HAS_FZF else None
        self.menu_options = [
            ("📊 Recent Speed Tests", self.view_recent_tests),
            ("📅 Daily Summaries", self.view_daily_summaries), 
            ("📋 Current Plan Details", self.show_plan_details),
            ("⚡ Run Speed Test Now", self.run_speed_test),
            ("🔍 Count Network Devices", self.count_devices),
            ("⚙️ Set Internet Plan", self.set_internet_plan),
            ("📈 Generate Daily Summary", self.daily_summary_menu),
            ("🕒 Setup/Remove Cron Job", self.cron_management),
            ("🚪 Exit", self.exit_app)
        ]
    
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_header(self):
        print("🌐 WiFi Speed Monitor")
        print("=" * 50)
    
    def show_current_plan(self):
        plan = self.db.get_current_plan()
        if plan:
            print(f"📋 Current Plan: {plan[1]} ({plan[2]} Mbps down / {plan[3]} Mbps up)")
        else:
            print("⚠️  No internet plan configured")
        print()
    
    def select_menu_option(self):
        if self.fzf:
            try:
                options = [f"{option[0]}" for option in self.menu_options]
                selected = self.fzf.prompt(options, '--header="🌐 WiFi Speed Monitor - Select an option:"')[0]
                
                for i, (option_text, _) in enumerate(self.menu_options):
                    if option_text == selected:
                        return i
                return None
            except:
                return self.fallback_menu()
        else:
            return self.fallback_menu()
    
    def fallback_menu(self):
        print("Choose an option:")
        print()
        for i, (option_text, _) in enumerate(self.menu_options):
            print(f"  {i + 1}. {option_text}")
        print()
        
        try:
            choice = input("Enter choice (1-9): ").strip()
            return int(choice) - 1 if choice.isdigit() else None
        except:
            return None
    
    def run_command(self, command, description):
        # Always resolve script paths relative to this file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        command_parts = command.split()
        if len(command_parts) >= 2 and command_parts[0] == "python3":
            script_name = command_parts[1]
            # If script_name is a .py file in this project, use absolute path
            if script_name.endswith('.py'):
                abs_script = os.path.join(script_dir, script_name)
                command_parts[1] = abs_script
                command = " ".join(command_parts)
        print(f"\n🔄 {description}...")
        print("-" * 50)
        try:
            result = subprocess.run(command, shell=True, capture_output=False)
            print("-" * 50)
            if result.returncode == 0:
                print(f"✅ {description} completed")
            else:
                print(f"❌ {description} failed")
        except Exception as e:
            print(f"❌ Error: {e}")
        input("\nPress Enter to continue...")
    
    def exit_app(self):
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    def run_speed_test(self):
        self.run_command("python3 wifi_monitor.py", "Running speed test")
    
    def count_devices(self):
        self.run_command("python3 device_scanner.py", "Scanning network devices")
    
    def view_recent_tests(self):
        print("\n📊 Recent Speed Tests")
        print("-" * 50)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            num = input("Number of tests to show (default 10): ").strip()
            if not num:
                num = "10"
            abs_script = os.path.join(script_dir, "view_results.py")
            cmd = f"python3 {abs_script} -n {num}"
            subprocess.run(cmd, shell=True)
        except:
            abs_script = os.path.join(script_dir, "view_results.py")
            subprocess.run(f"python3 {abs_script}", shell=True)
        input("\nPress Enter to continue...")
    
    def view_daily_summaries(self):
        print("\n📅 Daily Performance Summaries")
        print("-" * 50)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            num = input("Number of days to show (default 14): ").strip()
            if not num:
                num = "14"
            abs_script = os.path.join(script_dir, "view_daily.py")
            cmd = f"python3 {abs_script} -n {num}"
            subprocess.run(cmd, shell=True)
        except:
            abs_script = os.path.join(script_dir, "view_daily.py")
            subprocess.run(f"python3 {abs_script}", shell=True)
        input("\nPress Enter to continue...")
    
    def show_plan_details(self):
        print("\n📋 Internet Plan Details")
        print("-" * 50)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_script = os.path.join(script_dir, "set_plan.py")
        subprocess.run(f"python3 {abs_script} --show", shell=True)
        input("\nPress Enter to continue...")
    
    def set_internet_plan(self):
        print("\n⚙️  Set Internet Plan")
        print("-" * 50)
        print("Enter your internet plan details:")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_script = os.path.join(script_dir, "set_plan.py")
        try:
            plan_name = input("Plan name (e.g. '1 Gig Plan'): ").strip()
            if not plan_name:
                print("❌ Plan name required")
                input("Press Enter to continue...")
                return
            download = input("Download speed in Mbps (e.g. 1000): ").strip()
            upload = input("Upload speed in Mbps (e.g. 100): ").strip()
            if not download or not upload:
                print("❌ Both speeds required")
                input("Press Enter to continue...")
                return
            cmd = f'python3 {abs_script} "{plan_name}" {download} {upload}'
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"❌ Error: {e}")
        input("\nPress Enter to continue...")
    
    def daily_summary_menu(self):
        if self.fzf:
            try:
                options = [
                    "📅 Generate for yesterday",
                    "📆 Generate for specific date",
                    "🔙 Back to main menu"
                ]
                selected = self.fzf.prompt(options, '--header="📈 Generate Daily Summary:"')[0]
                
                if "yesterday" in selected:
                    self.run_command("python3 daily_rollup.py --yesterday", "Generating yesterday's summary")
                elif "specific date" in selected:
                    date = input("Enter date (YYYY-MM-DD): ").strip()
                    if date:
                        self.run_command(f"python3 daily_rollup.py --date {date}", f"Generating summary for {date}")
                return
            except:
                pass
        
        print("\n📈 Generate Daily Summary")
        print("-" * 50)
        print("ℹ️  Note: Daily summaries now update automatically with each speed test")
        print("1. Generate for yesterday")
        print("2. Generate for specific date")
        print("3. Back to main menu")
        
        sub_choice = input("\nChoice: ").strip()
        
        if sub_choice == "1":
            self.run_command("python3 daily_rollup.py --yesterday", "Generating yesterday's summary")
        elif sub_choice == "2":
            date = input("Enter date (YYYY-MM-DD): ").strip()
            if date:
                self.run_command(f"python3 daily_rollup.py --date {date}", f"Generating summary for {date}")
    
    def cron_management(self):
        if self.fzf:
            try:
                options = [
                    "🕒 Setup cron job (every 10 minutes)",
                    "🗑️ Remove cron job",
                    "🔙 Back to main menu"
                ]
                selected = self.fzf.prompt(options, '--header="🕒 Cron Job Management:"')[0]
                
                if "Setup" in selected:
                    self.run_command("python3 setup_cron.py", "Setting up cron job")
                elif "Remove" in selected:
                    self.run_command("python3 setup_cron.py remove", "Removing cron job")
                return
            except:
                pass
        
        print("\n🕒 Cron Job Management") 
        print("-" * 50)
        print("1. Setup cron job (every 10 minutes)")
        print("2. Remove cron job")
        print("3. Back to main menu")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            self.run_command("python3 setup_cron.py", "Setting up cron job")
        elif choice == "2":
            self.run_command("python3 setup_cron.py remove", "Removing cron job")
        elif choice == "3":
            return
        else:
            print("❌ Invalid choice")
            input("Press Enter to continue...")
    
    def run(self):
        while True:
            if not self.fzf:
                self.clear_screen()
                self.show_header()
                self.show_current_plan()
            
            choice_index = self.select_menu_option()
            
            if choice_index is not None and 0 <= choice_index < len(self.menu_options):
                try:
                    _, action = self.menu_options[choice_index]
                    action()
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    input("Press Enter to continue...")
            else:
                if not self.fzf:
                    print("\n❌ Invalid choice. Please try again.")
                    input("Press Enter to continue...")

def main():
    """Main entry point for the WiFi monitoring CLI"""
    try:
        menu = WiFiMonitorMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

def cli_main():
    """Alternative entry point for CLI installation"""
    main()

if __name__ == "__main__":
    main()