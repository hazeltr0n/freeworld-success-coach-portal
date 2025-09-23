#!/usr/bin/env python3
"""
FreeWorld Job Scraper - Complete GUI Version
Full GUI implementation with all job search functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import sys
import os
from pathlib import Path
import subprocess

# Import the job search functionality
sys.path.append(os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# SECURITY: API keys should be set via environment variables or .streamlit/secrets.toml
if not os.getenv('OPENAI_API_KEY'):
    print("⚠️  OPENAI_API_KEY not set - please configure environment variables")
if not os.getenv('OUTSCRAPER_API_KEY'):
    print("⚠️  OUTSCRAPER_API_KEY not set - please configure environment variables")

from job_scraper import FreeWorldJobScraper
from pipeline_v2 import FreeWorldJobPipeline

class FreeWorldJobScraperCompleteGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FreeWorld Job Scraper")
        self.root.geometry("800x700")
        
        # Job search state
        self.markets = {
            1: ("Houston", "Houston, TX"),
            2: ("Dallas", "Dallas, TX"), 
            3: ("Bay Area", "San Francisco, CA"),
            4: ("Stockton", "Stockton, CA"),
            5: ("Denver", "Denver, CO"),
            6: ("Vegas", "Las Vegas, NV"),
            7: ("Newark", "Newark, NJ"),
            8: ("Phoenix", "Phoenix, AZ"),
            9: ("Trenton", "Trenton, NJ"),
            10: ("Inland Empire", "Ontario, CA")
        }
        
        self.selected_markets = []
        self.search_mode = "sample"
        self.route_filter = "both"
        
        # Set icon if available
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "data", "freeworld_app_icon.icns")
            else:
                icon_path = "data/freeworld_app_icon.icns"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Setup tab
        self.setup_tab = ttk.Frame(notebook)
        notebook.add(self.setup_tab, text="Job Search Setup")
        
        # Results tab
        self.results_tab = ttk.Frame(notebook)
        notebook.add(self.results_tab, text="Results")
        
        self.setup_search_tab()
        self.setup_results_tab()
        
    def setup_search_tab(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.setup_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚛 FreeWorld Job Scraper", 
                               font=('Helvetica', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Market selection
        market_frame = ttk.LabelFrame(main_frame, text="Target Markets", padding="10")
        market_frame.pack(fill='x', pady=(0, 15))
        
        # Market checkboxes
        self.market_vars = {}
        market_grid = ttk.Frame(market_frame)
        market_grid.pack(fill='x')
        
        for i, (num, (name, location)) in enumerate(self.markets.items()):
            var = tk.BooleanVar()
            self.market_vars[num] = var
            checkbox = ttk.Checkbutton(market_grid, text=f"{name} ({location})", 
                                     variable=var)
            checkbox.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)
        
        # Search mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Search Mode", padding="10")
        mode_frame.pack(fill='x', pady=(0, 15))
        
        self.mode_var = tk.StringVar(value="sample")
        modes = [
            ("test", "Test (10 jobs) - Quick test"),
            ("sample", "Sample (100 jobs) - Balanced search"),
            ("full", "Full (1000 jobs) - Comprehensive search")
        ]
        
        for mode, description in modes:
            radio = ttk.Radiobutton(mode_frame, text=description, 
                                  variable=self.mode_var, value=mode)
            radio.pack(anchor='w', pady=2)
        
        # Route filter selection
        route_frame = ttk.LabelFrame(main_frame, text="Route Filter", padding="10")
        route_frame.pack(fill='x', pady=(0, 15))
        
        self.route_var = tk.StringVar(value="both")
        routes = [
            ("both", "All Routes - Local and OTR"),
            ("local", "Local Only - Home daily"),
            ("otr", "OTR Only - Over-the-road")
        ]
        
        for route, description in routes:
            radio = ttk.Radiobutton(route_frame, text=description,
                                  variable=self.route_var, value=route)
            radio.pack(anchor='w', pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Job Search", 
                                     command=self.start_search, width=20)
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Search", 
                                    command=self.stop_search, width=20, state='disabled')
        self.stop_button.pack(side='left')
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready to search", 
                                    foreground="green", font=('Helvetica', 10, 'bold'))
        self.status_label.pack(pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(10, 0))
        
    def setup_results_tab(self):
        # Results frame
        results_frame = ttk.Frame(self.results_tab, padding="20")
        results_frame.pack(fill='both', expand=True)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                    width=80, height=30,
                                                    font=('Monaco', 10))
        self.results_text.pack(fill='both', expand=True)
        
        # Results buttons
        button_frame = ttk.Frame(results_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Open Output Folder", 
                  command=self.open_output_folder).pack(side='left', padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_results).pack(side='left')
        
    def start_search(self):
        # Validate API key
        if not os.getenv('OPENAI_API_KEY'):
            messagebox.showerror("API Key Missing", 
                               "OpenAI API key not found!\n\n" +
                               "Please add your OpenAI API key to the .env file:\n" +
                               "OPENAI_API_KEY=your_key_here\n\n" +
                               "The .env file should be in the same folder as this app.")
            return
        
        # Validate selections
        selected_markets = [num for num, var in self.market_vars.items() if var.get()]
        
        if not selected_markets:
            messagebox.showerror("Error", "Please select at least one market")
            return
        
        # Update UI state
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Starting job search...", foreground="blue")
        self.progress.start()
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        
        # Start search in background thread
        self.search_thread = threading.Thread(target=self.run_search, 
                                            args=(selected_markets,))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def run_search(self, selected_markets):
        try:
            # Log start
            self.log_message("🚛 FreeWorld Job Scraper Starting...")
            self.log_message(f"Selected markets: {[self.markets[m][0] for m in selected_markets]}")
            self.log_message(f"Search mode: {self.mode_var.get()}")
            self.log_message(f"Route filter: {self.route_var.get()}")
            self.log_message("=" * 50)
            
            # Initialize scraper
            self.log_message("🔍 Initializing job scraper...")
            scraper = FreeWorldJobScraper()
            
            # Set search parameters based on mode
            mode = self.mode_var.get()
            if mode == "test":
                num_jobs = 10
            elif mode == "sample":
                num_jobs = 100
            else:  # full
                num_jobs = 1000
            
            # Create output directory
            output_dir = Path.home() / "Desktop" / "FreeWorld_Jobs"
            output_dir.mkdir(exist_ok=True)
            
            all_jobs = []
            
            # Search each market
            for market_num in selected_markets:
                market_name, market_location = self.markets[market_num]
                self.log_message(f"\n📍 Searching {market_name}...")
                
                # Update status
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Searching {market_name}...", foreground="blue"))
                
                try:
                    # Create search parameters for this market - Indeed only
                    search_params = {
                        'search_indeed': True,
                        'search_google': False,
                        'indeed_url': f"https://www.indeed.com/jobs?q=CDL+driver&l={market_location.replace(' ', '+')}",
                        'job_terms': 'CDL driver',
                        'location': market_location
                    }
                    
                    mode_info = {
                        'indeed_limit': num_jobs,  # All jobs from Indeed only
                        'name': mode
                    }
                    
                    self.log_message(f"  🔗 Searching Indeed for CDL jobs in {market_location}")
                    self.log_message(f"  🎯 Target: {num_jobs} jobs from Indeed")
                    self.log_message(f"  ⏳ This may take 30-60 seconds...")
                    
                    # Run search for this market
                    result = scraper.run_full_search(search_params, mode_info)
                    
                    if result is not None and not result.empty:
                        # Convert DataFrame to list of dictionaries
                        job_list = result.to_dict('records')
                        
                        # Add market info to jobs
                        for job in job_list:
                            job['market'] = market_name
                            job['market_location'] = market_location
                        
                        all_jobs.extend(job_list)
                        self.log_message(f"  ✅ Found {len(job_list)} jobs in {market_name}")
                    else:
                        self.log_message(f"  ⚠️ No jobs found in {market_name}")
                    
                except Exception as e:
                    self.log_message(f"  ❌ Error searching {market_name}: {e}")
                    import traceback
                    self.log_message(f"     Details: {traceback.format_exc()}")
            
            if not all_jobs:
                self.log_message("\n❌ No jobs found!")
                return
            
            self.log_message(f"\n📊 Total jobs found: {len(all_jobs)}")
            self.log_message("\n🔄 Processing jobs through pipeline...")
            self.log_message("  📝 Step 1: Normalizing job data...")
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(
                text="Processing jobs...", foreground="blue"))
            
            # Run through pipeline
            pipeline = FreeWorldJobPipeline()
            
            # Create temporary CSV
            import pandas as pd
            import tempfile
            df = pd.DataFrame(all_jobs)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                temp_csv = f.name
            
            try:
                # Process through pipeline
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_prefix = f"gui_search_{timestamp}"
                
                # Use first market as hardcoded market for now
                first_market = self.markets[selected_markets[0]][0]
                
                self.log_message("  🤖 Step 2: Running AI job classification...")
                self.log_message(f"     - Analyzing {len(all_jobs)} jobs for quality and route type")
                self.log_message("     - This may take 1-2 minutes depending on job count...")
                
                result = pipeline.run_full_pipeline(
                    [temp_csv],
                    output_prefix=output_prefix,
                    hardcoded_market=first_market,
                    route_filter=self.route_var.get()
                )
                
                self.log_message("  📋 Step 3: Filtering and sorting results...")
                self.log_message("  🎨 Step 4: Generating branded PDF report...")
                
                if result:
                    self.log_message("\n✅ Pipeline completed successfully!")
                    self.log_message(f"📄 Results saved to: {output_dir}")
                    
                    # Show summary
                    summary = result.get('summary', {})
                    self.log_message(f"\n📈 SUMMARY:")
                    self.log_message(f"  Initial jobs: {summary.get('initial_count', 0)}")
                    self.log_message(f"  Final included: {summary.get('final_included', 0)}")
                    self.log_message(f"  Excellent matches: {summary.get('excellent_matches', 0)}")
                    self.log_message(f"  Possible fits: {summary.get('possible_fits', 0)}")
                    
                    route_breakdown = summary.get('route_breakdown', {})
                    if route_breakdown:
                        self.log_message(f"  Local routes: {route_breakdown.get('Local', 0)}")
                        self.log_message(f"  OTR routes: {route_breakdown.get('OTR', 0)}")
                    
                    self.log_message(f"\n🎉 Job search completed successfully!")
                    
                else:
                    self.log_message("\n❌ Pipeline failed to process jobs")
                    
            finally:
                # Clean up temp file
                os.unlink(temp_csv)
            
        except Exception as e:
            self.log_message(f"\n❌ Error during search: {e}")
            import traceback
            self.log_message(f"Details: {traceback.format_exc()}")
            
        finally:
            # Update UI
            self.root.after(0, self.search_completed)
    
    def search_completed(self):
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Search completed", foreground="green")
        self.progress.stop()
        
    def stop_search(self):
        # Note: This is a simple implementation - actual thread stopping would need more work
        self.status_label.config(text="Stopping search...", foreground="orange")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress.stop()
        
    def log_message(self, message):
        """Add message to results text area"""
        def update_text():
            self.results_text.insert(tk.END, message + '\n')
            self.results_text.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            update_text()
        else:
            self.root.after(0, update_text)
    
    def open_output_folder(self):
        output_dir = Path.home() / "Desktop" / "FreeWorld_Jobs"
        if output_dir.exists():
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(output_dir)])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", str(output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_dir)])
        else:
            messagebox.showinfo("Info", f"Output folder will be created at:\n{output_dir}")
    
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = FreeWorldJobScraperCompleteGUI()
    app.run()

if __name__ == "__main__":
    main()