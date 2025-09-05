#!/usr/bin/env python3
"""
GUI Launcher for FreeWorld Job Scraper
This launches Terminal and runs the console app when double-clicked
"""
import subprocess
import sys
import os

def main():
    """Launch the job scraper in Terminal"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - get the app bundle path
        app_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))  # Go up to .app level
        console_executable = os.path.join(app_path, "Contents", "Resources", "console_scraper")
        
        # Check if we have a console version, if not, create a simple runner script
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(f'''#!/bin/bash
echo "🚛 Starting FreeWorld Job Scraper..."
cd "{os.path.dirname(sys.executable)}"

# Try to run the bundled Python with our modules
export PYTHONPATH="{sys._MEIPASS}"
python3 -c "
import sys
sys.path.insert(0, '{sys._MEIPASS}')

# Set API keys
import os
# SECURITY: API key should be set via environment variable or st.secrets
# os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'
os.environ['OUTSCRAPER_API_KEY'] = 'NmY3ZWU2ZDY4ZDE3NDE3YWJhNzM2NzJlN2NkMzU5ZmV8MzQwNWIyYmQ2ZA'

# Import and run the job scraper
exec(open('{sys._MEIPASS}/job_search_form_standalone.py').read(), {{'__file__': '{sys._MEIPASS}/job_search_form_standalone.py'}})
"

echo ""
echo "Press Enter to close this window..."
read
rm "{f.name}"
''')
            script_path = f.name
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # AppleScript to open Terminal and run our script
        applescript = f'''
        tell application "Terminal"
            activate
            do script "{script_path}"
        end tell
        '''
    else:
        # Development mode
        script_path = os.path.join(os.path.dirname(__file__), 'job_search_form_standalone.py')
        applescript = f'''
        tell application "Terminal"
            activate
            do script "cd '{os.path.dirname(__file__)}' && python3 '{script_path}'"
        end tell
        '''
    
    # Execute the AppleScript
    try:
        subprocess.run(['osascript', '-e', applescript], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch Terminal: {e}")
    except FileNotFoundError:
        print("osascript not found. This app only works on macOS.")

if __name__ == "__main__":
    main()