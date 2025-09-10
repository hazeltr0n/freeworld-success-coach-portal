import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
try:
    from link_tracker import LinkTracker
except ImportError:
    LinkTracker = None
import threading
from typing import Dict, List, Any

class AnalyticsDashboard:
    """
    Analytics dashboard for FreeWorld job link tracking.
    Shows engagement metrics and link performance data.
    """
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = None
        self.link_tracker = None
        self.analytics_data = {}
        # Handle different paths for development vs built app
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running in development
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.local_tracking_file = os.path.join(base_path, "data", "link_tracking_log.json")
        
        # Initialize link tracker
        try:
            if LinkTracker:
                # Temporarily disable for demo to avoid API issues
                # self.link_tracker = LinkTracker()
                self.link_tracker = None
            else:
                self.link_tracker = None
        except Exception as e:
            print(f"Warning: Could not initialize link tracker: {e}")
            self.link_tracker = None
        
        # Load local tracking data
        self.load_local_tracking_data()
    
    def load_local_tracking_data(self):
        """Load locally stored link tracking data"""
        try:
            if os.path.exists(self.local_tracking_file):
                with open(self.local_tracking_file, 'r') as f:
                    self.analytics_data = json.load(f)
            else:
                self.analytics_data = {
                    "links_created": [],
                    "summary": {
                        "total_links": 0,
                        "links_today": 0,
                        "links_this_week": 0
                    }
                }
        except Exception as e:
            print(f"Error loading tracking data: {e}")
            self.analytics_data = {"links_created": [], "summary": {}}
    
    def save_local_tracking_data(self):
        """Save link tracking data locally"""
        try:
            os.makedirs(os.path.dirname(self.local_tracking_file), exist_ok=True)
            with open(self.local_tracking_file, 'w') as f:
                json.dump(self.analytics_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving tracking data: {e}")
    
    def log_link_creation(self, original_url: str, short_url: str, metadata: Dict[str, Any]):
        """Log when a new tracked link is created"""
        link_entry = {
            "timestamp": datetime.now().isoformat(),
            "original_url": original_url,
            "short_url": short_url,
            "metadata": metadata,
            "clicks": 0  # Will be updated when we get real analytics
        }
        
        self.analytics_data["links_created"].append(link_entry)
        self.update_summary_stats()
        self.save_local_tracking_data()
    
    def update_summary_stats(self):
        """Update summary statistics"""
        now = datetime.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        
        links_today = 0
        links_this_week = 0
        
        for link in self.analytics_data["links_created"]:
            try:
                link_date = datetime.fromisoformat(link["timestamp"]).date()
                if link_date == today:
                    links_today += 1
                if datetime.fromisoformat(link["timestamp"]) >= week_ago:
                    links_this_week += 1
            except (ValueError, KeyError, TypeError):
                continue  # Skip malformed timestamp data
        
        self.analytics_data["summary"] = {
            "total_links": len(self.analytics_data["links_created"]),
            "links_today": links_today,
            "links_this_week": links_this_week,
            "last_updated": now.isoformat()
        }
    
    def show_dashboard(self):
        """Display the analytics dashboard window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("FreeWorld Job Link Analytics")
        self.window.geometry("900x700")
        self.window.configure(bg='#f0f0f0')
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        self.create_header(main_frame)
        self.create_summary_cards(main_frame)
        self.create_links_table(main_frame)
        self.create_refresh_section(main_frame)
        
        # Initial data refresh
        self.refresh_data()
    
    def create_header(self, parent):
        """Create dashboard header"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Title
        title_label = ttk.Label(
            header_frame, 
            text="📊 FreeWorld Job Link Analytics", 
            font=('Arial', 18, 'bold')
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame, 
            text="Track engagement with job opportunities shared to Free Agents",
            font=('Arial', 10)
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
    
    def create_summary_cards(self, parent):
        """Create summary statistics cards"""
        summary_frame = ttk.LabelFrame(parent, text="Summary Statistics", padding="15")
        summary_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        summary = self.analytics_data.get("summary", {})
        
        # Total Links
        total_frame = ttk.Frame(summary_frame)
        total_frame.grid(row=0, column=0, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(total_frame, text="Total Links Created", font=('Arial', 10, 'bold')).grid(row=0, column=0)
        ttk.Label(total_frame, text=str(summary.get("total_links", 0)), font=('Arial', 24, 'bold')).grid(row=1, column=0)
        
        # Today's Links
        today_frame = ttk.Frame(summary_frame)
        today_frame.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(today_frame, text="Links Today", font=('Arial', 10, 'bold')).grid(row=0, column=0)
        ttk.Label(today_frame, text=str(summary.get("links_today", 0)), font=('Arial', 24, 'bold')).grid(row=1, column=0)
        
        # This Week's Links
        week_frame = ttk.Frame(summary_frame)
        week_frame.grid(row=0, column=2, padx=(0, 20), sticky=tk.W)
        
        ttk.Label(week_frame, text="Links This Week", font=('Arial', 10, 'bold')).grid(row=0, column=0)
        ttk.Label(week_frame, text=str(summary.get("links_this_week", 0)), font=('Arial', 24, 'bold')).grid(row=1, column=0)
        
        # Status indicator
        status_frame = ttk.Frame(summary_frame)
        status_frame.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(status_frame, text="Tracking Status", font=('Arial', 10, 'bold')).grid(row=0, column=0)
        # Show active if we have tracking data, even without live API
        has_data = len(self.analytics_data.get("links_created", [])) > 0
        status_text = "🟢 Active" if (self.link_tracker or has_data) else "🔴 Disabled"
        ttk.Label(status_frame, text=status_text, font=('Arial', 12)).grid(row=1, column=0)
    
    def create_links_table(self, parent):
        """Create table showing recent links"""
        table_frame = ttk.LabelFrame(parent, text="Recent Tracked Links", padding="15")
        table_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Create treeview
        columns = ("Date", "Job Title", "Market", "Route", "Match", "Short URL", "Clicks")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.tree.heading("Date", text="Date")
        self.tree.heading("Job Title", text="Job Title")
        self.tree.heading("Market", text="Market")
        self.tree.heading("Route", text="Route")
        self.tree.heading("Match", text="Match")
        self.tree.heading("Short URL", text="Short URL")
        self.tree.heading("Clicks", text="Clicks")
        
        # Column widths
        self.tree.column("Date", width=100)
        self.tree.column("Job Title", width=200)
        self.tree.column("Market", width=80)
        self.tree.column("Route", width=60)
        self.tree.column("Match", width=80)
        self.tree.column("Short URL", width=150)
        self.tree.column("Clicks", width=60)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.populate_links_table()
    
    def populate_links_table(self):
        """Populate the links table with data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort links by timestamp (newest first)
        links = sorted(
            self.analytics_data.get("links_created", []),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # Add recent links (last 50)
        for link in links[:50]:
            try:
                timestamp = datetime.fromisoformat(link["timestamp"])
                date_str = timestamp.strftime("%m/%d/%Y")
                
                metadata = link.get("metadata", {})
                job_title = metadata.get("title", "Unknown Job")[:30] + "..." if len(metadata.get("title", "")) > 30 else metadata.get("title", "Unknown Job")
                market = metadata.get("market", "Unknown")
                route = metadata.get("route_type", "Unknown")
                match = metadata.get("match", "Unknown")
                short_url = link.get("short_url", "")
                clicks = link.get("clicks", "N/A")
                
                self.tree.insert("", "end", values=(
                    date_str, job_title, market, route, match, short_url, clicks
                ))
            except Exception as e:
                print(f"Error adding link to table: {e}")
    
    def create_refresh_section(self, parent):
        """Create refresh and analytics section"""
        refresh_frame = ttk.Frame(parent)
        refresh_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            refresh_frame, 
            text="🔄 Refresh Data", 
            command=self.refresh_data
        )
        self.refresh_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Export button
        export_btn = ttk.Button(
            refresh_frame, 
            text="📊 Export Data", 
            command=self.export_data
        )
        export_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(refresh_frame, text="Ready")
        self.status_label.grid(row=0, column=2, padx=(20, 0))
        
        # Note about analytics
        note_label = ttk.Label(
            refresh_frame, 
            text="Note: Click analytics will be available when Short.io analytics API is accessible",
            font=('Arial', 9),
            foreground='gray'
        )
        note_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
    
    def refresh_data(self):
        """Refresh analytics data"""
        self.status_label.config(text="Refreshing...")
        self.refresh_btn.config(state='disabled')
        
        def refresh_thread():
            try:
                # Reload local data
                self.load_local_tracking_data()
                self.update_summary_stats()
                
                # TODO: When analytics API is working, fetch real click data here
                # if self.link_tracker:
                #     analytics = self.link_tracker.get_all_links_analytics()
                #     if analytics:
                #         self.update_click_counts(analytics)
                
                # Update UI in main thread
                self.window.after(0, self.refresh_ui_complete)
                
            except Exception as e:
                self.window.after(0, lambda: self.refresh_ui_error(str(e)))
        
        # Run refresh in background thread
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def refresh_ui_complete(self):
        """Complete UI refresh in main thread"""
        self.populate_links_table()
        self.status_label.config(text=f"Updated at {datetime.now().strftime('%H:%M:%S')}")
        self.refresh_btn.config(state='normal')
    
    def refresh_ui_error(self, error_msg):
        """Handle refresh error in main thread"""
        self.status_label.config(text=f"Error: {error_msg}")
        self.refresh_btn.config(state='normal')
    
    def export_data(self):
        """Export analytics data to CSV"""
        try:
            # Prepare data for export
            export_data = []
            for link in self.analytics_data.get("links_created", []):
                metadata = link.get("metadata", {})
                export_data.append({
                    "Date": link.get("timestamp", ""),
                    "Job Title": metadata.get("title", ""),
                    "Company": metadata.get("company", ""),
                    "Market": metadata.get("market", ""),
                    "Route Type": metadata.get("route_type", ""),
                    "Match Quality": metadata.get("match", ""),
                    "Original URL": link.get("original_url", ""),
                    "Short URL": link.get("short_url", ""),
                    "Clicks": link.get("clicks", 0)
                })
            
            # Create DataFrame and save
            df = pd.DataFrame(export_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"freeworld_link_analytics_{timestamp}.csv"
            df.to_csv(filename, index=False)
            
            messagebox.showinfo("Export Complete", f"Analytics data exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")


def test_analytics_dashboard():
    """Test function for analytics dashboard"""
    
    # Create some sample tracking data
    dashboard = AnalyticsDashboard()
    
    # Add some sample data
    sample_links = [
        {
            "original_url": "https://www.indeed.com/viewjob?jk=123456",
            "short_url": "https://freeworldjobs.short.gy/abc123",
            "metadata": {
                "title": "CDL Driver - Local Routes",
                "company": "FreeWorld Logistics",
                "market": "Dallas",
                "route_type": "Local",
                "match": "good"
            }
        },
        {
            "original_url": "https://www.indeed.com/viewjob?jk=789012",
            "short_url": "https://freeworldjobs.short.gy/xyz789",
            "metadata": {
                "title": "OTR Driver - Premium Routes",
                "company": "Highway Express",
                "market": "Houston",
                "route_type": "OTR",
                "match": "so-so"
            }
        }
    ]
    
    for link_data in sample_links:
        dashboard.log_link_creation(
            link_data["original_url"],
            link_data["short_url"],
            link_data["metadata"]
        )
    
    # Show dashboard
    dashboard.show_dashboard()
    
    if not dashboard.parent:
        dashboard.window.mainloop()


if __name__ == "__main__":
    test_analytics_dashboard()