#!/usr/bin/env python3
import os
import sys
from speed_test import WiFiSpeedTester

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    tester = WiFiSpeedTester()
    success = tester.run_speed_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()