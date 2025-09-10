#!/usr/bin/env python3
"""
FreeWorld Job Scraper - GUI Wrapper
Preserves ALL functionality from job_search_form_standalone.py with a GUI interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
from pathlib import Path
import subprocess
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Add paths for both development and PyInstaller bundled modes
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# For PyInstaller bundled app, also add the bundled src directory
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    bundled_src = os.path.join(bundle_dir, 'src')
    if os.path.exists(bundled_src):
        sys.path.insert(0, bundled_src)
        print(f"Added PyInstaller bundled src path: {bundled_src}")

# Import the WORKING terminal search instead of pipeline_v2 form
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from terminal_job_search import EnhancedTerminalJobSearch
from shared_search import MARKET_SEARCH_QUERIES, build_indeed_query_url

class FreeWorldJobScraperGUIWrapper:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚚 FreeWorld Job Scraper v1.0 - Find Your Next Opportunity")
        self.root.geometry("1200x800")  # Increased height for settings tab
        self.root.minsize(1100, 750)  # Minimum size to see all content including settings
        
        # FreeWorld brand colors
        self.colors = {
            'primary_green': '#00B04F',      # FreeWorld primary green
            'light_green': '#4CAF50',        # Lighter, readable green
            'dark_green': '#388E3C',         # Darker green for accents
            'background': '#F8F9FA',         # Light background
            'card_bg': '#FFFFFF',            # White cards
            'text_primary': '#212121',       # Dark text
            'text_secondary': '#666666',     # Secondary text
            'accent_orange': '#FF6B35',      # Accent color for highlights
        }
        
        # Set root background
        self.root.configure(bg=self.colors['background'])
        
        # Initialize the WORKING terminal search backend (pipeline_v3 + Supabase)
        self.terminal_search = EnhancedTerminalJobSearch()
        
        # Keep GUI market structure but use terminal backend
        class MockCLIForm:
            def __init__(self, terminal_search):
                # Use the shared market mapping
                self.MARKET_SEARCH_QUERIES = MARKET_SEARCH_QUERIES
                self.terminal_search = terminal_search
                
            def build_indeed_url(self, search_term, location, radius, no_experience=True):
                return build_indeed_query_url(search_term, location, int(radius), no_experience)
        
        self.cli_form = MockCLIForm(self.terminal_search)
        
        # Configure custom styles
        self.setup_styles()
        
        # State variables to mirror CLI inputs
        self.selected_markets = []
        self.search_terms = []
        self.route_filter = "both"
        self.mode_info = {"mode": "sample", "limit": 100, "use_multi_search": False}
        
        # Set icon if available
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "data", "freeworld_app_icon.icns")
            else:
                icon_path = "data/freeworld_app_icon.icns"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except (FileNotFoundError, OSError):
            pass  # Icon file not found or not supported
        
        self.setup_ui()

    # ----- Utility: sanitize text for clipboard/files -----
    def _sanitize_text(self, text: str) -> str:
        try:
            import re, unicodedata
            # Remove NUL and other non-printable control chars except tab/newline/carriage return
            text = text.replace('\x00', '')
            text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
            # Normalize unicode and drop invalid surrogates
            text = unicodedata.normalize('NFC', text)
            text = text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
            return text
        except Exception:
            # Fallback best-effort
            try:
                return text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
            except Exception:
                return text
    
    def setup_styles(self):
        """Configure custom ttk styles for FreeWorld branding"""
        style = ttk.Style()
        
        # Configure main frame style
        style.configure('Card.TFrame', 
                       background=self.colors['card_bg'],
                       relief='raised',
                       borderwidth=1)
        
        # Configure header labels
        style.configure('Header.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['primary_green'],
                       font=('Helvetica', 26, 'bold'))
        
        # Configure subheader labels  
        style.configure('Subheader.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['text_secondary'],
                       font=('Helvetica', 14))
        
        # Configure primary buttons with FreeWorld styling
        style.configure('Primary.TButton',
                       background=self.colors['primary_green'],
                       foreground='white',
                       font=('Helvetica', 14, 'bold'),
                       padding=(20, 10))
        
        # Configure secondary buttons
        style.configure('Secondary.TButton',
                       background=self.colors['accent_orange'],
                       foreground='white', 
                       font=('Helvetica', 12, 'bold'),
                       padding=(15, 8))
        
        # Configure labelframes with green headers
        style.configure('Green.TLabelframe',
                       background=self.colors['background'],
                       borderwidth=2)
        style.configure('Green.TLabelframe.Label',
                       background=self.colors['background'],
                       foreground=self.colors['dark_green'],
                       font=('Helvetica', 13, 'bold'))
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Setup tab
        self.setup_tab = ttk.Frame(notebook)
        notebook.add(self.setup_tab, text="🚚 Job Search Command Center")
        
        # Results tab
        self.results_tab = ttk.Frame(notebook)
        notebook.add(self.results_tab, text="📈 Live Results & Progress")
        
        # Analytics tab
        self.analytics_tab = ttk.Frame(notebook)
        notebook.add(self.analytics_tab, text="📊 Link Performance Analytics")
        
        # Settings tab
        self.settings_tab = ttk.Frame(notebook)
        notebook.add(self.settings_tab, text="⚙️ Settings & Filters")
        
        self.setup_configuration_tab()
        self.setup_results_tab()
        self.setup_settings_tab()
        self.setup_analytics_tab()
        
    def setup_configuration_tab(self):
        # Main frame - improved padding for larger window
        main_frame = ttk.Frame(self.setup_tab, padding="10", style='Card.TFrame')
        main_frame.pack(fill='both', expand=True)
        
        # COMPACT HEADER - Side by side layout
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 5))
        
        # Left side - Title and tagline
        title_frame = ttk.Frame(header_frame, style='Card.TFrame')
        title_frame.pack(side='left', fill='x', expand=True)
        
        title_label = ttk.Label(title_frame, text="🚚 FreeWorld Job Scraper v1.0", 
                               font=('Helvetica', 20, 'bold'), foreground=self.colors['primary_green'])
        title_label.pack(anchor='w')
        
        subtitle_label = ttk.Label(title_frame, text="🚀 AI-Powered Multi-Market CDL Job Discovery Engine", 
                                 font=('Helvetica', 12), foreground='white')
        subtitle_label.pack(anchor='w')
        
        tagline_label = ttk.Label(title_frame, text="💪 Find Quality Opportunities • 🎯 Smart Memory", 
                                 font=('Helvetica', 11, 'bold'), foreground=self.colors['primary_green'])
        tagline_label.pack(anchor='w', pady=(3, 0))
        
        # No logo - clean header design
        
        # TWO COLUMN LAYOUT for main content - improved proportions
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, pady=(5, 10))
        
        # LEFT COLUMN - 60% width for input controls
        left_column = ttk.Frame(content_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Add weight configuration to better distribute space
        content_frame.grid_columnconfigure(0, weight=3)  # Left column gets more space
        content_frame.grid_columnconfigure(1, weight=2)  # Right column gets less space
        
        # === Step 1: Market Selection (Left) ===
        market_frame = ttk.LabelFrame(left_column, text="🗺️ Step 1: Markets & Location", 
                                     padding="8", style='Green.TLabelframe')
        market_frame.pack(fill='x', pady=(0, 8))
        
        # Remove redundant instruction label to save space
        
        # Market checkboxes in a more compact grid
        self.market_vars = {}
        markets_grid = ttk.Frame(market_frame)
        markets_grid.pack(fill='x', pady=(2, 0))
        
        # Display human-friendly market labels using location names; keep internal keys as market IDs
        for i, (market_id, location) in enumerate(self.cli_form.MARKET_SEARCH_QUERIES.items()):
            var = tk.BooleanVar()
            self.market_vars[market_id] = var
            checkbox = ttk.Checkbutton(
                markets_grid,
                text=f"{location}",  # show location name (e.g., Houston, TX)
                variable=var,
                command=self.update_configuration_preview
            )
            checkbox.grid(row=i//4, column=i%4, sticky='w', padx=(0, 8), pady=0)
        
        # Custom location input (inline with examples)
        custom_frame = ttk.Frame(market_frame)
        custom_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(custom_frame, text="Custom:", font=('Helvetica', 11)).pack(side='left')
        self.custom_location_entry = ttk.Entry(custom_frame, width=20)
        self.custom_location_entry.pack(side='left', padx=(5, 0))
        self.custom_location_entry.bind('<KeyRelease>', lambda e: self.on_custom_location_changed())
        
        # Examples label to the right - accessible contrast
        # Using dark green (#388E3C) for better contrast ratio on white background
        # Meets WCAG AA standard (4.5:1 ratio) unlike light green which only has 2.9:1
        ttk.Label(custom_frame, text="(Ex: Dallas, TX or 73401)", 
                 font=('Helvetica', 12), foreground=self.colors['dark_green']).pack(side='left', padx=(8, 0))
        
        # === Step 2: Search Terms (Left) ===
        terms_frame = ttk.LabelFrame(left_column, text="🔍 Step 2: Search Terms", 
                                    padding="8", style='Green.TLabelframe')
        terms_frame.pack(fill='x', pady=(0, 8))
        
        # Add explanation
        ttk.Label(terms_frame, text="Enter terms separated by commas (Ex: CDL Driver, Truck Driver, Delivery Driver)", 
                 font=('Helvetica', 12), foreground='white').pack(anchor='w', pady=(0, 3))
        
        self.terms_entry = tk.Text(terms_frame, height=2, width=30)
        self.terms_entry.pack(fill='x', pady=(2, 0))
        self.terms_entry.insert('1.0', "CDL Driver")
        self.terms_entry.bind('<KeyRelease>', lambda e: self.update_configuration_preview())
        
        # === Step 3: Route Filter (Left) ===
        route_frame = ttk.LabelFrame(left_column, text="🚛 Step 3: Route Type", 
                                    padding="5", style='Green.TLabelframe')
        route_frame.pack(fill='x', pady=(0, 3))
        
        self.route_var = tk.StringVar(value="both")
        routes = [
            ("both", "Both (Local & OTR)"),
            ("local", "Local only"),
            ("otr", "OTR only")
        ]
        
        # Inline radio buttons to save space
        radio_frame = ttk.Frame(route_frame)
        radio_frame.pack(fill='x')
        
        for i, (route, description) in enumerate(routes):
            radio = ttk.Radiobutton(radio_frame, text=description,
                                  variable=self.route_var, value=route,
                                  command=self.update_configuration_preview)
            radio.pack(side='left', padx=(0, 10) if i < len(routes)-1 else (0, 0))
        
        # === Step 4: Search Radius (Left) ===
        radius_frame = ttk.LabelFrame(left_column, text="📍 Step 4: Search Radius", 
                                     padding="5", style='Green.TLabelframe')
        radius_frame.pack(fill='x', pady=(0, 3))
        
        self.radius_var = tk.StringVar(value="50")
        # Indeed standard radius options
        radii = [
            ("0", "Exact location"),
            ("10", "10 miles"),
            ("25", "25 miles"), 
            ("50", "50 miles"),
            ("100", "100 miles")
        ]
        
        # Two rows of radio buttons for compact layout
        radius_grid = ttk.Frame(radius_frame)
        radius_grid.pack(fill='x')
        
        for i, (radius, description) in enumerate(radii):
            radio = ttk.Radiobutton(radius_grid, text=description,
                                  variable=self.radius_var, value=radius,
                                  command=self.update_configuration_preview)
            radio.grid(row=i//3, column=i%3, sticky='w', padx=(0, 8), pady=0)
        
        # === Step 5: Experience Filter (Left) ===
        experience_frame = ttk.LabelFrame(left_column, text="💼 Step 5: Experience Filter", 
                                         padding="5", style='Green.TLabelframe')
        experience_frame.pack(fill='x', pady=(0, 3))
        
        self.experience_var = tk.StringVar(value="no_experience")
        experience_options = [
            ("no_experience", "No experience required"),
            ("any_experience", "Any experience level")
        ]
        
        # Inline radio buttons
        experience_radio_frame = ttk.Frame(experience_frame)
        experience_radio_frame.pack(fill='x')
        
        for i, (exp_value, description) in enumerate(experience_options):
            radio = ttk.Radiobutton(experience_radio_frame, text=description,
                                  variable=self.experience_var, value=exp_value,
                                  command=self.update_configuration_preview)
            radio.pack(side='left', padx=(0, 15) if i < len(experience_options)-1 else (0, 0))
        
        # === Step 6: Smart Memory (Left) ===
        airtable_frame = ttk.LabelFrame(left_column, text="📊 Step 6: Smart Memory", 
                                       padding="5", style='Green.TLabelframe')
        airtable_frame.pack(fill='x', pady=(0, 3))
        
        self.airtable_upload_var = tk.BooleanVar(value=True)
        airtable_checkbox = ttk.Checkbutton(
            airtable_frame,
            text="Upload to Airtable",
            variable=self.airtable_upload_var,
            command=self.update_configuration_preview
        )
        airtable_checkbox.pack(anchor='w')
        ttk.Frame(airtable_frame, height=4).pack(fill='x')

        # Note: Force Fresh toggle is placed in Step 9 (Search Mode) for reliable visibility
        
        # Steps 7 & 8 moved to right column for better balance
        
        # RIGHT COLUMN - preview, output, and controls
        right_column = ttk.Frame(content_frame)
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # === Step 7: Output Folder (Right) ===
        output_frame = ttk.LabelFrame(right_column, text="📁 Step 7: Output Folder", 
                                     padding="8", style='Green.TLabelframe')
        output_frame.pack(fill='x', pady=(0, 8))
        
        # Output folder selection
        folder_selection_frame = ttk.Frame(output_frame)
        folder_selection_frame.pack(fill='x')
        
        # Default to Desktop
        import os
        default_output = os.path.join(os.path.expanduser("~"), "Desktop")
        self.output_folder_var = tk.StringVar(value=default_output)
        
        # Folder path display (read-only)
        self.folder_display = tk.Entry(folder_selection_frame, textvariable=self.output_folder_var, 
                                      state='readonly', font=('Monaco', 10))
        self.folder_display.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Browse button
        browse_button = ttk.Button(folder_selection_frame, text="Browse...", 
                                  command=self.browse_output_folder)
        browse_button.pack(side='right')
        
        # === Step 8: Output Options (Right) ===
        output_options_frame = ttk.LabelFrame(right_column, text="📄 Step 8: Output Options", 
                                            padding="5", style='Green.TLabelframe')
        output_options_frame.pack(fill='x', pady=(0, 3))
        
        # Output format checkboxes
        format_frame = ttk.Frame(output_options_frame)
        format_frame.pack(fill='x')
        
        self.generate_pdf_var = tk.BooleanVar(value=True)  # Default: PDF enabled (mobile-optimized)
        self.generate_csv_var = tk.BooleanVar(value=False)  # Default: CSV disabled
        
        pdf_checkbox = ttk.Checkbutton(format_frame, text="📱 Generate Mobile-Optimized PDF Report", 
                                      variable=self.generate_pdf_var,
                                      command=self.update_configuration_preview)
        pdf_checkbox.pack(anchor='w')
        
        csv_checkbox = ttk.Checkbutton(format_frame, text="📊 Generate CSV Files", 
                                      variable=self.generate_csv_var,
                                      command=self.update_configuration_preview)
        csv_checkbox.pack(anchor='w')
        
        # Info label - bigger and light green
        ttk.Label(output_options_frame, text="💡 Mobile PDF optimized for phones & viewable on desktop",
                 font=('Helvetica', 12, 'bold'), foreground='#4CAF50').pack(pady=(5, 0))
        
        # === Step 9: Search Mode (Right) ===
        mode_frame = ttk.LabelFrame(right_column, text="⚡ Step 9: Search Mode", 
                                   padding="5", style='Green.TLabelframe')
        # Let this section grow so the last child (checkbox) never gets clipped
        mode_frame.pack(fill='x', expand=True, pady=(0, 3))
        try:
            mode_frame.pack_propagate(False)
            mode_frame.configure(height=160)
        except Exception:
            pass
        
        self.mode_var = tk.StringVar(value="sample")
        # Accurate pricing: scraping + AI classification
        modes = [
            ("test", "Test (10 jobs) - $0.013"),
            ("sample", "Sample (100 jobs) - $0.13"),
            ("medium", "Medium (250 jobs) - $0.33"),
            ("large", "Large (500 jobs) - $0.65"),
            ("full", "Full (1000 jobs) - $1.30")
        ]
        
        # Two columns of radio buttons
        mode_grid = ttk.Frame(mode_frame)
        mode_grid.pack(fill='x')
        
        for i, (mode, description) in enumerate(modes):
            radio = ttk.Radiobutton(mode_grid, text=description, 
                                  variable=self.mode_var, value=mode,
                                  command=self.update_configuration_preview)
            radio.grid(row=i//2, column=i%2, sticky='w', padx=(0, 10), pady=0)
        
        # Dynamic cost preview - larger, light green text
        self.cost_preview_label = ttk.Label(mode_frame, text="📊 Your cost: Select options above", 
                                          font=('Helvetica', 14, 'bold'), foreground='#4CAF50')
        self.cost_preview_label.pack(pady=(6, 2))

        # Dedicated sub-frame for Force Fresh with padding to ensure visibility
        fresh_container = ttk.Frame(mode_frame)
        fresh_container.pack(fill='x', pady=(4, 2))
        # Reuse existing variable if already created (from earlier sessions)
        self.force_fresh_var = getattr(self, 'force_fresh_var', tk.BooleanVar(value=False))
        fresh_checkbox_mode = ttk.Checkbutton(
            fresh_container,
            text="🔄 Force Fresh Jobs (bypass cost savings)",
            variable=self.force_fresh_var,
            command=self.update_configuration_preview
        )
        fresh_checkbox_mode.pack(side='left', anchor='w', padx=(2, 0), ipady=2)
        
        # === Step 10: Configuration Preview (Right) ===
        preview_frame = ttk.LabelFrame(right_column, text="Step 10: Preview", padding="5")
        preview_frame.pack(fill='x', pady=(0, 3))
        
        self.config_text = scrolledtext.ScrolledText(preview_frame, height=6, width=45, 
                                                   font=('Monaco', 10))
        self.config_text.pack(fill='both')
        
        # === CONTROLS SECTION - Below Preview (Right) ===
        controls_frame = ttk.Frame(right_column)
        controls_frame.pack(fill='x')
        
        # Control Buttons and Status on same line
        control_line = ttk.Frame(controls_frame)
        control_line.pack(fill='x', pady=(0, 3))
        
        # Buttons on left
        self.start_button = ttk.Button(control_line, text="🚀 LAUNCH", 
                                     command=self.start_search, style='Primary.TButton')
        self.start_button.pack(side='left', padx=(0, 5))
        
        self.stop_button = ttk.Button(control_line, text="⏹️ STOP", 
                                    command=self.stop_search, style='Secondary.TButton', state='disabled')
        self.stop_button.pack(side='left', padx=(0, 10))
        
        # Status next to buttons
        self.status_label = ttk.Label(control_line, text="⚡ Ready to launch!", 
                                    foreground=self.colors['primary_green'], font=('Helvetica', 11, 'bold'))
        self.status_label.pack(side='left')
        
        # Progress bar on separate line (minimal)
        self.progress = ttk.Progressbar(controls_frame, mode='indeterminate')
        self.progress.pack(fill='x')
        
        # Initialize preview
        self.update_configuration_preview()
    
    def calculate_cost_estimate(self, num_searches, jobs_per_search):
        """Calculate accurate cost estimate: scraping + AI classification"""
        total_jobs = num_searches * jobs_per_search
        scraping_cost = total_jobs * 0.001  # $0.001 per job scraped
        ai_cost = total_jobs * 0.0003       # $0.0003 per job classified (GPT-4o Mini)
        return scraping_cost + ai_cost
        
    def setup_results_tab(self):
        results_frame = ttk.Frame(self.results_tab, padding="10")
        results_frame.pack(fill='both', expand=True)
        
        # Results buttons FIRST - always visible at top
        button_frame = ttk.Frame(results_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(button_frame, text="📁 Open Output Folder", 
                  command=self.open_output_folder, style='Primary.TButton').pack(side='left', padx=(0, 10))
        
        ttk.Button(button_frame, text="🗑️ Clear Results", 
                  command=self.clear_results, style='Secondary.TButton').pack(side='left')

        # Utility buttons for copying/saving logs
        ttk.Button(button_frame, text="📋 Copy All", command=self.copy_all_results).pack(side='right')
        ttk.Button(button_frame, text="💾 Save Log", command=self.save_results_log).pack(side='right', padx=(0, 8))
        
        # Results text area - takes remaining space
        self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                    width=100,
                                                    font=('Monaco', 10),
                                                    wrap='word')
        self.results_text.pack(fill='both', expand=True)

        # Keyboard shortcuts for copy/select all (works across platforms)
        self.results_text.bind('<Control-a>', lambda e: self.select_all_results() or 'break')
        self.results_text.bind('<Command-a>', lambda e: self.select_all_results() or 'break')
        self.results_text.bind('<Control-c>', lambda e: self.copy_selection_results() or 'break')
        self.results_text.bind('<Command-c>', lambda e: self.copy_selection_results() or 'break')

        # Context menu for right-click
        self.results_context_menu = tk.Menu(self.root, tearoff=0)
        self.results_context_menu.add_command(label="Copy", command=self.copy_selection_results)
        self.results_context_menu.add_command(label="Copy All", command=self.copy_all_results)
        self.results_context_menu.add_separator()
        self.results_context_menu.add_command(label="Save Log...", command=self.save_results_log)

        def show_context_menu(event):
            try:
                self.results_context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.results_context_menu.grab_release()
        self.results_text.bind('<Button-3>', show_context_menu)  # Right-click
        self.results_text.bind('<Button-2>', show_context_menu)  # Middle-click (mac variations)
    
    def setup_analytics_tab(self):
        """Setup the analytics tab for link tracking dashboard"""
        analytics_frame = ttk.Frame(self.analytics_tab, padding="20")
        analytics_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(analytics_frame, text="📊 Link Analytics Dashboard", 
                              font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Info text
        info_text = """
