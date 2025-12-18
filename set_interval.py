#!/usr/bin/env python3
import argparse
import sys
from database import WiFiSpeedDB

class IntervalManager:
    def __init__(self):
        self.db = WiFiSpeedDB()
        
        # Common interval presets in minutes
        self.presets = {
            "1": {"minutes": 1, "description": "Every minute", "warning": "Very frequent - high data usage"},
            "2": {"minutes": 2, "description": "Every 2 minutes", "warning": "Frequent monitoring"},
            "5": {"minutes": 5, "description": "Every 5 minutes", "warning": None},
            "10": {"minutes": 10, "description": "Every 10 minutes (default)", "warning": None},
            "15": {"minutes": 15, "description": "Every 15 minutes", "warning": None},
            "30": {"minutes": 30, "description": "Every 30 minutes", "warning": "Less frequent monitoring"},
            "60": {"minutes": 60, "description": "Every hour", "warning": "Infrequent - fewer data points"}
        }
    
    def minutes_to_cron(self, minutes):
        """Convert minutes to appropriate cron expression"""
        if minutes < 60:  # Less than 1 hour
            if 60 % minutes == 0:  # Evenly divides into hour
                return f"*/{minutes} * * * *", "cron"
            else:
                return f"*/{minutes} * * * *", "cron"
        elif minutes < 1440:  # Less than 1 day
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:  # Even hours
                return f"0 */{hours} * * *", "cron"
            else:
                return f"{remaining_minutes} */{hours} * * *", "cron"
        else:
            days = minutes // 1440
            return f"0 0 */{days} * *", "cron"
    
    def show_current_interval(self):
        """Display current monitoring interval"""
        config = self.db.get_config('monitoring_interval')
        
        if config:
            minutes = int(config)
            for preset, data in self.presets.items():
                if data['minutes'] == minutes:
                    print(f"📊 Current Interval: {data['description']} ({preset} min)")
                    return
            print(f"📊 Current Interval: {minutes} minutes (custom)")
        else:
            print("📊 Current Interval: 10 minutes (default)")
    
    def list_presets(self):
        """Show available interval presets"""
        print("\n⏱️  Available Interval Presets:")
        print("=" * 60)
        
        for preset, data in self.presets.items():
            warning = f" ⚠️ {data['warning']}" if data['warning'] else ""
            print(f"  {preset:<4} - {data['description']}{warning}")
        
        print("\n💡 You can also set custom intervals like: 3, 7, 45 (minutes)")
    
    def parse_interval(self, interval_str):
        """Parse interval string to minutes"""
        if not interval_str:
            return None
        
        interval_str = interval_str.strip()
        
        # Check presets first
        if interval_str in self.presets:
            return self.presets[interval_str]['minutes']
        
        # Parse as simple number (minutes)
        try:
            minutes = int(interval_str)
            return minutes if minutes > 0 else None
        except ValueError:
            return None
    
    def validate_interval(self, minutes):
        """Validate interval and return warnings/recommendations"""
        warnings = []
        
        if minutes < 1:
            warnings.append("❌ Minimum interval is 1 minute")
        elif minutes == 1:
            warnings.append("⚠️ Very frequent testing may impact network performance")
        elif minutes > 60:
            warnings.append("ℹ️ Infrequent testing provides fewer data points")
        
        # Data usage estimation
        tests_per_day = 1440 / minutes  # 1440 minutes in a day
        estimated_mb = tests_per_day * 50  # ~50MB per speed test
        
        if estimated_mb > 1000:  # > 1GB per day
            warnings.append(f"📊 High data usage: ~{estimated_mb:.0f}MB/day")
        
        return warnings
    
    def set_interval(self, interval_str):
        """Set new monitoring interval"""
        minutes = self.parse_interval(interval_str)
        
        if minutes is None:
            print(f"❌ Invalid interval format: {interval_str}")
            print("💡 Use numbers like: 5, 10, 15 (minutes) or presets: 1, 2, 5, 10, 15, 30, 60")
            return False
        
        # Validate interval
        warnings = self.validate_interval(minutes)
        if warnings:
            print("\n⚠️ Interval Warnings:")
            for warning in warnings:
                print(f"   {warning}")
            
            if "❌" in " ".join(warnings):
                print("❌ Invalid interval")
                return False
            
            confirm = input("\nContinue anyway? (y/N): ").lower().strip()
            if confirm != 'y':
                print("❌ Interval change cancelled")
                return False
        
        # Save to database
        self.db.set_config('monitoring_interval', str(minutes))
        
        # Show cron info
        cron_expr, scheduler = self.minutes_to_cron(minutes)
        
        print(f"\n✅ Interval set to {minutes} minutes")
        print(f"📋 Cron expression: {cron_expr}")
        print(f"🔧 Scheduler: {scheduler}")
        
        print(f"\n💡 Run 'python3 setup_cron.py' to update your cron job")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Configure WiFi monitoring interval')
    parser.add_argument('interval', nargs='?', help='Interval in minutes (e.g., 5, 10, 15)')
    parser.add_argument('--show', action='store_true', help='Show current interval')
    parser.add_argument('--list', action='store_true', help='List preset intervals')
    
    args = parser.parse_args()
    
    manager = IntervalManager()
    
    if args.show:
        manager.show_current_interval()
    elif args.list:
        manager.list_presets()
    elif args.interval:
        manager.set_interval(args.interval)
    else:
        # Interactive mode
        manager.show_current_interval()
        manager.list_presets()
        
        interval = input("\nEnter new interval (or press Enter to cancel): ").strip()
        if interval:
            manager.set_interval(interval)

if __name__ == "__main__":
    main()