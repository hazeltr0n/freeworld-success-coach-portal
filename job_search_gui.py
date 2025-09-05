#!/usr/bin/env python3
"""
FreeWorld Job Scraper - GUI Version
Simple GUI launcher for the job scraper app
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import sys
import os
import threading
from pathlib import Path

class FreeWorldJobScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FreeWorld Job Scraper")
        self.root.geometry("800x600")
        
        # Set icon if available
        try:
            if getattr(sys, 'frozen', False):
                # PyInstaller bundle
                icon_path = os.path.join(sys._MEIPASS, "data", "freeworld_app_icon.icns")
            else:
                icon_path = "data/freeworld_app_icon.icns"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🚛 FreeWorld Job Scraper", 
                               font=('Helvetica', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Instructions
        instructions = """This app helps FreeWorld find quality CDL driver positions.
        
Click 'Launch Job Scraper' to open the interactive terminal where you can:
• Select target markets
• Choose search parameters  
• Generate branded PDF reports

The scraper will open in a new terminal window."""
        
        instruction_label = ttk.Label(main_frame, text=instructions, 
                                    justify=tk.LEFT, wraplength=500)
        instruction_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Launch button
        self.launch_button = ttk.Button(main_frame, text="Launch Job Scraper", 
                                      command=self.launch_scraper,
                                      width=30)
        self.launch_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to launch", 
                                     foreground="green")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E))
        
        info_text = """• Results saved to: ~/Desktop/FreeWorld_Jobs/
• Requires OpenAI API key in .env file
• Internet connection required for job scraping"""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.grid(row=0, column=0)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
    def launch_scraper(self):
        """Launch the job scraper in a terminal window"""
        self.status_label.config(text="Launching scraper...", foreground="blue")
        self.launch_button.config(state='disabled')
        
        # Get the path to the standalone script
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            script_path = os.path.join(sys._MEIPASS, "src", "job_search_form_standalone.py")
            python_cmd = sys.executable
        else:
            # Running as normal Python script
            script_path = os.path.join(os.path.dirname(__file__), "job_search_form_standalone.py")
            python_cmd = sys.executable
        
        # Create the command to run in terminal
        cmd = f'cd "{os.path.dirname(script_path)}" && "{python_cmd}" "{script_path}"'
        
        # Platform-specific terminal launch
        if sys.platform == "darwin":  # macOS
            # Use osascript to open Terminal and run the command
            apple_script = f'''
            tell application "Terminal"
                do script "{cmd}"
                activate
            end tell
            '''
            try:
                subprocess.run(["osascript", "-e", apple_script], check=True)
                self.status_label.config(text="Scraper launched in Terminal!", foreground="green")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Launch Error", f"Failed to launch Terminal: {e}")
                self.status_label.config(text="Launch failed", foreground="red")
        elif sys.platform == "win32":  # Windows
            # Open command prompt with the script
            try:
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", cmd])
                self.status_label.config(text="Scraper launched in Command Prompt!", foreground="green")
            except Exception as e:
                messagebox.showerror("Launch Error", f"Failed to launch Command Prompt: {e}")
                self.status_label.config(text="Launch failed", foreground="red")
        else:  # Linux/Unix
            # Try various terminal emulators
            terminals = ["gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
            launched = False
            for terminal in terminals:
                try:
                    subprocess.Popen([terminal, "-e", f"bash -c '{cmd}; read -p \"Press Enter to close...\"'"])
                    self.status_label.config(text=f"Scraper launched in {terminal}!", foreground="green")
                    launched = True
                    break
                except:
                    continue
            
            if not launched:
                messagebox.showerror("Launch Error", "Could not find a suitable terminal emulator")
                self.status_label.config(text="Launch failed", foreground="red")
        
        # Re-enable button after a delay
        self.root.after(2000, lambda: self.launch_button.config(state='normal'))
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = FreeWorldJobScraperGUI()
    app.run()

if __name__ == "__main__":
    main()