This dashboard shows engagement metrics for job links shared to Free Agents.
Every job URL in generated PDFs is automatically tracked using Short.io.

🔗 Link Tracking Features:
• Automatic URL shortening with freeworldjobs.short.gy
• Market-based performance analysis (Dallas, Houston, etc.)
• Route type comparison (Local vs OTR)
• Match quality effectiveness tracking
• Export functionality for detailed analysis

📊 Analytics Available:
• Total links created and click-through rates
• Performance by market and route type  
• Engagement patterns and recommendations
• Real-time tracking of Free Agent activity
"""
        
        info_label = ttk.Label(analytics_frame, text=info_text.strip(), 
                             font=('Helvetica', 11), justify='left')
        info_label.pack(pady=(0, 20), fill='x')
        
        # Launch button
        def launch_analytics_dashboard():
            try:
                from analytics_dashboard import AnalyticsDashboard
                dashboard = AnalyticsDashboard(parent=self.root)
                dashboard.show_dashboard()
            except Exception as e:
                self.show_error(f"Failed to launch analytics dashboard: {e}")
        
        launch_button = ttk.Button(analytics_frame, text="🚀 Launch Analytics Dashboard",
                                 command=launch_analytics_dashboard)
        launch_button.pack(pady=10)
        
        # Status info
        status_frame = ttk.LabelFrame(analytics_frame, text="Tracking Status", padding="10")
        status_frame.pack(fill='x', pady=(20, 0))
        
        try:
            from link_tracker import LinkTracker
            tracker_status = "🟢 Active - Links will be tracked automatically"
        except ImportError:
            tracker_status = "🔴 Not Available - Check SHORT_API_KEY in .env file"
        
        status_label = ttk.Label(status_frame, text=tracker_status, font=('Helvetica', 11))
        status_label.pack()
    
    def setup_settings_tab(self):
        """Setup the settings tab with system prompt editor and filter toggles"""
        settings_frame = ttk.Frame(self.settings_tab, padding="20")
        settings_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(settings_frame, text="⚙️ Pipeline Settings & Configuration", 
                              font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create notebook for settings sections
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill='both', expand=True)
        
        # AI Prompt tab
        prompt_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(prompt_frame, text="🤖 AI System Prompt")
        
        prompt_container = ttk.Frame(prompt_frame, padding="15")
        prompt_container.pack(fill='both', expand=True)
        
        # System prompt label and info
        prompt_label = ttk.Label(prompt_container, text="CDL Career Coach System Prompt", 
                                font=('Helvetica', 14, 'bold'))
        prompt_label.pack(anchor='w', pady=(0, 5))
        
        # Development warning
        warning_frame = ttk.Frame(prompt_container)
        warning_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(warning_frame, text="⚠️ DEVELOPMENT ONLY", 
                 font=('Helvetica', 11, 'bold'), foreground='red').pack(anchor='w')
        ttk.Label(warning_frame, text="Modifying the system prompt may affect job classification accuracy.", 
                 font=('Helvetica', 10), foreground='#FF6B6B').pack(anchor='w')
        
        info_text = "Edit the AI system prompt that guides job classification. Changes take effect immediately for new searches."
        info_label = ttk.Label(prompt_container, text=info_text, font=('Helvetica', 10))
        info_label.pack(anchor='w', pady=(0, 10))
        
        # Text area for system prompt
        text_frame = ttk.Frame(prompt_container)
        text_frame.pack(fill='both', expand=True)
        
        # Scrolled text widget
        import tkinter as tk
        from tkinter import scrolledtext
        
        self.prompt_text = scrolledtext.ScrolledText(text_frame, 
                                                   width=80, height=25,
                                                   wrap=tk.WORD,
                                                   font=('Consolas', 10))
        self.prompt_text.pack(fill='both', expand=True)
        
        # Load current system prompt
        try:
            from job_classifier import JobClassifier
            classifier = JobClassifier()
            current_prompt = classifier._get_system_prompt()
            self.prompt_text.insert('1.0', current_prompt)
        except Exception as e:
            self.prompt_text.insert('1.0', f"Error loading current prompt: {e}\n\nDefault prompt will be used.")
        
        # Save button
        save_frame = ttk.Frame(prompt_container)
        save_frame.pack(fill='x', pady=(10, 0))
        
        save_button = ttk.Button(save_frame, text="💾 Save Prompt Changes", 
                               command=self.save_system_prompt)
        save_button.pack(anchor='e')
        
        # Pipeline Filters tab
        filters_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(filters_frame, text="🔧 Pipeline Filters")
        
        filters_container = ttk.Frame(filters_frame, padding="15")
        filters_container.pack(fill='both', expand=True)
        
        # Filters title
        filters_label = ttk.Label(filters_container, text="Business Rules & Filter Configuration", 
                                 font=('Helvetica', 14, 'bold'))
        filters_label.pack(anchor='w', pady=(0, 5))
        
        # Development warning for filters
        filter_warning_frame = ttk.Frame(filters_container)
        filter_warning_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(filter_warning_frame, text="⚠️ ADVANCED SETTINGS - DEVELOPMENT ONLY", 
                 font=('Helvetica', 11, 'bold'), foreground='red').pack(anchor='w')
        ttk.Label(filter_warning_frame, text="Disabling filters may result in lower quality job matches and duplicates.", 
                 font=('Helvetica', 10), foreground='#FF6B6B').pack(anchor='w')
        
        # Create filter variables and load saved settings
        if not hasattr(self, 'filter_vars'):
            self.filter_vars = {}
        
        # Load saved filter settings
        self.load_filter_settings()
        
        # Filter checkboxes with descriptions
        filter_configs = [
            ('owner_op', 'Owner-Operator Filter', 'Remove jobs requiring your own truck/CDL business'),
            ('school_bus', 'School Bus Filter', 'Remove school bus driving positions'),
            ('spam_filter', 'Spam Link Filter', 'Remove jobs with suspicious/spam website links'),
            ('experience_filter', 'Experience Requirement Filter', 'Remove jobs explicitly requiring experience'),
            ('r1_dedup', 'R1 Deduplication', 'Remove duplicate jobs by Company + Title + Market'),
            ('r2_dedup', 'R2 Deduplication', 'Remove duplicate jobs by Company + Location')
        ]
        
        for filter_key, filter_name, description in filter_configs:
            if filter_key not in self.filter_vars:
                self.filter_vars[filter_key] = tk.BooleanVar(value=True)  # Default enabled
            
            filter_frame = ttk.LabelFrame(filters_container, text=filter_name, padding="10")
            filter_frame.pack(fill='x', pady=(0, 10))
            
            checkbox = ttk.Checkbutton(filter_frame, 
                                     text=description,
                                     variable=self.filter_vars[filter_key])
            checkbox.pack(anchor='w')
        
        # Settings actions frame
        actions_frame = ttk.Frame(filters_container)
        actions_frame.pack(fill='x', pady=(20, 0))
        
        # Reset to defaults button
        reset_button = ttk.Button(actions_frame, text="🔄 Reset to Defaults",
                                command=self.reset_filter_defaults)
        reset_button.pack(side='left')
        
        # Save settings button
        save_settings_button = ttk.Button(actions_frame, text="💾 Save Filter Settings",
                                        command=self.save_filter_settings)
        save_settings_button.pack(side='right')
    
    def save_system_prompt(self):
        """Save the modified system prompt"""
        try:
            new_prompt = self.prompt_text.get('1.0', 'end-1c')
            
            # Save to a config file that can be loaded by the classifier
            config_path = "/Users/freeworld_james/Desktop/freeworld-job-scraper/config/system_prompt.txt"
            import os
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(new_prompt)
            
            self.show_success("System prompt saved successfully! Changes will take effect for new job searches.")
            
        except Exception as e:
            self.show_error(f"Failed to save system prompt: {e}")
    
    def save_filter_settings(self):
        """Save the filter configuration"""
        try:
            config_path = "/Users/freeworld_james/Desktop/freeworld-job-scraper/config/filter_settings.json"
            import os
            import json
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            settings = {}
            for filter_key, var in self.filter_vars.items():
                settings[filter_key] = var.get()
            
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.show_success("Filter settings saved successfully!")
            
        except Exception as e:
            self.show_error(f"Failed to save filter settings: {e}")
    
    def load_filter_settings(self):
        """Load filter settings from config file"""
        try:
            config_path = "/Users/freeworld_james/Desktop/freeworld-job-scraper/config/filter_settings.json"
            import os
            import json
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                
                # Apply loaded settings
                for filter_key, enabled in settings.items():
                    if filter_key not in self.filter_vars:
                        self.filter_vars[filter_key] = tk.BooleanVar(value=enabled)
                    else:
                        self.filter_vars[filter_key].set(enabled)
            else:
                # Initialize with defaults if no config file
                filter_keys = ['owner_op', 'school_bus', 'spam_filter', 'experience_filter', 'r1_dedup', 'r2_dedup']
                for filter_key in filter_keys:
                    if filter_key not in self.filter_vars:
                        self.filter_vars[filter_key] = tk.BooleanVar(value=True)
                        
        except Exception as e:
            print(f"Warning: Could not load filter settings: {e}")
            # Initialize with defaults on error
            filter_keys = ['owner_op', 'school_bus', 'spam_filter', 'experience_filter', 'r1_dedup', 'r2_dedup']
            for filter_key in filter_keys:
                if filter_key not in self.filter_vars:
                    self.filter_vars[filter_key] = tk.BooleanVar(value=True)
    
    def reset_filter_defaults(self):
        """Reset all filters to their default states"""
        for var in self.filter_vars.values():
            var.set(True)  # Default all filters to enabled
        self.show_success("Filter settings reset to defaults!")
    
    def on_custom_location_changed(self):
        """Handle custom location input changes"""
        custom_location = self.custom_location_entry.get().strip()
        
        # Auto-disable Airtable upload for custom locations as a suggestion
        if custom_location and self.airtable_upload_var.get():
            # Show a suggestion but don't force it
            pass  # Keep the current behavior for now
        
        self.update_configuration_preview()
    
    def browse_output_folder(self):
        """Open folder browser dialog"""
        from tkinter import filedialog
        
        current_folder = self.output_folder_var.get()
        new_folder = filedialog.askdirectory(
            title="Select Output Folder for Job Files",
            initialdir=current_folder
        )
        
        if new_folder:  # User didn't cancel
            self.output_folder_var.set(new_folder)
            self.update_configuration_preview()  # Update preview with new folder
    
    def update_configuration_preview(self):
        """Update the configuration preview to show current settings"""
        try:
            # Get current selections
            selected_markets = [market for market, var in self.market_vars.items() if var.get()]
            custom_location = self.custom_location_entry.get().strip()
            search_terms_text = self.terms_entry.get('1.0', tk.END).strip()
            search_terms = [term.strip() for term in search_terms_text.split(',') if term.strip()] if search_terms_text else []
            route_filter = self.route_var.get()
            radius = self.radius_var.get()
            experience_filter = self.experience_var.get()
            no_experience = (experience_filter == 'no_experience')
            airtable_upload = self.airtable_upload_var.get()
            mode = self.mode_var.get()
            generate_pdf = self.generate_pdf_var.get()
            generate_csv = self.generate_csv_var.get()
            
            # Get mode info (same logic as CLI)
            mode_configs = {
                "test": {"mode": "test", "limit": 10, "use_multi_search": False},
                "sample": {"mode": "sample", "limit": 100, "use_multi_search": False},
                "medium": {"mode": "medium", "limit": 250, "use_multi_search": False},
                "large": {"mode": "large", "limit": 500, "use_multi_search": False},
                "full": {"mode": "full", "limit": 1000, "use_multi_search": False}
            }
            mode_info = mode_configs.get(mode, mode_configs["sample"])
            
            # Build preview (same format as CLI)
            preview = "=== SEARCH CONFIGURATION ===\n\n"
            
            # Markets or Custom Location
            if custom_location:
                preview += f"Custom Location: {custom_location}\n"
                if selected_markets:
                    preview += "⚠️ Note: Custom location takes priority over selected markets\n"
            elif selected_markets:
                if len(selected_markets) == 1:
                    market_id = selected_markets[0]
                    location = self.cli_form.MARKET_SEARCH_QUERIES[market_id]
                    preview += f"Market: {location}\n"
                else:
                    preview += f"Markets: {len(selected_markets)} markets selected\n"
                    for market_id in selected_markets:
                        location = self.cli_form.MARKET_SEARCH_QUERIES[market_id]
                        preview += f"  • {location}\n"
            else:
                preview += "Location: ❌ No markets selected or custom location entered\n"
            
            # Search terms
            if search_terms:
                preview += f"Search Terms: {', '.join(search_terms)}\n"
            else:
                preview += "Search Terms: ❌ No terms entered\n"
            
            # Mode
            mode_names = {
                "test": "Test (10 jobs per search)",
                "sample": "Sample (100 jobs per search)",
                "medium": "Medium (250 jobs per search)",
                "large": "Large (500 jobs per search)",
                "full": "Full (1000 jobs per search)"
            }
            preview += f"Mode: {mode_names.get(mode, mode)}\n"
            
            # Route filter
            route_names = {
                "both": "Both Local and OTR jobs",
                "local": "Local jobs only (home daily)",
                "otr": "OTR jobs only (over-the-road)"
            }
            preview += f"Route Filter: {route_names.get(route_filter, route_filter)}\n"
            
            # Show selected radius
            radius_text = "Exact location only" if radius == "0" else f"Within {radius} miles"
            preview += f"Radius: {radius_text}\n"
            
            # Show experience filter
            experience_text = "No experience required filter enabled" if experience_filter == "no_experience" else "All experience levels included"
            preview += f"Experience: {experience_text}\n"
            
            # Calculate and show total cost estimate
            if (selected_markets or custom_location) and search_terms:
                if custom_location:
                    total_searches = len(search_terms)
                    num_locations = 1
                else:
                    total_searches = len(selected_markets) * len(search_terms)
                    num_locations = len(selected_markets)
                
                cost_estimate = self.calculate_cost_estimate(total_searches, mode_info['limit'])
                
                # Update dynamic cost preview
                num_terms = len(search_terms)
                self.cost_preview_label.config(
                    text=f"📊 Your cost: {num_terms} term(s) × {num_locations} location(s) = ${cost_estimate:.2f} total"
                )
                
                if cost_estimate == 0:
                    preview += f"💰 Cost: FREE\n"
                elif cost_estimate > 2.00:
                    preview += f"🚨 Cost: ${cost_estimate:.2f} (REQUIRES CONFIRMATION)\n"
                else:
                    preview += f"💰 Cost: ${cost_estimate:.2f} ($0.0013 per job total)\n"
            else:
                preview += f"💰 Total Cost: $0.00 (invalid configuration)\n"
                # Update dynamic cost preview for invalid config
                self.cost_preview_label.config(text="📊 Your cost: Select options above")
            
            # Airtable settings
            airtable_status = "✅ Enabled" if airtable_upload else "❌ Disabled"
            preview += f"Airtable Upload: {airtable_status}\n"
            if custom_location and airtable_upload:
                preview += "⚠️ Consider disabling Airtable upload for one-off custom locations\n"
            
            # Fresh jobs setting
            force_fresh = self.force_fresh_var.get()
            fresh_status = "🔄 Fresh Jobs" if force_fresh else "💰 Smart Savings"
            preview += f"Job Source: {fresh_status}\n"
            
            # Output folder
            output_folder = self.output_folder_var.get()
            # Show shortened path for readability
            if len(output_folder) > 40:
                shortened_path = "..." + output_folder[-37:]
            else:
                shortened_path = output_folder
            preview += f"Output Folder: {shortened_path}\n"
            
            # Scale calculation
            if (selected_markets or custom_location) and search_terms:
                num_terms = len(search_terms)
                
                if custom_location:
                    # Custom location search
                    num_locations = 1
                    total_searches = num_terms
                    expected_jobs = total_searches * mode_info['limit']
                    
                    preview += f"\n🔍 Search Scale:\n"
                    preview += f"  • {num_terms} search term(s)\n"
                    preview += f"  • 1 custom location\n"
                    preview += f"  • Total searches: {total_searches}\n"
                    preview += f"  • Jobs per search: {mode_info['limit']}\n"
                    preview += f"  • Expected total jobs: ~{expected_jobs}\n"
                    
                    # Calculate cost estimate
                    cost_estimate = self.calculate_cost_estimate(total_searches, mode_info['limit'])
                    if cost_estimate == 0:
                        preview += f"  • Estimated cost: FREE\n"
                    else:
                        preview += f"  • Max cost estimate: ${cost_estimate:.2f}\n"
                    
                    preview += f"\n📄 Output:\n"
                    if generate_pdf and generate_csv:
                        preview += f"  • PDF report + CSV files for custom location\n"
                    elif generate_pdf:
                        preview += f"  • PDF report for custom location\n"
                    elif generate_csv:
                        preview += f"  • CSV files for custom location (no PDF)\n"
                    else:
                        preview += f"  • ⚠️ No output formats selected!\n"
                    preview += f"  • All files saved to selected folder\n"
                    
                    # Sample URL for custom location
                    sample_url = self.cli_form.build_indeed_url(search_terms[0], custom_location, radius, no_experience=no_experience)
                    preview += f"\nSample Indeed URL:\n"
                    preview += f"  {sample_url[:100]}...\n"
                    
                elif selected_markets:
                    # Regular market search
                    num_markets = len(selected_markets)
                    total_searches = num_markets * num_terms
                    expected_jobs = total_searches * mode_info['limit']
                    
                    preview += f"\n🔍 Search Scale:\n"
                    preview += f"  • {num_terms} search term(s)\n"
                    preview += f"  • {num_markets} market(s)\n"
                    preview += f"  • Total searches: {num_terms} × {num_markets} = {total_searches}\n"
                    preview += f"  • Jobs per search: {mode_info['limit']}\n"
                    preview += f"  • Expected total jobs: ~{expected_jobs}\n"
                    
                    # Calculate cost estimate
                    cost_estimate = self.calculate_cost_estimate(total_searches, mode_info['limit'])
                    if cost_estimate == 0:
                        preview += f"  • Estimated cost: FREE\n"
                    else:
                        preview += f"  • Max cost estimate: ${cost_estimate:.2f}\n"
                    
                    preview += f"\n📄 Output:\n"
                    if generate_pdf and generate_csv:
                        preview += f"  • PDF reports + CSV files for each market ({num_markets} sets)\n"
                    elif generate_pdf:
                        preview += f"  • PDF reports for each market ({num_markets} PDFs)\n"
                    elif generate_csv:
                        preview += f"  • CSV files for each market ({num_markets} sets, no PDFs)\n"
                    else:
                        preview += f"  • ⚠️ No output formats selected!\n"
                    preview += f"  • All files saved to selected folder\n"
                    
                    # Sample URL
                    sample_url = self.cli_form.build_indeed_url(
                        search_terms[0],
                        self.cli_form.MARKET_SEARCH_QUERIES[selected_markets[0]],
                        radius,
                        no_experience=no_experience
                    )
                    preview += f"\nSample Indeed URL:\n"
                    preview += f"  {sample_url[:100]}...\n"
            
            # Validation
            preview += "\n=== VALIDATION ===\n"
            issues = []
            if not selected_markets and not custom_location:
                issues.append("❌ No markets selected or custom location entered")
            if not search_terms:
                issues.append("❌ No search terms entered")
                
            if issues:
                preview += "\n".join(issues)
                self.start_button.config(state='disabled')
            else:
                preview += "✅ Configuration is valid and ready for search"
                self.start_button.config(state='normal')
            
            # Update the text widget
            self.config_text.delete('1.0', tk.END)
            self.config_text.insert('1.0', preview)
            
        except Exception as e:
            # Handle any errors gracefully
            self.config_text.delete('1.0', tk.END)
            self.config_text.insert('1.0', f"Error updating preview: {e}")
    
    def start_search(self):
        """Start the search using the CLI backend"""
        # Collect current GUI settings
        selected_markets = [market for market, var in self.market_vars.items() if var.get()]
        custom_location = self.custom_location_entry.get().strip()
        search_terms_text = self.terms_entry.get('1.0', tk.END).strip()
        search_terms = [term.strip() for term in search_terms_text.split(',') if term.strip()]
        route_filter = self.route_var.get()
        experience_filter = self.experience_var.get()
        airtable_upload = self.airtable_upload_var.get()
        mode = self.mode_var.get()
        
        # Get output options
        generate_pdf = self.generate_pdf_var.get()
        generate_csv = self.generate_csv_var.get()
        
        # Collect filter settings
        filter_settings = {}
        if hasattr(self, 'filter_vars'):
            for filter_key, var in self.filter_vars.items():
                filter_settings[filter_key] = var.get()
        else:
            # Default all filters to enabled if settings tab not initialized
            filter_settings = {
                'owner_op': True,
                'school_bus': True,
                'spam_filter': True,
                'experience_filter': True,
                'r1_dedup': True,
                'r2_dedup': True
            }
        
        # Validate
        if not selected_markets and not custom_location:
            messagebox.showerror("Error", "Please select at least one market or enter a custom location")
            return
        if not search_terms:
            messagebox.showerror("Error", "Please enter at least one search term")
            return
        if not generate_pdf and not generate_csv:
            messagebox.showerror("Error", "Please select at least one output format (PDF or CSV)")
            return
        
        # Cost protection check
        mode_configs = {
            "test": {"mode": "test", "limit": 10, "use_multi_search": False},
            "sample": {"mode": "sample", "limit": 100, "use_multi_search": False},
            "medium": {"mode": "medium", "limit": 250, "use_multi_search": False},
            "large": {"mode": "large", "limit": 500, "use_multi_search": False},
            "full": {"mode": "full", "limit": 1000, "use_multi_search": False}
        }
        mode_info = mode_configs[mode]
        
        # Calculate cost
        if custom_location:
            total_searches = len(search_terms)
        else:
            total_searches = len(selected_markets) * len(search_terms)
        
        estimated_cost = self.calculate_cost_estimate(total_searches, mode_info['limit'])
        
        # Cost protection: Require confirmation for searches over $2.00
        if estimated_cost > 2.00:
            confirm_msg = f"""🚨 HIGH COST WARNING 🚨

