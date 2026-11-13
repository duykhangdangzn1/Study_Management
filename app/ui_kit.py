"""Bo widget giao dien dung chung: theme, icon, card, bieu do, toast, dialog."""
from __future__ import annotations

import os
import sys
import tempfile

from PySide6.QtCore import (QByteArray, QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRect, QRectF, QSize, Qt,
                            QTimer, Signal)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontDatabase, QFontMetrics, QIcon, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QPolygonF)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLayout, QPushButton,
                               QSizePolicy, QStyle, QStyledItemDelegate, QTabBar, QVBoxLayout, QWidget)


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


FONT_FAMILY = "Be Vietnam Pro"


def load_fonts() -> str:
    global FONT_FAMILY
    fam = None
    folder = resource_path(os.path.join("assets", "fonts"))
    if os.path.isdir(folder):
        for f in sorted(os.listdir(folder)):
            if f.endswith(".ttf"):
                fid = QFontDatabase.addApplicationFont(os.path.join(folder, f))
                fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
                if fams and fam is None:
                    fam = fams[0]
    FONT_FAMILY = fam or "Segoe UI"
    return FONT_FAMILY


# ---------------------------------------------------------------- palette
C = {
    "bg": "#F3F5FB",
    "surface": "#FFFFFF",
    "border": "#E6EAF3",
    "text": "#0F172A",
    "text2": "#334155",
    "muted": "#64748B",
    "faint": "#94A3B8",
    "primary": "#1F3BFF",
    "primary_dark": "#0B1FB8",
    "primary_soft": "#EBEEFF",
    "navy": "#0A1240",
    "navy2": "#121D5E",
    "yellow": "#FFD60A",
    "yellow_soft": "#FFF8D6",
    "red": "#E5383B",
    "red_soft": "#FDECEC",
    "green": "#10B981",
    "green_soft": "#E7F8F1",
    "amber": "#F59E0B",
    "amber_soft": "#FEF3DC",
    "violet": "#7C3AED",
    "violet_soft": "#F1EAFE",
    "cyan": "#0EA5E9",
    "cyan_soft": "#E6F5FD",
    "surface2": "#F8F9FE",
    "chip": "#F1F4F9",
    "track": "#EEF1F8",
    "grid": "#EDF0F7",
    "alt": "#FAFBFE",
    "line": "#F0F2F8",
    "scroll": "#CBD3E4",
    "scroll_h": "#9FAAC3",
    "primary_border": "#C9D1FF",
    "red_border": "#F6C9CA",
    "disabled_primary": "#AAB4F5",
}
LIGHT = dict(C)
DARK = {
    "bg": "#0B1020", "surface": "#141B2F", "border": "#252E4A", "text": "#E8ECF7", "text2": "#C4CBE0",
    "muted": "#8D97B5", "faint": "#606B8A", "primary": "#4C66FF", "primary_dark": "#2F49E8", "primary_soft": "#1D2754",
    "navy": "#070B1A", "navy2": "#0E1533", "yellow": "#FFD60A", "yellow_soft": "#2F2A10",
    "red": "#F05D5F", "red_soft": "#3A1C24", "green": "#22C58E", "green_soft": "#10302A",
    "amber": "#F5A524", "amber_soft": "#352812", "violet": "#9B6BFF", "violet_soft": "#2A1E4D",
    "cyan": "#38BDF8", "cyan_soft": "#0F2B3D", "surface2": "#19213A", "chip": "#1E2640", "track": "#222B47",
    "grid": "#1F2742", "alt": "#161D33", "line": "#1E2640", "scroll": "#2E3858", "scroll_h": "#46527A",
    "primary_border": "#34408A", "red_border": "#5A2A32", "disabled_primary": "#2F3A75",
}
THEME = "light"


def apply_theme(mode: str) -> str:
    global THEME
    THEME = "dark" if mode == "dark" else "light"
    C.update(DARK if THEME == "dark" else LIGHT)
    return THEME


