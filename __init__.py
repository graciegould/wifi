"""
WiFi Speed Monitor
==================

A comprehensive WiFi speed monitoring system with automatic scheduling,
data analysis, and performance tracking.

Features:
- Automatic speed tests every N minutes
- Daily and weekly performance summaries  
- Device count monitoring
- 3-tier data lifecycle management
- Interactive CLI with fuzzy search
- Plan comparison and analysis

Usage:
    wifi           # Launch interactive menu
    wifi-test      # Run single speed test
    wifi-view      # View recent results
    wifi-daily     # View daily summaries
    wifi-weekly    # View weekly trends
    wifi-cleanup   # Manage data storage
"""

__version__ = "1.0.0"
__author__ = "WiFi Monitor User"
__email__ = "user@example.com"

# Import main modules for easier access
from . import database
from . import speed_test
from . import menu

__all__ = [
    "database",
    "speed_test", 
    "menu",
]