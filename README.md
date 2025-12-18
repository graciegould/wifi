

# wifi

I designed this tool so that xfinity could stop ripping me off on my wifi plans. 
Customize your plan, interval checks, and data retention to monitor your internet speed, tracking device activity, and analyzing performance trends. It features an interactive menu, automatic scheduling, and robust data management.


## Features

- **Interactive CLI Menu**: Fuzzy finder (fzf) navigation if available, or fallback to a simple numbered menu.
- **Automatic Monitoring**: Schedule speed tests every 1-60 minutes.
- **Device Tracking**: Count active devices on your network.
- **Performance Analysis**: Daily and weekly trend summaries.
- **Plan Comparison**: Track your speeds against your internet plan.
- **Forgiving Plan Setup**: All plan fields (name, download, upload) default to "default" if left blank.
- **Clear Plan**: Remove your current plan from the menu at any time.
- **Hard Exit**: Type 'exit' or press Ctrl+C at any prompt to quit immediately.
- **3-Tier Data Management**: Automatic cleanup and archival.
- **Cron Integration**: Seamless background monitoring.


## Quick Start

git clone https://github.com/graciegould/wifi.git

### Installation


**Step 1: Run the install script**

```bash
git clone https://github.com/graciegould/wifi.git
cd wifi
./install.sh --dev   # for development mode (auto-reloads changes)
# or
./install.sh         # for normal install
```


This will install the WiFi CLI commands globally for your user. The installer will automatically add the correct bin directory to your PATH if needed.



### Basic Usage

```bash
# Launch the interactive menu
wifi

# Run a single speed test
wifi-test

# View recent results
wifi-view

# Set your internet plan (all fields optional, defaults used if left blank)
wifi-plan

# Remove your current plan
wifi-clear-plan

# Setup automatic monitoring
wifi-cron
```



## Menu & Plan Setup

When you launch `wifi`, you'll see an interactive menu. If you haven't set an internet plan, you'll be prompted to do so, but you can skip this and still use basic features (speed test, view results, set plan, exit). Advanced features (summaries, device count, cron, etc.) require a plan to be set.

**Setting your plan:**
- You can set your plan from the menu or with `wifi-plan`.
- If you leave any field blank (plan name, download, upload), it will default to "default".
- You can clear your plan at any time from the menu or with `wifi-clear-plan`.

**Navigation:**
- If `fzf` is installed, you get a fuzzy finder menu. Otherwise, a simple numbered menu is shown.
- Type `exit` or press Ctrl+C at any prompt to quit immediately.

## CLI Commands

| Command         | Purpose                        |
|-----------------|--------------------------------|
| `wifi`          | Interactive menu (main interface) |
| `wifi-test`     | Run single speed test          |
| `wifi-view`     | View recent test results       |
| `wifi-daily`    | Daily performance summaries    |
| `wifi-weekly`   | Weekly trend analysis          |
| `wifi-plan`     | Set/view internet plan (all fields default if blank) |
| `wifi-clear-plan` | Remove current internet plan |
| `wifi-interval` | Configure monitoring frequency |
| `wifi-cron`     | Setup/remove cron job          |
| `wifi-cleanup`  | Data management and cleanup    |



## Performance Tracking

### Status Indicators

**Daily Status:**
- 🟢 **Good**: <10% bad samples
- 🟡 **Meh**: 10-30% bad samples
- 🔴 **Bad**: >30% bad samples

**Weekly Status:**
- 🟦 **Excellent**: 5+ good days
- 🟩 **Good**: 5+ good/meh days
- 🟧 **Poor**: 3+ good/meh days
- 🟥 **Bad**: Mostly bad days

### Status Indicators

**Daily Status:**
-  **Good**: <10% bad samples
- � **Meh**: 10-30% bad samples  
- L **Bad**: >30% bad samples

**Weekly Status:**
- < **Excellent**: 5+ good days
-  **Good**: 5+ good/meh days
- � **Poor**: 3+ good/meh days
- L **Bad**: Mostly bad days



## Data Lifecycle

**3-Tier Storage System:**
1. **Raw Data** (30 days): Individual speed tests
2. **Daily Summaries** (365 days): Aggregated daily metrics
3. **Weekly Summaries** (52 weeks): Sunday-to-Sunday trends

