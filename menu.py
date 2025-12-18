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
    def clear_internet_plan(self):
        print("\n🧹 Clear Internet Plan")
        print("-" * 50)
        abs_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "clear_plan.py"))
        subprocess.run([sys.executable, abs_script])
        self.safe_input("\nPress Enter to continue...")
    def __init__(self):
        self.db = WiFiSpeedDB()
        self.fzf = FzfPrompt() if HAS_FZF else None
        self.plan_required_options = [
            ("📅 Daily Summaries", self.view_daily_summaries),
            ("📋 Current Plan Details", self.show_plan_details),
            ("⚡ Run Speed Test Now", self.run_speed_test),
            ("🔍 Count Network Devices", self.count_devices),
            ("📈 Generate Daily Summary", self.daily_summary_menu),
            ("🕒 Setup/Remove Cron Job", self.cron_management),
            ("🧹 Clear Internet Plan", self.clear_internet_plan),
        ]
        self.basic_options = [
            ("📊 Recent Speed Tests", self.view_recent_tests),
            ("⚡ Run Speed Test Now", self.run_speed_test),
            ("⚙️ Set Internet Plan", self.set_internet_plan),
            ("🚪 Exit", self.exit_app)
        ]
        self.full_options = [
            ("📊 Recent Speed Tests", self.view_recent_tests),
            ("📅 Daily Summaries", self.view_daily_summaries),
            ("📋 Current Plan Details", self.show_plan_details),
            ("⚡ Run Speed Test Now", self.run_speed_test),
            ("🔍 Count Network Devices", self.count_devices),
            ("⚙️ Set Internet Plan", self.set_internet_plan),
            ("🧹 Clear Internet Plan", self.clear_internet_plan),
            ("📈 Generate Daily Summary", self.daily_summary_menu),
            ("🕒 Setup/Remove Cron Job", self.cron_management),
            ("🚪 Exit", self.exit_app)
        ]
        self.menu_options = self.full_options
    
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def safe_input(self, prompt, allow_exit=True):
        """Input with exit handling"""
        try:
            if allow_exit and "Press Enter to continue" in prompt:
                prompt = prompt.replace("Press Enter to continue...", "Press Enter to continue or type 'exit' to quit...")
            response = input(prompt)
            if allow_exit and response.strip().lower() == 'exit':
                print("\n👋 Goodbye!")
                os._exit(0)
            return response
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            os._exit(0)
    
    def show_header(self):
        print("🌐 wifi")
        print("=" * 50)
    
    def show_current_plan(self, prompt_if_missing=False):
        plan = self.db.get_current_plan()
        if plan:
            print(f"📋 Current Plan: {plan[1]} ({plan[2]} Mbps down / {plan[3]} Mbps up)")
        else:
            print("⚠️  No internet plan configured")
            if prompt_if_missing:
                resp = self.safe_input("Would you like to set your internet plan now? (y/n/exit): ").strip().lower()
                if resp == 'y':
                    self.set_internet_plan()
        print()
    
    def select_menu_option(self):
        if self.fzf:
            try:
                options = [f"{option[0]}" for option in self.menu_options]
                selected_list = self.fzf.prompt(options, '--header="🌐 wifi - Select an option:"')
                if not selected_list:
                    print("\n👋 Goodbye!")
                    os._exit(0)
                selected = selected_list[0]
                for i, (option_text, _) in enumerate(self.menu_options):
                    if option_text == selected:
                        if option_text == "🚪 Exit":
                            print("\n👋 Goodbye!")
                            os._exit(0)
                        return i
                return None
            except Exception:
                print("\n👋 Goodbye!")
                os._exit(0)
        else:
            return self.fallback_menu()
    
    def fallback_menu(self):
        while True:
            print("Choose an option (or type 'exit' to quit):")
            print()
            for i, (option_text, _) in enumerate(self.menu_options):
                print(f"  {i + 1}. {option_text}")
            print()
            try:
                choice = input(f"Enter choice (1-{len(self.menu_options)} or 'exit'): ").strip().lower()
                if choice == 'exit':
                    print("\n👋 Goodbye!")
                    os._exit(0)
                if choice.isdigit():
                    choice_num = int(choice) - 1
                    if 0 <= choice_num < len(self.menu_options):
                        return choice_num
                print("\n❌ Invalid choice. Please try again.")
                self.safe_input("Press Enter to continue...")
                self.clear_screen()
                self.show_header()
                self.show_current_plan()
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                os._exit(0)
            except:
                print("\n👋 Goodbye!")
                os._exit(0)
    
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
        self.safe_input("\nPress Enter to continue...")
    
    def exit_app(self):
        print("\n👋 Goodbye!")
        os._exit(0)
    
    def run_speed_test(self):
        self.run_command("python3 wifi_monitor.py", "Running speed test")
    
    def count_devices(self):
        self.run_command("python3 device_scanner.py", "Scanning network devices")
    
    def view_recent_tests(self):
        print("\n📊 Recent Speed Tests")
        print("-" * 50)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            num = self.safe_input("Number of tests to show (default 10 or 'exit' to quit): ").strip()
            if not num:
                num = "10"
            abs_script = os.path.join(script_dir, "view_results.py")
            cmd = f"python3 {abs_script} -n {num}"
            subprocess.run(cmd, shell=True)
        except:
            abs_script = os.path.join(script_dir, "view_results.py")
            subprocess.run(f"python3 {abs_script}", shell=True)
        self.safe_input("\nPress Enter to continue...")
    
    def view_daily_summaries(self):
        print("\n📅 Daily Performance Summaries")
        print("-" * 50)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            num = self.safe_input("Number of days to show (default 14 or 'exit' to quit): ").strip()
            if not num:
                num = "14"
            abs_script = os.path.join(script_dir, "view_daily.py")
            cmd = f"python3 {abs_script} -n {num}"
            subprocess.run(cmd, shell=True)
        except:
            abs_script = os.path.join(script_dir, "view_daily.py")
            subprocess.run(f"python3 {abs_script}", shell=True)
        self.safe_input("\nPress Enter to continue...")
    
    def show_plan_details(self):
        print("\n📋 Internet Plan Details")
        print("-" * 50)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_script = os.path.join(script_dir, "set_plan.py")
        subprocess.run(f"python3 {abs_script} --show", shell=True)
        self.safe_input("\nPress Enter to continue...")
    
    def set_internet_plan(self):
        print("\n⚙️  Set Internet Plan")
        print("-" * 50)
        print("Enter your internet plan details:")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_script = os.path.join(script_dir, "set_plan.py")
        try:
            plan_name = self.safe_input("Plan name (e.g. '1 Gig Plan' or 'exit' to quit): ").strip()
            if not plan_name:
                print("❌ Plan name required")
                self.safe_input("Press Enter to continue...")
                return
            download = self.safe_input("Download speed in Mbps (e.g. 1000 or 'exit' to quit): ").strip()
            if not download:
                print("❌ Download speed required")
                self.safe_input("Press Enter to continue...")
                return
            upload = self.safe_input("Upload speed in Mbps (e.g. 100 or 'exit' to quit): ").strip()
            if not upload:
                print("❌ Upload speed required") 
                self.safe_input("Press Enter to continue...")
                return
            cmd = f'python3 {abs_script} "{plan_name}" {download} {upload}'
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"❌ Error: {e}")
        self.safe_input("\nPress Enter to continue...")
    
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
                    date = self.safe_input("Enter date (YYYY-MM-DD or 'exit' to quit): ").strip()
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
        
        sub_choice = self.safe_input("\nChoice (or 'exit' to quit): ").strip()
        
        if sub_choice == "1":
            self.run_command("python3 daily_rollup.py --yesterday", "Generating yesterday's summary")
        elif sub_choice == "2":
            date = self.safe_input("Enter date (YYYY-MM-DD or 'exit' to quit): ").strip()
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
        
        choice = self.safe_input("\nChoice (or 'exit' to quit): ").strip()
        
        if choice == "1":
            self.run_command("python3 setup_cron.py", "Setting up cron job")
        elif choice == "2":
            self.run_command("python3 setup_cron.py remove", "Removing cron job")
        elif choice == "3":
            return
        else:
            print("❌ Invalid choice")
            self.safe_input("Press Enter to continue...")
    
    def run(self):
        first_run = True
        plan_set = bool(self.db.get_current_plan())
        prompted = False
        while True:
            if not plan_set and not prompted:
                self.clear_screen()
                self.show_header()
                print("⚠️  No internet plan is set.")
                print("To compare your speeds against your plan, set your plan now.")
                print("You can also continue with basic speed/status checks only.")
                try:
                    resp = input("Would you like to set your internet plan now? (y/n/exit): ").strip().lower()
                    if resp == 'exit':
                        print("\n👋 Goodbye!")
                        os._exit(0)
                    elif resp == 'y':
                        self.set_internet_plan()
                        plan_set = bool(self.db.get_current_plan())
                        self.menu_options = self.full_options
                    else:
                        self.menu_options = self.basic_options
                    prompted = True
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    os._exit(0)
            elif not plan_set:
                self.menu_options = self.basic_options
            else:
                self.menu_options = self.full_options
            if not self.fzf:
                self.clear_screen()
                self.show_header()
                self.show_current_plan(prompt_if_missing=first_run)
                first_run = False
            choice_index = self.select_menu_option()
            if 0 <= choice_index < len(self.menu_options):
                try:
                    _, action = self.menu_options[choice_index]
                    if not plan_set and action not in [self.view_recent_tests, self.run_speed_test, self.set_internet_plan, self.exit_app]:
                        print("\n⚠️  Please set your internet plan to use this feature.")
                        self.safe_input("Press Enter to continue...")
                        continue
                    action()
                    # After setting plan, unlock all options
                    if action == self.set_internet_plan:
                        plan_set = bool(self.db.get_current_plan())
                        if plan_set:
                            self.menu_options = self.full_options
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    self.safe_input("Press Enter to continue...")
            else:
                if not self.fzf:
                    print("\n❌ Invalid choice. Please try again.")
                    self.safe_input("Press Enter to continue...")

def main():
    """Main entry point for the WiFi monitoring CLI"""
    try:
        menu = WiFiMonitorMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        import os
        os._exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import os
        os._exit(1)

def cli_main():
    """Alternative entry point for CLI installation"""
    main()

if __name__ == "__main__":
    main()