def chevron_png(color: str, up: bool, size: int = 11) -> str:
    """Vẽ mũi tên lên/xuống ra PNG vì QSS chỉ nhận ảnh, không vẽ được vector.

    Trả về đường dẫn dạng '/' để dùng trong url("...") của stylesheet.
    """
    folder = os.path.join(tempfile.gettempdir(), "tinhocxaydung_ui")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        return ""
    path = os.path.join(folder, f"chevron_{'up' if up else 'down'}_{color.strip('#')}_{size}.png")
    if not os.path.exists(path):
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(color), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        mid = size / 2
        if up:
            pts = [QPointF(2.2, size - 3.9), QPointF(mid, 3.8), QPointF(size - 2.2, size - 3.9)]
        else:
            pts = [QPointF(2.2, 3.9), QPointF(mid, size - 3.8), QPointF(size - 2.2, 3.9)]
        p.drawPolyline(QPolygonF(pts))
        p.end()
        try:
            pm.save(path, "PNG")
        except Exception:  # pragma: no cover - ảnh chỉ để trang trí
            return ""
    return path.replace(os.sep, "/")


def qss() -> str:
    f = FONT_FAMILY
    check_icon = resource_path(os.path.join("assets", "icons", "check_white.svg")).replace(os.sep, "/")
    up_arrow = chevron_png(C["muted"], True)
    down_arrow = chevron_png(C["muted"], False)
    return f"""
    * {{ font-family: '{f}'; color: {C['text']}; }}
    QMainWindow, #Content {{ background: {C['bg']}; }}
    QToolTip {{ background: {C['navy']}; color: white; border: none; padding: 6px 10px; border-radius: 6px; }}
    #Sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {C['navy']}, stop:1 {C['navy2']}); }}
    #Sidebar QLabel {{ color: white; }}
    #Sidebar {{ border-right: 1px solid {C['border'] if THEME == 'dark' else C['navy']}; }}
    #ThemeSwitch {{ background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 14px; }}
    #ThemeBtn {{ background: transparent; color: #C7CEF5; border: none; border-radius: 10px; padding: 8px 10px;
                font-weight: 600; font-size: 13px; }}
    #ThemeBtn:hover:!checked {{ background: rgba(255,255,255,0.08); color: white; }}
    #ThemeBtn:checked {{ background: {C['yellow']}; color: {C['navy']}; font-weight: 800; }}
    #NavButton {{ background: transparent; color: #C7CEF5; border: none; border-radius: 12px;
                 text-align: left; padding: 12px 16px; font-size: 14px; font-weight: 500; }}
    #NavButton:hover {{ background: rgba(255,255,255,0.08); color: white; }}
    #NavButton:checked {{ background: rgba(255,255,255,0.14); color: white; font-weight: 700; }}
    #SideCard {{ background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.10); border-radius: 16px; }}
    #Card {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 18px; }}
    #PageTitle {{ font-size: 26px; font-weight: 800; }}
    #PageSub {{ font-size: 13px; color: {C['muted']}; }}
    #CardTitle {{ font-size: 15px; font-weight: 700; }}
    #Muted {{ color: {C['muted']}; font-size: 12px; }}
    #Value {{ font-size: 30px; font-weight: 800; }}
    QPushButton#Primary {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {C['primary']}, stop:1 {C['primary_dark']});
                          color: white; border: none; border-radius: 12px; padding: 11px 22px; font-weight: 700; font-size: 14px; }}
    QPushButton#Primary:hover {{ background: {C['primary_dark']}; }}
    QPushButton#Primary:disabled {{ background: {C['disabled_primary']}; }}
    QPushButton#Ghost {{ background: {C['surface']}; color: {C['text2']}; border: 1px solid {C['border']};
                        border-radius: 12px; padding: 10px 18px; font-weight: 600; font-size: 13px; }}
    QPushButton#Ghost:hover {{ background: {C['primary_soft']}; color: {C['primary']}; border-color: {C['primary_border']}; }}
    QPushButton#Danger {{ background: {C['surface']}; color: {C['red']}; border: 1px solid {C['red_border']};
                         border-radius: 12px; padding: 10px 18px; font-weight: 600; font-size: 13px; }}
    QPushButton#Danger:hover {{ background: {C['red_soft']}; }}
    QPushButton#Danger:disabled, QPushButton#Ghost:disabled {{ color: {C['faint']}; border-color: {C['border']}; }}
    QPushButton#Pill {{ background: {C['surface']}; color: {C['text2']}; border: 1px solid {C['border']}; border-radius: 17px;
                       padding: 7px 14px; font-weight: 600; font-size: 13px; min-height: 20px; }}
    QPushButton#Pill:hover {{ border-color: {C['primary']}; color: {C['primary']}; }}
    QPushButton#Pill:checked {{ background: {C['primary']}; color: white; border-color: {C['primary']}; }}
    QLineEdit {{ background: {C['surface']}; border: 1.5px solid {C['border']}; border-radius: 12px; padding: 10px 14px;
                font-size: 14px; selection-background-color: {C['primary']}; }}
    QLineEdit:focus {{ border-color: {C['primary']}; }}
    QLineEdit#ScoreInput {{ font-size: 20px; font-weight: 700; padding: 8px 12px; qproperty-alignment: AlignCenter; }}
    QLineEdit#ScoreInput:disabled {{ background: {C['surface2']}; color: {C['faint']}; }}
    QTableWidget {{ background: {C['surface']}; border: none; gridline-color: transparent; font-size: 13px;
                   selection-background-color: {C['primary_soft']}; selection-color: {C['text']};
                   alternate-background-color: {C['alt']}; outline: 0; }}
    QTableWidget::item {{ padding: 4px 8px; border-bottom: 1px solid {C['line']}; }}
    QTableWidget::item:selected {{ background: {C['primary_soft']}; color: {C['text']}; }}
    QHeaderView::section {{ background: {C['surface']}; color: {C['muted']}; border: none; border-bottom: 1px solid {C['border']};
                           padding: 10px 8px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {C['scroll']}; border-radius: 4px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {C['scroll_h']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {C['scroll']}; border-radius: 4px; min-width: 30px; }}
    QProgressBar {{ background: {C['track']}; border: none; border-radius: 4px; height: 8px; text-align: center; }}
    QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {C['primary']}, stop:1 #6F7DFF); border-radius: 4px; }}
    QSplitter::handle {{ background: transparent; }}
    QTabWidget::pane {{ border: none; background: transparent; }}
    QTabBar {{ background: transparent; border: none; }}
    QTabBar::tab {{ background: transparent; border: none; padding: 0px; margin: 0px; }}
    QComboBox {{ background: {C['surface']}; border: 1.5px solid {C['border']}; border-radius: 11px;
                padding: 8px 28px 8px 12px; font-size: 13px; min-height: 20px; }}
    QComboBox:focus {{ border-color: {C['primary']}; }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox::down-arrow {{ image: url("{down_arrow}"); width: 11px; height: 11px; }}
    QComboBox QAbstractItemView {{ background: {C['surface']}; border: 1px solid {C['border']};
                                  border-radius: 10px; padding: 4px; outline: 0;
                                  selection-background-color: {C['primary_soft']}; selection-color: {C['text']}; }}
    QCheckBox {{ font-size: 13px; color: {C['text2']}; spacing: 9px; padding: 2px 0; }}
    QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1.5px solid {C['border']};
                           background: {C['surface']}; }}
    QCheckBox::indicator:hover {{ border-color: {C['primary']}; }}
    QCheckBox::indicator:checked {{ background: {C['primary']}; border-color: {C['primary']};
                                   image: url("{check_icon}"); }}
    QTimeEdit, QSpinBox, QDoubleSpinBox {{ background: {C['surface']}; border: 1.5px solid {C['border']};
                                         border-radius: 10px; padding: 6px 24px 6px 10px; font-size: 13px;
                                         min-height: 22px; }}
    QTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {C['primary']}; }}
    QTimeEdit::up-button, QSpinBox::up-button, QDoubleSpinBox::up-button {{
        subcontrol-origin: border; subcontrol-position: top right; width: 20px; height: 15px;
        border: none; background: transparent; margin: 3px 3px 0 0; }}
    QTimeEdit::down-button, QSpinBox::down-button, QDoubleSpinBox::down-button {{
        subcontrol-origin: border; subcontrol-position: bottom right; width: 20px; height: 15px;
        border: none; background: transparent; margin: 0 3px 3px 0; }}
    QTimeEdit::up-button:hover, QTimeEdit::down-button:hover, QSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background: {C['chip']}; border-radius: 5px; }}
    QTimeEdit::up-arrow, QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
        image: url("{up_arrow}"); width: 11px; height: 11px; }}
    QTimeEdit::down-arrow, QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: url("{down_arrow}"); width: 11px; height: 11px; }}
    QFrame#SegNav {{ background: {C['chip']}; border: 1px solid {C['border']}; border-radius: 15px; }}
    QPushButton#SegBtn {{ background: transparent; border: none; border-radius: 11px; padding: 8px 16px;
                         color: {C['muted']}; font-size: 13px; font-weight: 600; }}
    QPushButton#SegBtn:hover {{ color: {C['text']}; background: {C['surface2']}; }}
    QPushButton#SegBtn:checked {{ background: {C['surface']}; color: {C['primary']}; font-weight: 700; }}
    QFrame#Composer {{ background: {C['surface']}; border: 1.5px solid {C['border']}; border-radius: 20px; }}
    QFrame#Composer[focus="true"] {{ border-color: {C['primary']}; }}
    QFrame#Composer[onCanvas="true"] {{ background: {C['surface2']}; }}
    QFrame#ChatCanvas {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 18px; }}
    QLineEdit#ComposerInput {{ background: transparent; border: none; padding: 0px 2px; font-size: 13px;
                              selection-background-color: {C['primary']}; }}
    QPushButton#SendBtn {{ background: {C['primary']}; border: none; border-radius: 19px; padding: 0px; }}
    QPushButton#SendBtn:hover {{ background: {C['primary_dark']}; }}
    QPushButton#SendBtn:disabled {{ background: {C['disabled_primary']}; }}
    QPushButton#Suggest {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 13px;
                          padding: 10px 14px; color: {C['text2']}; font-size: 12px; font-weight: 600;
                          text-align: left; }}
    QPushButton#Suggest:hover {{ background: {C['primary_soft']}; border-color: {C['primary_border']};
                                color: {C['primary']}; }}
    """


