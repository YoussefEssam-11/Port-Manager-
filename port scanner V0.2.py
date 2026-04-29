import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import socket
import threading
from datetime import datetime
import subprocess
import platform
import os
import tempfile
import time

class PortScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2pro scanner - Professional Port Security Tool")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))
        self.root.geometry("1920x1080")
        self.root.configure(bg='#1a1a2e')
        
        # Store data (hneg data)
        self.target_ip = None
        self.target_domain = None
        self.start_port = None
        self.end_port = None
        self.open_ports = []  # List of dicts (lista mn el dicts)
        self.scan_complete = False
        self.is_scanning = False  # check law kan fe scan (ycheck law fi scan)
        
        # Known services with emojis (el khadmat el m3rofa)
        self.services = {
            20: "📁 FTP-Data", 21: "📁 FTP", 22: "🔒 SSH", 23: "⚠️ Telnet", 25: "📧 SMTP",
            53: "🌐 DNS", 80: "🌍 HTTP", 110: "📧 POP3", 111: "🔧 RPC", 135: "🔧 RPC",
            139: "🖥️ NetBIOS", 143: "📧 IMAP", 443: "🔒 HTTPS", 445: "⚠️ SMB", 993: "🔒 IMAPS",
            995: "🔒 POP3S", 1433: "🗄️ MSSQL", 3306: "🐬 MySQL", 3389: "🖥️ RDP",
            5432: "🐘 PostgreSQL", 5900: "🖥️ VNC", 6379: "📊 Redis", 8080: "🌍 HTTP-Alt",
            8443: "🔒 HTTPS-Alt", 27017: "🍃 MongoDB"
        }
        
        # Dangerous ports (el portat el khatra)
        self.dangerous_ports = [21, 23, 135, 139, 445, 3389, 5900, 1433, 3306]
        
        # Create notebook (a3ml el tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs (a3ml el tabs)
        self.create_tab1_target()
        self.create_tab2_scan()
        self.create_tab3_management()
        self.create_tab4_report()
        self.create_tab5_powershell()  # PowerShell Terminal Tab
        
        # Create status bar (a3ml el status bar)
        self.create_status_bar()
        self.configure_styles()
    
    def check_admin(self):
        """ycheck law el program ysh8l b sal7yat admin"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def restart_as_admin(self):
        """y3ml restart lprogram b sal7yat admin"""
        try:
            import ctypes
            import sys
            
            script = os.path.abspath(sys.argv[0])
            
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script}"', 
                None, 
                1
            )
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot restart as admin: {str(e)}")
    
    def cleanup_temp_files(self, *files):
        """Clean up multiple temp files (yms7 el temp files)"""
        for file in files:
            try:
                if file and os.path.exists(file):
                    os.unlink(file)
            except:
                pass
    
    def run_powershell_admin(self, command):
        """y8y2 command PowerShell b sal7yat admin - WORKING WITH UAC"""
        try:
            # Minimize main window to show UAC (y5fy el window 3ashan yzhr el UAC)
            self.root.iconify()
            self.root.update()
            
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"🔑 Running command with Admin rights...\n")
            self.output_text.insert(tk.END, f"$> {command}\n")
            self.output_text.insert(tk.END, "-" * 70 + "\n")
            self.output_text.see(tk.END)
            self.root.update()
            
            self.status_label.config(text=f"⚡ Sending admin command...")
            
            # Create a temporary PowerShell script file (a3ml file powershell wa2ti)
            temp_ps1 = os.path.join(tempfile.gettempdir(), f"admin_cmd_{int(time.time())}.ps1")
            with open(temp_ps1, 'w', encoding='utf-8') as f:
                f.write(command)
            
            # Create a VBS script to run PowerShell as admin (works 100% on all Windows)
            temp_vbs = os.path.join(tempfile.gettempdir(), f"run_admin_{int(time.time())}.vbs")
            with open(temp_vbs, 'w', encoding='utf-8') as f:
                f.write(f'''
' This script runs PowerShell as Administrator
Set UAC = CreateObject("Shell.Application")
UAC.ShellExecute "powershell.exe", "-ExecutionPolicy Bypass -File ""{temp_ps1}""", "", "runas", 1
''')
            
            # Run the VBS script
            subprocess.Popen(['wscript.exe', temp_vbs], shell=True)
            
            self.output_text.insert(tk.END, "\n" + "-" * 70 + "\n")
            self.output_text.insert(tk.END, "✅ A UAC prompt will open in a moment.\n")
            self.output_text.insert(tk.END, "⚠️ Look for the 'User Account Control' window.\n")
            self.output_text.insert(tk.END, "⚠️ Click 'YES' on the UAC prompt.\n")
            self.output_text.insert(tk.END, "✅ The command will run in PowerShell.\n")
            self.output_text.insert(tk.END, "⏰ The window will close automatically.\n")
            
            self.status_label.config(text="✅ UAC prompt sent - click YES to allow")
            
            # Clean up files after 15 seconds (yms7 el temp files ba3d 15 seconds)
            self.root.after(15000, lambda: self.cleanup_temp_files(temp_ps1, temp_vbs))
            
            # Restore window after UAC (y5ly el window yzhr tany)
            self.root.after(2000, lambda: self.root.deiconify())
            
        except Exception as e:
            self.output_text.insert(tk.END, f"\n❌ Error: {str(e)}")
            self.status_label.config(text="❌ Error running admin command")
            self.root.deiconify()  # Restore window on error
    
    def run_powershell_command(self, command):
        """y8y2 command PowerShell (l2gl awamr 3adya)"""
        # Check if command needs admin (ycheck law command m7tag admin)
        admin_keywords = ["netsh advfirewall", "New-NetFirewallRule", "Set-NetFirewallRule", 
                          "Remove-NetFirewallRule", "Enable-NetFirewallRule", "Disable-NetFirewallRule"]
        
        needs_admin = any(keyword in command for keyword in admin_keywords)
        
        if needs_admin:
            self.run_powershell_admin(command)
        else:
            try:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, f"$> {command}\n")
                self.output_text.insert(tk.END, "-" * 70 + "\n")
                self.output_text.see(tk.END)
                self.root.update()
                
                self.status_label.config(text=f"⚡ Running command...")
                
                process = subprocess.Popen(
                    ["powershell.exe", "-Command", command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True
                )
                
                stdout, stderr = process.communicate(timeout=30)
                
                if stdout:
                    self.output_text.insert(tk.END, stdout)
                if stderr:
                    self.output_text.insert(tk.END, f"\n⚠️ {stderr}")
                
                if process.returncode == 0:
                    self.output_text.insert(tk.END, "\n✅ Command executed successfully")
                    self.status_label.config(text="✅ Command completed")
                else:
                    if "Access denied" in stderr or "elevation" in stderr:
                        self.output_text.insert(tk.END, "\n🔑 This command needs Administrator privileges!")
                    self.status_label.config(text="❌ Command failed")
                
                self.output_text.see(tk.END)
                
            except subprocess.TimeoutExpired:
                self.output_text.insert(tk.END, "\n⏰ Command timed out")
            except Exception as e:
                self.output_text.insert(tk.END, f"\n❌ Error: {str(e)}")
    
    def run_custom_command(self):
        """y8y2 custom command mn el entry box"""
        command = self.command_entry.get().strip()
        if not command:
            messagebox.showwarning("Empty Command", "Please enter a command first!")
            return
        
        admin_keywords = ["netsh advfirewall", "New-NetFirewallRule", "Set-NetFirewallRule", 
                          "Remove-NetFirewallRule", "Enable-NetFirewallRule", "Disable-NetFirewallRule"]
        
        needs_admin = any(keyword in command for keyword in admin_keywords)
        
        if needs_admin:
            self.run_powershell_admin(command)
        else:
            self.run_powershell_command(command)
    
    def run_custom_command_from_btn(self, command):
        """y8y2 command mn el zoryar"""
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, command)
        self.run_custom_command()
    
    def clear_output(self):
        """y5ly el output area"""
        self.output_text.delete(1.0, tk.END)
        self.status_label.config(text="✅ Output cleared")
    
    def create_status_bar(self):
        """Create status bar at bottom (a3ml status bar fel footer)"""
        self.status_bar = tk.Frame(self.root, bg='#2c3e50', height=30)
        self.status_bar.pack(side='bottom', fill='x')
        
        self.status_label = tk.Label(self.status_bar, text="✅ Ready to scan", 
                                     font=('Arial', 9), fg='#ecf0f1', bg='#2c3e50')
        self.status_label.pack(side='left', padx=10, pady=5)
        
        self.time_label = tk.Label(self.status_bar, text="", 
                                   font=('Arial', 9), fg='#ecf0f1', bg='#2c3e50')
        self.time_label.pack(side='right', padx=10, pady=5)
        self.update_clock()
    
    def update_clock(self):
        """Update clock in status bar (b7dd el wa2t fel status bar)"""
        current_time = datetime.now().strftime("%H:%M:%S - %Y-%m-%d")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_clock)
    
    def configure_styles(self):
        """Configure GUI styles (bzwe7 el shakl)"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#1a1a2e', foreground='white', font=('Segoe UI', 10))
        style.configure('TFrame', background='#1a1a2e')
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=5)
        style.configure('TNotebook', background='#1a1a2e')
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=10)
    
    def create_tab1_target(self):
        """Tab 1: Get IP/Domain from user (y5od el target mn el user)"""
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="🎯 Target Setup")
        
        # Main frame with centering (el frame el ra2eesi)
        main_frame = tk.Frame(tab1, bg='#1a1a2e')
        main_frame.pack(expand=True)
        
        # Card-like container
        card = tk.Frame(main_frame, bg='#2d2d44', relief='flat', bd=0)
        card.pack(pady=50, padx=50, ipadx=40, ipady=40)
        
        # Title
        title = tk.Label(card, text="🔐 2Pro Security Scanner", 
                        font=('Segoe UI', 28, 'bold'), bg='#2d2d44', fg='#6c63ff')
        title.pack(pady=20)
        
        # Subtitle
        subtitle = tk.Label(card, text="Professional Port Security Assessment Tool",
                           font=('Segoe UI', 12), bg='#2d2d44', fg='#a0a0c0')
        subtitle.pack(pady=10)
        
        # Input frame
        input_frame = tk.Frame(card, bg='#2d2d44')
        input_frame.pack(pady=40)
        
        tk.Label(input_frame, text="Target IP or Domain:", font=('Segoe UI', 12),
                bg='#2d2d44', fg='white').grid(row=0, column=0, padx=10, pady=10)
        
        self.target_entry = tk.Entry(input_frame, width=40, font=('Segoe UI', 12),
                                     bg='#1a1a2e', fg='white', insertbackground='white',
                                     relief='flat', bd=1)
        self.target_entry.grid(row=0, column=1, padx=10, pady=10)
        self.target_entry.insert(0, "scanme.nmap.org")
        
        # Info box
        info_text = """
        ℹ️  LEGAL TEST TARGETS (Targetat ylzmo 2zn):
        • scanme.nmap.org - Official test server (Recommended)
        • localhost or 127.0.0.1 - Your own computer
        • Your home network devices (192.168.x.x)
        
        ⚠️  WARNING: Only scan targets you own or have permission to scan!
        """
        
        info_label = tk.Label(card, text=info_text, bg='#1a1a2e', fg='#a0a0c0',
                             font=('Segoe UI', 9), justify='left', padx=20, pady=15)
        info_label.pack(pady=20, fill='x')
        
        # Next button
        next_btn = tk.Button(card, text="NEXT →", command=self.validate_target,
                            bg='#6c63ff', fg='white', font=('Segoe UI', 14, 'bold'),
                            padx=40, pady=12, cursor='hand2', relief='flat')
        next_btn.pack(pady=20)
    
    def validate_target(self):
        """Validate and resolve target IP (yata2ked mn el target)"""
        target = self.target_entry.get().strip()
        
        if not target:
            messagebox.showerror("Error", "Please enter a target IP or domain")
            return
        
        self.status_label.config(text=f"🔄 Resolving {target}...")
        
        try:
            self.target_domain = target
            self.target_ip = socket.gethostbyname(target)
            self.status_label.config(text=f"✅ Target resolved: {self.target_ip}")
            messagebox.showinfo("Success", f"Target resolved!\n\n🌐 Domain: {target}\n📍 IP: {self.target_ip}")
            self.notebook.select(1)
        except socket.gaierror:
            self.status_label.config(text="❌ Resolution failed")
            messagebox.showerror("Error", f"Cannot resolve domain: {target}\n\nPlease check the address")
    
    def create_tab2_scan(self):
        """Tab 2: Port range and scanning (y7dd el port range we yscan)"""
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="🔍 Scan Ports")
        
        # Main frame
        main_frame = tk.Frame(tab2, bg='#1a1a2e')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Controls
        control_panel = tk.Frame(main_frame, bg='#2d2d44', width=350)
        control_panel.pack(side='left', fill='y', padx=(0, 20), pady=10)
        control_panel.pack_propagate(False)
        
        # Control panel title
        tk.Label(control_panel, text="⚙️ Scan Configuration", 
                font=('Segoe UI', 16, 'bold'), bg='#2d2d44', fg='#6c63ff').pack(pady=20)
        
        # Port range
        range_frame = tk.Frame(control_panel, bg='#2d2d44')
        range_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(range_frame, text="Port Range:", font=('Segoe UI', 12),
                bg='#2d2d44', fg='white').pack(anchor='w', pady=(0, 10))
        
        port_input_frame = tk.Frame(range_frame, bg='#2d2d44')
        port_input_frame.pack(fill='x')
        
        tk.Label(port_input_frame, text="From:", bg='#2d2d44', fg='white').pack(side='left', padx=5)
        self.start_port_entry = tk.Entry(port_input_frame, width=8, font=('Segoe UI', 11),
                                         bg='#1a1a2e', fg='white', relief='flat')
        self.start_port_entry.pack(side='left', padx=5)
        self.start_port_entry.insert(0, "1")
        
        tk.Label(port_input_frame, text="To:", bg='#2d2d44', fg='white').pack(side='left', padx=5)
        self.end_port_entry = tk.Entry(port_input_frame, width=8, font=('Segoe UI', 11),
                                       bg='#1a1a2e', fg='white', relief='flat')
        self.end_port_entry.pack(side='left', padx=5)
        self.end_port_entry.insert(0, "1024")
        
        # Quick select
        tk.Label(control_panel, text="Quick Select:", font=('Segoe UI', 12),
                bg='#2d2d44', fg='white').pack(anchor='w', padx=20, pady=(20, 10))
        
        quick_buttons = [
            ("🚀 Common (1-1024)", "1", "1024"),
            ("🌐 All Ports (1-65535)", "1", "65535"),
            ("🌍 Web (80,443)", "80", "443"),
            ("🗄️ Database (3306,5432)", "3306", "5432")
        ]
        
        for text, start, end in quick_buttons:
            btn = tk.Button(control_panel, text=text, 
                           command=lambda s=start, e=end: self.set_port_range(s, e),
                           bg='#1a1a2e', fg='white', font=('Segoe UI', 10),
                           relief='flat', cursor='hand2')
            btn.pack(pady=5, padx=20, fill='x')
        
        # Scan button
        self.scan_btn = tk.Button(control_panel, text="🚀 START SCAN", command=self.start_scan,
                                 bg='#e74c3c', fg='white', font=('Segoe UI', 16, 'bold'),
                                 padx=20, pady=15, cursor='hand2', relief='flat')
        self.scan_btn.pack(pady=30, padx=20, fill='x')
        
        # Right panel - Results
        results_panel = tk.Frame(main_frame, bg='#2d2d44')
        results_panel.pack(side='right', fill='both', expand=True)
        
        tk.Label(results_panel, text="📊 Live Scan Results", 
                font=('Segoe UI', 16, 'bold'), bg='#2d2d44', fg='#6c63ff').pack(pady=20)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(results_panel, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(pady=10)
        
        self.progress_label = tk.Label(results_panel, text="Ready to scan", 
                                      bg='#2d2d44', fg='#a0a0c0')
        self.progress_label.pack()
        
        # Status text area
        self.scan_status = scrolledtext.ScrolledText(results_panel, height=20,
                                                     bg='#1a1a2e', fg='#00ff88',
                                                     font=('Consolas', 10), wrap=tk.WORD)
        self.scan_status.pack(fill='both', expand=True, padx=20, pady=20)
    
    def set_port_range(self, start, end):
        """Set port range from quick select buttons (y7dd mdey2 el portat)"""
        self.start_port_entry.delete(0, tk.END)
        self.start_port_entry.insert(0, start)
        self.end_port_entry.delete(0, tk.END)
        self.end_port_entry.insert(0, end)
    
    def start_scan(self):
        """Start scanning (ybd2 el scan)"""
        if self.is_scanning:
            messagebox.showwarning("Scan in Progress", "Please wait for current scan to complete!")
            return
        
        try:
            self.start_port = int(self.start_port_entry.get())
            self.end_port = int(self.end_port_entry.get())
            
            if self.start_port < 1 or self.end_port > 65535 or self.start_port > self.end_port:
                messagebox.showerror("Error", "Invalid port range!\nPorts must be between 1-65535")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid port numbers")
            return
        
        self.is_scanning = True
        self.scan_btn.config(state='disabled', text='⏳ SCANNING...', bg='#f39c12')
        self.scan_status.delete(1.0, tk.END)
        self.open_ports = []
        self.progress_var.set(0)
        self.status_label.config(text="🔍 Scanning in progress...")
        
        # Start scan in separate thread
        scan_thread = threading.Thread(target=self.perform_scan)
        scan_thread.daemon = True
        scan_thread.start()
    
    def perform_scan(self):
        """Perform actual port scanning (y3ml el scan fl portat)"""
        total_ports = self.end_port - self.start_port + 1
        scanned = 0
        
        self.scan_status.insert(tk.END, "=" * 60 + "\n")
        self.scan_status.insert(tk.END, "🔍 2PRO SECURITY SCAN\n")
        self.scan_status.insert(tk.END, "=" * 60 + "\n")
        self.scan_status.insert(tk.END, f"🎯 Target: {self.target_domain} ({self.target_ip})\n")
        self.scan_status.insert(tk.END, f"📡 Port Range: {self.start_port}-{self.end_port}\n")
        self.scan_status.insert(tk.END, f"⏰ Started: {datetime.now()}\n")
        self.scan_status.insert(tk.END, "=" * 60 + "\n\n")
        self.scan_status.see(tk.END)
        
        for port in range(self.start_port, self.end_port + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                result = sock.connect_ex((self.target_ip, port))
                
                if result == 0:
                    service = self.services.get(port, "❓ Unknown")
                    self.open_ports.append({
                        'port': port,
                        'service': service,
                        'keep': None
                    })
                    
                    if port in self.dangerous_ports:
                        self.scan_status.insert(tk.END, f"⚠️  DANGER: Port {port} - {service}\n")
                    else:
                        self.scan_status.insert(tk.END, f"✅ OPEN: Port {port} - {service}\n")
                    self.scan_status.see(tk.END)
                
                sock.close()
                
                scanned += 1
                progress = (scanned / total_ports) * 100
                self.progress_var.set(progress)
                self.progress_label.config(text=f"Scanning: {scanned}/{total_ports} ports ({progress:.1f}%)")
                
            except:
                pass
        
        self.is_scanning = False
        self.scan_complete = True
        self.scan_btn.config(state='normal', text='🚀 START SCAN', bg='#e74c3c')
        self.progress_label.config(text=f"✅ Scan complete! Found {len(self.open_ports)} open ports")
        self.status_label.config(text="✅ Scan completed successfully")
        
        self.scan_status.insert(tk.END, "\n" + "=" * 60 + "\n")
        self.scan_status.insert(tk.END, f"✅ Scan completed: {datetime.now()}\n")
        self.scan_status.insert(tk.END, f"📊 Total open ports found: {len(self.open_ports)}\n")
        self.scan_status.insert(tk.END, "=" * 60 + "\n")
        
        if self.open_ports:
            self.scan_status.insert(tk.END, "\n⚠️  Moving to Port Management tab...\n")
            messagebox.showinfo("Scan Complete", 
                               f"Found {len(self.open_ports)} open ports!\n\nPlease go to the 'Port Management' tab to secure them.")
            self.notebook.select(2)
            self.update_management_tab()
        else:
            messagebox.showinfo("Scan Complete", "✅ No open ports found!")
    
    def create_tab3_management(self):
        """Tab 3: Manage open ports (n2om bta5od el2rarat)"""
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="⚙️ Port Management")
        
        self.management_frame = tk.Frame(tab3, bg='#1a1a2e')
        self.management_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(self.management_frame, bg='#2d2d44')
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="🔐 Port Security Decisions", 
                font=('Segoe UI', 18, 'bold'), bg='#2d2d44', fg='#6c63ff').pack(pady=20)
        
        tk.Label(header_frame, text="For each open port, decide: Keep (with security) or Close",
                font=('Segoe UI', 11), bg='#2d2d44', fg='#a0a0c0').pack(pady=(0, 20))
        
        # Scrollable frame
        canvas_frame = tk.Frame(self.management_frame, bg='#1a1a2e')
        canvas_frame.pack(fill='both', expand=True)
        
        self.ports_canvas = tk.Canvas(canvas_frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.ports_canvas.yview)
        self.ports_frame = tk.Frame(self.ports_canvas, bg='#1a1a2e')
        
        self.ports_frame.bind("<Configure>",
                              lambda e: self.ports_canvas.configure(scrollregion=self.ports_canvas.bbox("all")))
        self.ports_canvas.create_window((0, 0), window=self.ports_frame, anchor="nw")
        self.ports_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.ports_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Complete button
        self.complete_btn = tk.Button(self.management_frame, text="✓ GENERATE SECURITY REPORT", 
                                     command=self.generate_report,
                                     bg='#27ae60', fg='white', font=('Segoe UI', 14, 'bold'),
                                     padx=40, pady=12, cursor='hand2', relief='flat')
        self.complete_btn.pack(pady=20)
    
    def update_management_tab(self):
        """Update management tab (y3ml update llmanagement tab)"""
        for widget in self.ports_frame.winfo_children():
            widget.destroy()
        
        if not self.open_ports:
            label = tk.Label(self.ports_frame, text="🎉 No open ports found!",
                            font=('Segoe UI', 16), bg='#1a1a2e', fg='#00ff88')
            label.pack(pady=50)
            return
        
        # Header
        header_frame = tk.Frame(self.ports_frame, bg='#2d2d44')
        header_frame.pack(fill='x', pady=10)
        
        headers = ["Port", "Service", "Risk Level", "Decision", ""]
        for i, header in enumerate(headers):
            tk.Label(header_frame, text=header, font=('Segoe UI', 12, 'bold'),
                    bg='#2d2d44', fg='white', width=15 if i < 3 else 20).grid(row=0, column=i, padx=5, pady=10)
        
        self.port_widgets = []
        
        for i, port_info in enumerate(self.open_ports):
            port = port_info['port']
            service = port_info['service']
            
            if port in self.dangerous_ports:
                risk = "🔴 HIGH"
                risk_color = '#e74c3c'
            elif port < 1024:
                risk = "🟡 MEDIUM"
                risk_color = '#f39c12'
            else:
                risk = "🟢 LOW"
                risk_color = '#27ae60'
            
            row_frame = tk.Frame(self.ports_frame, bg='#2d2d44')
            row_frame.pack(fill='x', pady=5)
            
            tk.Label(row_frame, text=str(port), font=('Segoe UI', 11, 'bold'),
                    bg='#2d2d44', fg='white', width=15).grid(row=0, column=0, padx=5, pady=10)
            
            tk.Label(row_frame, text=service, font=('Segoe UI', 11),
                    bg='#2d2d44', fg='white', width=15).grid(row=0, column=1, padx=5, pady=10)
            
            tk.Label(row_frame, text=risk, font=('Segoe UI', 11, 'bold'),
                    bg='#2d2d44', fg=risk_color, width=15).grid(row=0, column=2, padx=5, pady=10)
            
            keep_btn = tk.Button(row_frame, text="✅ Keep", 
                                command=lambda p=port: self.decide_port(p, "keep"),
                                bg='#27ae60', fg='white', font=('Segoe UI', 10),
                                cursor='hand2', width=10)
            keep_btn.grid(row=0, column=3, padx=5, pady=10)
            
            close_btn = tk.Button(row_frame, text="❌ Close", 
                                 command=lambda p=port: self.decide_port(p, "close"),
                                 bg='#e74c3c', fg='white', font=('Segoe UI', 10),
                                 cursor='hand2', width=10)
            close_btn.grid(row=0, column=4, padx=5, pady=10)
            
            self.port_widgets.append({
                'port': port,
                'keep_btn': keep_btn,
                'close_btn': close_btn
            })
    
    def decide_port(self, port, decision):
        """Handle user decision (y5od el2rar mn el user)"""
        for port_info in self.open_ports:
            if port_info['port'] == port:
                port_info['keep'] = (decision == "keep")
                break
        
        for widget in self.port_widgets:
            if widget['port'] == port:
                if decision == "keep":
                    widget['keep_btn'].config(state='disabled', bg='#2ecc71', text='✓ Kept')
                    widget['close_btn'].config(state='disabled', bg='#7f8c8d')
                    self.status_label.config(text=f"✅ Port {port} marked as KEEP")
                else:
                    widget['keep_btn'].config(state='disabled', bg='#7f8c8d')
                    widget['close_btn'].config(state='disabled', bg='#c0392b', text='✗ Closed')
                    self.status_label.config(text=f"❌ Port {port} marked as CLOSE - Use PowerShell tab to close it!")
                break
    
    def create_tab4_report(self):
        """Tab 4: Final Report (el report el nahay)"""
        tab4 = ttk.Frame(self.notebook)
        self.notebook.add(tab4, text="📄 Security Report")
        
        report_frame = tk.Frame(tab4, bg='#1a1a2e')
        report_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        header_frame = tk.Frame(report_frame, bg='#2d2d44')
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="📊 Security Assessment Report", 
                font=('Segoe UI', 18, 'bold'), bg='#2d2d44', fg='#6c63ff').pack(pady=20)
        
        self.report_text = scrolledtext.ScrolledText(report_frame, height=25,
                                                     bg='#1a1a2e', fg='#00ff88',
                                                     font=('Consolas', 10), wrap=tk.WORD)
        self.report_text.pack(fill='both', expand=True, pady=10)
        
        button_frame = tk.Frame(report_frame, bg='#1a1a2e')
        button_frame.pack(fill='x', pady=10)
        
        buttons = [
            ("🖨️ Print Report", self.print_report, '#3498db'),
            ("💾 Save to File", self.save_report, '#27ae60'),
            ("🔄 New Scan", self.new_scan, '#e74c3c')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                           bg=color, fg='white', font=('Segoe UI', 11, 'bold'),
                           padx=30, pady=8, cursor='hand2', relief='flat')
            btn.pack(side='left', padx=10)
    
    def generate_report(self):
        """Generate report (y3ml el report)"""
        for port_info in self.open_ports:
            if port_info['keep'] is None:
                messagebox.showwarning("Incomplete", "Please make a decision for all open ports first!")
                return
        
        self.notebook.select(3)
        self.update_report_tab()
        self.status_label.config(text="📄 Report generated")
    
    def update_report_tab(self):
        """Generate and display report (y3ml we yzhr el report)"""
        report = []
        
        report.append("=" * 80)
        report.append("🔐 2PRO SECURITY SCANNER - COMPREHENSIVE REPORT")
        report.append("=" * 80)
        report.append(f"\n📋 SCAN INFORMATION")
        report.append("-" * 80)
        report.append(f"Target: {self.target_domain} ({self.target_ip})")
        report.append(f"Scan Date: {datetime.now()}")
        report.append(f"Port Range: {self.start_port} - {self.end_port}")
        report.append(f"Total Open Ports Found: {len(self.open_ports)}")
        
        report.append("\n" + "=" * 80)
        report.append("🔧 TO CLOSE PORTS - USE POWERSHELL TAB")
        report.append("=" * 80)
        report.append("Go to the 'PowerShell Terminal' tab and run:")
        report.append("netsh advfirewall firewall add rule name='Block_Port' dir=in action=block protocol=TCP localport=PORTNUMBER")
        
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, "\n".join(report))
    
    def create_tab5_powershell(self):
        """Tab 5: PowerShell Terminal to close ports (el terminal bta3 PowerShell)"""
        tab5 = ttk.Frame(self.notebook)
        self.notebook.add(tab5, text="💻 PowerShell Terminal")
        
        # Main frame (el frame el ra2eesi)
        main_frame = tk.Frame(tab5, bg='#1a1a2e')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Check admin status and show warning (ycheck law admin wala la we yzhr tanbeeh)
        if not self.check_admin():
            admin_warning = tk.Frame(main_frame, bg='#e74c3c')
            admin_warning.pack(fill='x', pady=10, padx=20)
            
            warning_text = "⚠️ NOT RUNNING AS ADMINISTRATOR - Firewall commands will NOT work! ⚠️\nClick 'Run as Admin' button below or restart program as Administrator"
            warning_label = tk.Label(admin_warning, text=warning_text, 
                                    font=('Segoe UI', 10, 'bold'), bg='#e74c3c', fg='white')
            warning_label.pack(pady=10)
            
            # Button to restart as admin (zoryar y3ml restart b admin)
            restart_btn = tk.Button(admin_warning, text="🔑 RESTART AS ADMINISTRATOR", 
                                   command=self.restart_as_admin,
                                   bg='#c0392b', fg='white', font=('Segoe UI', 11, 'bold'),
                                   cursor='hand2', relief='flat', padx=20, pady=5)
            restart_btn.pack(pady=5)
        
        # Title (3onwan)
        title = tk.Label(main_frame, text="💻 PowerShell Command Center", 
                        font=('Segoe UI', 18, 'bold'), bg='#1a1a2e', fg='#6c63ff')
        title.pack(pady=10)
        
        # Description (shar7)
        desc = tk.Label(main_frame, text="Run PowerShell commands directly - Auto-elevates for firewall commands", 
                       font=('Segoe UI', 11), bg='#1a1a2e', fg='#a0a0c0')
        desc.pack(pady=5)
        
        # Quick command buttons frame (zoryar l2gl awamr m3yna)
        quick_frame = tk.Frame(main_frame, bg='#2d2d44')
        quick_frame.pack(fill='x', pady=10, padx=20)
        
        tk.Label(quick_frame, text="⚡ Quick Commands (Auto-Admin):", font=('Segoe UI', 12, 'bold'),
                bg='#2d2d44', fg='white').pack(pady=10)
        
        # Buttons for common commands (zoryar lel awamr el mhmma)
        button_frame = tk.Frame(quick_frame, bg='#2d2d44')
        button_frame.pack(pady=5)
        
        # Command buttons definition
        quick_commands = [
            ("🔒 Close Port 445 (SMB)", "netsh advfirewall firewall add rule name=\"Close_Port_445\" dir=in action=block protocol=TCP localport=445"),
            ("🔒 Close Port 3389 (RDP)", "netsh advfirewall firewall add rule name=\"Close_Port_3389\" dir=in action=block protocol=TCP localport=3389"),
            ("🔒 Close Port 21 (FTP)", "netsh advfirewall firewall add rule name=\"Close_Port_21\" dir=in action=block protocol=TCP localport=21"),
            ("🔒 Close Port 23 (Telnet)", "netsh advfirewall firewall add rule name=\"Close_Port_23\" dir=in action=block protocol=TCP localport=23"),
            ("🔒 Close Port 5900 (VNC)", "netsh advfirewall firewall add rule name=\"Close_Port_5900\" dir=in action=block protocol=TCP localport=5900"),
            ("📋 Show Firewall Rules", "netsh advfirewall firewall show rule name=all"),
            ("🗑️ Delete All 2Pro Rules", "netsh advfirewall firewall delete rule name=\"Close_Port_*\""),
            ("🔍 Test Port 445", "Test-NetConnection localhost -Port 445"),
            ("📊 Show Open Ports", "netstat -an | findstr LISTENING")
        ]
        
        # Create buttons grid (3ml zoryar fe grid)
        row, col = 0, 0
        for i, (text, command) in enumerate(quick_commands):
            btn = tk.Button(button_frame, text=text, 
                           command=lambda cmd=command: self.run_custom_command_from_btn(cmd),
                           bg='#3498db', fg='white', font=('Segoe UI', 9),
                           cursor='hand2', relief='flat', padx=10, pady=5)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        # Custom command input
        custom_frame = tk.Frame(main_frame, bg='#2d2d44')
        custom_frame.pack(fill='x', pady=10, padx=20)
        
        tk.Label(custom_frame, text="✏️ Custom PowerShell Command:", font=('Segoe UI', 11),
                bg='#2d2d44', fg='white').pack(anchor='w', padx=10, pady=(10, 5))
        
        self.command_entry = tk.Entry(custom_frame, font=('Consolas', 11),
                                      bg='#1a1a2e', fg='#00ff88', insertbackground='white',
                                      relief='flat', bd=1)
        self.command_entry.pack(fill='x', padx=10, pady=5)
        self.command_entry.insert(0, "Test-NetConnection localhost -Port 445")
        
        # Run button
        run_btn = tk.Button(custom_frame, text="▶️ RUN COMMAND (Auto-Admin if needed)", 
                           command=self.run_custom_command,
                           bg='#27ae60', fg='white', font=('Segoe UI', 12, 'bold'),
                           cursor='hand2', relief='flat', padx=20, pady=8)
        run_btn.pack(pady=10)
        
        # Output area
        output_frame = tk.Frame(main_frame, bg='#1a1a2e')
        output_frame.pack(fill='both', expand=True, pady=10, padx=20)
        
        tk.Label(output_frame, text="📟 Command Output:", font=('Segoe UI', 11, 'bold'),
                bg='#1a1a2e', fg='white').pack(anchor='w', pady=(0, 5))
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15,
                                                      bg='#1a1a2e', fg='#00ff88',
                                                      font=('Consolas', 10), wrap=tk.WORD)
        self.output_text.pack(fill='both', expand=True)
        
        # Add clear button
        clear_btn = tk.Button(main_frame, text="🗑️ Clear Output", 
                             command=self.clear_output,
                             bg='#e74c3c', fg='white', font=('Segoe UI', 10),
                             cursor='hand2', relief='flat', padx=15, pady=5)
        clear_btn.pack(pady=5)
        
        # Instruction label
        instruction = tk.Label(main_frame, 
                              text="💡 TIP: When you click a 'Close Port' button:\n"
                                   "   1. Your program will minimize\n"
                                   "   2. A UAC prompt will appear - Click 'YES'\n"
                                   "   3. PowerShell will run the command\n"
                                   "   4. Your program will restore automatically",
                              font=('Segoe UI', 9), bg='#1a1a2e', fg='#f39c12', justify='left')
        instruction.pack(pady=5)
    
    def print_report(self):
        """Print report (y5zn el report)"""
        report_content = self.report_text.get(1.0, tk.END)
        filename = f"2pro_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        messagebox.showinfo("Report Saved", f"✅ Report saved as:\n{filename}")
        self.status_label.config(text=f"📄 Report saved: {filename}")
    
    def save_report(self):
        """Save report to file (y5zn el report fl file)"""
        report_content = self.report_text.get(1.0, tk.END)
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"2pro_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            messagebox.showinfo("Success", f"✅ Report saved to:\n{filename}")
            self.status_label.config(text=f"💾 Report saved: {os.path.basename(filename)}")
    
    def new_scan(self):
        """Reset everything (y3ml reset ll program)"""
        self.target_ip = None
        self.target_domain = None
        self.open_ports = []
        self.scan_complete = False
        self.is_scanning = False
        
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, "scanme.nmap.org")
        self.start_port_entry.delete(0, tk.END)
        self.start_port_entry.insert(0, "1")
        self.end_port_entry.delete(0, tk.END)
        self.end_port_entry.insert(0, "1024")
        
        if hasattr(self, 'scan_status'):
            self.scan_status.delete(1.0, tk.END)
        
        self.progress_var.set(0)
        self.progress_label.config(text="Ready to scan")
        self.status_label.config(text="✅ Ready for new scan")
        
        self.notebook.select(0)
        messagebox.showinfo("New Scan", "🔄 Ready for a new scan!")


# Run the application (t8y2 el program)
if __name__ == "__main__":
    root = tk.Tk()
    app = PortScannerGUI(root)
    root.mainloop()