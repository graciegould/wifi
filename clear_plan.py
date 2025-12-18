#!/usr/bin/env python3
"""
clear_plan.py - Remove the current internet plan from the wifi database.
"""
from database import WiFiSpeedDB

def main():
    db = WiFiSpeedDB()
    plan = db.get_current_plan()
    if not plan:
        print("No internet plan is currently set.")
        return
    confirm = input(f"Are you sure you want to clear the current plan '{plan[1]}'? (y/n): ").strip().lower()
    if confirm == 'y':
        db.clear_current_plan() if hasattr(db, 'clear_current_plan') else db.set_current_plan(None, None, None)
        print("✅ Internet plan cleared.")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()