# ---------------------------------------------------------------- icons (Lucide-style)
_ICONS = {
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "home": '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "alert": '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "cap": '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M15.5 13 17 22l-5-3-5 3 1.5-9"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    "calc": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8"/><path d="M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h4"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/>',
    "star": '<path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    "message": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "sparkles": '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/>',
}


def icon_pixmap(name: str, color: str = "#0F172A", size: int = 20, stroke: float = 2.0) -> QPixmap:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{_ICONS[name]}</svg>')
    ratio = 2
    pm = QPixmap(size * ratio, size * ratio)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def icon(name: str, color: str = "#0F172A", size: int = 20) -> QIcon:
    return QIcon(icon_pixmap(name, color, size))


def shadow(w: QWidget, blur=28, y=6, alpha=22):
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(blur)
    eff.setOffset(0, y)
    eff.setColor(QColor(15, 23, 42, alpha))
    w.setGraphicsEffect(eff)


def label(text="", obj=None, size=None, weight=None, color=None, wrap=False) -> QLabel:
    lb = QLabel(text)
    if obj:
        lb.setObjectName(obj)
    css = []
    if size:
        css.append(f"font-size:{size}px")
    if weight:
        css.append(f"font-weight:{weight}")
    if color:
        css.append(f"color:{color}")
    if css:
        lb.setStyleSheet(";".join(css) + ";")
    lb.setWordWrap(wrap)
    return lb


