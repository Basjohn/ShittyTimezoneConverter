import sys
import warnings
warnings.filterwarnings("ignore", message=r"sipPyTypeDict\(\) is deprecated, the extension module should use sipPyTypeDictRef\(\) instead", category=DeprecationWarning)
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QMessageBox, QDialog, QGridLayout, QListView, QSystemTrayIcon, QMenu, QAction, QSlider
from PyQt5.QtGui import QFont, QIcon, QPixmap, QDesktopServices
from PyQt5.QtCore import Qt, QTimer, QUrl
import pytz
from dateutil import parser
from datetime import datetime
import platform
import os
import json

import sys
if hasattr(sys, "_MEIPASS"):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
APP_ICON_PATH = os.path.join(base_path, "poopicon.ico")
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "countdown_settings.json")

DEFAULT_SETTINGS = {
    "transparency": 0.5,
    "click_through": False,
    "play_sound": False,
    "double_click_overlay": False
}

TIMEZONES = [
    ("PST", "PDT", "UTC-8", "UTC-7", "America Pacific", "US/Pacific"),
    ("MST", "MDT", "UTC-7", "UTC-6", "America Mountain", "US/Mountain"),
    ("CST", "CDT", "UTC-6", "UTC-5", "America Central", "US/Central"),
    ("EST", "EDT", "UTC-5", "UTC-4", "America Eastern", "US/Eastern"),
    ("AST", "ADT", "UTC-4", "UTC-3", "America Atlantic", "Canada/Atlantic"),
    ("GMT", "BST", "UTC+0", "UTC+1", "UK", "Europe/London"),
    ("CET", "CEST", "UTC+1", "UTC+2", "Europe Central", "Europe/Paris"),
    ("EET", "EEST", "UTC+2", "UTC+3", "Europe Eastern", "Europe/Athens"),
    ("SAST", "SAST", "UTC+2", "UTC+2", "South Africa", "Africa/Johannesburg"),
    ("MSK", "MSD", "UTC+3", "UTC+4", "Moscow", "Europe/Moscow"),
    ("IST", "IDT", "UTC+2", "UTC+3", "Israel", "Asia/Jerusalem"),
    ("UTC", "UTC", "UTC+0", "UTC+0", "Universal", "UTC"),
    ("JST", "JST", "UTC+9", "UTC+9", "Japan", "Asia/Tokyo"),
    ("CST", "CST", "UTC+8", "UTC+8", "China", "Asia/Shanghai"),
    ("IST", "IST", "UTC+5:30", "UTC+5:30", "India", "Asia/Kolkata"),
    ("AEST", "AEDT", "UTC+10", "UTC+11", "Australia East", "Australia/Sydney"),
    ("NZST", "NZDT", "UTC+12", "UTC+13", "New Zealand", "Pacific/Auckland"),
    ("BRT", "BRST", "UTC-3", "UTC-2", "Brazil", "America/Sao_Paulo"),
    ("GST", "GST", "UTC+4", "UTC+4", "Dubai", "Asia/Dubai"),
    ("SGT", "SGT", "UTC+8", "UTC+8", "Singapore", "Asia/Singapore"),
]

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f)

def get_theme():
    # Try to detect dark mode on Windows
    if platform.system() == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize')
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value == 1 else "dark"
        except Exception:
            pass
    return "light"

class TimezoneComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setView(QListView())
        self.setFont(QFont("Segoe UI", 14))  # Increased font size
        self.setMinimumWidth(260)
        for abbr, dst_abbr, offset_std, offset_dst, loc, pytz_name in TIMEZONES:
            # Show both standard and DST abbrev/offset, and region in brackets
            label = f"{abbr} / {dst_abbr} ({loc})"
            self.addItem(label)
            self.setItemData(self.count()-1, label, Qt.DisplayRole)
            self.setItemData(self.count()-1, label, Qt.ToolTipRole)

class TimezoneConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.theme = get_theme()
        self.setWindowTitle("Shitty Timezone Converter")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setMinimumSize(700, 370)
        self.setStyleSheet(self.stylesheet())
        self.init_ui()
        # System tray icon for minimize/restore
        self.tray_icon = QSystemTrayIcon(QIcon(APP_ICON_PATH), self)
        self.tray_icon.setToolTip("Shitty Timezone Converter")
        tray_menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.showNormal)
        tray_menu.addAction(restore_action)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.tray_icon.hide()

    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.show()

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.tray_icon.hide()

    def stylesheet(self):
        if self.theme == "dark":
            bg = "#23272E"; fg = "#fff"; box = "#2e3540"; accent = "#4682B4"
        else:
            bg = "#f4f8fc"; fg = "#222"; box = "#fff"; accent = "#4682B4"
        return f"""
            QWidget {{ background: {bg}; color: {fg}; font-size: 17px; }}
            QComboBox, QLineEdit {{
                background: {box}; border-radius: 10px; border: 2px solid {accent}; padding: 10px 14px;
                font-size: 17px; color: {fg};
            }}
            QComboBox::drop-down {{ border-radius: 10px; }}
            QComboBox QListView {{ background: {box}; color: {fg}; font-size: 16px; }}
            QPushButton {{ background: {accent}; color: #fff; border: none; border-radius: 10px; padding: 10px 18px; font-size: 17px; }}
            QPushButton:hover {{ background: #5a9bd6; }}
            QFrame#resultBox {{ background: {box}; border-radius: 18px; border: 2px solid {accent}; padding: 18px; }}
            QLabel#resultText {{ font-weight: bold; font-size: 20px; border-radius: 16px; background: transparent; }}
        """

    def init_ui(self):
        layout = QVBoxLayout()
        input_row = QHBoxLayout()

        # Source timezone
        self.src_tz = TimezoneComboBox()
        input_row.addWidget(self.src_tz)

        # Date entry
        self.date_entry = QLineEdit()
        self.date_entry.setPlaceholderText("MM/DD")
        self.date_entry.setMaximumWidth(90)
        input_row.addWidget(self.date_entry)
        self.date_entry.textChanged.connect(self.date_autofmt)

        # Time entry
        self.time_entry = QLineEdit()
        self.time_entry.setPlaceholderText("HH:MM")
        self.time_entry.setMaximumWidth(90)
        input_row.addWidget(self.time_entry)
        self.time_entry.textChanged.connect(self.time_autofmt)

        # Destination timezone
        self.dst_tz = TimezoneComboBox()
        input_row.addWidget(self.dst_tz)

        layout.addLayout(input_row)

        # Result box
        self.result_box = QFrame()
        self.result_box.setObjectName("resultBox")
        self.result_label = QLabel("Enter all fields to see result.")
        self.result_label.setObjectName("resultText")
        self.result_label.setWordWrap(True)
        self.result_box_layout = QVBoxLayout()
        self.result_box_layout.setContentsMargins(18, 18, 18, 18)
        self.result_box_layout.addWidget(self.result_label)
        self.result_box.setLayout(self.result_box_layout)
        layout.addWidget(self.result_box)

        # Icons row
        icons_row = QHBoxLayout()
        self.clock_btn = QPushButton("🕒")
        self.clock_btn.setToolTip("Show countdown")
        icons_row.addWidget(self.clock_btn)
        self.about_btn = QPushButton("?")
        self.about_btn.setToolTip("About")
        icons_row.addWidget(self.about_btn)
        icons_row.addStretch()
        layout.addLayout(icons_row)

        self.setLayout(layout)

        # Connect events
        self.src_tz.currentIndexChanged.connect(self.update_result)
        self.dst_tz.currentIndexChanged.connect(self.update_result)
        self.date_entry.textChanged.connect(self.update_result)
        self.time_entry.textChanged.connect(self.update_result)
        self.clock_btn.clicked.connect(self.show_countdown)
        self.about_btn.clicked.connect(self.show_about)

        # Set default date to today
        now = datetime.now()
        self.date_entry.setText(f"{now.month:02}/{now.day:02}")

    def date_autofmt(self, text):
        # Auto-insert / for MM/DD
        if len(text) == 2 and not text.endswith('/'):
            self.date_entry.setText(text + '/')
            self.date_entry.setCursorPosition(3)
        elif len(text) > 5:
            self.date_entry.setText(text[:5])

    def time_autofmt(self, text):
        # Auto-insert : for HH:MM
        if len(text) == 2 and not text.endswith(':'):
            self.time_entry.setText(text + ':')
            self.time_entry.setCursorPosition(3)
        elif len(text) > 5:
            self.time_entry.setText(text[:5])

    def update_result(self):
        src_idx = self.src_tz.currentIndex()
        dst_idx = self.dst_tz.currentIndex()
        date_str = self.date_entry.text().strip()
        time_str = self.time_entry.text().strip()
        if src_idx < 0 or dst_idx < 0 or not time_str:
            self.result_label.setText("Enter all fields to see result.")
            return
        try:
            now = datetime.now()
            # If no date entered, use current date
            if date_str:
                dt = parser.parse(f"{now.year}/{date_str} {time_str}")
            else:
                dt = parser.parse(f"{now.year}/{now.month:02}/{now.day:02} {time_str}")
            src_abbr, src_dst_abbr, _, _, _, src_pytz = TIMEZONES[src_idx]
            dst_abbr, dst_dst_abbr, _, _, _, dst_pytz = TIMEZONES[dst_idx]
            src_tz = pytz.timezone(src_pytz)
            dst_tz = pytz.timezone(dst_pytz)
            src_dt = src_tz.localize(dt, is_dst=None)
            dst_dt = src_dt.astimezone(dst_tz)
            dst_str = dst_dt.strftime("%A, %d %B %Y %H:%M (%Z%z)")
            is_dst = bool(src_dt.dst()) or bool(dst_dt.dst())
            dst_note = "<br><span style='font-size:12pt;color:#888;'>Daylight Savings taken into account</span>" if is_dst else ""
            # Check if the target time has passed
            delta = dst_dt - datetime.now(dst_tz)
            if delta.total_seconds() < 0:
                neg = str(abs(delta)).split('.')[0]
                self.result_label.setText(f"<span style='color:#c00;font-weight:bold;'>YOU'RE TOO LATE HARRY!</span><br>Missed by {neg}{dst_note}")
            else:
                self.result_label.setText(f"{src_dt.strftime('%m/%d %H:%M')} {src_dt.tzname()} → {dst_str}{dst_note}")
        except Exception as e:
            self.result_label.setText(f"Invalid input: {e}")

    def show_countdown(self):
        src_idx = self.src_tz.currentIndex()
        date_str = self.date_entry.text().strip()
        time_str = self.time_entry.text().strip()
        if src_idx < 0 or not time_str:
            QMessageBox.warning(self, "Countdown", "Please enter a valid time and source timezone.")
            return
        try:
            now = datetime.now()
            if date_str:
                dt = parser.parse(f"{now.year}/{date_str} {time_str}")
            else:
                dt = parser.parse(f"{now.year}/{now.month:02}/{now.day:02} {time_str}")
            src_abbr, src_dst_abbr, _, _, _, src_pytz = TIMEZONES[src_idx]
            src_tz = pytz.timezone(src_pytz)
            src_dt = src_tz.localize(dt, is_dst=None)
            local_dt = src_dt.astimezone()
            self.countdown_dialog = CountdownDialog(local_dt)
            self.countdown_dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Countdown", f"Invalid input: {e}")

    def show_about(self):
        self.about_dialog = AboutDialog()
        self.about_dialog.exec_()

