#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read the README file
def read_long_description():
    try:
        with open("README.md", "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return "wifi - Automatic wifi monitoring and analysis"

# Read requirements from requirements.txt
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "speedtest-cli>=2.1.3",
            "requests>=2.31.0", 
            "beautifulsoup4>=4.12.2",
            "pysnmp>=4.4.12",
            "pyfzf>=0.3.1"
        ]

setup(
    name="wifi",
    version="1.0.0",
    author="Gracie Gould",
    author_email="user@example.com",
    description="Automatic wifi monitoring with cron scheduling and data analysis",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/wifi",
    packages=find_packages(),
    py_modules=[
        "database",
        "speed_test", 
        "device_scanner",
        "daily_rollup",
        "set_interval",
        "set_plan",
        "setup_cron",
        "cleanup",
        "view_results",
        "view_daily",
        "view_weekly",
        "wifi_monitor",
        "menu"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Internet",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "wifi=menu:main",
            "wifi-test=wifi_monitor:main",
            "wifi-menu=menu:main", 
            "wifi-view=view_results:main",
            "wifi-daily=view_daily:main",
            "wifi-weekly=view_weekly:main",
            "wifi-cleanup=cleanup:main",
            "wifi-plan=set_plan:main",
            "wifi-interval=set_interval:main",
            "wifi-cron=setup_cron:main",
            "wifi-rollup=daily_rollup:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
        "fzf": ["pyfzf>=0.3.1"],
    },
    project_urls={
        "Bug Reports": "https://github.com/username/wifi/issues",
        "Source": "https://github.com/username/wifi/",
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.rst"],
    },
    keywords="wifi speedtest monitoring cron automation network performance",
    platforms=["any"],
)