class Card(QFrame):
    def __init__(self, parent=None, pad=22, spacing=14, with_shadow=True):
        super().__init__(parent)
        self.setObjectName("Card")
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(pad, pad, pad, pad)
        self.lay.setSpacing(spacing)
        if with_shadow:
            shadow(self)


class IconTile(QLabel):
    def __init__(self, name, color, bg, size=44, isize=22, radius=12):
        super().__init__()
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setPixmap(icon_pixmap(name, color, isize))
        self.setStyleSheet(f"background:{bg}; border-radius:{radius}px;")


def chip(text, fg, bg, size=12, bold=600, pad="4px 10px", icon_name=None) -> QLabel:
    lb = QLabel(text)
    lb.setStyleSheet(f"background:{bg}; color:{fg}; border-radius:10px; padding:{pad}; font-size:{size}px; font-weight:{bold};")
    lb.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    return lb


def tint(color: str, alpha: int) -> str:
    """Màu nhấn mờ (alpha 0-255) để làm nền cảnh báo trong cả theme sáng và tối."""
    c = QColor(color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"


class SoftRow(QFrame):
    """Khối nền mềm, tự vẽ theo theme hiện tại (không dùng QSS tĩnh nên không bị lệch màu).

    accent=None  -> nền surface2 + viền mảnh (khối trung tính)
    accent=color -> nền pha màu nhấn rất nhẹ + viền nhấn, tuỳ chọn thanh nhấn bên trái.
    Quan trọng: đặt style bằng QSS lên QFrame mà thiếu selector sẽ làm border/background
    rò xuống mọi widget con (QLabel, QTextBrowser) tạo các ô vuông lồng nhau.
    """

    def __init__(self, accent=None, radius=14, fill=34, bar=False, parent=None):
        super().__init__(parent)
        self._accent = accent
        self._radius = radius
        self._fill = fill
        self._bar = bar
        self.setAttribute(Qt.WA_StyledBackground, False)

    def set_accent(self, color):
        self._accent = color
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._accent:
            bg = QColor(self._accent)
            bg.setAlpha(self._fill if THEME == "dark" else max(16, self._fill - 10))
            border = QColor(self._accent)
            border.setAlpha(72 if THEME == "dark" else 56)
        else:
            bg = QColor(C["surface2"])
            border = QColor(C["border"])
        p.setPen(QPen(border, 1))
        p.setBrush(bg)
        p.drawRoundedRect(r, self._radius, self._radius)
        if self._accent and self._bar:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(self._accent))
            p.drawRoundedRect(QRectF(r.left() + 1.5, r.top() + 11, 3.5, max(6.0, r.height() - 22)), 1.75, 1.75)


