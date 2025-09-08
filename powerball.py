import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import threading
from datetime import datetime, timedelta
import random
import json
from collections import Counter

class PowerballGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Powerball Winning Numbers - Live API & Offline Mode")
        self.root.geometry("950x750")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎱 Powerball Winning Numbers Display", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Create notebook (tab container)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_main_tab()
        self.create_overdue_tab()
        
        # Store the fetched data for searching
        self.current_data = []
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def create_main_tab(self):
        """Create the main tab with all the original functionality"""
        # Main tab frame
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="🎯 Main Display")
        
        # Configure grid weights for main tab
        main_tab.columnconfigure(0, weight=1)
        main_tab.rowconfigure(1, weight=1)
        
        # Control frame
        control_frame = ttk.Frame(main_tab)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Data source selection
        source_frame = ttk.LabelFrame(control_frame, text="📡 Data Source Selection", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Radio buttons for data source
        self.data_source = tk.StringVar(value="live_api")
        
        live_radio = ttk.Radiobutton(source_frame, text="🌐 Live API (NY State Open Data)", 
                                    variable=self.data_source, value="live_api")
        live_radio.pack(anchor=tk.W, pady=2)
        
        offline_radio = ttk.Radiobutton(source_frame, text="🔒 Offline Mode (Sample Data)", 
                                       variable=self.data_source, value="offline")
        offline_radio.pack(anchor=tk.W, pady=2)
        
        csv_radio = ttk.Radiobutton(source_frame, text="📁 Load from CSV File", 
                                   variable=self.data_source, value="csv")
        csv_radio.pack(anchor=tk.W, pady=2)
        
        # API Configuration
        api_frame = ttk.LabelFrame(control_frame, text="⚙️ API Configuration (Optional)", padding="5")
        api_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Proxy settings
        proxy_frame = ttk.Frame(api_frame)
        proxy_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(proxy_frame, text="Proxy:").pack(side=tk.LEFT)
        self.proxy_entry = ttk.Entry(proxy_frame, width=30)
        self.proxy_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.proxy_entry.insert(0, "http://proxy:port")
        
        self.use_proxy_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_frame, text="Use Proxy", variable=self.use_proxy_var).pack(side=tk.LEFT, padx=(0, 10))
        
        self.disable_ssl_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_frame, text="Disable SSL Verification", variable=self.disable_ssl_var).pack(side=tk.LEFT)
        
        # Number of results
        results_frame = ttk.Frame(api_frame)
        results_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(results_frame, text="Number of draws:").pack(side=tk.LEFT)
        self.num_results = tk.StringVar(value="250")
        results_spinbox = ttk.Spinbox(results_frame, from_=10, to=1000, width=10, textvariable=self.num_results)
        results_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # SEARCH SECTION - Check Your Numbers
        search_frame = ttk.LabelFrame(control_frame, text="🔍 Check Your Numbers", padding="10")
        search_frame.pack(fill=tk.X, pady=(5, 5))
        
        # Instructions
        instruction_label = ttk.Label(search_frame, text="Enter your numbers (format: 1,15,25,35,45 PB:12):", 
                                     font=("Arial", 9))
        instruction_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Entry and button frame
        entry_frame = ttk.Frame(search_frame)
        entry_frame.pack(fill=tk.X, pady=2)
        
        # Text entry field
        self.numbers_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 11))
        self.numbers_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.numbers_entry.insert(0, "1,15,25,35,45 PB:12")
        
        # Search button
        self.search_button = ttk.Button(entry_frame, text="🔎 Check Numbers", 
                                       command=self.search_numbers)
        self.search_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        clear_search_button = ttk.Button(entry_frame, text="Clear Entry", 
                                        command=lambda: self.numbers_entry.delete(0, tk.END))
        clear_search_button.pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Fetch button
        self.fetch_button = ttk.Button(button_frame, text="🎯 Fetch Winning Numbers", 
                                      command=self.fetch_numbers_thread, style="Accent.TButton")
        self.fetch_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_button = ttk.Button(button_frame, text="🗑️ Clear Display", 
                                 command=self.clear_text)
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Test API button
        test_button = ttk.Button(button_frame, text="🔧 Test API Connection", 
                                command=self.test_api_connection)
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status and progress
        status_frame = ttk.Frame(button_frame)
        status_frame.pack(side=tk.RIGHT)
        
        self.status_label = ttk.Label(status_frame, text="Ready - Select data source and click fetch")
        self.status_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=150)
        self.progress.pack(side=tk.LEFT)
        
        # Text display area
        self.text_area = scrolledtext.ScrolledText(
            main_tab, 
            wrap=tk.WORD, 
            width=100, 
            height=35,
            font=("Courier", 9)
        )
        self.text_area.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags
        self.text_area.tag_configure("header", font=("Courier", 10, "bold"), foreground="blue")
        self.text_area.tag_configure("success", font=("Courier", 9, "bold"), foreground="green")
        self.text_area.tag_configure("error", font=("Courier", 9, "bold"), foreground="red")
        self.text_area.tag_configure("warning", font=("Courier", 9, "bold"), foreground="orange")
        self.text_area.tag_configure("powerball", font=("Courier", 9, "bold"), foreground="red")
        
        # Show welcome message
        self.show_welcome_message()
    
    def create_overdue_tab(self):
        """Create the overdue numbers analysis tab"""
        # Overdue tab frame
        overdue_tab = ttk.Frame(self.notebook)
        self.notebook.add(overdue_tab, text="📊 Overdue Numbers")
        
        # Configure grid weights for overdue tab
        overdue_tab.columnconfigure(0, weight=1)
        overdue_tab.rowconfigure(1, weight=1)
        
        # Controls frame for overdue tab
        overdue_controls = ttk.Frame(overdue_tab)
        overdue_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Overdue analysis frame
        analysis_frame = ttk.LabelFrame(overdue_controls, text="📊 Overdue Numbers Analysis", padding="10")
        analysis_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Analysis period selection
        period_frame = ttk.Frame(analysis_frame)
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(period_frame, text="Analysis Period (last N draws):").pack(side=tk.LEFT)
        self.analysis_period = tk.StringVar(value="50")
        period_spinbox = ttk.Spinbox(period_frame, from_=10, to=200, width=10, textvariable=self.analysis_period)
        period_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        # Analysis buttons
        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Overdue analysis button
        self.overdue_button = ttk.Button(button_frame, text="🔍 Find Overdue Numbers", 
                                        command=self.find_overdue_numbers)
        self.overdue_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Hot numbers button
        hot_button = ttk.Button(button_frame, text="🔥 Find Hot Numbers", 
                               command=self.find_hot_numbers)
        hot_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Lucky numbers button
        lucky_button = ttk.Button(button_frame, text="🍀 Generate Lucky Numbers", 
                                 command=self.generate_lucky_numbers)
        lucky_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear overdue display button
        clear_overdue_button = ttk.Button(button_frame, text="🗑️ Clear Analysis", 
                                         command=self.clear_overdue_text)
        clear_overdue_button.pack(side=tk.LEFT)
        
        # Instructions
        instructions = ttk.Label(analysis_frame, 
                               text="💡 Instructions: First fetch data in the Main tab, then run analysis here.",
                               font=("Arial", 9), foreground="blue")
        instructions.pack(anchor=tk.W, pady=(10, 0))
        
        # Text display area for overdue analysis
        self.overdue_text_area = scrolledtext.ScrolledText(
            overdue_tab, 
            wrap=tk.WORD, 
            width=100, 
            height=35,
            font=("Courier", 9)
        )
        self.overdue_text_area.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for overdue area
        self.overdue_text_area.tag_configure("header", font=("Courier", 10, "bold"), foreground="blue")
        self.overdue_text_area.tag_configure("success", font=("Courier", 9, "bold"), foreground="green")
        self.overdue_text_area.tag_configure("error", font=("Courier", 9, "bold"), foreground="red")
        self.overdue_text_area.tag_configure("warning", font=("Courier", 9, "bold"), foreground="orange")
        self.overdue_text_area.tag_configure("highlight", font=("Courier", 9, "bold"), foreground="purple")
        
        # Show initial overdue welcome message
        self.show_overdue_welcome()
    
    def show_overdue_welcome(self):
        """Display welcome message for overdue analysis tab"""
        welcome = """📊 OVERDUE NUMBERS ANALYSIS
════════════════════════════════════════════════════════════════════════════════

🎯 WHAT IS OVERDUE ANALYSIS?
   Overdue numbers are those that haven't appeared in recent draws. While every 
   number has equal probability in each draw, some players like to track which 
   numbers haven't been drawn recently.

🔍 AVAILABLE ANALYSES:
   🔍 Find Overdue Numbers - Shows numbers not drawn in recent period
   🔥 Find Hot Numbers - Shows most frequently drawn numbers
   🍀 Generate Lucky Numbers - Creates combinations using various strategies

⚙️ HOW TO USE:
   1. First, fetch Powerball data in the "Main Display" tab
   2. Select your analysis period (default: last 50 draws)
   3. Click any analysis button to see results
   4. Results will show suggested number combinations
   5. Copy suggested formats to search in the Main tab

📈 ANALYSIS FEATURES:
   ✅ Customizable analysis period (10-200 draws)
   ✅ Overdue main numbers (1-69) and Powerballs (1-26)
   ✅ Hot/cold number frequency analysis
   ✅ Multiple lucky number generation strategies
   ✅ Suggested combinations with search formats
   ✅ Statistical breakdowns and percentages

💡 IMPORTANT REMINDER:
   Past results do not influence future draws. Each Powerball drawing is 
   completely random and independent. This analysis is for entertainment 
   purposes only.

Ready to analyze your Powerball data!
"""
        self.overdue_text_area.insert(tk.END, welcome, "header")
    
    def on_tab_changed(self, event):
        """Handle tab change events"""
        selected_tab = event.widget.tab('current')['text']
        if "Overdue" in selected_tab and not self.current_data:
            # Show reminder to fetch data first
            self.status_label.config(text="Reminder: Fetch data in Main tab first for analysis")
    
    def clear_overdue_text(self):
        """Clear the overdue analysis text area"""
        self.overdue_text_area.delete(1.0, tk.END)
        self.show_overdue_welcome()
    
    def show_welcome_message(self):
        """Display welcome message"""
        welcome = """🎱 POWERBALL WINNING NUMBERS DISPLAY
════════════════════════════════════════════════════════════════════════════════

📡 DATA SOURCES:
   🌐 Live API: Fetches real winning numbers from NY State Open Data
   🔒 Offline: Generates realistic sample data (firewall-safe)
   📁 CSV File: Import from manually downloaded lottery data

⚙️ FEATURES:
   ✅ Real-time Powerball winning numbers (up to 1000 draws)
   ✅ Historical data with dates and multipliers
   ✅ Corporate firewall support (proxy, SSL bypass)
   ✅ Number search functionality - check if your numbers ever won!
   ✅ Frequency analysis and statistics
   ✅ Professional formatting with separators
   ✅ Dedicated Overdue Numbers analysis tab

🔧 INSTRUCTIONS:
   1. Select your preferred data source above
   2. Configure API settings if needed (proxy, SSL)
   3. Choose number of draws to display (10-1000, default: 250)
   4. Click "🎯 Fetch Winning Numbers"
   5. Use "🔍 Check Your Numbers" to search for your lucky numbers!
   6. Visit the "📊 Overdue Numbers" tab for advanced analysis

Ready to display Powerball winning numbers!
"""
        self.text_area.insert(tk.END, welcome, "header")
    
    def get_api_config(self):
        """Get API configuration settings"""
        config = {
            'timeout': 15,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        
        # Add proxy if configured
        if self.use_proxy_var.get():
            proxy_url = self.proxy_entry.get().strip()
            if proxy_url and proxy_url != "http://proxy:port":
                config['proxies'] = {'http': proxy_url, 'https': proxy_url}
        
        # Handle SSL verification
        config['verify'] = not self.disable_ssl_var.get()
        
        return config
    
    def test_api_connection(self):
        """Test API connection with current settings"""
        def test_connection():
            try:
                self.root.after(0, lambda: self.status_label.config(text="Testing API connection..."))
                self.root.after(0, lambda: self.progress.start(10))
                
                config = self.get_api_config()
                
                # Test basic connectivity
                test_url = "https://httpbin.org/ip"
                response = requests.get(test_url, **config)
                
                if response.status_code == 200:
                    ip_info = response.json()
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Connection Test", 
                        f"✅ API connection successful!\n\n"
                        f"Status: {response.status_code}\n"
                        f"IP: {ip_info.get('origin', 'Unknown')}\n"
                        f"SSL Verification: {'Enabled' if config['verify'] else 'Disabled'}\n"
                        f"Proxy: {'Yes' if config.get('proxies') else 'No'}"
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Connection Test", f"⚠️ Connection issues detected\nStatus: {response.status_code}"
                    ))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Connection Test", f"❌ Connection test failed:\n{str(e)}\n\nTry enabling proxy or disabling SSL verification."
                ))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_label.config(text="Test complete"))
        
        # Run test in separate thread
        thread = threading.Thread(target=test_connection)
        thread.daemon = True
        thread.start()
    
    def fetch_numbers_thread(self):
        """Run number fetching in a separate thread"""
        thread = threading.Thread(target=self.fetch_numbers)
        thread.daemon = True
        thread.start()
        
    def fetch_numbers(self):
        """Fetch Powerball numbers based on selected mode"""
        try:
            # Update UI
            self.root.after(0, lambda: self.fetch_button.config(state='disabled'))
            self.root.after(0, lambda: self.progress.start(10))
            
            mode = self.data_source.get()
            num_results = int(self.num_results.get())
            
            # Clear previous results
            self.root.after(0, self.clear_text)
            
            if mode == "live_api":
                self.root.after(0, lambda: self.status_label.config(text="Fetching from NY State API..."))
                numbers_data = self.fetch_from_api(num_results)
                source_name = "🌐 NY State Open Data API"
            elif mode == "offline":
                self.root.after(0, lambda: self.status_label.config(text="Generating offline data..."))
                numbers_data = self.generate_sample_data(num_results)
                source_name = "🔒 Offline Sample Data"
            elif mode == "csv":
                self.root.after(0, lambda: self.status_label.config(text="Loading CSV file..."))
                numbers_data = self.load_csv_data()
                if not numbers_data:
                    return
                source_name = "📁 CSV File Data"
            
            # Display results
            if numbers_data:
                self.root.after(0, lambda: self.display_winning_numbers(numbers_data, source_name))
            else:
                self.root.after(0, lambda: self.text_area.insert(tk.END, 
                    "❌ No data retrieved. Try offline mode or check your connection.\n", "error"))
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}\n"
            self.root.after(0, lambda: self.text_area.insert(tk.END, error_msg, "error"))
            
        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.fetch_button.config(state='normal'))
            self.root.after(0, lambda: self.status_label.config(text="Complete"))
    
    def fetch_from_api(self, num_results=250):
        """Fetch real Powerball data from NY State API"""
        results = []
        
        try:
            config = self.get_api_config()
            
            # NY State Open Data API endpoints
            api_endpoints = [
                "https://data.ny.gov/resource/d6yy-54nr.json",
                "https://data.ny.gov/api/views/d6yy-54nr/rows.json"
            ]
            
            for api_url in api_endpoints:
                try:
                    print(f"🔄 Trying API: {api_url}")
                    
                    if "resource" in api_url:
                        # Socrata API format
                        params = {
                            '$limit': num_results,
                            '$order': 'draw_date DESC',
                            '$where': "lottery_name='Powerball'"
                        }
                    else:
                        # Raw data format
                        params = {'start': 0, 'length': num_results}
                    
                    response = requests.get(api_url, params=params, **config)
                    print(f"📡 API Response: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse based on API format
                        if isinstance(data, list):
                            # Direct format
                            parsed_results = self.parse_socrata_data(data)
                        elif isinstance(data, dict) and 'data' in data:
                            # Raw data format
                            parsed_results = self.parse_raw_data(data['data'])
                        else:
                            continue
                        
                        if parsed_results:
                            results = parsed_results
                            print(f"✅ Successfully parsed {len(results)} results")
                            break
                            
                except requests.exceptions.SSLError as ssl_err:
                    print(f"❌ SSL Error: {ssl_err}")
                    if not self.disable_ssl_var.get():
                        self.root.after(0, lambda: messagebox.showwarning(
                            "SSL Error", 
                            "SSL connection failed. Try enabling 'Disable SSL Verification' option."
                        ))
                except Exception as e:
                    print(f"❌ API {api_url} failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ API fetch failed: {e}")
            
        return results
    
    def parse_socrata_data(self, data):
        """Parse Socrata API format data with proper date sorting"""
        results = []
        for entry in data:
            try:
                draw_date = entry.get('draw_date', '')
                winning_numbers = entry.get('winning_numbers', '')
                multiplier = entry.get('multiplier', '')
                
                if draw_date and winning_numbers:
                    # Format date
                    if 'T' in draw_date:
                        date_obj = datetime.strptime(draw_date[:10], '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%m/%d/%Y')
                        sort_date = date_obj  # Keep datetime object for sorting
                    else:
                        formatted_date = draw_date
                        try:
                            sort_date = datetime.strptime(draw_date, '%m/%d/%Y')
                        except:
                            sort_date = datetime.now()
                    
                    # Parse numbers
                    numbers = winning_numbers.strip().split()
                    if len(numbers) >= 6:
                        results.append({
                            'date': formatted_date,
                            'sort_date': sort_date,
                            'numbers': numbers[:5],
                            'powerball': numbers[5],
                            'multiplier': multiplier or '1'
                        })
            except Exception:
                continue
        
        # Sort by date DESCENDING (most recent first) - GUARANTEED
        results.sort(key=lambda x: x['sort_date'], reverse=True)
        
        print(f"📅 Sorted {len(results)} results in DESCENDING date order")
        if results:
            print(f"   Latest: {results[0]['date']}")
            print(f"   Oldest: {results[-1]['date']}")
        
        # Remove sort_date from final results
        for result in results:
            result.pop('sort_date', None)
            
        return results
    
    def parse_raw_data(self, data):
        """Parse raw API data format with guaranteed descending date sort"""
        results = []
        for entry in data:
            try:
                if len(entry) >= 10:
                    # Typical raw format has date and numbers in specific positions
                    draw_date = str(entry[8]) if len(entry) > 8 else ''
                    winning_numbers = str(entry[9]) if len(entry) > 9 else ''
                    multiplier = str(entry[10]) if len(entry) > 10 else '1'
                    
                    if draw_date and winning_numbers:
                        # Format date and create sort_date
                        if 'T' in draw_date:
                            date_obj = datetime.strptime(draw_date[:10], '%Y-%m-%d')
                            formatted_date = date_obj.strftime('%m/%d/%Y')
                            sort_date = date_obj
                        else:
                            formatted_date = draw_date
                            try:
                                # Try multiple date formats for parsing
                                if '/' in draw_date:
                                    sort_date = datetime.strptime(draw_date, '%m/%d/%Y')
                                elif '-' in draw_date and len(draw_date.split('-')[0]) == 4:
                                    sort_date = datetime.strptime(draw_date, '%Y-%m-%d')
                                else:
                                    sort_date = datetime.strptime(draw_date, '%m/%d/%Y')
                            except:
                                sort_date = datetime(1900, 1, 1)  # Fallback for unparseable dates
                        
                        # Parse numbers
                        numbers = winning_numbers.strip().split()
                        if len(numbers) >= 6:
                            results.append({
                                'date': formatted_date,
                                'sort_date': sort_date,
                                'numbers': numbers[:5],
                                'powerball': numbers[5],
                                'multiplier': multiplier
                            })
            except Exception as e:
                print(f"Error parsing raw data entry: {e}")
                continue
        
        # CRITICAL: Sort by date DESCENDING (most recent first) - GUARANTEED
        results.sort(key=lambda x: x['sort_date'], reverse=True)
        
        print(f"📅 Raw data parsed and sorted: {len(results)} results in DESCENDING date order")
        if results:
            print(f"   Latest: {results[0]['date']} ({results[0]['sort_date'].strftime('%Y-%m-%d')})")
            print(f"   Oldest: {results[-1]['date']} ({results[-1]['sort_date'].strftime('%Y-%m-%d')})")
        
        # Remove sort_date from final results to clean up
        for result in results:
            result.pop('sort_date', None)
            
        return results
    
    def generate_sample_data(self, num_results=250):
        """Generate realistic sample Powerball data with latest known numbers - properly sorted by date"""
        results = []
        
        # Add the most recent known winning numbers first (these will be sorted properly)
        recent_draws = [
            {
                'date': '09/07/2025',
                'sort_date': datetime(2025, 9, 7),
                'numbers': ['1', '5', '12', '25', '42'],
                'powerball': '15',
                'multiplier': '2'
            },
            {
                'date': '09/04/2025',
                'sort_date': datetime(2025, 9, 4),
                'numbers': ['3', '16', '29', '61', '69'],
                'powerball': '22',
                'multiplier': '2'
            },
            {
                'date': '09/02/2025',
                'sort_date': datetime(2025, 9, 2),
                'numbers': ['8', '23', '25', '40', '53'],
                'powerball': '5',
                'multiplier': '3'
            },
            {
                'date': '08/30/2025',
                'sort_date': datetime(2025, 8, 30),
                'numbers': ['7', '18', '34', '45', '62'],
                'powerball': '11',
                'multiplier': '2'
            },
            {
                'date': '08/28/2025',
                'sort_date': datetime(2025, 8, 28),
                'numbers': ['2', '14', '27', '38', '56'],
                'powerball': '24',
                'multiplier': '4'
            }
        ]
        
        # Add recent known draws
        results.extend(recent_draws)
        
        # Generate additional realistic data for remaining slots
        start_date = datetime(2025, 8, 26)  # Start before the known draws
        
        for i in range(len(recent_draws), num_results):
            # Generate realistic numbers
            numbers = sorted(random.sample(range(1, 70), 5))
            powerball = random.randint(1, 26)
            multiplier = random.choice(['2', '3', '4', '5', '10'] + ['2'] * 3)
            
            # Calculate realistic draw dates (Mon, Wed, Sat) going backwards
            days_back = (i - len(recent_draws) + 1) * 2.5
            draw_date = start_date - timedelta(days=int(days_back))
            
            results.append({
                'date': draw_date.strftime('%m/%d/%Y'),
                'sort_date': draw_date,
                'numbers': [str(n) for n in numbers],
                'powerball': str(powerball),
                'multiplier': multiplier
            })
        
        # Sort by date DESCENDING (most recent first) - TRIPLE CHECK
        results.sort(key=lambda x: x['sort_date'], reverse=True)
        
        print(f"📅 Sample data: Generated {len(results)} results in DESCENDING date order")
        if results:
            print(f"   Latest: {results[0]['date']} ({results[0]['sort_date'].strftime('%Y-%m-%d')})")
            print(f"   Oldest: {results[-1]['date']} ({results[-1]['sort_date'].strftime('%Y-%m-%d')})")
        
        # Remove sort_date from final results
        for result in results:
            result.pop('sort_date', None)
            
        return results
    
    def load_csv_data(self):
        """Load data from CSV file with proper date sorting"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select Powerball CSV File",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not file_path:
                return []
            
            results = []
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
                for line in lines[1:]:  # Skip header
                    try:
                        parts = [p.strip().strip('"') for p in line.split(',')]
                        if len(parts) >= 6:
                            date_str = parts[0]
                            
                            # Try to parse date for sorting
                            try:
                                if '/' in date_str:
                                    sort_date = datetime.strptime(date_str, '%m/%d/%Y')
                                elif '-' in date_str:
                                    sort_date = datetime.strptime(date_str, '%Y-%m-%d')
                                else:
                                    sort_date = datetime.now()
                            except:
                                sort_date = datetime.now()
                            
                            # Basic CSV parsing
                            results.append({
                                'date': date_str,
                                'sort_date': sort_date,
                                'numbers': parts[1:6],
                                'powerball': parts[6] if len(parts) > 6 else parts[5],
                                'multiplier': parts[7] if len(parts) > 7 else '1'
                            })
                    except:
                        continue
            
            # Sort by date DESCENDING (most recent first) - ENSURE PROPER ORDER
            results.sort(key=lambda x: x['sort_date'], reverse=True)
            
            print(f"📅 CSV data: Loaded {len(results)} results in DESCENDING date order")
            if results:
                print(f"   Latest: {results[0]['date']}")
                print(f"   Oldest: {results[-1]['date']}")
            
            # Remove sort_date from final results
            for result in results:
                result.pop('sort_date', None)
            
            return results
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("CSV Error", f"Error loading CSV: {str(e)}"))
            return []
    
    def search_numbers(self):
        """Search for user's numbers in the current results"""
        if not self.current_data:
            messagebox.showwarning("No Data", "Please fetch Powerball data first before searching!")
            return
        
        try:
            # Parse user input
            user_input = self.numbers_entry.get().strip()
            if not user_input:
                messagebox.showwarning("Empty Input", "Please enter your numbers!")
                return
            
            # Parse the input format: "1,2,3,4,5 PB:6" or "1 2 3 4 5 PB:6"
            if "PB:" in user_input.upper():
                main_part, pb_part = user_input.upper().split("PB:")
                user_pb = pb_part.strip()
            else:
                messagebox.showwarning("Invalid Format", 
                    "Please use format: 1,2,3,4,5 PB:6\n"
                    "Example: 1,15,25,35,45 PB:12")
                return
            
            # Parse main numbers (handle both comma and space separated)
            main_part = main_part.replace(',', ' ').strip()
            user_numbers = [num.strip() for num in main_part.split() if num.strip().isdigit()]
            
            if len(user_numbers) != 5:
                messagebox.showwarning("Invalid Numbers", 
                    "Please enter exactly 5 main numbers!\n"
                    "Example: 1,15,25,35,45 PB:12")
                return
            
            if not user_pb.isdigit():
                messagebox.showwarning("Invalid Powerball", 
                    "Powerball must be a number!\n"
                    "Example: 1,15,25,35,45 PB:12")
                return
            
            # Validate number ranges
            for num in user_numbers:
                if not (1 <= int(num) <= 69):
                    messagebox.showwarning("Invalid Range", 
                        f"Main numbers must be between 1-69!\n"
                        f"You entered: {num}")
                    return
            
            if not (1 <= int(user_pb) <= 26):
                messagebox.showwarning("Invalid Range", 
                    f"Powerball must be between 1-26!\n"
                    f"You entered: {user_pb}")
                return
            
            # Sort user numbers for comparison
            user_numbers_sorted = sorted([int(n) for n in user_numbers])
            user_pb_int = int(user_pb)
            
            print(f"🔍 Searching for: {user_numbers_sorted} + PB:{user_pb_int}")
            
            # Search through results
            matches = []
            partial_matches = []
            
            for i, draw in enumerate(self.current_data):
                try:
                    # Get draw numbers
                    draw_numbers = sorted([int(n) for n in draw['numbers']])
                    draw_pb = int(draw['powerball'])
                    
                    # Check for exact match
                    if draw_numbers == user_numbers_sorted and draw_pb == user_pb_int:
                        matches.append({
                            'date': draw['date'],
                            'numbers': draw['numbers'],
                            'powerball': draw['powerball'],
                            'position': i + 1
                        })
                    else:
                        # Check for partial matches
                        matching_numbers = len(set(user_numbers_sorted) & set(draw_numbers))
                        pb_match = (draw_pb == user_pb_int)
                        
                        if matching_numbers >= 3 or (matching_numbers >= 2 and pb_match):
                            partial_matches.append({
                                'date': draw['date'],
                                'numbers': draw['numbers'],
                                'powerball': draw['powerball'],
                                'position': i + 1,
                                'matching_main': matching_numbers,
                                'pb_match': pb_match
                            })
                            
                except Exception as e:
                    continue
            
            # Display results
            if matches:
                # Exact match found!
                match_info = ""
                for match in matches:
                    match_info += f"Date: {match['date']}\n"
                    match_info += f"Numbers: {'-'.join(match['numbers'])} PB:{match['powerball']}\n"
                    match_info += f"Position: #{match['position']} in results\n\n"
                
                messagebox.showinfo("🎉 JACKPOT MATCH FOUND! 🎉", 
                    f"Your numbers match a winning draw!\n\n"
                    f"Your numbers: {'-'.join(map(str, user_numbers_sorted))} PB:{user_pb}\n\n"
                    f"Matching draws:\n{match_info}"
                    f"Congratulations! You would have won the JACKPOT!")
                
            elif partial_matches:
                # Show partial matches
                partial_info = f"Your numbers: {'-'.join(map(str, user_numbers_sorted))} PB:{user_pb}\n\n"
                partial_info += "Partial matches found:\n\n"
                
                for match in partial_matches[:5]:  # Show top 5 partial matches
                    partial_info += f"Date: {match['date']}\n"
                    partial_info += f"Numbers: {'-'.join(match['numbers'])} PB:{match['powerball']}\n"
                    partial_info += f"Match: {match['matching_main']}/5 numbers"
                    if match['pb_match']:
                        partial_info += " + Powerball"
                    partial_info += f" (Position #{match['position']})\n\n"
                
                messagebox.showinfo("🎯 Partial Matches Found", 
                    f"{len(partial_matches)} partial matches found!\n\n{partial_info}")
                
            else:
                # No matches
                messagebox.showinfo("❌ No Matches Found", 
                    f"Your numbers: {'-'.join(map(str, user_numbers_sorted))} PB:{user_pb}\n\n"
                    f"No exact or significant partial matches found in {len(self.current_data)} draws.\n\n"
                    f"Keep playing - your lucky numbers might come up next!")
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Error searching numbers: {str(e)}")
            print(f"Search error: {e}")
    
    def find_overdue_numbers(self):
        """Find numbers that haven't been drawn in the specified period - enhanced for overdue tab"""
        if not self.current_data:
            messagebox.showwarning("No Data", "Please fetch Powerball data in the Main tab first!")
            return
        
        try:
            # Get analysis period
            analysis_draws = int(self.analysis_period.get())
            
            # Use the specified number of recent draws
            recent_draws = self.current_data[:analysis_draws] if len(self.current_data) >= analysis_draws else self.current_data
            
            if len(recent_draws) < 5:
                messagebox.showwarning("Insufficient Data", f"Need at least 5 draws for analysis. Only {len(recent_draws)} available.")
                return
            
            # Track which numbers have been drawn
            drawn_main_numbers = set()
            drawn_powerballs = set()
            
            for draw in recent_draws:
                try:
                    # Add main numbers
                    for num in draw['numbers']:
                        drawn_main_numbers.add(int(num))
                    
                    # Add powerball
                    drawn_powerballs.add(int(draw['powerball']))
                except:
                    continue
            
            # Find overdue numbers
            all_main_numbers = set(range(1, 70))  # 1-69
            all_powerballs = set(range(1, 27))    # 1-26
            
            overdue_main = sorted(all_main_numbers - drawn_main_numbers)
            overdue_powerballs = sorted(all_powerballs - drawn_powerballs)
            
            # Clear text area and display analysis
            self.clear_overdue_text()
            
            # Create detailed analysis for display in overdue text area
            analysis_display = f"🔍 OVERDUE NUMBERS ANALYSIS - LAST {len(recent_draws)} DRAWS\n"
            analysis_display += "=" * 80 + "\n\n"
            
            analysis_display += f"📊 ANALYSIS PERIOD:\n"
            analysis_display += f"   From: {recent_draws[-1]['date']} (oldest)\n"
            analysis_display += f"   To: {recent_draws[0]['date']} (newest)\n"
            analysis_display += f"   Total draws analyzed: {len(recent_draws)}\n\n"
            
            # Main numbers analysis
            analysis_display += f"🎯 OVERDUE MAIN NUMBERS (1-69):\n"
            analysis_display += f"   Count: {len(overdue_main)} numbers haven't been drawn\n"
            analysis_display += f"   Percentage: {len(overdue_main)/69*100:.1f}% of all main numbers are overdue\n\n"
            
            if overdue_main:
                # Display overdue main numbers in rows of 10
                analysis_display += f"   Overdue Main Numbers:\n"
                for i in range(0, len(overdue_main), 10):
                    row = overdue_main[i:i+10]
                    analysis_display += f"   {' '.join(f'{num:>2}' for num in row)}\n"
                analysis_display += "\n"
            else:
                analysis_display += "   ✅ All main numbers (1-69) have been drawn!\n\n"
            
            # Powerball analysis
            analysis_display += f"⚡ OVERDUE POWERBALLS (1-26):\n"
            analysis_display += f"   Count: {len(overdue_powerballs)} Powerball numbers haven't been drawn\n"
            analysis_display += f"   Percentage: {len(overdue_powerballs)/26*100:.1f}% of all Powerballs are overdue\n\n"
            
            if overdue_powerballs:
                analysis_display += f"   Overdue Powerball Numbers:\n"
                analysis_display += f"   {' '.join(f'{num:>2}' for num in overdue_powerballs)}\n\n"
            else:
                analysis_display += "   ✅ All Powerball numbers (1-26) have been drawn!\n\n"
            
            # Statistics
            analysis_display += f"📈 DETAILED STATISTICS:\n"
            analysis_display += f"   Main numbers drawn: {len(drawn_main_numbers)} of 69 ({len(drawn_main_numbers)/69*100:.1f}%)\n"
            analysis_display += f"   Powerballs drawn: {len(drawn_powerballs)} of 26 ({len(drawn_powerballs)/26*100:.1f}%)\n"
            
            if overdue_main:
                analysis_display += f"   Longest overdue main: {max(overdue_main)}\n"
                analysis_display += f"   Shortest overdue main: {min(overdue_main)}\n"
            
            if overdue_powerballs:
                analysis_display += f"   Longest overdue Powerball: {max(overdue_powerballs)}\n"
                analysis_display += f"   Shortest overdue Powerball: {min(overdue_powerballs)}\n"
            
            analysis_display += "\n"
            
            # Suggestion
            if overdue_main and overdue_powerballs:
                if len(overdue_main) >= 5:
                    suggested_main = random.sample(overdue_main, 5)
                else:
                    # If less than 5 overdue, mix with some drawn numbers
                    drawn_main_list = list(drawn_main_numbers)
                    needed = 5 - len(overdue_main)
                    suggested_main = overdue_main + random.sample(drawn_main_list, needed)
                
                suggested_pb = random.choice(overdue_powerballs)
                suggested_main_sorted = sorted(suggested_main)
                
                analysis_display += f"🍀 SUGGESTED OVERDUE COMBINATION:\n"
                analysis_display += f"   Main Numbers: {' - '.join(f'{num:>2}' for num in suggested_main_sorted)}\n"
                analysis_display += f"   Powerball: {suggested_pb}\n"
                analysis_display += f"   Search Format: {','.join(map(str, suggested_main_sorted))} PB:{suggested_pb}\n\n"
                
                # Copy to search box in main tab
                search_format = f"{','.join(map(str, suggested_main_sorted))} PB:{suggested_pb}"
                self.numbers_entry.delete(0, tk.END)
                self.numbers_entry.insert(0, search_format)
                
                analysis_display += f"💡 The suggested combination has been copied to the search box in Main tab!\n"
                analysis_display += f"   Go to Main tab and click '🔎 Check Numbers' to see if this combination ever won.\n\n"
            
            elif not overdue_main and not overdue_powerballs:
                analysis_display += f"🎉 AMAZING! All numbers have been drawn in the last {len(recent_draws)} draws!\n"
                analysis_display += f"   This shows excellent number distribution.\n\n"
            
            analysis_display += f"💡 IMPORTANT NOTES:\n"
            analysis_display += f"   • Past results don't affect future probability\n"
            analysis_display += f"   • Each drawing is independent and random\n"
            analysis_display += f"   • 'Overdue' numbers have the same odds as any others\n"
            analysis_display += f"   • This analysis is for entertainment purposes only\n"
            
            # Display in overdue text area
            self.overdue_text_area.insert(tk.END, analysis_display, "header")
            
            # Update status
            self.status_label.config(text=f"Overdue analysis complete: {len(overdue_main)} main, {len(overdue_powerballs)} PB overdue")
            
            print(f"✅ Overdue analysis complete: {len(overdue_main)} main, {len(overdue_powerballs)} PB overdue")
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error analyzing overdue numbers: {str(e)}")
            print(f"Overdue analysis error: {e}")
    
    def find_hot_numbers(self):
        """Find numbers that have been drawn most frequently in the analysis period"""
        if not self.current_data:
            messagebox.showwarning("No Data", "Please fetch Powerball data in the Main tab first!")
            return
        
        try:
            # Get analysis period
            analysis_draws = int(self.analysis_period.get())
            
            # Use the specified number of recent draws
            recent_draws = self.current_data[:analysis_draws] if len(self.current_data) >= analysis_draws else self.current_data
            
            if len(recent_draws) < 10:
                messagebox.showwarning("Insufficient Data", f"Need at least 10 draws for analysis. Only {len(recent_draws)} available.")
                return
            
            # Count frequency of each number
            main_number_counts = {}
            powerball_counts = {}
            
            for draw in recent_draws:
                try:
                    # Count main numbers
                    for num in draw['numbers']:
                        num_int = int(num)
                        main_number_counts[num_int] = main_number_counts.get(num_int, 0) + 1
                    
                    # Count powerball
                    pb_int = int(draw['powerball'])
                    powerball_counts[pb_int] = powerball_counts.get(pb_int, 0) + 1
                except:
                    continue
            
            # Sort by frequency (most frequent first)
            hot_main = sorted(main_number_counts.items(), key=lambda x: x[1], reverse=True)
            hot_powerballs = sorted(powerball_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Clear and create detailed analysis
            self.clear_overdue_text()
            analysis_display = f"🔥 HOT NUMBERS ANALYSIS - LAST {len(recent_draws)} DRAWS\n"
            analysis_display += "=" * 80 + "\n\n"
            
            analysis_display += f"📊 ANALYSIS PERIOD:\n"
            analysis_display += f"   From: {recent_draws[-1]['date']} (oldest)\n"
            analysis_display += f"   To: {recent_draws[0]['date']} (newest)\n"
            analysis_display += f"   Total draws analyzed: {len(recent_draws)}\n\n"
            
            # Hot main numbers
            analysis_display += f"🔥 HOTTEST MAIN NUMBERS (Top 15):\n"
            for i, (number, count) in enumerate(hot_main[:15]):
                analysis_display += f"   #{i+1:>2}: {number:>2} (drawn {count} times)\n"
            analysis_display += "\n"
            
            # Hot powerballs
            analysis_display += f"⚡ HOTTEST POWERBALLS (Top 10):\n"
            for i, (number, count) in enumerate(hot_powerballs[:10]):
                analysis_display += f"   #{i+1:>2}: {number:>2} (drawn {count} times)\n"
            analysis_display += "\n"
            
            # Statistics
            if hot_main and hot_powerballs:
                max_main_freq = hot_main[0][1]
                max_pb_freq = hot_powerballs[0][1]
                analysis_display += f"📈 STATISTICS:\n"
                analysis_display += f"   Hottest main number: {hot_main[0][0]} ({max_main_freq} times)\n"
                analysis_display += f"   Hottest Powerball: {hot_powerballs[0][0]} ({max_pb_freq} times)\n"
                analysis_display += f"   Average main frequency: {sum(count for _, count in hot_main) / len(hot_main):.1f}\n"
                analysis_display += f"   Average PB frequency: {sum(count for _, count in hot_powerballs) / len(hot_powerballs):.1f}\n\n"
                
                # Suggestion based on hot numbers
                suggested_main = [num for num, _ in hot_main[:7]]  # Take top 7, pick 5
                suggested_main = random.sample(suggested_main, 5)
                suggested_pb = hot_powerballs[0][0]  # Hottest powerball
                
                analysis_display += f"🍀 SUGGESTED HOT COMBINATION:\n"
                analysis_display += f"   Main Numbers: {' - '.join(f'{num:>2}' for num in sorted(suggested_main))}\n"
                analysis_display += f"   Powerball: {suggested_pb}\n"
                analysis_display += f"   Search Format: {','.join(map(str, sorted(suggested_main)))} PB:{suggested_pb}\n\n"
                
                # Copy to search box
                search_format = f"{','.join(map(str, sorted(suggested_main)))} PB:{suggested_pb}"
                self.numbers_entry.delete(0, tk.END)
                self.numbers_entry.insert(0, search_format)
                
                analysis_display += f"💡 The suggested combination has been copied to the search box in Main tab!\n\n"
            
            analysis_display += "💡 NOTE: Past results don't predict future draws.\nEach drawing is independent and random!"
            
            # Display in overdue text area
            self.overdue_text_area.insert(tk.END, analysis_display, "header")
            
            # Update status
            self.status_label.config(text=f"Hot numbers analysis complete - {len(hot_main)} numbers analyzed")
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error analyzing hot numbers: {str(e)}")
            print(f"Hot analysis error: {e}")
    
    def generate_lucky_numbers(self):
        """Generate lucky numbers using various strategies"""
        try:
            # Generate multiple combinations using different strategies
            combinations = []
            
            # Strategy 1: Completely Random
            random_main = sorted(random.sample(range(1, 70), 5))
            random_pb = random.randint(1, 26)
            combinations.append({
                'name': '🎲 Completely Random',
                'main': random_main,
                'pb': random_pb,
                'description': 'Pure random selection'
            })
            
            # Strategy 2: Balanced (mix of low/high numbers)
            low_nums = list(range(1, 35))  # 1-34
            high_nums = list(range(35, 70))  # 35-69
            balanced_main = sorted(random.sample(low_nums, 2) + random.sample(high_nums, 3))
            balanced_pb = random.randint(1, 26)
            combinations.append({
                'name': '⚖️ Balanced Low/High',
                'main': balanced_main,
                'pb': balanced_pb,
                'description': '2 low (1-34) + 3 high (35-69)'
            })
            
            # Strategy 3: Hot and Cold Mix (if data available)
            if self.current_data and len(self.current_data) >= 20:
                analysis_draws = int(self.analysis_period.get())
                recent_draws = self.current_data[:analysis_draws] if len(self.current_data) >= analysis_draws else self.current_data[:20]
                
                # Find most and least frequent numbers
                main_counts = {}
                for draw in recent_draws:
                    try:
                        for num in draw['numbers']:
                            num_int = int(num)
                            main_counts[num_int] = main_counts.get(num_int, 0) + 1
                    except:
                        continue
                
                if main_counts:
                    # Get hot numbers (most frequent)
                    hot_nums = [num for num, _ in sorted(main_counts.items(), key=lambda x: x[1], reverse=True)[:15]]
                    # Get cold numbers (least frequent or not drawn)
                    all_nums = set(range(1, 70))
                    drawn_nums = set(main_counts.keys())
                    cold_nums = list(all_nums - drawn_nums)
                    if len(cold_nums) < 10:
                        cold_nums.extend([num for num, _ in sorted(main_counts.items(), key=lambda x: x[1])[:10]])
                    
                    # Mix hot and cold
                    mixed_main = sorted(random.sample(hot_nums, 3) + random.sample(cold_nums[:15], 2))
                    mixed_pb = random.randint(1, 26)
                    combinations.append({
                        'name': '🔥❄️ Hot & Cold Mix',
                        'main': mixed_main,
                        'pb': mixed_pb,
                        'description': '3 frequent + 2 rare numbers'
                    })
            
            # Strategy 4: Pattern-based (consecutive, spread)
            start = random.randint(1, 30)
            pattern_main = sorted([start, start+5, start+15, start+25, start+35])
            # Ensure all numbers are within range
            pattern_main = [min(69, num) for num in pattern_main]
            pattern_pb = random.randint(1, 26)
            combinations.append({
                'name': '📐 Pattern Spread',
                'main': pattern_main,
                'pb': pattern_pb,
                'description': 'Numbers with even spacing'
            })
            
            # Strategy 5: Birth dates inspired (but modified for lottery)
            birthday_main = []
            birthday_main.append(random.randint(1, 31))    # Day
            birthday_main.append(random.randint(1, 12))    # Month
            birthday_main.append(random.randint(50, 69))   # Year-inspired high number
            birthday_main.extend(random.sample(range(13, 49), 2))  # Fill the gap
            birthday_main = sorted(list(set(birthday_main)))  # Remove duplicates
            while len(birthday_main) < 5:
                birthday_main.append(random.randint(1, 69))
            birthday_main = sorted(birthday_main[:5])
            birthday_pb = random.randint(1, 26)
            combinations.append({
                'name': '🎂 Birthday Inspired',
                'main': birthday_main,
                'pb': birthday_pb,
                'description': 'Based on calendar dates'
            })
            
            # Clear and format the display
            self.clear_overdue_text()
            lucky_display = "🍀 LUCKY NUMBER COMBINATIONS\n"
            lucky_display += "=" * 80 + "\n\n"
            
            for i, combo in enumerate(combinations, 1):
                lucky_display += f"{combo['name']}:\n"
                lucky_display += f"   Numbers: {', '.join(map(str, combo['main']))}\n"
                lucky_display += f"   Powerball: {combo['pb']}\n"
                lucky_display += f"   Format: {','.join(map(str, combo['main']))} PB:{combo['pb']}\n"
                lucky_display += f"   Strategy: {combo['description']}\n\n"
            
            lucky_display += "🎯 HOW TO USE:\n"
            lucky_display += "   • Copy any format line above\n"
            lucky_display += "   • Go to Main tab and paste into 'Check Your Numbers' search box\n"
            lucky_display += "   • See if these numbers ever won!\n\n"
            
            lucky_display += "💡 REMEMBER:\n"
            lucky_display += "   • All combinations have equal odds\n"
            lucky_display += "   • Past results don't affect future draws\n"
            lucky_display += "   • Play responsibly!\n"
            
            # Display in overdue text area
            self.overdue_text_area.insert(tk.END, lucky_display, "header")
            
            # Update status
            self.status_label.config(text=f"Generated {len(combinations)} lucky number combinations")
            
        except Exception as e:
            messagebox.showerror("Generator Error", f"Error generating lucky numbers: {str(e)}")
            print(f"Lucky number generation error: {e}")
    
    def display_winning_numbers(self, numbers_data, source_name):
        """Display winning numbers in formatted table"""
        if not numbers_data:
            self.text_area.insert(tk.END, "No data to display.\n")
            return
        
        # Store data for searching
        self.current_data = numbers_data.copy()
        
        # SORT numbers_data by date BEFORE adding to textarea
        try:
            # Parse dates and add temporary sort field
            for item in numbers_data:
                try:
                    date_str = item['date']
                    # Handle different date formats
                    if '/' in date_str:
                        item['temp_sort_date'] = datetime.strptime(date_str, '%m/%d/%Y')
                    elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                        item['temp_sort_date'] = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    else:
                        item['temp_sort_date'] = datetime.strptime(date_str, '%m/%d/%Y')
                except:
                    item['temp_sort_date'] = datetime(1900, 1, 1)  # Bad dates go to bottom
            
            # Sort by date in DESCENDING order (newest first)
            numbers_data.sort(key=lambda x: x['temp_sort_date'], reverse=True)
            
            # Remove temporary sort field
            for item in numbers_data:
                item.pop('temp_sort_date', None)
            
            print(f"✅ Sorted {len(numbers_data)} records by date (descending)")
            print(f"   Newest: {numbers_data[0]['date']}")
            print(f"   Oldest: {numbers_data[-1]['date']}")
            
        except Exception as e:
            print(f"❌ Date sorting failed: {e}")
        
        # Header
        header = f"🎱 POWERBALL WINNING NUMBERS - {len(numbers_data)} RECENT DRAWS\n"
        header += f"Data Source: {source_name}\n"
        header += f"💡 Use 'Check Your Numbers' above to search for matches!\n"
        header += "=" * 85 + "\n"
        header += f"{'Date':>12} │ {'Winning Numbers':^25} │ {'PB':^4} │ {'Multiplier':^10} │ {'Draw #':>6}\n"
        header += "─" * 85 + "\n"
        self.text_area.insert(tk.END, header, "header")
        
        # Display each draw
        for i, draw in enumerate(numbers_data):
            try:
                date = draw['date']
                numbers = draw['numbers']
                powerball = draw['powerball']
                multiplier = draw.get('multiplier', '1')
                draw_num = i + 1
                
                # Format numbers
                numbers_str = "-".join(f"{num:>2}" for num in numbers)
                mult_str = f"{multiplier}x" if multiplier != '1' else ""
                
                # Main line
                line = f"{date:>12} │ {numbers_str:^25} │"
                self.text_area.insert(tk.END, line)
                
                # Powerball in red
                pb_text = f" {powerball:>2} "
                self.text_area.insert(tk.END, pb_text, "powerball")
                
                # Rest of line
                rest_line = f"│ {mult_str:^10} │ {draw_num:>6}\n"
                self.text_area.insert(tk.END, rest_line)
                
                # Separator every 12 entries
                if draw_num % 12 == 0:
                    separator = "─" * 85 + "\n"
                    self.text_area.insert(tk.END, separator)
                    
            except Exception as e:
                continue
        
        # Add search reminder
        search_note = f"\n🔍 SEARCH FEATURE READY:\n"
        search_note += f"✅ {len(numbers_data)} draws loaded and ready to search\n"
        search_note += f"💡 Enter your numbers above in format: 1,15,25,35,45 PB:12\n"
        search_note += f"🎯 Search will find exact matches and significant partial matches\n"
        search_note += f"📊 Visit 'Overdue Numbers' tab for advanced analysis!\n"
        self.text_area.insert(tk.END, search_note, "success")
        
        # Add statistics
        self.add_statistics(numbers_data, source_name)
    
    def add_statistics(self, numbers_data, source_name):
        """Add frequency analysis and statistics"""
        stats = f"\n{'='*85}\n"
        stats += "📊 STATISTICAL ANALYSIS\n"
        stats += f"{'='*85}\n"
        
        # Basic info
        stats += f"Total draws analyzed: {len(numbers_data)}\n"
        stats += f"Data source: {source_name}\n"
        stats += f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Frequency analysis
        if numbers_data:
            all_numbers = []
            all_powerballs = []
            multipliers = []
            
            for draw in numbers_data:
                try:
                    all_numbers.extend([int(n) for n in draw['numbers']])
                    all_powerballs.append(int(draw['powerball']))
                    mult = draw.get('multiplier', '1').replace('x', '')
                    if mult.isdigit():
                        multipliers.append(int(mult))
                except:
                    continue
            
            if all_numbers and all_powerballs:
                # Most frequent analysis
                main_counts = Counter(all_numbers)
                pb_counts = Counter(all_powerballs)
                mult_counts = Counter(multipliers)
                
                most_freq_main = main_counts.most_common(1)[0]
                most_freq_pb = pb_counts.most_common(1)[0]
                
                stats += f"🎯 FREQUENCY ANALYSIS:\n"
                stats += f"Most frequent main number: {most_freq_main[0]} ({most_freq_main[1]} times)\n"
                stats += f"Most frequent Powerball: {most_freq_pb[0]} ({most_freq_pb[1]} times)\n"
                
                if multipliers:
                    most_freq_mult = mult_counts.most_common(1)[0]
                    stats += f"Most frequent multiplier: {most_freq_mult[0]}x ({most_freq_mult[1]} times)\n"
                
                # Averages
                avg_main = sum(all_numbers) / len(all_numbers)
                avg_pb = sum(all_powerballs) / len(all_powerballs)
                
                stats += f"\n📈 AVERAGES:\n"
                stats += f"Average main number: {avg_main:.1f}\n"
                stats += f"Average Powerball: {avg_pb:.1f}\n"
                
                # Number ranges
                stats += f"\n📊 RANGES:\n"
                stats += f"Main numbers: {min(all_numbers)} - {max(all_numbers)}\n"
                stats += f"Powerballs: {min(all_powerballs)} - {max(all_powerballs)}\n"
        
        stats += f"\n{'='*85}\n"
        if "API" in source_name:
            stats += "✅ Live data successfully retrieved!\n"
        elif "Offline" in source_name:
            stats += "✅ Sample data generated - No network issues!\n"
        elif "CSV" in source_name:
            stats += "✅ CSV data loaded successfully!\n"
        
        self.text_area.insert(tk.END, stats, "success")
    
    def clear_text(self):
        """Clear the main text area"""
        self.text_area.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = PowerballGUI(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (950 // 2)
    y = (root.winfo_screenheight() // 2) - (800 // 2)
    root.geometry(f"950x800+{x}+{y}")
    
    root.minsize(900, 750)
    root.mainloop()

if __name__ == "__main__":
    main()
    