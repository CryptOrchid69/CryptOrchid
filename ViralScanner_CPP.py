import os
import sys
import re
import html
import importlib.util
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QFileDialog, QVBoxLayout,
    QWidget, QPushButton, QPlainTextEdit
)

APP_W, APP_H = 768, 576  # 8in x 6in @ 96 DPI
APP_NAME = "ViralScanner IDE"
ICON_FILE = "Umbrella.ico"


# =========================
# REGEX SAFETY ENGINE
# =========================
class RegexAnalyzer:
    RISKY_INCLUDES = {"system", "exec", "popen", "fork", "socket.h", "unistd.h"}
    UNSAFE_CALLS = {"system", "exec", "execv", "popen", "fork", "strcpy", "gets", "scanf"}

    def analyze(self, code: str):
        findings = []
        
        try:
            lines = code.split('\n')
        except Exception as e:
            return [f"ERROR: {e}"]

        for line_num, line in enumerate(lines, 1):
            # Check for risky includes
            include_match = re.search(r'#include\s+[<"](\S+)[>"]', line)
            if include_match:
                included_file = include_match.group(1)
                for risky in self.RISKY_INCLUDES:
                    if risky.lower() in included_file.lower():
                        findings.append(f"Risky include at line {line_num}: {included_file}")
            
            # Check for unsafe function calls
            for unsafe_func in self.UNSAFE_CALLS:
                # Look for function calls like unsafe_func(
                pattern = r'\b' + re.escape(unsafe_func) + r'\s*\('
                if re.search(pattern, line):
                    findings.append(f"Unsafe call at line {line_num}: {unsafe_func}()")
        
        return findings


# =========================
# PLUGIN SYSTEM
# =========================
class PluginManager:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder = self._prepare_folder(self.folder)
        self.plugins = []
        self.errors = []

    def _prepare_folder(self, folder):
        try:
            folder.mkdir(parents=True, exist_ok=True)
            return folder
        except OSError:
            fallback = Path(os.getenv("LOCALAPPDATA", tempfile.gettempdir())) / "ViralScanner" / "plugins"
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                return fallback
            except OSError:
                return None

    def load_plugins(self):
        self.plugins.clear()
        self.errors.clear()
        if not self.folder:
            self.errors.append("Plugin folder is unavailable. Core scanning still works.")
            return
        for file in self.folder.glob("*.py"):
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                if not spec or not spec.loader:
                    self.errors.append(f"Could not load plugin: {file.name}")
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "scan"):
                    self.plugins.append(mod.scan)
                else:
                    self.errors.append(f"Plugin has no scan(code) function: {file.name}")
            except Exception:
                self.errors.append(f"Plugin failed to load: {file.name}")

    def run(self, code):
        results = []
        for plugin in self.plugins:
            try:
                results.extend(plugin(code))
            except Exception as e:
                results.append(f"PLUGIN ERROR: {e}")
        return results


# =========================
# BACKGROUND SCANNER THREAD
# =========================
class ScanThread(QThread):
    update = pyqtSignal(str)

    def __init__(self, analyzer, plugins, code):
        super().__init__()
        self.analyzer = analyzer
        self.plugins = plugins
        self.code = code

    def run(self):
        self.update.emit("Scanning started...")

        for i in self.analyzer.analyze(self.code):
            self.update.emit(i)

        for i in self.plugins.run(self.code):
            self.update.emit(i)

        self.update.emit("Scan complete.")


