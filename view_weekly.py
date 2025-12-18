#!/usr/bin/env python3
import argparse
from database import WiFiSpeedDB

def format_weekly_status(status):
    """Add emoji indicators for weekly status"""
    status_map = {
        'excellent': '🌟 excellent',
        'good': '✅ good',
        'poor': '⚠️ poor', 
        'bad': '❌ bad'
    }
    return status_map.get(status, status)

def format_week_range(week_start, week_end):
    """Format week range as readable string"""
    from datetime import datetime
    try:
        start_dt = datetime.fromisoformat(week_start)
        end_dt = datetime.fromisoformat(week_end)
        
        # If same month, show "Dec 15-21"
        if start_dt.month == end_dt.month:
            return f"{start_dt.strftime('%b %d')}-{end_dt.strftime('%d')}"
        else:
            # Different months, show "Dec 30 - Jan 5"
            return f"{start_dt.strftime('%b %d')} - {end_dt.strftime('%b %d')}"
    except:
        return f"{week_start} to {week_end}"

def view_weekly_summaries(limit=12):
    db = WiFiSpeedDB()
    summaries = db.get_weekly_summaries(limit)
    
    if not summaries:
        print("No weekly summaries found.")
        print("💡 Weekly summaries are created automatically from daily data")
        print("💡 Run: python3 cleanup.py --auto to trigger weekly rollup")
        return
    
    print(f"\n📅 Last {len(summaries)} Weekly WiFi Performance Summaries")
    print("=" * 110)
    print(f"{'Week':<12} {'Days':<5} {'Samples':<8} {'Down':<10} {'Up':<8} {'Ping':<8} {'Bad%':<6} {'Good/Meh/Bad':<12} {'Status':<15}")
    print("-" * 110)
    
    for summary in summaries:
        week_range = format_week_range(summary[0], summary[1])
        days_with_data = summary[2]
        total_samples = summary[3]
        avg_download = f"{summary[4]:.0f} Mbps"
        avg_upload = f"{summary[5]:.0f} Mbps"
        avg_ping = f"{summary[6]:.0f} ms"
        weekly_pct_bad = f"{summary[7]:.1f}%"
        
        # Day breakdown
        good_days = summary[8]
        meh_days = summary[9] 
        bad_days = summary[10]
        no_data_days = summary[11]
        day_breakdown = f"{good_days}/{meh_days}/{bad_days}"
        
        status = format_weekly_status(summary[12])
        
        print(f"{week_range:<12} {days_with_data:<5} {total_samples:<8} {avg_download:<10} {avg_upload:<8} {avg_ping:<8} {weekly_pct_bad:<6} {day_breakdown:<12} {status:<15}")
    
    # Calculate overall trends
    if summaries:
        recent_4_weeks = summaries[:4] if len(summaries) >= 4 else summaries
        
        avg_weekly_samples = sum(s[3] for s in recent_4_weeks) / len(recent_4_weeks)
        avg_weekly_down = sum(s[4] for s in recent_4_weeks) / len(recent_4_weeks)
        avg_weekly_up = sum(s[5] for s in recent_4_weeks) / len(recent_4_weeks)
        avg_weekly_bad = sum(s[7] for s in recent_4_weeks) / len(recent_4_weeks)
        
        excellent_weeks = len([s for s in recent_4_weeks if s[12] == 'excellent'])
        good_weeks = len([s for s in recent_4_weeks if s[12] == 'good'])
        poor_weeks = len([s for s in recent_4_weeks if s[12] == 'poor'])
        bad_weeks = len([s for s in recent_4_weeks if s[12] == 'bad'])
        
        print("-" * 110)
        print(f"4-Week Average: {avg_weekly_samples:.0f} samples, {avg_weekly_down:.0f} Mbps down, {avg_weekly_up:.0f} Mbps up, {avg_weekly_bad:.1f}% bad")
        print(f"Week Quality: {excellent_weeks} excellent, {good_weeks} good, {poor_weeks} poor, {bad_weeks} bad")
        
        # Trend analysis
        if len(summaries) >= 2:
            latest_bad = summaries[0][7]
            previous_bad = summaries[1][7] 
            
            if latest_bad < previous_bad - 5:
                print("📈 Trend: Performance improving")
            elif latest_bad > previous_bad + 5:
                print("📉 Trend: Performance declining")
            else:
                print("➡️ Trend: Stable performance")

def main():
    parser = argparse.ArgumentParser(description='View weekly WiFi performance summaries')
    parser.add_argument('-n', '--number', type=int, default=12,
                        help='Number of recent weekly summaries to show (default: 12)')
    
    args = parser.parse_args()
    view_weekly_summaries(args.number)

if __name__ == "__main__":
    main()