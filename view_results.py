#!/usr/bin/env python3
import argparse
from database import WiFiSpeedDB
from datetime import datetime

def format_timestamp(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def view_results(limit=10):
    db = WiFiSpeedDB()
    plan = db.get_current_plan()
    results = db.get_speed_test_with_plan_comparison(limit)
    
    if not results:
        print("No speed test results found.")
        return
    
    if plan:
        print(f"📋 Current Plan: {plan[1]} (Down: {plan[2]} Mbps, Up: {plan[3]} Mbps)")
        print("=" * 105)
        print(f"{'Timestamp':<20} {'Download':<15} {'Upload':<13} {'Ping':<8} {'Devices':<8} {'Performance':<15} {'Server':<20}")
        print("-" * 105)
        
        for result in results:
            timestamp = format_timestamp(result[1])
            download = f"{result[2]:.1f} Mbps"
            upload = f"{result[3]:.1f} Mbps"
            ping = f"{result[4]:.1f} ms"
            devices = str(result[7]) if result[7] is not None else "?"
            server = result[5] if result[5] else "Unknown"
            
            if result[9] and result[10]:
                performance = f"↓{result[9]:.0f}% ↑{result[10]:.0f}%"
            else:
                performance = "No plan set"
            
            print(f"{timestamp:<20} {download:<15} {upload:<13} {ping:<8} {devices:<8} {performance:<15} {server:<20}")
    else:
        print("⚠️  No internet plan configured. Set one with: python3 set_plan.py")
        print(f"\n📊 Last {len(results)} WiFi Speed Test Results:")
        print("=" * 90)
        print(f"{'Timestamp':<20} {'Download':<12} {'Upload':<10} {'Ping':<8} {'Devices':<8} {'Server':<25}")
        print("-" * 90)
        
        for result in results:
            timestamp = format_timestamp(result[1])
            download = f"{result[2]:.1f} Mbps"
            upload = f"{result[3]:.1f} Mbps"
            ping = f"{result[4]:.1f} ms"
            devices = str(result[7]) if result[7] is not None else "?"
            server = result[5] if result[5] else "Unknown"
            
            print(f"{timestamp:<20} {download:<12} {upload:<10} {ping:<8} {devices:<8} {server:<25}")
    
    if results:
        avg_download = sum(r[2] for r in results) / len(results)
        avg_upload = sum(r[3] for r in results) / len(results)
        avg_ping = sum(r[4] for r in results) / len(results)
        
        print("-" * 105 if plan else "-" * 90)
        print(f"{'Average:':<20} {avg_download:.1f} Mbps {avg_upload:.1f} Mbps {avg_ping:.1f} ms")
        
        if plan and any(r[9] for r in results if r[9]):
            avg_down_perf = sum(r[9] for r in results if r[9]) / len([r for r in results if r[9]])
            avg_up_perf = sum(r[10] for r in results if r[10]) / len([r for r in results if r[10]])
            print(f"{'Performance:':<20} ↓{avg_down_perf:.0f}% ↑{avg_up_perf:.0f}% of plan speeds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='View WiFi speed test results')
    parser.add_argument('-n', '--number', type=int, default=10, 
                        help='Number of recent results to show (default: 10)')
    
    args = parser.parse_args()
    view_results(args.number)