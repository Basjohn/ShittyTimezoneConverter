import sys
import warnings
warnings.filterwarnings("ignore", message=r"sipPyTypeDict\(\) is deprecated, the extension module should use sipPyTypeDictRef\(\) instead", category=DeprecationWarning)
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFrame, QMessageBox, QDialog, QGridLayout, QListView, QSystemTrayIcon, QMenu, QAction, QSlider
from PyQt5.QtGui import QFont, QIcon, QPixmap, QDesktopServices, QFontMetrics, QIntValidator
from PyQt5.QtCore import Qt, QTimer, QUrl
import pytz
from dateutil import parser
import platform
import os
import json
import tzlocal
import pygame
from datetime import datetime, timezone, timedelta
import locale

import sys
if hasattr(sys, "_MEIPASS"):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# Set up Moist directory for all settings, databases, and other app files
MOIST_DIR = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Moist")
os.makedirs(MOIST_DIR, exist_ok=True)

APP_ICON_PATH = os.path.join(base_path, "poopicon.ico")
SETTINGS_PATH = os.path.join(MOIST_DIR, "countdown_settings.json")
OFFSET_DB_PATH = os.path.join(MOIST_DIR, "timezone_offset_map.json")

DEFAULT_SETTINGS = {
    "transparency": 0.5,
    "click_through": False,
    "play_sound": False,
    "double_click_overlay": False,
    "countdown_normal_size": [600, 180],
    "countdown_normal_pos": [100, 100],
    "countdown_overlay_size": [400, 120],
    "countdown_overlay_pos": [200, 200],
    "theme": "auto",  # "light", "dark", or "auto"
    "main_window_pos": [100, 100],
    "main_window_size": [700, 370],
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

def get_theme(settings=None):
    if settings and settings.get("theme") in ("light", "dark"):
        return settings["theme"]
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

class ThemeManager:
    def __init__(self, theme):
        self.theme = theme
        self.apply_theme()

    def set_theme(self, theme):
        self.theme = theme
        self.apply_theme()

    def apply_theme(self):
        if self.theme == "dark":
            self.bg = "#23272E"
            self.fg = "#fff"
            self.box = "#23272E"
            self.accent = "#fff"
            self.button_bg = "#23272E"
            self.button_fg = "#fff"
            self.button_border = "#fff"
            self.toggle_on_bg = "#fff"
            self.toggle_on_fg = "#23272E"
            self.symbol = "#fff"
            self.edit_fg = "#fff"  # Bright white for QLineEdit text
            self.negative = "#FFA500"  # orange
        else:
            self.bg = "#f4f8fc"
            self.fg = "#222"
            self.box = "#fff"
            self.accent = "#4682B4"
            self.button_bg = "#4682B4"
            self.button_fg = "#fff"
            self.button_border = "#4682B4"
            self.toggle_on_bg = "#fff"
            self.toggle_on_fg = "#222"
            self.symbol = "#222"
            self.edit_fg = "#222"
            self.negative = "#d32f2f"  # red

    def widget_stylesheet(self):
        return f"""
        QWidget {{ background: {self.bg}; color: {self.fg}; }}
        QFrame#resultBox {{ background: transparent; border: none; padding: 0px; margin: 0px; }}
        QLabel#resultText {{ font-weight: bold; font-size: 20px; border-radius: 16px; background: transparent; }}
        QComboBox, QLineEdit {{ background: {self.box}; border-radius: 12px; border: 2px solid {self.accent}; padding: 5px 7px; font-size: 17px; color: {self.edit_fg}; }}
        QComboBox::drop-down {{ border-radius: 12px; }}
        QComboBox QListView {{ background: {self.box}; color: {self.fg}; font-size: 16px; }}
        QPushButton.options-dialog-btn {{ border-radius: 12px; }}
        """

    def button_stylesheet(self, toggle=False, checked=False, symbol=False):
        base = f"border-radius: 12px; border: 2px solid {self.button_border};"
        if symbol:
            return f"QPushButton {{ background: transparent; color: {self.symbol}; font-size: 22px; {base} min-width:32px; min-height:32px; border: none; }} QPushButton:pressed {{ background: transparent; color: {self.symbol}; }}"
        if toggle and checked:
            # Invert ON-state for light mode
            if self.theme == "light":
                return f"QPushButton {{ background: {self.button_fg}; color: {self.button_bg}; {base} }}"
            else:
                return f"QPushButton {{ background: {self.toggle_on_bg}; color: {self.toggle_on_fg}; {base} }}"
        else:
            return f"QPushButton {{ background: {self.button_bg}; color: {self.button_fg}; {base} }} QPushButton:pressed {{ background: {self.button_fg}; color: {self.button_bg}; }}"

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
        self.addItem("UTC Custom")
        self.setItemData(self.count()-1, "UTC Custom", Qt.DisplayRole)
        self.setItemData(self.count()-1, "Custom UTC offset", Qt.ToolTipRole)

class SnappableWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def moveEvent(self, event):
        super().moveEvent(event)

class SnappableDialog(QDialog):
    def moveEvent(self, event):
        super().moveEvent(event)
        self.snap_to_corners()

    def snap_to_corners(self):
        # Default no-op; override in subclasses if needed
        pass

class CustomUTCDialog(QDialog):
    def __init__(self, parent=None, initial_offset=0):
        super().__init__(parent)
        self.setWindowTitle("Custom UTC Offset")
        self.setFixedSize(260, 120)
        layout = QVBoxLayout()
        row = QHBoxLayout()
        self.plus_btn = QPushButton("+")
        self.minus_btn = QPushButton("-")
        self.plus_btn.setCheckable(True)
        self.minus_btn.setCheckable(True)
        self.plus_btn.setChecked(initial_offset >= 0)
        self.minus_btn.setChecked(initial_offset < 0)
        self.plus_btn.clicked.connect(lambda: self.minus_btn.setChecked(False))
        self.minus_btn.clicked.connect(lambda: self.plus_btn.setChecked(False))
        row.addWidget(self.plus_btn)
        row.addWidget(self.minus_btn)
        self.offset_edit = QLineEdit(str(abs(initial_offset)))
        self.offset_edit.setValidator(QIntValidator(0, 18))
        self.offset_edit.setMaximumWidth(50)
        row.addWidget(self.offset_edit)
        layout.addLayout(row)
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)
    def get_offset(self):
        sign = 1 if self.plus_btn.isChecked() else -1
        try:
            val = int(self.offset_edit.text())
        except Exception:
            val = 0
        return sign * val

