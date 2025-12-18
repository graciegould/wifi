#!/usr/bin/env python3
import argparse
from database import WiFiSpeedDB

def set_plan_speeds(plan_name, download_mbps, upload_mbps):
    db = WiFiSpeedDB()
    db.set_plan_speed(plan_name, download_mbps, upload_mbps)
    
    print(f"✅ Internet plan updated:")
    print(f"   Plan: {plan_name}")
    print(f"   Download: {download_mbps} Mbps")
    print(f"   Upload: {upload_mbps} Mbps")

def show_current_plan():
    db = WiFiSpeedDB()
    plan = db.get_current_plan()
    
    if plan:
        print(f"📋 Current Plan: {plan[1]}")
        print(f"   Download: {plan[2]} Mbps")
        print(f"   Upload: {plan[3]} Mbps")
        print(f"   Set on: {plan[4]}")
    else:
        print("❌ No internet plan configured")
        print("💡 Use: python3 set_plan.py \"1 Gig Plan\" 1000 100")

def main():
    parser = argparse.ArgumentParser(description='Set your internet plan speeds for comparison')
    parser.add_argument('plan_name', nargs='?', help='Name of your internet plan')
    parser.add_argument('download_mbps', nargs='?', type=float, help='Download speed in Mbps')
    parser.add_argument('upload_mbps', nargs='?', type=float, help='Upload speed in Mbps')
    parser.add_argument('--show', action='store_true', help='Show current plan')
    
    args = parser.parse_args()
    
    if args.show:
        show_current_plan()
    elif args.plan_name and args.download_mbps and args.upload_mbps:
        set_plan_speeds(args.plan_name, args.download_mbps, args.upload_mbps)
    else:
        show_current_plan()
        print("\n💡 To update plan:")
        print('   python3 set_plan.py "1 Gig Plan" 1000 100')

if __name__ == "__main__":
    main()