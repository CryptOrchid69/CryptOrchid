import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import platform
import socket
import subprocess
import shutil
import ctypes
import logging
from datetime import datetime
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pc_diagnostic.log'),
        logging.StreamHandler()
    ]
)

# Attempt to import psutil, handle gracefully if missing
try:
    import psutil
except ImportError:
    psutil = None
    logging.warning("psutil not available — performance monitoring limited")


class SystemScanner:
    """Handles system scanning operations safely"""
    
    def __init__(self):
        self.issues_found = []
    
    def scan_performance(self):
        """Check CPU and memory usage"""
        if psutil:
            try:
                cpu_load = psutil.cpu_percent(interval=0.5)
                if cpu_load > 75:
                    self.issues_found.append(f"High CPU usage detected ({cpu_load}%)")
                
                ram = psutil.virtual_memory()
                if ram.percent > 80:
                    self.issues_found.append(f"Critical Memory Pressure ({ram.percent}% used)")
                
                logging.info(f"Performance scan: CPU={cpu_load}%, RAM={ram.percent}%")
            except Exception as e:
                logging.error(f"Error scanning performance: {e}")
    
    def scan_temp_files(self):
        """Check temporary files size"""
        temp_path = os.environ.get('TEMP') or os.environ.get('TMP')
        if temp_path and os.path.exists(temp_path):
            try:
                total_size = self._get_directory_size(temp_path, max_depth=2)
                size_mb = total_size // (1024 * 1024)
                if total_size > 100 * 1024 * 1024:  # 100MB threshold
                    self.issues_found.append(f"System Bloat: {size_mb}MB of temporary cache")
                logging.info(f"Temp directory size: {size_mb}MB")
            except Exception as e:
                logging.error(f"Error scanning temp files: {e}")
    
    def _get_directory_size(self, path, max_depth=2):
        """Calculate directory size with depth limit"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                # Limit depth to prevent excessive scanning
                current_depth = dirpath[len(path):].count(os.sep)
                if current_depth > max_depth:
                    dirnames.clear()  # Don't descend deeper
                    continue
                
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        if os.path.isfile(filepath):
                            total += os.path.getsize(filepath)
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError) as e:
            logging.error(f"Error calculating directory size: {e}")
        return total
    
    def scan_network(self):
        """Check internet connectivity"""
        try:
            socket.setdefaulttimeout(3)
            # Test connectivity to Google's public DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("8.8.8.8", 443))  # HTTPS port for better reliability
            sock.close()
            logging.info("Network connectivity: OK")
        except Exception as e:
            self.issues_found.append("Internet Connectivity: Gateway Unreachable")
            logging.warning(f"Network connectivity issue: {e}")
    
    def scan_vpn_services(self):
        """Check VPN service statuses (Windows only)"""
        if platform.system() != "Windows":
            logging.info("VPN service check skipped (non-Windows platform)")
            return
        
        vpn_protocols = ["WireGuard", "OpenVPN", "SoftEther", "Amnezia"]
        for vpn in vpn_protocols:
            try:
                # Use safe subprocess call without shell=True
                result = subprocess.run(
                    ["sc", "query", vpn],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and "STOPPED" in result.stdout:
                    self.issues_found.append(f"Protocol Warning: {vpn} service is inactive")
                    logging.warning(f"VPN service {vpn} is stopped")
            except subprocess.TimeoutExpired:
                logging.debug(f"VPN service {vpn} check timed out")
            except FileNotFoundError:
                logging.debug(f"sc.exe not found (unexpected on Windows)")
            except Exception as e:
                logging.debug(f"VPN service {vpn} check failed: {e}")
    
    def run_scan(self):
        """Execute all scan operations"""
        self.issues_found = []
        
        logging.info("Starting system scan...")
        self.scan_performance()
        self.scan_temp_files()
        self.scan_network()
        self.scan_vpn_services()
        logging.info(f"Scan complete. Issues found: {len(self.issues_found)}")
        
        return self.issues_found


class SystemRepairer:
    """Handles system repair operations safely"""
    
    def repair_temp_files(self):
        """Clean temporary files safely"""
        temp_path = os.environ.get('TEMP') or os.environ.get('TMP')
        deleted_count = 0
        failed_count = 0
        
        if not temp_path or not os.path.exists(temp_path):
            logging.warning("Temp path not found or doesn't exist")
            return deleted_count, failed_count
        
        try:
            for filename in os.listdir(temp_path):
                filepath = os.path.join(temp_path, filename)
                try:
                    # Only delete files, not directories
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        deleted_count += 1
                        logging.debug(f"Deleted temp file: {filename}")
                except (PermissionError, OSError) as e:
                    failed_count += 1
                    logging.warning(f"Could not delete {filename}: {e}")
        except Exception as e:
            logging.error(f"Error during temp file cleanup: {e}")
        
        return deleted_count, failed_count
    
    def repair_network(self):
        """Reset network settings safely (Windows only)"""
        if platform.system() != "Windows":
            logging.info("Network repair skipped (non-Windows platform)")
            return True
        
        try:
            # DNS cache flush
            subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                timeout=10
            )
            logging.info("DNS cache flushed")
            
            # Note: "netsh winsock reset" requires admin and system restart
            # We'll skip it as it's too aggressive for automatic repair
            # Users can manually run: netsh winsock reset catalog
            
            return True
        except subprocess.TimeoutExpired:
            logging.error("Network repair timed out")
            return False
        except FileNotFoundError:
            logging.error("ipconfig not found")
            return False
        except Exception as e:
            logging.error(f"Network repair failed: {e}")
            return False
    
    def repair_vpn_service(self, service_name):
        """Start VPN service safely (Windows only)"""
        if platform.system() != "Windows":
            logging.info(f"VPN service start skipped (non-Windows platform)")
            return False
        
        # Validate service name to prevent injection
        if not self._validate_service_name(service_name):
            logging.error(f"Invalid service name: {service_name}")
            return False
        
        try:
            result = subprocess.run(
                ["net", "start", service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logging.info(f"Service {service_name} started successfully")
                return True
            else:
                logging.warning(f"Failed to start service {service_name}")
                return False
        except subprocess.TimeoutExpired:
            logging.error(f"Service start timeout: {service_name}")
            return False
        except FileNotFoundError:
            logging.error("net.exe not found")
            return False
        except Exception as e:
            logging.error(f"Failed to start service {service_name}: {e}")
            return False
    
    @staticmethod
    def _validate_service_name(name):
        """Validate service name against whitelist"""
        valid_services = ["WireGuard", "OpenVPN", "SoftEther", "Amnezia"]
        return name in valid_services


class PCUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Master Diagnostic Tool")
        
        # Dimensions: 6 inches wide (576px), 5 inches high (480px) @ 96 DPI
        self.width = 576
        self.height = 480
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.resizable(False, False)

        # Color Palette
        self.gold_color = "#FFD700"      # Luminous Gold
        self.black_color = "#000000"     # Jet Black
        self.white_color = "#FFFFFF"     # Solid White
        self.red_color = "#FF0000"       # Bright Red
        self.dark_gray = "#333333"       # Dark Gray
        
        self.current_theme = "GOLD"
        self.issues_found = []
        self.is_running_task = False
        self.scan_performed = False
        self.is_admin_user = self.is_admin()

        # Component initialization
        self.scanner = SystemScanner()
        self.repairer = SystemRepairer()

        # UI Setup
        self.setup_ui()
        logging.info("Application initialized")

    def setup_ui(self):
        """Setup the user interface"""
        # Main Background Frame
        self.bg_frame = tk.Frame(self.root, bg=self.gold_color, width=self.width, height=self.height)
        self.bg_frame.pack_propagate(False)
        self.bg_frame.pack(fill=tk.BOTH, expand=True)

        # White Display Screen (5" wide x 3" high -> 480px x 288px)
        self.display_frame = tk.Frame(
            self.bg_frame,
            bg=self.white_color,
            highlightbackground="black",
            highlightthickness=1
        )
        self.display_frame.place(x=(self.width - 480) // 2, y=20, width=480, height=288)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.display_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text Display
        self.text_display = tk.Text(
            self.display_frame,
            bg=self.white_color,
            fg=self.black_color,
            font=("Tahoma", 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bd=0,
            yscrollcommand=self.scrollbar.set
        )
        self.text_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_display.yview)

        # Buttons Container
        self.btn_frame = tk.Frame(self.bg_frame, bg=self.gold_color)
        self.btn_frame.place(x=48, y=325, width=480, height=50)

        btn_opt = {
            "bg": self.white_color,
            "fg": self.black_color,
            "font": ("Tahoma", 10, "bold"),
            "relief": "raised",
            "borderwidth": 2,
            "width": 10
        }
        
        self.scan_btn = tk.Button(self.btn_frame, text="SCAN", command=self.start_scan, **btn_opt)
        self.scan_btn.pack(side=tk.LEFT, padx=10)

        self.file_btn = tk.Button(self.btn_frame, text="FILE", command=self.save_report, **btn_opt)
        self.file_btn.pack(side=tk.LEFT, padx=10)

        self.fix_btn = tk.Button(self.btn_frame, text="FIX", command=self.start_fix, **btn_opt)
        self.fix_btn.pack(side=tk.LEFT, padx=10)

        self.theme_btn = tk.Button(self.btn_frame, text="THEME", command=self.toggle_theme, **btn_opt)
        self.theme_btn.pack(side=tk.LEFT, padx=10)

        # Circular Progress Radial (1 inch diameter -> 96px)
        self.canvas = tk.Canvas(
            self.bg_frame,
            width=96,
            height=96,
            bg=self.gold_color,
            highlightthickness=0
        )
        self.canvas.place(x=460, y=375)
        self.draw_progress(0)
        
        # Add admin status indicator
        status_text = "Admin: Yes" if self.is_admin_user else "Admin: No"
        self.status_label = tk.Label(
            self.bg_frame,
            text=status_text,
            bg=self.gold_color,
            fg=self.black_color,
            font=("Tahoma", 8)
        )
        self.status_label.place(x=48, y=390)

    def is_admin(self):
        """Check if application is running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except AttributeError:
            # Non-Windows platform
            return os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        except Exception as e:
            logging.error(f"Error checking admin status: {e}")
            return False

    def log(self, message):
        """Log message to the text display"""
        self.text_display.config(state=tk.NORMAL)
        self.text_display.insert(tk.END, f"{message}\n")
        self.text_display.see(tk.END)
        self.text_display.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def draw_progress(self, percent):
        """Draw circular progress indicator"""
        self.canvas.delete("all")
        # Background track
        self.canvas.create_oval(10, 10, 86, 86, outline="#330000", width=2)
        # Progress Arc
        extent = -(percent / 100) * 359.9
        self.canvas.create_arc(
            10, 10, 86, 86,
            start=90,
            extent=extent,
            outline=self.white_color,
            width=6,
            style=tk.ARC
        )
        # Percentage Text
        self.canvas.create_text(
            48, 48,
            text=f"{int(percent)}%",
            fill=self.white_color,
            font=("Tahoma", 11, "bold")
        )

    def toggle_theme(self):
        """Toggle between gold and black theme"""
        if self.current_theme == "GOLD":
            new_bg = self.black_color
            self.current_theme = "BLACK"
        else:
            new_bg = self.gold_color
            self.current_theme = "GOLD"
        
        self.bg_frame.config(bg=new_bg)
        self.btn_frame.config(bg=new_bg)
        self.canvas.config(bg=new_bg)
        self.status_label.config(bg=new_bg)
        logging.info(f"Theme changed to: {self.current_theme}")

    def start_scan(self):
        """Initiate system scan"""
        if self.is_running_task:
            messagebox.showwarning("Busy", "A task is already running. Please wait.")
            return
        
        if not self.is_admin_user:
            messagebox.showwarning(
                "Permission Recommended",
                "For a complete deep scan, please run this application as Administrator.\n"
                "Some checks may be limited without elevated privileges."
            )
        
        self.is_running_task = True
        self.scan_performed = False
        self.issues_found = []
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete('1.0', tk.END)
        self.text_display.config(state=tk.DISABLED)
        
        threading.Thread(target=self.run_deep_scan, daemon=True).start()

    def run_deep_scan(self):
        """Execute deep system scan in background thread"""
        try:
            self.log(">>> INITIALIZING DEEP SYSTEM SCAN...")
            self.log(f"Scan started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # 1. Performance Analysis
            self.update_ui_progress(10)
            self.log("[1/4] Analyzing Performance Latency...")
            self.scanner.scan_performance()
            time.sleep(0.5)  # Visual feedback delay
            
            # 2. Temporary Files Analysis
            self.update_ui_progress(35)
            self.log("[2/4] Analyzing Temporary Files...")
            self.scanner.scan_temp_files()
            time.sleep(0.5)
            
            # 3. Network Analysis
            self.update_ui_progress(60)
            self.log("[3/4] Analyzing Network Integrity...")
            self.scanner.scan_network()
            time.sleep(0.5)
            
            # 4. VPN Services Analysis
            self.update_ui_progress(85)
            self.log("[4/4] Analyzing VPN Services...")
            self.scanner.scan_vpn_services()
            time.sleep(0.5)
            
            # Display results
            self.update_ui_progress(100)
            self.log("\n" + "=" * 40)
            self.log("SCAN RESULTS")
            self.log("=" * 40)
            
            if not self.scanner.issues_found:
                self.log("Status: Optimal. No issues detected.")
                self.issues_found = []
            else:
                self.log(f"Found {len(self.scanner.issues_found)} issue(s):\n")
                for i, issue in enumerate(self.scanner.issues_found, 1):
                    self.log(f"{i}. {issue}")
                self.issues_found = self.scanner.issues_found
            
            self.scan_performed = True
            logging.info("Scan completed successfully")
            
        except Exception as e:
            self.log(f"\nERROR: Scan failed: {e}")
            logging.error(f"Scan failed with exception: {e}")
        finally:
            self.is_running_task = False

    def start_fix(self):
        """Initiate system repairs"""
        if self.is_running_task:
            messagebox.showwarning("Busy", "A task is already running. Please wait.")
            return
        
        if not self.issues_found:
            messagebox.showinfo("No Issues", "No issues detected to repair. Run a scan first.")
            return
        
        if not self.is_admin_user:
            messagebox.showerror(
                "Admin Required",
                "Administrator privileges are required to perform repairs.\n"
                "Please run this application as Administrator."
            )
            return
        
        # Confirm with user
        confirm = messagebox.askyesno(
            "Confirm Repairs",
            f"About to repair {len(self.issues_found)} issue(s).\n"
            "This may require a system restart.\n\nContinue?"
        )
        
        if not confirm:
            return
        
        self.is_running_task = True
        threading.Thread(target=self.run_repairs, daemon=True).start()

    def run_repairs(self):
        """Execute repairs in background thread"""
        try:
            self.log("\n>>> INITIATING SYSTEM REPAIRS...")
            self.log(f"Repair started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            total = len(self.issues_found)
            
            for idx, issue in enumerate(self.issues_found, 1):
                progress = (idx / total) * 100
                self.update_ui_progress(progress)
                self.log(f"\n[{idx}/{total}] Processing: {issue}")
                
                if "System Bloat" in issue:
                    self.log("  -> Cleaning temporary files...")
                    deleted, failed = self.repairer.repair_temp_files()
                    self.log(f"     Deleted {deleted} file(s), Failed to delete {failed} file(s)")
                
                elif "Internet" in issue:
                    self.log("  -> Resetting network configuration...")
                    success = self.repairer.repair_network()
                    if success:
                        self.log("     Network repair completed")
                    else:
                        self.log("     Network repair failed (check logs)")
                
                elif "Protocol Warning" in issue:
                    # Extract service name safely
                    service_name = self._extract_service_name(issue)
                    if service_name:
                        self.log(f"  -> Starting {service_name} service...")
                        success = self.repairer.repair_vpn_service(service_name)
                        if success:
                            self.log(f"     {service_name} service started")
                        else:
                            self.log(f"     Failed to start {service_name} (check logs)")
                
                time.sleep(0.5)  # Visual feedback delay
            
            self.update_ui_progress(100)
            self.log("\n" + "=" * 40)
            self.log("REPAIRS COMPLETE")
            self.log("=" * 40)
            self.log("\nA system reboot is recommended to apply all changes.")
            logging.info("Repairs completed successfully")
            messagebox.showinfo("Success", "All repair operations completed.\n\nA system reboot is recommended.")
            
        except Exception as e:
            self.log(f"\nERROR: Repair failed: {e}")
            logging.error(f"Repair failed with exception: {e}")
            messagebox.showerror("Error", f"Repair failed: {e}")
        finally:
            self.is_running_task = False

    @staticmethod
    def _extract_service_name(issue_string):
        """Extract service name from issue string safely"""
        # Expected format: "Protocol Warning: ServiceName service is inactive"
        match = re.search(r"Protocol Warning:\s+(\w+)\s+service", issue_string)
        if match:
            return match.group(1)
        return None

    def save_report(self):
        """Save diagnostic report to desktop"""
        if not self.scan_performed:
            messagebox.showwarning(
                "Action Required",
                "Please run a scan first before saving a report."
            )
            return
        
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = f"PC_Diagnostic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(desktop, filename)
            
            content = self.text_display.get("1.0", tk.END)
            
            with open(filepath, "w", encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("PC DIAGNOSTIC REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)
            
            messagebox.showinfo(
                "File Saved",
                f"Report saved successfully:\n{filepath}"
            )
            logging.info(f"Report saved to: {filepath}")
        except PermissionError:
            messagebox.showerror("Error", "Permission denied. Cannot write to Desktop.")
            logging.error("Permission denied when saving report")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")
            logging.error(f"Failed to save report: {e}")

    def update_ui_progress(self, value):
        """Update progress indicator safely"""
        self.root.after(0, lambda: self.draw_progress(value))


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = PCUtilityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