class TimezoneConverter(SnappableWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.theme = get_theme(self.settings)
        self.theme_mgr = ThemeManager(self.theme)
        self.setWindowTitle("Shitty Timezone Converter")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        # Calculate minimum width for text boxes + combo boxes + spacing
        min_width = 260*2 + 90*2 + 40*3 + 60  # 2 combos, 2 text, 3 spacers/buttons, extra
        self.setMinimumSize(min_width, 370)
        self.move(*self.settings.get("main_window_pos", [100, 100]))
        self.resize(*self.settings.get("main_window_size", [max(min_width, 700), 370]))
        self.setStyleSheet(self.theme_mgr.widget_stylesheet())
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
        # --- Connect time/date changes to countdown update ---
        self.date_entry.textChanged.connect(self._update_countdown_if_open)
        self.time_entry.textChanged.connect(self._update_countdown_if_open)
        self.src_tz.currentIndexChanged.connect(self._update_countdown_if_open)
        self.dst_tz.currentIndexChanged.connect(self._update_countdown_if_open)
        self.custom_src_offset = None
        self.custom_dst_offset = None
        self.src_tz.activated.connect(lambda idx: self._handle_custom_tz(idx, True))
        self.dst_tz.activated.connect(lambda idx: self._handle_custom_tz(idx, False))

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
        # --- Move focus from date to time entry when date is complete ---
        def date_to_time_focus(text):
            # Accept MM/DD or M/D, but only move if length is 5 (e.g. 12/31)
            if len(text) == 5 and self.date_entry.cursorPosition() == 5:
                self.time_entry.clear()
                self.time_entry.setFocus()
                self.time_entry.setCursorPosition(0)
        self.date_entry.textChanged.connect(date_to_time_focus)

        # Time entry
        self.time_entry = QLineEdit()
        self.time_entry.setPlaceholderText("HH:MM")
        self.time_entry.setMaximumWidth(90)
        now = datetime.now()
        self.default_time = f"{now.hour:02}:{now.minute:02}"
        self.time_entry.setText(self.default_time)
        self.time_entry.setStyleSheet("color: #888; font-weight: normal;")
        input_row.addWidget(self.time_entry)
        self.time_entry.textChanged.connect(self.time_autofmt)
        # Focus cursor to time_entry at position 0 and select all after window is shown
        def focus_time_entry():
            self.time_entry.setFocus()
            self.time_entry.setCursorPosition(0)
            self.time_entry.selectAll()
        QTimer.singleShot(0, focus_time_entry)
        # Replace default text on first user input
        def on_time_entry_change(text):
            if text == self.default_time:
                self.time_entry.setStyleSheet("color: #888; font-weight: normal;")
            elif text:
                self.time_entry.setStyleSheet("color: #222; font-weight: bold;")
        self.time_entry.textChanged.connect(on_time_entry_change)
        def on_time_entry_first_input():
            if self.time_entry.text() == self.default_time:
                self.time_entry.clear()
                self.time_entry.setStyleSheet("color: #222; font-weight: bold;")
                self.time_entry.textChanged.disconnect(on_time_entry_first_input)
        self.time_entry.textChanged.connect(on_time_entry_first_input)

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
        self.clock_btn = QPushButton("\U0001F551")  # 
        self.clock_btn.setToolTip("Show countdown")
        self.clock_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
        icons_row.addWidget(self.clock_btn)
        icon_color = self.theme_mgr.symbol
        # Create a pixmap for the question mark icon
        from PyQt5.QtGui import QPixmap, QPainter, QColor
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor(icon_color))
        font = QFont("Segoe UI", 22)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "?")
        painter.end()
        self.about_btn = QPushButton()
        self.about_btn.setToolTip("No no dear god no, stop you fiend!")
        self.about_btn.setIcon(QIcon(pixmap))
        self.about_btn.setIconSize(pixmap.size())
        self.about_btn.setText("")  # Remove text so only icon shows
        self.about_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
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
        self.date_entry.setText(f"{now.month:02}/{now.day:02}")

        # Default destination timezone to user's system timezone if available
        import tzlocal
        import pytz
        import json
        try:
            local_tz = tzlocal.get_localzone_name()
            found = False
            # Try exact match first
            for i in range(self.dst_tz.count()):
                if local_tz in self.dst_tz.itemText(i) or local_tz.replace('_', ' ') in self.dst_tz.itemText(i):
                    self.dst_tz.setCurrentIndex(i)
                    found = True
                    break
            # If not found, try robust offset-based fallback
            if not found:
                # Get current system offset (including DST)
                now = datetime.now(pytz.timezone(local_tz))
                offset_td = now.utcoffset()
                if offset_td is not None:
                    total_minutes = int(offset_td.total_seconds() // 60)
                    hours = total_minutes // 60
                    minutes = abs(total_minutes % 60)
                    sign = '+' if total_minutes >= 0 else '-'
                    offset_str = f"{sign}{abs(hours):02}:{minutes:02}"
                    # Load offset map
                    try:
                        with open(OFFSET_DB_PATH, 'r', encoding='utf-8') as f:
                            offset_map = json.load(f)
                        zones = offset_map.get(offset_str)
                        if not zones and offset_str.startswith('+0'):
                            zones = offset_map.get('+00:00')
                        if zones:
                            # Try to determine region/country from system locale
                            system_region = None
                            try:
                                # Use getlocale() and fallback to environment if needed
                                loc = locale.getlocale()
                                if (not loc or not loc[0]) and hasattr(locale, 'getdefaultlocale'):
                                    loc = locale.getdefaultlocale()
                                # Try environment variables as last resort
                                if (not loc or not loc[0]):
                                    import os
                                    env_vars = [os.environ.get('LANG'), os.environ.get('LC_ALL'), os.environ.get('LC_CTYPE')]
                                    for env in env_vars:
                                        if env and '_' in env:
                                            loc = (env, None)
                                            break
                                if loc and loc[0]:
                                    # e.g. 'en_ZA' -> 'ZA'
                                    system_region = loc[0].split('_')[-1].split('.')[0]
                            except Exception:
                                pass
                            # Reorder zones so that the one closest to the system locale is first
                            def region_score(zone, region):
                                # Score: 0 = perfect match, 1 = region in zone name, 2 = region in label, 3 = no match
                                for idx, (abbr, dst_abbr, offset_std, offset_dst, loc_name, pytz_name) in enumerate(TIMEZONES):
                                    if zone == pytz_name:
                                        if region:
                                            if region.lower() in pytz_name.lower():
                                                return 0
                                            if region.lower() in loc_name.lower():
                                                return 1
                                        return 2
                                return 3
                            if system_region:
                                zones = sorted(zones, key=lambda z: region_score(z, system_region))
                            # For each candidate IANA zone, find its index in TIMEZONES
                            for zone in zones:
                                for idx, (abbr, dst_abbr, offset_std, offset_dst, loc_name, pytz_name) in enumerate(TIMEZONES):
                                    if zone == pytz_name:
                                        label = f"{abbr} / {dst_abbr} ({loc_name})"
                                        for i in range(self.dst_tz.count()):
                                            if self.dst_tz.itemText(i) == label:
                                                self.dst_tz.setCurrentIndex(i)
                                                found = True
                                                break
                                        if found:
                                            break
                                if found:
                                    break
                    except Exception as e:
                        pass
        except Exception:
            pass

        # --- Clear date or time entry on user click (fixed: no tuple return) ---
        def make_clear_on_click(entry):
            orig_event = entry.mousePressEvent
            def handler(event):
                entry.clear()
                entry.setCursorPosition(0)
                orig_event(event)
            entry.mousePressEvent = handler
        make_clear_on_click(self.date_entry)
        make_clear_on_click(self.time_entry)

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
        # Only show result if user has entered a time different from the default
        if src_idx < 0 or dst_idx < 0 or not time_str or time_str == getattr(self, 'default_time', None):
            self.result_label.setText("Enter all fields to see result.")
            if hasattr(self, 'dst_note_label'):
                self.dst_note_label.setText("")
            return
        try:
            now = datetime.now()
            # If no date entered, use current date
            if date_str:
                dt = parser.parse(f"{now.year}/{date_str} {time_str}")
            else:
                dt = parser.parse(f"{now.year}/{now.month:02}/{now.day:02} {time_str}")
            # Handle custom UTC for src
            if self.src_tz.currentText().startswith("UTC") and self.custom_src_offset is not None:
                import pytz
                from datetime import timedelta, tzinfo
                class FixedOffset(tzinfo):
                    def __init__(self, offset):
                        self.__offset = timedelta(hours=offset)
                    def utcoffset(self, dt):
                        return self.__offset
                    def tzname(self, dt):
                        return f"UTC{'+' if self.__offset.total_seconds() >= 0 else '-'}{abs(int(self.__offset.total_seconds()//3600))}"
                    def dst(self, dt):
                        return timedelta(0)
                src_tz = FixedOffset(self.custom_src_offset)
                src_dt = dt.replace(tzinfo=src_tz)
            else:
                src_abbr, src_dst_abbr, _, _, _, src_pytz = TIMEZONES[src_idx]
                import pytz
                src_tz = pytz.timezone(src_pytz)
                src_dt = src_tz.localize(dt)
            # Handle custom UTC for dst
            if self.dst_tz.currentText().startswith("UTC") and self.custom_dst_offset is not None:
                dst_offset = self.custom_dst_offset
                dst_tz = FixedOffset(dst_offset)
                dst_dt = src_dt.astimezone(dst_tz)
                dst_str = dst_dt.strftime('%m/%d %H:%M') + f' UTC{dst_offset:+d}'
            else:
                dst_abbr, dst_dst_abbr, _, _, _, dst_pytz = TIMEZONES[dst_idx]
                import pytz
                dst_tz = pytz.timezone(dst_pytz)
                dst_dt = src_dt.astimezone(dst_tz)
                dst_str = dst_dt.strftime('%m/%d %H:%M') + f' {dst_dt.tzname()}'
            delta = dst_dt - src_dt
            # DST note logic
            is_dst = False
            try:
                is_dst = bool(src_dt.dst()) or bool(dst_dt.dst())
            except Exception:
                pass
            dst_note = ''
            if abs(delta.total_seconds()) > 0:
                sign = '+' if delta.total_seconds() > 0 else '-'
                h = abs(int(delta.total_seconds()) // 3600)
                m = abs(int(delta.total_seconds()) % 3600 // 60)
                dst_note = f" (UTC{sign}{h:02}:{m:02})"
            # If negative, show futility message
            if delta.total_seconds() < 0:
                neg = str(abs(delta)).split('.')[0]
                color = self.theme_mgr.negative
                self.result_label.setText(f"<span style='color:{color};font-weight:bold;font-size:32pt;'>YOU'RE TOO LATE HARRY, YOU ALWAYS WERE.<br>Fucked up by {neg}</span>{dst_note}")
                if hasattr(self, 'dst_note_label'):
                    self.dst_note_label.setText("")
                return
            h, rem = divmod(int(delta.total_seconds()), 3600)
            m, s = divmod(rem, 60)

            self.result_label.setText(f"<span style='font-size:32pt;font-weight:bold'>{src_dt.strftime('%m/%d %H:%M')} {src_dt.tzname()} → {dst_str}</span>")
            # DST note label below
            if not hasattr(self, 'dst_note_label'):
                self.dst_note_label = QLabel()
                self.dst_note_label.setStyleSheet("font-size:13pt;color:#888;")
                self.result_box_layout.addWidget(self.dst_note_label)
            if is_dst:
                self.dst_note_label.setText("Daylight Savings Time was taken into account.")
            else:
                self.dst_note_label.setText("Daylight Savings Time was NOT taken into account.")
        except Exception as e:
            self.result_label.setText(f"Invalid input: {e}")
            if hasattr(self, 'dst_note_label'):
                self.dst_note_label.setText("")

    def _update_countdown_if_open(self, *args):
        # Only update if time entry has a complete value (HH:MM)
        text = self.time_entry.text().strip()
        # Consider incomplete if less than 4 chars or doesn't match pattern
        import re
        if len(text) < 4 or not re.match(r"^\d{1,2}:\d{2}$", text):
            return
        if hasattr(self, 'countdown_dialog') and self.countdown_dialog is not None:
            try:
                self.show_countdown()
            except Exception:
                pass

    def show_countdown(self):
        # If the countdown dialog is already open and visible, close it and return
        if hasattr(self, 'countdown_dialog') and self.countdown_dialog is not None:
            try:
                if self.countdown_dialog.isVisible():
                    self.countdown_dialog.close()
                    self.countdown_dialog = None
                    return
            except Exception:
                self.countdown_dialog = None
        src_idx = self.src_tz.currentIndex()
        date_str = self.date_entry.text().strip()
        time_str = self.time_entry.text().strip()
        import re
        now = datetime.now()
        # If time_str is empty or invalid, use system time (current hour:minute)
        if not time_str or not re.match(r"^\d{1,2}:\d{2}$", time_str):
            time_str = f"{now.hour:02}:{now.minute:02}"
        if src_idx < 0:
            return  # No valid timezone selected
        try:
            if date_str:
                dt = parser.parse(f"{now.year}/{date_str} {time_str}")
            else:
                dt = parser.parse(f"{now.year}/{now.month:02}/{now.day:02} {time_str}")
            src_abbr, src_dst_abbr, _, _, _, src_pytz = TIMEZONES[src_idx]
            import pytz
            src_tz = pytz.timezone(src_pytz)
            src_dt = src_tz.localize(dt)
            local_dt = src_dt.astimezone()
            if hasattr(self, 'countdown_dialog') and self.countdown_dialog is not None:
                try:
                    self.countdown_dialog.set_target_dt(local_dt)
                    self.countdown_dialog.raise_()
                    self.countdown_dialog.activateWindow()
                    return
                except Exception:
                    self.countdown_dialog.close()
                    self.countdown_dialog = None
            self.countdown_dialog = CountdownDialog(local_dt)
            def cleanup_dialog():
                self.countdown_dialog = None
            self.countdown_dialog.finished.connect(cleanup_dialog)
            self.countdown_dialog.show()
        except Exception:
            pass  # Ignore parse errors while typing

    def show_about(self):
        # If the about dialog is already open and visible, close it and return
        if hasattr(self, 'about_dialog') and self.about_dialog is not None:
            try:
                if self.about_dialog.isVisible():
                    self.about_dialog.close()
                    self.about_dialog = None
                    return
            except Exception:
                self.about_dialog = None
        # Position AboutDialog 100px above or below main window
        about_dialog = AboutDialog(parent=self)
        # Calculate preferred position
        main_geom = self.geometry()
        screen_geom = self.screen().geometry() if hasattr(self, 'screen') else self.frameGeometry()
        dialog_width = about_dialog.width()
        dialog_height = about_dialog.height()
        x = main_geom.x() + (main_geom.width() - dialog_width) // 2
        # Prefer above if there's space, else below
        if main_geom.y() - dialog_height - 100 > screen_geom.y():
            y = main_geom.y() - dialog_height - 100
        else:
            y = min(main_geom.y() + main_geom.height() + 100, screen_geom.y() + screen_geom.height() - dialog_height)
        about_dialog.move(x, y)
        self.about_dialog = about_dialog
        def cleanup_about():
            self.about_dialog = None
        self.about_dialog.finished.connect(cleanup_about)
        self.about_dialog.show()

    def closeEvent(self, event):
        self.settings["main_window_pos"] = [self.x(), self.y()]
        self.settings["main_window_size"] = [self.width(), self.height()]
        save_settings(self.settings)
        super().closeEvent(event)

    def _handle_custom_tz(self, idx, is_src):
        combo = self.src_tz if is_src else self.dst_tz
        if combo.itemText(idx).startswith("UTC Custom") or combo.itemText(idx).startswith("UTC+") or combo.itemText(idx).startswith("UTC-"):
            initial = self.custom_src_offset if is_src else self.custom_dst_offset
            dlg = CustomUTCDialog(self, initial_offset=initial or 0)
            if dlg.exec_():
                offset = dlg.get_offset()
                if is_src:
                    self.custom_src_offset = offset
                else:
                    self.custom_dst_offset = offset
                # Update dropdown label
                sign = '+' if offset >= 0 else '-'
                label = f"UTC{sign}{abs(offset)}"
                combo.setItemText(combo.count()-1, label)
                combo.setCurrentIndex(combo.count()-1)
            else:
                # If cancelled, revert selection
                combo.setCurrentIndex(0)

class CountdownDialog(SnappableDialog):
    def __init__(self, target_dt, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.Tool, True)
        self.snapping = True
        self.settings = load_settings()
        self.theme = get_theme(self.settings)
        self.theme_mgr = ThemeManager(self.theme)
        self.setWindowTitle("Countdown")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.target_dt = target_dt
        self.overlay_mode = False
        # Restore size/pos for normal mode
        self.base_size = self.settings.get("countdown_normal_size", [720, 220])  # Larger default
        self.base_font_size = 36
        self.min_font_scale = 0.8 * 1.3  # +30%
        self.max_font_scale = 1.5 * 1.4  # +40%
        size = self.base_size
        self.resize(*size)
        pos = self.settings.get("countdown_normal_pos", [100, 100])
        self.move(*pos)
        self.setMinimumSize(320, 120)  # Ensure minimum readable size
        # Widgets
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)  # Set overlay padding here
        self.label = QLabel("00:00:00")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Segoe UI", self.base_font_size, QFont.Bold))
        layout.addWidget(self.label)
        self.info = QLabel("")
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setFont(QFont("Segoe UI", 18))
        layout.addWidget(self.info)
        # Always create overlay and options buttons (even if not visible)
        btn_row = QHBoxLayout()
        self.overlay_btn = QPushButton("\u23FB")  # Power symbol
        self.overlay_btn.setToolTip("Toggle overlay mode")
        self.overlay_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        btn_row.addWidget(self.overlay_btn)
        self.options_btn = QPushButton("\u2699")  # Cogwheel symbol
        self.options_btn.setToolTip("Options")
        self.options_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
        self.options_btn.clicked.connect(self.show_options)
        btn_row.addWidget(self.options_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)
        # Resizing/dragging state
        self.resizing = False
        self.drag_pos = None
        self.start_geom = None
        self.resize_margin = 12  # Ensure margin for snapping
        self.setMouseTracking(True)
        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        self.update_countdown()
        self.apply_settings()
        self.sound_played = False
        # Overlay mode settings
        self.overlay_base_size = self.settings.get("countdown_overlay_size", [400, 120])
        self.overlay_base_pos = self.settings.get("countdown_overlay_pos", [200, 200])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_font_scale()
        self.update_overlay_visibility()
        # Save size for current mode
        if self.overlay_mode:
            self.settings["countdown_overlay_size"] = [self.width(), self.height()]
        else:
            self.settings["countdown_normal_size"] = [self.width(), self.height()]
        save_settings(self.settings)

    def moveEvent(self, event):
        super().moveEvent(event)
        # Only snap if in overlay mode
        if getattr(self, 'overlay_mode', False):
            self.snap_to_corners()
        # Save position for current mode
        if self.overlay_mode:
            self.settings["countdown_overlay_pos"] = [self.x(), self.y()]
        else:
            self.settings["countdown_normal_pos"] = [self.x(), self.y()]
        save_settings(self.settings)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_on_edge(event.pos()):
                self.resizing = True
                self.drag_pos = event.globalPos()
                self.start_geom = self.geometry()
                event.accept()
            else:
                self.resizing = False
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
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
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.drag_pos = None
        self.setCursor(Qt.ArrowCursor)
        event.accept()

    def is_on_edge(self, pos):
        margin = self.resize_margin
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        on_left = x <= margin
        on_right = x >= w - margin
        on_top = y <= margin
        on_bottom = y >= h - margin
        # Allow resizing from any edge or corner
        return on_left or on_right or on_top or on_bottom

    def update_font_scale(self):
        # Dynamically shrink font so text always fits, prioritizing width over height
        min_font_size = 10
        margin_w = 18  # Margin for width
        margin_h = 8   # Smaller margin for height
        avail_w = self.width() - margin_w
        avail_h = self.label.height() - margin_h
        # Prioritize width scaling (allow taller text if needed)
        font_size = int(self.base_font_size * (self.width() / self.base_size[0]))
        font_size = max(int(self.base_font_size * self.min_font_scale), min(int(self.base_font_size * self.max_font_scale), font_size))
        font = QFont("Segoe UI", font_size, QFont.Bold)
        fm = QFontMetrics(font)
        rect = fm.boundingRect(self.label.text())
        # Shrink font until width fits, allow some vertical overflow
        while rect.width() > avail_w and font_size > min_font_size:
            font_size -= 1
            font.setPointSize(font_size)
            font.setWeight(QFont.Bold)
            fm = QFontMetrics(font)
            rect = fm.boundingRect(self.label.text())
        # If height is still way too large, shrink a bit more, but less aggressively
        while rect.height() > avail_h * 1.2 and font_size > min_font_size:
            font_size -= 1
            font.setPointSize(font_size)
            font.setWeight(QFont.Bold)
            fm = QFontMetrics(font)
            rect = fm.boundingRect(self.label.text())
        self.label.setFont(font)
        info_font = QFont("Segoe UI", int(18 * (font_size / self.base_font_size)))
        self.info.setFont(info_font)
        self.label.setAlignment(Qt.AlignCenter)

    def closeEvent(self, event):
        # Save position and size for current mode
        if self.overlay_mode:
            self.settings["countdown_overlay_pos"] = [self.x(), self.y()]
            self.settings["countdown_overlay_size"] = [self.width(), self.height()]
        else:
            self.settings["countdown_normal_pos"] = [self.x(), self.y()]
            self.settings["countdown_normal_size"] = [self.width(), self.height()]
        save_settings(self.settings)
        super().closeEvent(event)

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
                self.info.setText(f"Missed by {neg}")
                if hasattr(self, 'futile_label'):
                    self.futile_label.setText("ALAS, YOUR EFFORTS ARE FUTILE!")
            return
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)

        self.label.setText(f"{h:02}:{m:02}:{s:02}")
        # If negative, show negative time and futility message
        if delta.total_seconds() < 0:
            neg = str(abs(delta)).split('.')[0]
            self.info.setText(f"Missed by {neg}")
            if hasattr(self, 'futile_label'):
                self.futile_label.setText("ALAS, YOUR EFFORTS ARE FUTILE!")
        else:
            if hasattr(self, 'futile_label'):
                self.futile_label.setText("")

    def _update_countdown_if_open(self, *args):
        # Only update if time entry has a complete value (HH:MM)
        text = self.time_entry.text().strip()
        # Consider incomplete if less than 4 chars or doesn't match pattern
        import re
        if len(text) < 4 or not re.match(r"^\d{1,2}:\d{2}$", text):
            return
        if hasattr(self, 'countdown_dialog') and self.countdown_dialog is not None:
            try:
                self.show_countdown()
            except Exception:
                pass

    def show_countdown(self):
        src_idx = self.src_tz.currentIndex()
        date_str = self.date_entry.text().strip()
        time_str = self.time_entry.text().strip()
        import re
        now = datetime.now()
        # If time_str is empty or invalid, use system time (current hour:minute)
        if not time_str or not re.match(r"^\d{1,2}:\d{2}$", time_str):
            time_str = f"{now.hour:02}:{now.minute:02}"
        if src_idx < 0:
            return  # No valid timezone selected
        try:
            if date_str:
                dt = parser.parse(f"{now.year}/{date_str} {time_str}")
            else:
                dt = parser.parse(f"{now.year}/{now.month:02}/{now.day:02} {time_str}")
            src_abbr, src_dst_abbr, _, _, _, src_pytz = TIMEZONES[src_idx]
            import pytz
            src_tz = pytz.timezone(src_pytz)
            src_dt = src_tz.localize(dt)
            local_dt = src_dt.astimezone()
            if hasattr(self, 'countdown_dialog') and self.countdown_dialog is not None:
                try:
                    self.countdown_dialog.set_target_dt(local_dt)
                    self.countdown_dialog.raise_()
                    self.countdown_dialog.activateWindow()
                    return
                except Exception:
                    self.countdown_dialog.close()
                    self.countdown_dialog = None
            self.countdown_dialog = CountdownDialog(local_dt)
            def cleanup_dialog():
                self.countdown_dialog = None
            self.countdown_dialog.finished.connect(cleanup_dialog)
            self.countdown_dialog.show()
        except Exception:
            pass  # Ignore parse errors while typing

    def show_about(self):
        # Ensure any previous dialog is cleaned up
        if hasattr(self, 'about_dialog') and self.about_dialog is not None:
            try:
                self.about_dialog.close()
            except Exception:
                pass
            self.about_dialog = None
        self.about_dialog = AboutDialog()
        def cleanup_about():
            self.about_dialog = None
        self.about_dialog.finished.connect(cleanup_about)
        self.about_dialog.exec_()

    def closeEvent(self, event):
        self.settings["main_window_pos"] = [self.x(), self.y()]
        self.settings["main_window_size"] = [self.width(), self.height()]
        save_settings(self.settings)
        super().closeEvent(event)

    def _handle_custom_tz(self, idx, is_src):
        combo = self.src_tz if is_src else self.dst_tz
        if combo.itemText(idx).startswith("UTC Custom") or combo.itemText(idx).startswith("UTC+") or combo.itemText(idx).startswith("UTC-"):
            initial = self.custom_src_offset if is_src else self.custom_dst_offset
            dlg = CustomUTCDialog(self, initial_offset=initial or 0)
            if dlg.exec_():
                offset = dlg.get_offset()
                if is_src:
                    self.custom_src_offset = offset
                else:
                    self.custom_dst_offset = offset
                # Update dropdown label
                sign = '+' if offset >= 0 else '-'
                label = f"UTC{sign}{abs(offset)}"
                combo.setItemText(combo.count()-1, label)
                combo.setCurrentIndex(combo.count()-1)
            else:
                # If cancelled, revert selection
                combo.setCurrentIndex(0)

    def play_tada(self):
        play_custom_sound()

    def toggle_overlay(self):
        # Save main window position before hiding
        if not hasattr(self, '_pre_overlay_pos'):
            self._pre_overlay_pos = None
        if not self.overlay_mode:
            # Save position and minimize to tray
            self._pre_overlay_pos = self.pos()
            # Always minimize the main TimezoneConverter window to tray
            main_window = self.parent()
            if main_window is None:
                # Try to find the main window via QApplication
                from PyQt5.QtWidgets import QApplication
                for w in QApplication.topLevelWidgets():
                    if isinstance(w, TimezoneConverter):
                        main_window = w
                        break
            if main_window and hasattr(main_window, 'minimize_to_tray'):
                main_window.minimize_to_tray()
        # Existing overlay logic
        if not self.overlay_mode:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.overlay_mode = True
            self.update_overlay_visibility()
            if self.settings.get("double_click_overlay", False):
                self.setMouseTracking(True)
            self.setStyleSheet(self.theme_mgr.widget_stylesheet() + f"""
QDialog {{
    border-radius: 0px;
    border: 0.5px solid rgba(255, 255, 255, 0.4);
    padding: 8px; margin: 0px;
    background-color: rgba(35, 39, 46, {self.settings.get('transparency', 0.5)});
}}
QFrame#resultBox {{ border: none; padding: 8px; margin: 0px; background: transparent; }}
""")
            self.setMinimumSize(200, 100)
            self.setMaximumSize(16777215, 16777215)
            self.apply_settings()
            self.show()
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.setWindowFlag(Qt.FramelessWindowHint, False)
            self.overlay_mode = False
            self.update_overlay_visibility()
            self.setStyleSheet(self.theme_mgr.widget_stylesheet())
            self.setFixedSize(*self.settings.get("countdown_normal_size", [600, 180]))
            self.setWindowOpacity(1.0)
            self.set_click_through(False)
            self.show()
            # Restore main window from tray and position
            main_window = self.parent()
            if main_window is None:
                from PyQt5.QtWidgets import QApplication
                for w in QApplication.topLevelWidgets():
                    if isinstance(w, TimezoneConverter):
                        main_window = w
                        break
            if main_window and hasattr(main_window, 'restore_from_tray'):
                main_window.restore_from_tray()
            if hasattr(self, '_pre_overlay_pos') and self._pre_overlay_pos:
                self.move(self._pre_overlay_pos)
                self._pre_overlay_pos = None

    def mouseDoubleClickEvent(self, event):
        if self.overlay_mode and self.settings.get("double_click_overlay", False):
            self.toggle_overlay()  # disables overlay
            # Move to screen centre
            screen = QApplication.primaryScreen().geometry()
            win = self.geometry()
            x = screen.x() + (screen.width() - win.width()) // 2
            y = screen.y() + (screen.height() - win.height()) // 2
            self.move(x, y)
            event.accept()
        elif not self.overlay_mode and self.settings.get("double_click_overlay", False):
            self.toggle_overlay()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def update_overlay_visibility(self):
        # Hide/show power and cog buttons and info label based on overlay mode
        borderless = "QPushButton { background: transparent; border: none; outline: none; color: %s; font-size: 28px; min-width:32px; min-height:32px; border: none; } QPushButton:pressed { background: transparent; border: none; outline: none; }" % self.theme_mgr.symbol
        if self.overlay_mode:
            if hasattr(self, 'overlay_btn') and self.overlay_btn:
                self.overlay_btn.hide()
            if hasattr(self, 'options_btn') and self.options_btn:
                self.options_btn.hide()
            self.info.setVisible(False)
        else:
            if hasattr(self, 'overlay_btn') and self.overlay_btn:
                self.overlay_btn.show()
                self.overlay_btn.setStyleSheet(borderless)
            if hasattr(self, 'options_btn') and self.options_btn:
                self.options_btn.show()
                self.options_btn.setStyleSheet(borderless)
            self.info.setVisible(True)

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

    def snap_to_corners(self):
        if not getattr(self, 'overlay_mode', False):
            return
        if getattr(self, '_snapping_in_progress', False):
            return
        self._snapping_in_progress = True
        try:
            # Use the screen the window is currently on for snapping
            center_point = self.frameGeometry().center()
            screen = QApplication.screenAt(center_point)
            if screen is not None:
                screen_geom = screen.geometry()
            else:
                screen_geom = QApplication.primaryScreen().geometry()
            margin = 12  # Use a practical margin for snapping
            x, y, w, h = self.geometry().x(), self.geometry().y(), self.width(), self.height()
            cx = x + w // 2
            mid_x = screen_geom.x() + screen_geom.width() // 2
            snapped = False
            if abs(x - screen_geom.x()) <= margin:
                self.move(screen_geom.x(), y)
                snapped = True
            elif abs(x + w - (screen_geom.x() + screen_geom.width())) <= margin:
                self.move(screen_geom.x() + screen_geom.width() - w, y)
                snapped = True
            elif abs(cx - mid_x) <= margin:
                self.move(mid_x - w // 2, y)
                snapped = True
            # PATCH: Visual snap cue (only in overlay mode)
            if snapped:
                if getattr(self, '_snapping_style_update', False):
                    return
                self._snapping_style_update = True
                try:
                    theme = getattr(self, 'theme', None)
                    theme_mgr = getattr(self, 'theme_mgr', None)
                    if theme_mgr is not None:
                        border_color = theme_mgr.accent if theme == "light" else theme_mgr.button_border
                        self.setStyleSheet(self.styleSheet() +
                            f"\nQDialog {{ border: 0.5px solid {border_color}; border-radius: 0px; }}")
                    else:
                        print("[Snap Cue] theme_mgr is None!")
                except Exception as e:
                    print(f"[Snap Cue ERROR] {e}")
                finally:
                    self._snapping_style_update = False
        finally:
            self._snapping_in_progress = False

    def mouseDoubleClickEvent(self, event):
        if self.overlay_mode and self.settings.get("double_click_overlay", False):
            self.toggle_overlay()  # disables overlay
            # Move to screen centre
            screen = QApplication.primaryScreen().geometry()
            win = self.geometry()
            x = screen.x() + (screen.width() - win.width()) // 2
            y = screen.y() + (screen.height() - win.height()) // 2
            self.move(x, y)
            event.accept()
        elif not self.overlay_mode and self.settings.get("double_click_overlay", False):
            self.toggle_overlay()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def set_target_dt(self, new_dt):
        """Update the countdown's target datetime and refresh display."""
        self.target_dt = new_dt
        self.sound_played = False
        self.timer.start(1000)
        self.update_countdown()

class CountdownOptionsDialog(SnappableDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.Tool, True)
        self.setWindowFlag(Qt.Tool, True)
        self.settings = settings
        self.theme = get_theme(settings)
        self.theme_mgr = ThemeManager(self.theme)
        self.setWindowTitle("Countdown Options")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setFixedSize(420, 260)
        self.setStyleSheet(self.theme_mgr.widget_stylesheet())
        layout = QVBoxLayout()
        # Theme toggle row
        theme_row = QHBoxLayout()
        self.sun_btn = QPushButton("\u2600")  # 
        self.sun_btn.setToolTip("Switch to Light Mode")
        self.sun_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
        self.sun_btn.setFixedWidth(32)
        self.sun_btn.clicked.connect(self.set_light_mode)
        theme_row.addWidget(self.sun_btn)
        self.moon_btn = QPushButton("\U0001F319")  # 
        self.moon_btn.setToolTip("Switch to Dark Mode")
        self.moon_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
        self.moon_btn.setFixedWidth(32)
        self.moon_btn.clicked.connect(self.set_dark_mode)
        theme_row.addWidget(self.moon_btn)
        self.auto_btn = QPushButton("\U0001F5D0")  # 
        self.auto_btn.setToolTip("Auto Theme (System)")
        self.auto_btn.setStyleSheet(self.theme_mgr.button_stylesheet(symbol=True))
        self.auto_btn.setFixedWidth(32)
        self.auto_btn.clicked.connect(self.set_auto_mode)
        theme_row.addWidget(self.auto_btn)
        theme_row.addStretch()
        layout.addLayout(theme_row)
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
        self.click_chk.setStyleSheet(self.theme_mgr.button_stylesheet(toggle=True, checked=self.click_chk.isChecked()))
        self.click_chk.toggled.connect(lambda checked: self.click_chk.setStyleSheet(self.theme_mgr.button_stylesheet(toggle=True, checked=checked)))
        layout.addWidget(self.click_chk)
        self.sound_chk = QPushButton("Play annoying sound when countdown finishes")
        self.sound_chk.setCheckable(True)
        self.sound_chk.setChecked(settings.get("play_sound", False))
        self.sound_chk.setStyleSheet(self.theme_mgr.button_stylesheet(toggle=True, checked=self.sound_chk.isChecked()))
        self.sound_chk.toggled.connect(lambda checked: self.sound_chk.setStyleSheet(self.theme_mgr.button_stylesheet(toggle=True, checked=checked)))
        self.sound_chk.clicked.connect(self.preview_sound)
        layout.addWidget(self.sound_chk)
        self.dblclick_chk = QPushButton("Double Click Overlay Control")
        self.dblclick_chk.setCheckable(True)
        self.dblclick_chk.setChecked(settings.get("double_click_overlay", False))
        self.dblclick_chk.setStyleSheet(self.theme_mgr.button_stylesheet(toggle=True, checked=self.dblclick_chk.isChecked()))
        self.dblclick_chk.toggled.connect(lambda checked: self.dblclick_chk.setStyleSheet(self.theme_mgr.button_stylesheet(toggle=True, checked=checked)))
        layout.addWidget(self.dblclick_chk)
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(self.theme_mgr.button_stylesheet())
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(self.theme_mgr.button_stylesheet())
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def set_light_mode(self):
        self.settings["theme"] = "light"
        save_settings(self.settings)
        self.theme_mgr.set_theme("light")
        self.setStyleSheet(self.theme_mgr.widget_stylesheet())
        self.update_all_themes()

    def set_dark_mode(self):
        self.settings["theme"] = "dark"
        save_settings(self.settings)
        self.theme_mgr.set_theme("dark")
        self.setStyleSheet(self.theme_mgr.widget_stylesheet())
        self.update_all_themes()

    def set_auto_mode(self):
        self.settings["theme"] = "auto"
        save_settings(self.settings)
        self.theme_mgr.set_theme(get_theme(self.settings))
        self.setStyleSheet(self.theme_mgr.widget_stylesheet())
        self.update_all_themes()

    def update_all_themes(self):
        app = QApplication.instance()
        for w in app.topLevelWidgets():
            if hasattr(w, "theme_mgr"):
                theme = get_theme(self.settings)
                w.theme_mgr.set_theme(theme)
                w.setStyleSheet(w.theme_mgr.widget_stylesheet())
                for attr in dir(w):
                    obj = getattr(w, attr)
                    if isinstance(obj, QPushButton):
                        if hasattr(obj, "isCheckable") and obj.isCheckable():
                            obj.setStyleSheet(w.theme_mgr.button_stylesheet(toggle=True, checked=obj.isChecked(), symbol=(obj.text() in ["", "", "", ""])) )
                        else:
                            obj.setStyleSheet(w.theme_mgr.button_stylesheet(symbol=(obj.text() in ["", "", "", ""])) )

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
            play_custom_sound()

    def accept(self):
        # Save window positions and size for all relevant windows
        parent = self.parentWidget()
        if parent:
            self.settings["main_window_pos"] = [parent.x(), parent.y()]
            self.settings["main_window_size"] = [parent.width(), parent.height()]
        # If this is the countdown dialog, save its size/pos too
        if hasattr(parent, "target_dt"):
            self.settings["countdown_normal_pos"] = [parent.x(), parent.y()]
            self.settings["countdown_normal_size"] = [parent.width(), parent.height()]
        save_settings(self.settings)
        super().accept()

class AboutDialog(SnappableDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.Tool, True)
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setFixedSize(600, 260)
        # Use parent's theme if available
        theme = None
        if parent is not None and hasattr(parent, 'theme_mgr'):
            theme = getattr(parent.theme_mgr, 'theme', None)
        if theme is None:
            # fallback to parent's settings if available
            settings = getattr(parent, 'settings', None)
            theme = get_theme(settings) if settings else 'light'
        self.theme_mgr = ThemeManager(theme)
        self.setStyleSheet(self.theme_mgr.widget_stylesheet())
        layout = QVBoxLayout()

        # Message text
        label = QLabel(
            "Made for my own incompetent self, shared freely for yours. You can always donate to my dumbass or buy my shitty literature though."
        )
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 13))
        layout.addWidget(label)

        # Links row
        link_color = self.theme_mgr.accent if hasattr(self.theme_mgr, 'accent') else '#0078d7'
        link_style = f"color: {link_color}; text-decoration: underline;"
        links_html = f'''<div style="text-align:center; font-size:14px; margin-top:10px;">
            <a href="https://www.paypal.com/donate/?business=UBZJY8KHKKLGC&no_recurring=0&item_name=Why+are+you+doing+this?+Are+you+drunk?+&currency_code=USD" style="{link_style}">Donate via Paypal</a> |
            <a href="https://www.goodreads.com/book/show/25006763-usu" style="{link_style}">Usu on Goodreads</a> |
            <a href="https://www.amazon.com/Usu-Jayde-Ver-Elst-ebook/dp/B00V8A5K7Y" style="{link_style}">Usu on Amazon</a>
        </div>'''
        links_label = QLabel()
        links_label.setTextFormat(Qt.RichText)
        links_label.setText(links_html)
        links_label.setOpenExternalLinks(True)
        links_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(links_label)

        self.setLayout(layout)

def play_custom_sound():
    AUDIO_PATH = r'F:\\Programming\\Resources\\Sound\\tutuogg.ogg'
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(AUDIO_PATH)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Failed to play sound: {e}")

if __name__ == "__main__":
    import os
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    import pygame
    app = QApplication(sys.argv)
    window = TimezoneConverter()
    window.show()
    sys.exit(app.exec_())
