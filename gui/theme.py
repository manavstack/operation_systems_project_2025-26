"""
D-RTOS: GUI Theme
Tactical dark Command-Center color palette and widget styles.
"""

from __future__ import annotations
from typing import Dict, Any


# ============================================================
# Color Palette
# ============================================================

class Colors:
    # Backgrounds
    BG_DEEP    = "#090E1A"    # Main canvas background
    BG_PANEL   = "#111827"    # Panel / card background
    BG_SIDEBAR = "#0D1525"    # Sidebar navigation
    BG_HEADER  = "#0A1020"    # Header bar
    BG_INPUT   = "#1A2540"    # Input fields
    BG_TABLE   = "#141E30"    # Table background
    BG_ROW_ALT = "#1A2540"    # Alternating table row
    BG_HOVER   = "#1E2F50"    # Hover state

    # Accent Colors
    RADAR_GREEN   = "#00FF66"  # Primary radar accent
    HUD_CYAN      = "#00E5FF"  # HUD/info accent
    AMBER_WARN    = "#FFB300"  # Warning indicator
    ALERT_RED     = "#FF3366"  # Alert/critical indicator
    PURPLE_ACCENT = "#7B5EA7"  # Secondary accent
    BLUE_ACCENT   = "#3B82F6"  # Informational blue

    # Text
    TEXT_PRIMARY   = "#E8F4FD"  # Main text
    TEXT_SECONDARY = "#8BA3C7"  # Secondary / muted text
    TEXT_DIM       = "#4A6080"  # Dimmed text / labels
    TEXT_ACCENT    = "#00E5FF"  # Highlighted text

    # Threat Level Colors
    CRITICAL = "#FF3366"
    HIGH     = "#FF6B35"
    MEDIUM   = "#FFB300"
    LOW      = "#00FF66"

    # Process State Colors
    STATE_NEW        = "#7B5EA7"
    STATE_READY      = "#3B82F6"
    STATE_RUNNING    = "#00FF66"
    STATE_WAITING    = "#FFB300"
    STATE_TERMINATED = "#4A6080"

    # Chart Colors
    CHART_PALETTE = [
        "#00E5FF", "#00FF66", "#FFB300", "#FF3366",
        "#7B5EA7", "#3B82F6", "#FF6B35", "#00BFA5",
    ]

    # Border
    BORDER       = "#1E3A5F"
    BORDER_LIGHT = "#2A4A6F"

    @classmethod
    def for_threat(cls, threat: str) -> str:
        return {
            "CRITICAL": cls.CRITICAL,
            "HIGH":     cls.HIGH,
            "MEDIUM":   cls.MEDIUM,
            "LOW":      cls.LOW,
        }.get(threat.upper(), cls.TEXT_PRIMARY)

    @classmethod
    def for_state(cls, state: str) -> str:
        return {
            "NEW":        cls.STATE_NEW,
            "READY":      cls.STATE_READY,
            "RUNNING":    cls.STATE_RUNNING,
            "WAITING":    cls.STATE_WAITING,
            "TERMINATED": cls.STATE_TERMINATED,
        }.get(state.upper(), cls.TEXT_PRIMARY)


# ============================================================
# Typography
# ============================================================

class Fonts:
    # Primary monospace for data
    MONO_LG   = ("Courier New", 14, "bold")
    MONO_MD   = ("Courier New", 11, "bold")
    MONO_SM   = ("Courier New", 9)

    # Sans-serif for labels
    LABEL_LG  = ("Helvetica Neue", 14, "bold")
    LABEL_MD  = ("Helvetica Neue", 11)
    LABEL_SM  = ("Helvetica Neue", 9)

    # Headers
    HEADER    = ("Helvetica Neue", 20, "bold")
    SUBHEADER = ("Helvetica Neue", 14, "bold")
    TITLE     = ("Helvetica Neue", 11, "bold")

    # Value display
    VALUE_LG  = ("Courier New", 18, "bold")
    VALUE_MD  = ("Courier New", 13, "bold")
    VALUE_SM  = ("Courier New", 10, "bold")

    # Nav
    NAV       = ("Helvetica Neue", 10, "bold")