This search will cost approximately ${estimated_cost:.2f}
(Estimated at $0.0013 per job total)

Details:
• {total_searches} total searches
• {mode_info['limit']} jobs per search  
• {total_searches * mode_info['limit']} total jobs expected

Type 'CONFIRM' to proceed with this expensive search:"""
            
            from tkinter import simpledialog
            user_input = simpledialog.askstring(
                "Cost Protection - Confirmation Required", 
                confirm_msg,
                show='*'  # Hide input like password
            )
            
            if user_input != 'CONFIRM':
                messagebox.showinfo("Search Cancelled", "Search cancelled for cost protection.")
                return
        
        # Update UI state
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="🚀 SEARCH IN PROGRESS - Finding those quality opportunities!", foreground=self.colors['primary_green'])
        self.progress.start()
        
        # Clear results and switch to results tab
        self.results_text.delete(1.0, tk.END)
        # Switch to results tab
        for i, tab_id in enumerate(self.root.children.values()):
            if isinstance(tab_id, ttk.Notebook):
                tab_id.select(1)  # Select results tab
                break
        
        # Get mode info
        mode_configs = {
            "test": {"mode": "test", "limit": 10, "use_multi_search": False},
            "sample": {"mode": "sample", "limit": 100, "use_multi_search": False},
            "medium": {"mode": "medium", "limit": 250, "use_multi_search": False},
            "large": {"mode": "large", "limit": 500, "use_multi_search": False},
            "full": {"mode": "full", "limit": 1000, "use_multi_search": False}
        }
        mode_info = mode_configs[mode]
        
        # Get output folder and options
        output_folder = self.output_folder_var.get()
        generate_pdf = self.generate_pdf_var.get()
        generate_csv = self.generate_csv_var.get()
        force_fresh = self.force_fresh_var.get()
        
        # Derive radius and experience flag
        try:
            radius = int(self.radius_var.get())
        except Exception:
            radius = 50
        no_experience = (self.experience_var.get() == 'no_experience')
        
        # Start search in background thread
        self.search_thread = threading.Thread(
            target=self.run_cli_search, 
            args=(selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info, output_folder, generate_pdf, generate_csv, force_fresh, radius, no_experience, filter_settings)
        )
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def run_cli_search(self, selected_markets, custom_location, search_terms, route_filter, airtable_upload, mode_info, output_folder, generate_pdf, generate_csv, force_fresh, radius, no_experience, filter_settings):
        """Run the search using the CLI backend methods"""
        import io
        import contextlib
        
        # Create a custom stdout capture to show CLI progress
        class GUIStdoutCapture(io.StringIO):
            def __init__(self, gui_logger):
                super().__init__()
                self.gui_logger = gui_logger
                
            def write(self, text):
                if text.strip():  # Only log non-empty lines
                    self.gui_logger(text.rstrip())
                return super().write(text)
        
        try:
            self.log_message("🚛 FreeWorld Job Scraper v1.0")
            self.log_message("=" * 50)
            
            # Handle custom location vs regular markets
            if custom_location:
                self.log_message(f"Custom location: {custom_location}")
                markets_to_use = ["Custom"]
                locations_to_use = [custom_location]
                # For custom locations, we'll set the market field to the location for deduplication
                market_name = custom_location
            else:
                # Use human-friendly location labels for display; keep IDs for backend
                selected_locations = [self.cli_form.MARKET_SEARCH_QUERIES[mid] for mid in selected_markets]
                self.log_message(f"Selected markets: {', '.join(selected_locations)}")
                markets_to_use = selected_locations
                locations_to_use = selected_locations
                market_name = None
            
            self.log_message(f"Search terms: {', '.join(search_terms)}")
            self.log_message(f"Route filter: {route_filter}")
            self.log_message(f"Mode: {mode_info['mode']}")
            self.log_message(f"Experience filter: {'No experience' if no_experience else 'Any experience'}")
            self.log_message(f"Radius: {radius} miles")
            self.log_message(f"Force Fresh Jobs: {'Yes' if force_fresh else 'No (Smart Savings)'}")
            self.log_message(f"Airtable upload: {'Enabled' if airtable_upload else 'Disabled'}")
            self.log_message("=" * 50)
            
            # Call the CLI's run_search method directly
            self.log_message("\n🚀 Starting job search...")
            self.log_message(f"📋 Processing {len(markets_to_use)} location(s) with {len(search_terms)} search term(s)")
            self.log_message(f"📊 Total searches: {len(markets_to_use)} × {len(search_terms)} = {len(markets_to_use) * len(search_terms)}")
            self.log_message(f"⏱️ Estimated time: {len(markets_to_use) * len(search_terms) * 30} seconds")
            
            self.log_message(f"⚡ Starting pipeline execution...")
            
            # Change to output directory before running search
            original_cwd = os.getcwd()
            try:
                os.chdir(output_folder)
                self.log_message(f"📁 Output folder: {output_folder}")
                # Prepare auto-save log path inside FreeWorld_Jobs/logs/
                try:
                    from datetime import datetime
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    base_dir = os.path.join(os.getcwd(), 'FreeWorld_Jobs')
                    logs_dir = os.path.join(base_dir, 'logs')
                    os.makedirs(logs_dir, exist_ok=True)
                    self.current_log_path = os.path.join(logs_dir, f'session_{ts}.log')
                    self.log_message(f"🧾 Saving log to: {self.current_log_path}")
                except Exception as log_init_err:
                    self.current_log_path = None
                    self.log_message(f"⚠️ Log file setup failed: {log_init_err}")
                
                # Use the WORKING terminal search run_search method directly
                stdout_capture = GUIStdoutCapture(self.log_message)
                with contextlib.redirect_stdout(stdout_capture):
                    # selected_markets is already in the correct format (numbers from GUI)
                    # Ensure empty custom location is passed as None for accurate pipeline behavior
                    success = self.terminal_search.run_search(
                        selected_markets=selected_markets if not custom_location else [],
                        custom_location=(custom_location if custom_location else None),
                        search_terms=search_terms,
                        route_filter=route_filter,
                        airtable_upload=airtable_upload,
                        mode_info=mode_info,
                        force_fresh=force_fresh,
                        radius=radius,
                        no_experience=no_experience,
                        filter_settings=filter_settings
                    )
            finally:
                # Always restore original directory
                os.chdir(original_cwd)
            
            if success:
                self.log_message(f"\n🎉 Job search completed successfully!")
                self.log_message(f"📁 Results saved to: {output_folder}/FreeWorld_Jobs/")
                self.log_message(f"   Check your Desktop for the 'FreeWorld_Jobs' folder")
                self.log_message(f"   Separate PDF reports generated for each market")
            else:
                self.log_message(f"\n❌ Search failed or returned no results")
                
        except Exception as e:
            self.log_message(f"\n❌ Error during search: {e}")
            import traceback
            self.log_message(f"Details: {traceback.format_exc()}")
        finally:
            # Update UI
            self.root.after(0, self.search_completed)
    
    def search_completed(self):
        """Called when search is completed"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Search completed - Check results tab", foreground="green")
        self.progress.stop()
        
    def stop_search(self):
        """Stop the current search"""
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

        # Also append to current session log file if configured
        try:
            log_path = getattr(self, 'current_log_path', None)
            if log_path:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(message + '\n')
        except Exception:
            pass
    
    def open_output_folder(self):
        """Open the output folder"""
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
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)
        # Reset current log path reference (do not delete file on disk)
        self.current_log_path = None
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

    # ----- Results utilities: copy/save/logging -----
    def select_all_results(self):
        try:
            self.results_text.tag_add('sel', '1.0', 'end-1c')
        except Exception:
            pass

    def copy_selection_results(self):
        try:
            selected = self.results_text.get('sel.first', 'sel.last')
        except Exception:
            selected = ''
        if not selected:
            return
        sanitized = self._sanitize_text(selected)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(sanitized)
            # Ensure clipboard data persists even after window closes
            self.root.update()
            if sanitized != selected:
                messagebox.showinfo("Copied (Cleaned)", "Some unsupported characters were removed during copy.")
        except Exception as e:
            messagebox.showerror("Copy Failed", f"Unable to copy selection: {e}")

    def copy_all_results(self):
        all_text = self.results_text.get('1.0', 'end-1c')
        sanitized = self._sanitize_text(all_text)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(sanitized)
            self.root.update()
            if sanitized != all_text:
                messagebox.showinfo("Copied (Cleaned)", "All results copied. Some unsupported characters were removed.")
            else:
                messagebox.showinfo("Copied", "All results copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Copy Failed", f"Unable to copy results: {e}")

    def save_results_log(self):
        from tkinter import filedialog
        default_name = "freeworld_job_search_log.txt"
        path = filedialog.asksaveasfilename(
            title="Save Results Log",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            text = self.results_text.get('1.0', 'end-1c')
            text = self._sanitize_text(text)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Saved", f"Log saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Save Failed", f"Unable to save log: {e}")

def main():
    """Main entry point"""
    app = FreeWorldJobScraperGUIWrapper()
    app.run()

if __name__ == "__main__":
    main()
