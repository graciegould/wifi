#!/usr/bin/env python3
import argparse
from database import WiFiSpeedDB

def format_status(status):
    """Add emoji indicators for status"""
    status_map = {
        'good': '✅ good',
        'meh': '⚠️ meh', 
        'bad': '❌ bad',
        'no_data': '⚫ no data'
    }
    return status_map.get(status, status)

def view_daily_summaries(limit=14):
    db = WiFiSpeedDB()
    summaries = db.get_daily_summaries(limit)
    
    if not summaries:
        print("No daily summaries found.")
        print("💡 Run: python3 daily_rollup.py --backfill")
        return
    
    print(f"\n📅 Last {len(summaries)} Daily WiFi Performance Summaries")
    print("=" * 95)
    print(f"{'Day':<12} {'Samples':<8} {'Down':<10} {'Up':<8} {'Ping':<8} {'Bad%':<6} {'Devices':<8} {'Status':<12}")
    print("-" * 95)
    
    for summary in summaries:
        day = summary[0]
        sample_count = summary[1]
        median_down = f"{summary[2]:.0f} Mbps"
        median_up = f"{summary[3]:.0f} Mbps"
        p95_ping = f"{summary[4]:.0f} ms"
        pct_bad = f"{summary[5]:.1f}%"
        avg_devices = f"{summary[6]:.0f}" if summary[6] else "?"
        status = format_status(summary[7])
        
        print(f"{day:<12} {sample_count:<8} {median_down:<10} {median_up:<8} {p95_ping:<8} {pct_bad:<6} {avg_devices:<8} {status:<12}")
    
    # Calculate overall stats
    if summaries:
        total_samples = sum(s[1] for s in summaries)
        avg_bad_pct = sum(s[5] for s in summaries) / len(summaries)
        
        good_days = len([s for s in summaries if s[7] == 'good'])
        meh_days = len([s for s in summaries if s[7] == 'meh'])
        bad_days = len([s for s in summaries if s[7] == 'bad'])
        
        print("-" * 95)
        print(f"Summary: {total_samples} total samples, {avg_bad_pct:.1f}% avg bad rate")
        print(f"Days: {good_days} good, {meh_days} meh, {bad_days} bad")

def main():
    parser = argparse.ArgumentParser(description='View daily WiFi performance summaries')
    parser.add_argument('-n', '--number', type=int, default=14,
                        help='Number of recent summaries to show (default: 14)')
    
    args = parser.parse_args()
    view_daily_summaries(args.number)

if __name__ == "__main__":
    main()