class CountdownDialog(QDialog):
    def __init__(self, target_dt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Countdown")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.target_dt = target_dt
        self.normal_size = (600, 180)
        self.setFixedSize(*self.normal_size)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.overlay_mode = False
        self.settings = load_settings()
        self.drag_pos = None
        self.resizing = False
        self.resize_margin = 8
        self.snapping = True
        self.sound_played = False  # Always initialize
        # Store main window reference robustly
        from PyQt5.QtWidgets import QApplication, QWidget
        for w in QApplication.topLevelWidgets():
            if w.objectName() == "MainWindow" or w.windowTitle() == "Shitty Timezone Converter":
                self.main_window = w
                break
        else:
            self.main_window = parent if isinstance(parent, QWidget) else None
        layout = QHBoxLayout()
        left = QVBoxLayout()
        # Add futility label
        self.futile_label = QLabel("")
        self.futile_label.setAlignment(Qt.AlignCenter)
        self.futile_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.futile_label.setStyleSheet("color:#c00;")
        left.addWidget(self.futile_label)
        self.label = QLabel("Calculating...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        left.addWidget(self.label)
        self.info = QLabel("Time left until entered time")
        self.info.setAlignment(Qt.AlignCenter)
        left.addWidget(self.info)
        layout.addLayout(left)
        btn_col = QVBoxLayout()
        btn_col.addStretch()
        self.overlay_btn = QPushButton("OM")
        self.overlay_btn.setToolTip("Enables Overlay and Always on Top mode.")
        self.overlay_btn.setCheckable(True)
        self.overlay_btn.setFixedWidth(40)
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        btn_col.addWidget(self.overlay_btn)
        self.options_btn = QPushButton("O")
        self.options_btn.setToolTip("Countdown Options")
        self.options_btn.setFixedWidth(30)
        self.options_btn.clicked.connect(self.show_options)
        btn_col.addWidget(self.options_btn)
        btn_col.addStretch()
        layout.addLayout(btn_col)
        self.setLayout(layout)
        self.setStyleSheet("QDialog { border-radius: 18px; background: white; }")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        self.update_countdown()
        self.apply_settings()
        # Show futility message if negative
        now = datetime.now(self.target_dt.tzinfo)
        delta = self.target_dt - now
        if delta.total_seconds() < 0:
            self.futile_label.setText("ALAS, YOUR EFFORTS ARE FUTILE!")

    def toggle_overlay(self):
        if not self.overlay_mode:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.overlay_btn.setText("OM")
            self.overlay_btn.setToolTip("Disables Overlay and Always on Top mode.")
            self.overlay_mode = True
            if self.settings.get("double_click_overlay", False):
                self.overlay_btn.hide()
            self.options_btn.hide()
            self.setStyleSheet("QDialog { border-radius: 18px; background: white; }")
            self.setMinimumSize(200, 100)
            self.setMaximumSize(16777215, 16777215)
            self.setMouseTracking(True)
            # Robustly minimize main window to tray
            if self.main_window and hasattr(self.main_window, 'minimize_to_tray'):
                self.main_window.minimize_to_tray()
            self.apply_settings()
            self.show()
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.setWindowFlag(Qt.FramelessWindowHint, False)
            self.overlay_btn.setText("OM")
            self.overlay_btn.setToolTip("Enables Overlay and Always on Top mode.")
            self.overlay_mode = False
            if self.settings.get("double_click_overlay", False):
                self.overlay_btn.show()
            self.options_btn.show()
            self.setStyleSheet("QDialog { border-radius: 18px; background: white; }")
            self.setFixedSize(*self.normal_size)
            # Robustly restore main window from tray
            if self.main_window and hasattr(self.main_window, 'restore_from_tray'):
                self.main_window.restore_from_tray()
            self.setWindowOpacity(1.0)
            self.set_click_through(False)
            self.show()

    def mouseDoubleClickEvent(self, event):
        if self.overlay_mode and self.settings.get("double_click_overlay", False):
            self.toggle_overlay()
            event.accept()
        elif not self.overlay_mode and self.settings.get("double_click_overlay", False):
            self.toggle_overlay()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def moveEvent(self, event):
        if self.overlay_mode and self.snapping:
            self.snap_to_corners()
        super().moveEvent(event)

    def snap_to_corners(self):
        screen = QApplication.primaryScreen().geometry()
        win = self.geometry()
        snap_dist = 32
        x, y = win.x(), win.y()
        w, h = win.width(), win.height()
        new_x, new_y = x, y
        # Snap to left/right
        if abs(x - screen.x()) < snap_dist:
            new_x = screen.x()
        elif abs((x + w) - (screen.x() + screen.width())) < snap_dist:
            new_x = screen.x() + screen.width() - w
        # Snap to top/bottom
        if abs(y - screen.y()) < snap_dist:
            new_y = screen.y()
        elif abs((y + h) - (screen.y() + screen.height())) < snap_dist:
            new_y = screen.y() + screen.height() - h
        if (new_x, new_y) != (x, y):
            self.move(new_x, new_y)

    def mousePressEvent(self, event):
        if self.overlay_mode and event.button() == Qt.LeftButton:
            if self.is_on_edge(event.pos()):
                self.resizing = True
                self.drag_pos = event.globalPos()
                self.start_geom = self.geometry()
            else:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.overlay_mode:
            if self.resizing and self.drag_pos:
                diff = event.globalPos() - self.drag_pos
                new_width = max(200, self.start_geom.width() + diff.x())
                new_height = max(100, self.start_geom.height() + diff.y())
                self.resize(new_width, new_height)
                event.accept()
            elif self.drag_pos and not self.resizing:
                self.move(event.globalPos() - self.drag_pos)
                event.accept()
            else:
                if self.is_on_edge(event.pos()):
                    self.setCursor(Qt.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.overlay_mode:
            self.resizing = False
            self.drag_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def is_on_edge(self, pos):
        return pos.x() >= self.width() - self.resize_margin and pos.y() >= self.height() - self.resize_margin

    def update_countdown(self):
        now = datetime.now(self.target_dt.tzinfo)
        delta = self.target_dt - now
        if delta.total_seconds() <= 0:
            self.label.setText("00:00:00")
            self.info.setText("Time reached!")
            self.timer.stop()
            if self.settings.get("play_sound") and not self.sound_played:
                self.play_tada()
                self.sound_played = True
            # Show futility message if negative
            if delta.total_seconds() < 0:
                neg = str(abs(delta)).split('.')[0]
                self.info.setText(f"<span style='color:#c00;'>Missed by {neg}</span>")
                self.futile_label.setText("ALAS, YOUR EFFORTS ARE FUTILE!")
            return
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        self.label.setText(f"{h:02}:{m:02}:{s:02}")
        # If negative, show negative time and futility message
        if delta.total_seconds() < 0:
            neg = str(abs(delta)).split('.')[0]
            self.info.setText(f"<span style='color:#c00;'>Missed by {neg}</span>")
            self.futile_label.setText("ALAS, YOUR EFFORTS ARE FUTILE!")
        else:
            self.futile_label.setText("")

    def show_options(self):
        dlg = CountdownOptionsDialog(self.settings, self)
        if dlg.exec_():
            self.settings = dlg.get_settings()
            save_settings(self.settings)
            self.apply_settings()

    def apply_settings(self):
        self.setWindowOpacity(self.settings.get("transparency", 0.5) if self.overlay_mode else 1.0)
        self.set_click_through(self.overlay_mode and self.settings.get("click_through", False))

    def set_click_through(self, enable):
        if sys.platform == "win32":
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if enable:
                style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                self.enable_overlay_context_menu()
            else:
                style &= ~WS_EX_TRANSPARENT
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                self.setContextMenuPolicy(Qt.NoContextMenu)

    def enable_overlay_context_menu(self):
        # Enable right-click context menu in click-through mode
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_overlay_context_menu)

    def show_overlay_context_menu(self, pos):
        menu = QMenu(self)
        disable_action = menu.addAction("Disable click-through")
        center_action = menu.addAction("Move to screen centre")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == disable_action:
            self.settings["click_through"] = False
            save_settings(self.settings)
            self.set_click_through(False)
            self.apply_settings()
        elif action == center_action:
            screen = QApplication.primaryScreen().geometry()
            win = self.geometry()
            x = screen.x() + (screen.width() - win.width()) // 2
            y = screen.y() + (screen.height() - win.height()) // 2
            self.move(x, y)

    def play_tada(self):
        import sys
        import subprocess
        # Use built-in OS sound for maximum reliability
        if sys.platform == 'win32':
            try:
                import winsound
                winsound.PlaySound("SystemExit", winsound.SND_ALIAS | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        elif sys.platform == 'darwin':
            # macOS: play the "Glass" system sound
            try:
                subprocess.Popen(['afplay', '/System/Library/Sounds/Glass.aiff'])
                return
            except Exception:
                pass
        else:
            # Linux: try canberra-gtk-play or fallback to beep
            try:
                subprocess.Popen(['canberra-gtk-play', '--id', 'desktop-login'])
                return
            except Exception:
                pass
            try:
                print('\a')  # ASCII Bell
            except Exception:
                pass

    def keyPressEvent(self, event):
        if self.overlay_mode and event.key() == Qt.Key_Escape:
            self.toggle_overlay()  # disables overlay
            # Move to screen centre
            screen = QApplication.primaryScreen().geometry()
            win = self.geometry()
            x = screen.x() + (screen.width() - win.width()) // 2
            y = screen.y() + (screen.height() - win.height()) // 2
            self.move(x, y)
            event.accept()
        else:
            super().keyPressEvent(event)

class CountdownOptionsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Countdown Options")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setFixedSize(420, 260)
        self.setStyleSheet("QDialog { border-radius: 18px; background: white; }")
        layout = QVBoxLayout()
        tr_label = QLabel("Transparency:")
        layout.addWidget(tr_label)
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setMinimum(10)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setValue(int(settings.get("transparency", 0.5) * 100))
        layout.addWidget(self.transparency_slider)
        self.click_chk = QPushButton("Click-through mode")
        self.click_chk.setCheckable(True)
        self.click_chk.setChecked(settings.get("click_through", False))
        layout.addWidget(self.click_chk)
        self.sound_chk = QPushButton("Play annoying sound when countdown finishes")
        self.sound_chk.setCheckable(True)
        self.sound_chk.setChecked(settings.get("play_sound", False))
        self.sound_chk.clicked.connect(self.preview_sound)
        layout.addWidget(self.sound_chk)
        self.dblclick_chk = QPushButton("Double Click Overlay Control")
        self.dblclick_chk.setCheckable(True)
        self.dblclick_chk.setChecked(settings.get("double_click_overlay", False))
        layout.addWidget(self.dblclick_chk)
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def get_settings(self):
        return {
            "transparency": self.transparency_slider.value() / 100.0,
            "click_through": self.click_chk.isChecked(),
            "play_sound": self.sound_chk.isChecked(),
            "double_click_overlay": self.dblclick_chk.isChecked()
        }

    def preview_sound(self):
        # Play sound once when enabling the option
        if self.sound_chk.isChecked():
            parent = self.parent() if self.parent() else self
            if hasattr(parent, 'play_tada'):
                parent.play_tada()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setFixedSize(540, 180)
        layout = QVBoxLayout()
        label = QLabel(
            "Made for my own incompetent self, shared freely for yours. You can always donate to my dumbass though or buy my shitty literature."
        )
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 11))  # 2pt smaller than main UI
        layout.addWidget(label)
        link_row = QVBoxLayout()
        paypal_link = QLabel('<a href="https://www.paypal.com/donate/?business=UBZJY8KHKKLGC&no_recurring=0&item_name=Why+are+you+doing+this?+Are+you+drunk?+&currency_code=USD">Donate via Paypal</a>')
        paypal_link.setOpenExternalLinks(True)
        paypal_link.setAlignment(Qt.AlignCenter)
        paypal_link.setFont(QFont("Segoe UI", 10, QFont.Bold))
        link_row.addWidget(paypal_link)
        goodreads_link = QLabel('<a href="https://www.goodreads.com/book/show/25006763-usu">Usu on Goodreads</a>')
        goodreads_link.setOpenExternalLinks(True)
        goodreads_link.setAlignment(Qt.AlignCenter)
        goodreads_link.setFont(QFont("Segoe UI", 10, QFont.Bold))
        link_row.addWidget(goodreads_link)
        amazon_link = QLabel('<a href="https://www.amazon.com/Usu-Jayde-Ver-Elst-ebook/dp/B00V8A5K7Y">Usu on Amazon</a>')
        amazon_link.setOpenExternalLinks(True)
        amazon_link.setAlignment(Qt.AlignCenter)
        amazon_link.setFont(QFont("Segoe UI", 10, QFont.Bold))
        link_row.addWidget(amazon_link)
        layout.addLayout(link_row)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimezoneConverter()
    window.show()
    sys.exit(app.exec_())