# =========================
# MAIN APP
# =========================
class ViralScanner(QMainWindow):
    def __init__(self):
        super().__init__()

        self.app_dir = self._app_directory()
        self.current_path = None
        self.dark_theme = False

        self.setWindowTitle(APP_NAME)
        self.setFixedSize(APP_W, APP_H)
        self._set_window_icon()

        self.analyzer = RegexAnalyzer()
        self.plugins = PluginManager(self.app_dir / "plugins")
        self.plugins.load_plugins()

        self._build_ui()
        self._apply_light_theme()

    def _app_directory(self):
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent

    def _resource_path(self, filename):
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            return Path(bundle_dir) / filename
        return self.app_dir / filename

    def _set_window_icon(self):
        icon_path = self._resource_path(ICON_FILE)
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    # -------------------------
    # UI BUILD
    # -------------------------
    def _build_ui(self):
        # Central Editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.setCentralWidget(self.editor)

        # OUTPUT DOCK (log / red alerts)
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        dock_output = QDockWidget("Scan Output", self)
        dock_output.setWidget(self.output)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_output)

        # PROJECT WORKSPACE DOCK
        self.workspace = QTreeWidget()
        self.workspace.setHeaderLabel("Workspace")
        self.workspace.itemDoubleClicked.connect(self.on_tree_item_double_clicked)

        dock_workspace = QDockWidget("Project", self)
        dock_workspace.setWidget(self.workspace)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_workspace)

        # CONTROL PANEL DOCK
        controls = QWidget()
        layout = QVBoxLayout()

        btn_scan = QPushButton("SCAN FILE")
        btn_scan.clicked.connect(self.scan)

        btn_open = QPushButton("OPEN FILE")
        btn_open.clicked.connect(self.open_file)

        btn_theme = QPushButton("TOGGLE THEME")
        btn_theme.clicked.connect(self.toggle_theme)

        btn_plugins = QPushButton("RELOAD PLUGINS")
        btn_plugins.clicked.connect(self.reload_plugins)

        layout.addWidget(btn_scan)
        layout.addWidget(btn_open)
        layout.addWidget(btn_theme)
        layout.addWidget(btn_plugins)

        controls.setLayout(layout)

        dock_controls = QDockWidget("Controls", self)
        dock_controls.setWidget(controls)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_controls)

        # MENU
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

    # -------------------------
    # FILE & TREE HANDLING
    # -------------------------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if path:
            self.current_path = path
            self.editor.setPlainText(Path(path).read_text(encoding="utf-8", errors="ignore"))
            self.populate_workspace_tree(Path(path).parent)

    def populate_workspace_tree(self, folder_path: Path):
        self.workspace.clear()
        self.workspace.setHeaderLabel(folder_path.name)
        
        root_item = QTreeWidgetItem(self.workspace, [folder_path.name])
        root_item.setData(0, Qt.ItemDataRole.UserRole, str(folder_path))
        
        self._add_tree_nodes(folder_path, root_item)
        root_item.setExpanded(True)

    def _add_tree_nodes(self, folder_path: Path, parent_item: QTreeWidgetItem):
        try:
            for item in sorted(folder_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                # Ignore hidden files/folders
                if item.name.startswith('.'):
                    continue
                    
                node = QTreeWidgetItem(parent_item, [item.name])
                node.setData(0, Qt.ItemDataRole.UserRole, str(item))
                
                if item.is_dir():
                    self._add_tree_nodes(item, node)
        except OSError as exc:
            self.output.append(f"Could not read folder: {exc}")

    def on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        file_path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path_str and os.path.isfile(file_path_str):
            self.current_path = file_path_str
            self.editor.setPlainText(Path(file_path_str).read_text(encoding="utf-8", errors="ignore"))

    # -------------------------
    # SCANNING ENGINE (STREAMING)
    # -------------------------
    def scan(self):
        code = self.editor.toPlainText()
        self.output.clear()
        if not code.strip():
            self.output.append("Open a file or type code before scanning.")
            return

        self.thread = ScanThread(
            self.analyzer,
            self.plugins,
            code
        )

        self.thread.update.connect(self.add_output)
        self.thread.start()

    def add_output(self, text):
        # highlight risky lines in red
        if "Unsafe" in text or "Risky" in text:
            safe_text = html.escape(text)
            self.output.append(f"<span style='color:red'><b>{safe_text}</b></span>")
        else:
            self.output.append(text)

    def reload_plugins(self):
        self.plugins.load_plugins()
        self.output.append(f"Loaded {len(self.plugins.plugins)} plugin(s).")
        for error in self.plugins.errors:
            self.output.append(error)

    # -------------------------
    # THEMES
    # -------------------------
    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: white; }
            QDockWidget { background-color: #1e1e1e; color: white; }
            QTreeWidget { background: #252526; color: #dcdcdc; }
            QTextEdit { background: #252526; color: #dcdcdc; }
            QPushButton { background: white; color: black; font-weight: bold; }
            QPlainTextEdit { background: #252526; color: #dcdcdc; }
        """)
        self.dark_theme = True

    def _apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #e6f2f2; }
            QDockWidget { background-color: #e6f2f2; color: black; }
            QTreeWidget { background: white; color: black; }
            QTextEdit { background: white; color: black; }
            QPushButton { background: white; color: black; font-weight: bold; }
            QPlainTextEdit { background: white; color: black; }
        """)
        self.dark_theme = False

    def toggle_theme(self):
        if self.dark_theme:
            self._apply_light_theme()
        else:
            self._apply_dark_theme()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ViralScanner()
    win.show()
    sys.exit(app.exec())