class FlowLayout(QLayout):
    def __init__(self, parent=None, spacing=8):
        super().__init__(parent)
        self._items = []
        self._sp = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return self._do(QRect(0, 0, w, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        return s

    def clear(self):
        while self._items:
            it = self._items.pop()
            if it.widget():
                it.widget().hide()
                it.widget().deleteLater()

    def _do(self, rect, test):
        x, y, line_h = rect.x(), rect.y(), 0
        for it in self._items:
            hint = it.sizeHint()
            nx = x + hint.width() + self._sp
            if nx - self._sp > rect.right() and line_h > 0:
                x = rect.x()
                y += line_h + self._sp
                nx = x + hint.width() + self._sp
                line_h = 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), hint))
            x = nx
            line_h = max(line_h, hint.height())
        return y + line_h - rect.y()


class ChipColumn(QVBoxLayout):
    def __init__(self, parent=None, spacing=6):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(spacing)

    def addWidget(self, w):
        super().addWidget(w, 0, Qt.AlignLeft)

    def clear(self):
        while self.count():
            it = self.takeAt(0)
            if it.widget():
                it.widget().hide()
                it.widget().deleteLater()


class Ring(QWidget):
    """Vong tien do."""

    def __init__(self, size=118, width=12, color_a=None, color_b=None):
        super().__init__()
        self.setFixedSize(size, size)
        self._w = width
        self.value = 0.0
        self.center_text = "0%"
        self.sub_text = ""
        self.ca = QColor(color_a or C["primary"])
        self.cb = QColor(color_b or "#7C8BFF")

    def set(self, frac, text, sub=""):
        self.value = max(0.0, min(1.0, frac))
        self.center_text = text
        self.sub_text = sub
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self._w / 2 + 1, self._w / 2 + 1, self.width() - self._w - 2, self.height() - self._w - 2)
        p.setPen(QPen(QColor(C["track"]), self._w, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(r, 0, 360 * 16)
        if self.value > 0:
            g = QLinearGradient(r.topLeft(), r.bottomRight())
            g.setColorAt(0, self.ca)
            g.setColorAt(1, self.cb)
            p.setPen(QPen(QBrush(g), self._w, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(r, 90 * 16, int(-self.value * 360 * 16))
        p.setPen(QColor(C["text"]))
        f = QFont(FONT_FAMILY, 15)
        f.setWeight(QFont.ExtraBold)
        p.setFont(f)
        tr = QRectF(self.rect()).adjusted(0, -8 if self.sub_text else 0, 0, -8 if self.sub_text else 0)
        p.drawText(tr, Qt.AlignCenter, self.center_text)
        if self.sub_text:
            f2 = QFont(FONT_FAMILY, 8)
            p.setFont(f2)
            p.setPen(QColor(C["muted"]))
            p.drawText(QRectF(self.rect()).adjusted(0, 22, 0, 22), Qt.AlignCenter, self.sub_text)


class GpaChart(QWidget):
    """Cot GPA hoc ky (he 4) + duong CPA tich luy."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.gpa = [None] * 9
        self.cpa = [None] * 9

    def set_data(self, gpa, cpa):
        self.gpa, self.cpa = gpa, cpa
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        left, right, top, bottom = 40, 16, 22, 34
        cw, ch = W - left - right, H - top - bottom
        small = QFont(FONT_FAMILY, 8)
        p.setFont(small)
        for i in range(5):
            y = top + ch - ch * i / 4
            p.setPen(QPen(QColor(C["grid"]), 1, Qt.DashLine if i else Qt.SolidLine))
            p.drawLine(QPointF(left, y), QPointF(W - right, y))
            p.setPen(QColor(C["faint"]))
            p.drawText(QRectF(0, y - 8, left - 8, 16), Qt.AlignRight | Qt.AlignVCenter, f"{i:.1f}")
        n = len(self.gpa)
        slot = cw / n
        bw = min(34.0, slot * 0.5)
        pts = []
        for i, v in enumerate(self.gpa):
            cx = left + slot * i + slot / 2
            p.setPen(QColor(C["muted"]))
            p.setFont(small)
            p.drawText(QRectF(cx - slot / 2, H - bottom + 8, slot, 18), Qt.AlignCenter, f"HK{i + 1}")
            if v is not None:
                h = ch * v / 4
                rect = QRectF(cx - bw / 2, top + ch - h, bw, h)
                g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                g.setColorAt(0, QColor(C["primary"]))
                g.setColorAt(1, QColor("#8E9BFF"))
                path = QPainterPath()
                path.addRoundedRect(rect, 7, 7)
                p.fillPath(path, g)
                p.setPen(QColor(C["text2"]))
                fb = QFont(FONT_FAMILY, 8)
                fb.setBold(True)
                p.setFont(fb)
                p.drawText(QRectF(cx - 30, rect.top() - 18, 60, 16), Qt.AlignCenter, f"{v:.2f}")
            else:
                rect = QRectF(cx - bw / 2, top + ch - 6, bw, 6)
                path = QPainterPath()
                path.addRoundedRect(rect, 3, 3)
                p.fillPath(path, QColor(C["track"]))
            c = self.cpa[i] if i < len(self.cpa) else None
            if c is not None:
                pts.append(QPointF(cx, top + ch - ch * c / 4))
        if len(pts) >= 2:
            p.setPen(QPen(QColor(C["amber"]), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            path = QPainterPath(pts[0])
            for pt in pts[1:]:
                path.lineTo(pt)
            p.drawPath(path)
        for pt in pts:
            p.setPen(QPen(QColor(C["amber"]), 3))
            p.setBrush(QColor(C["surface"]))
            p.drawEllipse(pt, 5, 5)


class StatusDelegate(QStyledItemDelegate):
    @staticmethod
    def styles():
        return {
            "Đạt": (C["green"], C["green_soft"]),
            "Không đạt": (C["red"], C["red_soft"]),
            "Chưa nhập": (C["muted"], C["chip"]),
            "Bị khóa": (C["amber"], C["amber_soft"]),
            "Tự chọn": (C["violet"], C["violet_soft"]),
            "Bắt buộc": (C["primary"], C["primary_soft"]),
        }

    def paint(self, painter, option, index):
        text = index.data() or ""
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(C["primary_soft"]))
        fg, bg = self.styles().get(text, (C["text2"], C["chip"]))
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        f = QFont(FONT_FAMILY, 8)
        f.setBold(True)
        painter.setFont(f)
        tw = painter.fontMetrics().horizontalAdvance(text) + 22
        r = QRectF(option.rect.x() + 6, option.rect.center().y() - 12, tw, 24)
        path = QPainterPath()
        path.addRoundedRect(r, 12, 12)
        painter.fillPath(path, QColor(bg))
        painter.setPen(QColor(fg))
        painter.drawText(r, Qt.AlignCenter, text)
        painter.restore()


class Toast(QFrame):
    """Thông báo nổi: tự ẩn sau 7 giây, có nút ×, tạm dừng khi rê chuột."""

    WIDTH = 392

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_Hover, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 10, 12)
        lay.setSpacing(10)
        self.ic = QLabel()
        self.ic.setFixedSize(22, 22)
        self.txt = QLabel()
        self.txt.setWordWrap(True)
        self.txt.setTextFormat(Qt.PlainText)
        self.txt.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600; background: transparent;")
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setToolTip("Đóng thông báo")
        self.close_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.14); color:#E8ECF7; border:none; border-radius:13px;"
            " font-size:14px; font-weight:800; padding:0; }"
            "QPushButton:hover { background: rgba(255,255,255,0.28); color:white; }")
        self.close_btn.clicked.connect(self.hide_now)
        lay.addWidget(self.ic, 0, Qt.AlignTop)
        lay.addWidget(self.txt, 1)
        lay.addWidget(self.close_btn, 0, Qt.AlignTop)
        self.setFixedWidth(self.WIDTH)
        shadow(self, 38, 8, 55)
        self.hide()
        self._timer = QTimer(self, singleShot=True, timeout=self.hide_now)
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self._after_anim)
        self._closing = False
        self._text = ""

    def show_message(self, text, kind="success"):
        colors = {"success": (C["green"], "check"), "error": (C["red"], "x"), "info": (C["primary"], "bell"),
                  "warning": (C["amber"], "alert")}
        col, ic = colors.get(kind, colors["info"])
        self.setStyleSheet(f"#Toast {{ background: {C['navy']}; border-radius: 14px; border-left: 5px solid {col}; }}")
        self.ic.setPixmap(icon_pixmap(ic, col, 22))
        self._text = text
        self.txt.setText(text)
        self._closing = False
        self._anim.stop()
        self.txt.setFixedWidth(self.WIDTH - 14 - 10 - 22 - 10 - 26 - 10)
        self.txt.setFixedHeight(max(18, self.txt.heightForWidth(self.txt.width())))
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._timer.start(7000)

    def reposition(self):
        par = self.parentWidget()
        if not par:
            return
        self.adjustSize()
        x = max(12, par.width() - self.width() - 26)
        y = max(64, par.height() - self.height() - 108)
        self.move(x, y)

    def hide_now(self, immediate=False):
        """Đóng thông báo ngay (immediate=True) hoặc trượt xuống rồi ẩn."""
        if not self.isVisible():
            return
        self._timer.stop()
        if immediate:
            self._closing = False
            self._anim.stop()
            self.hide()
            return
        self._closing = True
        self._anim.stop()
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(QPoint(self.x(), self.y() + 18))
        self._anim.start()

    def _after_anim(self):
        if self._closing:
            self._closing = False
            self.hide()

    def enterEvent(self, e):
        self._timer.stop()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self.isVisible() and not self._closing:
            self._timer.start(2500)
        super().leaveEvent(e)


class SegmentedTabBar(QTabBar):
    """Tab bar dạng segmented control: viên thuốc bo tròn trên nền chip, không đường kẻ.

    Chiều cao trong sizeHint() phải khớp tabSizeHint()/minimumHeight; nếu lệch,
    QTabWidget sẽ đặt pane chồng lên thanh tab và nội dung bị đè (lỗi giao diện cũ).
    """

    H = 44

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setUsesScrollButtons(False)
        self.setMouseTracking(True)
        self.setElideMode(Qt.ElideNone)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMinimumHeight(self.H)
        self._hover = -1

    def tabSizeHint(self, i):
        f = QFont(self.font())
        f.setBold(True)
        fm = QFontMetrics(f)
        return QSize(fm.horizontalAdvance(self.tabText(i)) + 36, self.H - 8)

    def minimumTabSizeHint(self, i):
        return self.tabSizeHint(i)

    def sizeHint(self):
        total = sum(self.tabSizeHint(i).width() for i in range(self.count()))
        return QSize(total + 10, self.H)

    def minimumSizeHint(self):
        return QSize(self.sizeHint().width(), self.H)

    def mouseMoveEvent(self, e):
        idx = self.tabAt(e.position().toPoint())
        if idx != self._hover:
            self._hover = idx
            self.update()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        if self._hover != -1:
            self._hover = -1
            self.update()
        super().leaveEvent(e)

    def paintEvent(self, _e):
        n = self.count()
        if not n:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        widths = [self.tabSizeHint(i).width() for i in range(n)]
        total = sum(widths)
        h = self.height()
        p.setPen(QPen(QColor(C["border"]), 1))
        p.setBrush(QColor(C["chip"]))
        p.drawRoundedRect(QRectF(0.5, 0.5, total + 9, h - 1), 14, 14)
        f = QFont(self.font())
        f.setBold(True)
        p.setFont(f)
        x = 5.0
        for i, w in enumerate(widths):
            r = QRectF(x, 4, w, h - 8)
            if i == self.currentIndex():
                p.setPen(QPen(QColor(C["border"]), 1))
                p.setBrush(QColor(C["surface"]))
                p.drawRoundedRect(r, 10, 10)
                p.setPen(QColor(C["primary"]))
            elif i == self._hover:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(C["surface2"]))
                p.drawRoundedRect(r, 10, 10)
                p.setPen(QColor(C["text2"]))
            else:
                p.setPen(QColor(C["muted"]))
            p.drawText(r, Qt.AlignCenter, self.tabText(i))
            x += w


class MessageDialog(QDialog):
    @staticmethod
    def kinds():
        return {
            "error": ("x", C["red"], C["red_soft"]),
            "warning": ("lock", C["amber"], C["amber_soft"]),
            "success": ("award", C["green"], C["green_soft"]),
            "info": ("bell", C["primary"], C["primary_soft"]),
            "confirm": ("alert", C["red"], C["red_soft"]),
        }

    def __init__(self, parent, title, message, items=None, kind="info", ok_text="Đã hiểu", cancel_text=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 30, 30, 30)
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(f"#Card {{ background: {C['surface']}; border-radius: 22px; border: 1px solid {C['border']}; }}")
        shadow(card, 60, 16, 70)
        outer.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(30, 28, 30, 24)
        lay.setSpacing(14)
        kinds = self.kinds()
        ic, col, bg = kinds.get(kind, kinds["info"])
        tile = IconTile(ic, col, bg, 56, 28, 28)
        lay.addWidget(tile, 0, Qt.AlignLeft)
        lay.addWidget(label(title, size=19, weight=800, wrap=True))
        msg = label(message, size=13, color=C["text2"], wrap=True)
        lay.addWidget(msg)
        if items:
            box = QFrame()
            box.setObjectName("DlgItems")
            box.setStyleSheet(f"QFrame#DlgItems {{ background:{bg}; border-radius:12px; }}"
                              "QFrame#DlgItems QLabel { background: transparent; }")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(14, 12, 14, 12)
            bl.setSpacing(6)
            for it in items[:14]:
                row = QHBoxLayout()
                dot = QLabel()
                dot.setFixedSize(7, 7)
                dot.setStyleSheet(f"background:{col}; border-radius:3px;")
                row.addWidget(dot, 0, Qt.AlignTop | Qt.AlignHCenter)
                row.itemAt(0).widget().setContentsMargins(0, 6, 0, 0)
                row.addWidget(label(it, size=13, color=C["text"], wrap=True), 1)
                bl.addLayout(row)
            if len(items) > 14:
                bl.addWidget(label(f"… và {len(items) - 14} học phần khác", size=12, color=C["muted"]))
            lay.addWidget(box)
        btns = QHBoxLayout()
        btns.addStretch(1)
        if cancel_text:
            cb = QPushButton(cancel_text)
            cb.setObjectName("Ghost")
            cb.setCursor(Qt.PointingHandCursor)
            cb.clicked.connect(self.reject)
            btns.addWidget(cb)
        ok = QPushButton(ok_text)
        ok.setObjectName("Primary")
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        ok.setDefault(True)
        btns.addWidget(ok)
        lay.addLayout(btns)
        self.setFixedWidth(520)

    @staticmethod
    def show_msg(parent, title, message, items=None, kind="info"):
        return MessageDialog(parent, title, message, items, kind).exec()

    @staticmethod
    def confirm(parent, title, message, ok_text="Xác nhận"):
        d = MessageDialog(parent, title, message, None, "confirm", ok_text, "Huỷ")
        return d.exec() == QDialog.Accepted


class Clickable(QFrame):
    clicked = Signal()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)