# ============================================================
# Widget Style Helpers
# ============================================================

class Styles:
    """Centralized tkinter widget style kwargs."""

    @staticmethod
    def frame() -> Dict[str, Any]:
        return {"bg": Colors.BG_PANEL}

    @staticmethod
    def label(fg: str = Colors.TEXT_PRIMARY,
              bg: str = Colors.BG_PANEL,
              font=Fonts.LABEL_MD) -> Dict[str, Any]:
        return {"fg": fg, "bg": bg, "font": font}

    @staticmethod
    def header_label(text_color: str = Colors.HUD_CYAN) -> Dict[str, Any]:
        return {"fg": text_color, "bg": Colors.BG_PANEL, "font": Fonts.SUBHEADER}

    @staticmethod
    def button(bg: str = Colors.BG_INPUT,
               fg: str = Colors.HUD_CYAN,
               active_bg: str = Colors.BG_HOVER) -> Dict[str, Any]:
        return {
            "bg": bg, "fg": fg,
            "activebackground": active_bg,
            "activeforeground": Colors.TEXT_PRIMARY,
            "font": Fonts.LABEL_MD,
            "relief": "flat",
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2",
        }

    @staticmethod
    def danger_button() -> Dict[str, Any]:
        d = Styles.button(Colors.ALERT_RED, Colors.TEXT_PRIMARY, "#CC2244")
        return d

    @staticmethod
    def success_button() -> Dict[str, Any]:
        return Styles.button(Colors.RADAR_GREEN, Colors.BG_DEEP, "#00CC55")

    @staticmethod
    def entry() -> Dict[str, Any]:
        return {
            "bg": Colors.BG_INPUT,
            "fg": Colors.TEXT_PRIMARY,
            "insertbackground": Colors.HUD_CYAN,
            "font": Fonts.MONO_MD,
            "relief": "flat",
            "bd": 2,
            "highlightthickness": 1,
            "highlightcolor": Colors.BORDER_LIGHT,
            "highlightbackground": Colors.BORDER,
        }

    @staticmethod
    def text_widget() -> Dict[str, Any]:
        return {
            "bg": Colors.BG_INPUT,
            "fg": Colors.TEXT_PRIMARY,
            "insertbackground": Colors.HUD_CYAN,
            "font": Fonts.MONO_SM,
            "relief": "flat",
            "bd": 0,
            "selectbackground": Colors.BG_HOVER,
        }

    @staticmethod
    def treeview_style(style_obj) -> None:
        """Configure ttk.Treeview style for dark theme."""
        try:
            style_obj.configure("Custom.Treeview",
                                 background=Colors.BG_TABLE,
                                 foreground=Colors.TEXT_PRIMARY,
                                 fieldbackground=Colors.BG_TABLE,
                                 font=Fonts.MONO_SM,
                                 rowheight=24)
            style_obj.configure("Custom.Treeview.Heading",
                                 background=Colors.BG_SIDEBAR,
                                 foreground=Colors.HUD_CYAN,
                                 font=Fonts.TITLE,
                                 relief="flat")
            style_obj.map("Custom.Treeview",
                           background=[("selected", Colors.BG_HOVER)],
                           foreground=[("selected", Colors.TEXT_PRIMARY)])
        except Exception:
            pass


# ============================================================
# Layout Constants
# ============================================================

SIDEBAR_WIDTH  = 200
HEADER_HEIGHT  = 60
STATUS_HEIGHT  = 28
PADDING        = 10
INNER_PADDING  = 8
CARD_RADIUS    = 4


def apply_dark_titlebar(root):
    """Attempt to apply dark title bar on supported platforms."""
    try:
        root.tk.call("tk::unsupported::MacWindowStyle", "style", root._w,
                     "document", "closeBox collapseBox resizeBox")
    except Exception:
        pass
