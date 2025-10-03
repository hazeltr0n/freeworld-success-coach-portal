#!/bin/bash
# Setup cron job for daily job health report
# Runs at 7am Central Time (12pm UTC during CST, 1pm UTC during CDT)

# Get the absolute path to the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Python path
PYTHON_PATH=$(which python3)

# Load Gmail credentials from secrets
GMAIL_CLIENT_ID="1078514472937-13053f5ap8ogtpmtkk99i0rpa84ebg5m.apps.googleusercontent.com"
GMAIL_CLIENT_SECRET="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"

# Cron job command (runs at 7am Central = 12pm UTC during Standard Time)
# Note: Adjust to 13 (1pm UTC) during Daylight Saving Time
CRON_COMMAND="0 12 * * * export GMAIL_CLIENT_ID='$GMAIL_CLIENT_ID' && export GMAIL_CLIENT_SECRET='$GMAIL_CLIENT_SECRET' && cd $PROJECT_DIR && $PYTHON_PATH market_monitor.py 72 >> $PROJECT_DIR/logs/daily_health.log 2>&1"

echo "Setting up daily job health report cron job..."
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"
echo ""
echo "Cron job will run at 7am Central Time (12pm UTC)"
echo "Command: $CRON_COMMAND"
echo ""

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "market_monitor.py"; then
    echo "⚠️  Cron job already exists. Removing old version..."
    crontab -l 2>/dev/null | grep -v "market_monitor.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "To view your cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the market_monitor.py line)"
echo "To view logs: tail -f $PROJECT_DIR/logs/daily_health.log"
echo ""
echo "Note: During Daylight Saving Time (March-November), manually adjust the hour from 12 to 13 in crontab"
