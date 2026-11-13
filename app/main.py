"""Phan mem Quan ly Hoc phan - Nganh Tin hoc Xay dung (DUT)."""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QEvent, QPointF, QPropertyAnimation, QRegularExpression, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QIcon, QImage, QLinearGradient, QPen, QPainter, QPainterPath, QPixmap,
                           QRegularExpressionValidator, QRadialGradient)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QBoxLayout, QButtonGroup, QFileDialog, QFrame, QGridLayout,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QProgressBar, QPushButton,
                               QGraphicsOpacityEffect, QMenu, QScrollArea, QSizePolicy, QStackedWidget, QSystemTrayIcon,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

import core
import ai_engine
from ai_page import AIPage, ChatSession, FloatingChatBubble
from automation import AutomationEngine, ReminderStore
from core import COURSE_BY_ID, COURSES, PROGRAM, SEMESTERS, GradeBook, fmt_credits, letter_of, total_score
from ui_kit import (FONT_FAMILY, C, apply_theme, Card, ChipColumn, Clickable, GpaChart, IconTile, MessageDialog, Ring, StatusDelegate, Toast,
                    chip, icon, icon_pixmap, label, load_fonts, qss, resource_path, shadow)

APP_NAME = "BK Tin học Xây dựng"
APP_VERSION = "2.0.6 AI"
MEMBERS = ["Đặng Duy Khang", "Trần Bảo Khang", "Đỗ Chí Kiên", "Đỗ Công Tuấn Anh"]
UNIVERSITY = "TRƯỜNG ĐẠI HỌC BÁCH KHOA ĐÀ NẴNG"
FACULTY = "KHOA XÂY DỰNG"
CLASS_LINE = "LỚP 26THXD1 – NGÀNH HỌC TIN HỌC XÂY DỰNG"
ADVISOR = "Nguyễn Thanh Hải"
BUILD_DATE = "11/11/2026"
LOGO = resource_path("assets/logo_dut.png")
LOGO_BADGE = resource_path("assets/logo_badge.png")
MEMBER_PHOTOS = [resource_path(f"assets/members/{n}.jpg") for n in ("m1", "m3", "m4", "m2")]
ADVISOR_PHOTO = resource_path("assets/members/advisor.jpg")
COVER_IMAGE = resource_path("assets/cover_banner.jpg")


def course_names(ids):
    if "ALL" in ids:
        return ["Tất cả học phần (trừ ĐATN)"]
    return [COURSE_BY_ID[i]["name"] for i in ids]


def fmt(v, nd=2, dash="—"):
    return dash if v is None else f"{v:.{nd}f}"


def scroll_page(inner: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.NoFrame)
    sa.setWidget(inner)
    inner.setObjectName("Content")
    return sa


def page_header(title, sub, right=None):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    v = QVBoxLayout()
    v.setSpacing(4)
    v.addWidget(label(title, "PageTitle"))
    v.addWidget(label(sub, "PageSub"))
    h.addLayout(v, 1)
    if right:
        for r in right:
            h.addWidget(r, 0, Qt.AlignBottom)
    return w


def ui_font(px, weight=QFont.Normal):
    f = QFont(FONT_FAMILY)
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


class LogoBadge(QWidget):
    def __init__(self, size=56, radius=16, pad=None, ring=None):
        super().__init__()
        self.setFixedSize(size, size)
        self.radius = radius
        self.pad = round(size * 0.075) if pad is None else pad
        self.ring = ring or C["yellow"]
        self._img = QImage(LOGO_BADGE)
        self._cache = None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, self.radius, self.radius)
        p.fillPath(path, QColor("white"))
        dpr = self.devicePixelRatioF()
        inner = self.width() - 2 * self.pad
        px = max(1, round(inner * dpr))
        if not self._img.isNull():
            if self._cache is None or self._cache[0] != px:
                pm = QPixmap.fromImage(self._img.scaled(px, px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                pm.setDevicePixelRatio(dpr)
                self._cache = (px, pm)
            p.save()
            p.setClipPath(path)
            p.drawPixmap(QPointF(self.pad, self.pad), self._cache[1])
            p.restore()
        bw = max(1.5, self.width() / 36)
        p.setPen(QPen(QColor(self.ring), bw))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r.adjusted(bw / 2, bw / 2, -bw / 2, -bw / 2), self.radius - bw / 2, self.radius - bw / 2)


def logo_tile(size=64, radius=16, pad=None):
    return LogoBadge(size, radius, pad)


def round_avatar(path, size, ring="#FFD60A", ring_w=3, dpr=1.0):
    px = max(1, round(size * dpr))
    out = QPixmap(px, px)
    out.fill(Qt.transparent)
    img = QImage(path)
    p = QPainter(out)
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(ring))
    p.drawEllipse(QRectF(0, 0, px, px))
    rw = ring_w * dpr
    inner = QRectF(rw, rw, px - 2 * rw, px - 2 * rw)
    if not img.isNull():
        sc = img.scaled(int(inner.width()) + 1, int(inner.height()) + 1, Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation)
        clip = QPainterPath()
        clip.addEllipse(inner)
        p.setClipPath(clip)
        p.drawImage(QPointF(inner.x() + (inner.width() - sc.width()) / 2, inner.y() + (inner.height() - sc.height()) / 2), sc)
    p.end()
    out.setDevicePixelRatio(dpr)
    return out


class AdvisorCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        shadow(self, 30, 8, 16)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        lay.setSpacing(20)
        av = QLabel()
        av.setStyleSheet("background: transparent;")
        av.setPixmap(round_avatar(ADVISOR_PHOTO, 96, C["yellow"], 4, self.devicePixelRatioF()))
        av.setFixedSize(96, 96)
        lay.addWidget(av, 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(chip("GIẢNG VIÊN HƯỚNG DẪN", C["navy"], C["yellow"], 11, 800, "4px 12px"), 0, Qt.AlignLeft)
        col.addWidget(label(ADVISOR, "CardTitle", size=22, weight=800))
        col.addWidget(label(f"{FACULTY}  •  {UNIVERSITY}", "Muted"))
        lay.addLayout(col, 1)


class MemberCard(QWidget):
    BANNER = 78
    AV = 40

    def __init__(self, idx, name, ca, cb, photo=None):
        super().__init__()
        self._photo = QImage(photo) if photo else QImage()
        self._pcache = None
        self.idx, self.name, self.ca, self.cb = idx, name, ca, cb
        words = name.split()
        self.initials = (words[-2][0] + words[-1][0]).upper()
        self._hover = False
        self.f_ini = ui_font(22, QFont.ExtraBold)
        self.f_name = ui_font(16, QFont.Bold)
        self.f_sub = ui_font(12)
        self.f_role = ui_font(12, QFont.Bold)
        self.name_h = QFontMetrics(self.f_name).height() + 2
        self.sub_h = QFontMetrics(self.f_sub).height()
        self.role_h = QFontMetrics(self.f_role).height() + 10
        h = self.BANNER + self.AV + 5 + 14 + self.name_h + 2 + self.sub_h + 12 + self.role_h + 20
        self.setFixedHeight(int(h))
        self.setMinimumWidth(190)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_Hover)
        shadow(self, 30, 8, 16)

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(r, 18, 18)
        p.fillPath(path, QColor(C["surface"]))
        p.save()
        p.setClipPath(path)
        band = QRectF(r.left(), r.top(), r.width(), self.BANNER)
        g = QLinearGradient(band.topLeft(), band.bottomRight())
        g.setColorAt(0, QColor(self.ca))
        g.setColorAt(1, QColor(self.cb))
        p.fillRect(band, g)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 38))
        p.drawEllipse(QRectF(band.right() - 74, band.top() - 46, 128, 128))
        p.setBrush(QColor(255, 255, 255, 24))
        p.drawEllipse(QRectF(band.left() - 34, band.bottom() - 40, 86, 86))
        p.setBrush(QColor(255, 255, 255, 60))
        for k in range(4):
            p.drawEllipse(QRectF(band.left() + 16 + k * 10, band.top() + 14, 4, 4))
        p.restore()
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(self.ca) if self._hover else QColor(C["border"]), 1.6 if self._hover else 1))
        p.drawPath(path)

        cx, cy = r.center().x(), r.top() + self.BANNER
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(15, 23, 42, 22))
        p.drawEllipse(QPointF(cx, cy + 3), self.AV + 6, self.AV + 6)
        p.setBrush(QColor(C["surface"]))
        p.drawEllipse(QPointF(cx, cy), self.AV + 5, self.AV + 5)
        ga = QLinearGradient(cx - self.AV, cy - self.AV, cx + self.AV, cy + self.AV)
        ga.setColorAt(0, QColor(self.ca))
        ga.setColorAt(1, QColor(self.cb))
        p.setBrush(ga)
        p.drawEllipse(QPointF(cx, cy), self.AV, self.AV)
        if not self._photo.isNull():
            r_in = self.AV - 3
            dpr = self.devicePixelRatioF()
            px = max(1, round(2 * r_in * dpr))
            if self._pcache is None or self._pcache[0] != px:
                pm = QPixmap.fromImage(self._photo.scaled(px, px, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                pm.setDevicePixelRatio(dpr)
                self._pcache = (px, pm)
            clip = QPainterPath()
            clip.addEllipse(QPointF(cx, cy), r_in, r_in)
            p.save()
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.setClipPath(clip)
            p.drawPixmap(QPointF(cx - r_in, cy - r_in), self._pcache[1])
            p.restore()
        else:
            p.setPen(QColor("white"))
            p.setFont(self.f_ini)
            p.drawText(QRectF(cx - self.AV, cy - self.AV, 2 * self.AV, 2 * self.AV), Qt.AlignCenter, self.initials)

        y = cy + self.AV + 5 + 14
        tw = r.width() - 24
        p.setPen(QColor(C["text"]))
        p.setFont(self.f_name)
        nm = QFontMetrics(self.f_name).elidedText(self.name, Qt.ElideRight, int(tw))
        p.drawText(QRectF(r.left() + 12, y, tw, self.name_h), Qt.AlignCenter, nm)
        y += self.name_h + 2
        p.setPen(QColor(C["muted"]))
        p.setFont(self.f_sub)
        p.drawText(QRectF(r.left() + 12, y, tw, self.sub_h), Qt.AlignCenter, "Sinh viên lớp 26THXD1")
        y += self.sub_h + 12
        role = f"Thành viên {self.idx:02d}"
        rw = QFontMetrics(self.f_role).horizontalAdvance(role) + 26
        pill = QRectF(cx - rw / 2, y, rw, self.role_h)
        bg = QColor(self.ca)
        bg.setAlpha(26)
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(pill, self.role_h / 2, self.role_h / 2)
        p.setPen(QColor(self.ca))
        p.setFont(self.f_role)
        p.drawText(pill, Qt.AlignCenter, role)


# ====================================================================== Intro
class Hero(QWidget):
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, 26, 26)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#0A1240"))
        g.setColorAt(0.55, QColor("#1427B8"))
        g.setColorAt(1, QColor("#2E4BFF"))
        p.fillPath(path, g)
        p.setClipPath(path)
        rg = QRadialGradient(r.right() - 120, r.top() + 40, 260)
        rg.setColorAt(0, QColor(255, 214, 10, 120))
        rg.setColorAt(1, QColor(255, 214, 10, 0))
        p.fillRect(r, rg)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawEllipse(QRectF(r.right() - 330, r.bottom() - 170, 380, 380))
        p.setBrush(QColor(255, 255, 255, 12))
        p.drawEllipse(QRectF(r.right() - 190, r.top() - 120, 300, 300))
        p.setBrush(QColor(255, 214, 10, 40))
        p.drawEllipse(QRectF(r.left() - 80, r.bottom() - 90, 180, 180))


class IntroPage(QWidget):
    start = Signal()

    def __init__(self):
        super().__init__()
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(24)

        hero = Hero()
        hero.setMinimumHeight(300)
        shadow(hero, 50, 14, 60)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(44, 36, 44, 36)
        hl.setSpacing(34)
        hl.addWidget(logo_tile(176, 30, 14), 0, Qt.AlignVCenter)
        tv = QVBoxLayout()
        tv.setSpacing(10)
        tv.addWidget(chip(f"{UNIVERSITY}  •  {FACULTY}", C["navy"], C["yellow"], 11, 800, "6px 14px"),
                     0, Qt.AlignLeft)
        t1 = label("Phần mềm Quản lý Học phần", size=36, weight=800, color="white")
        t2 = label(CLASS_LINE, size=22, weight=800, color=C["yellow"], wrap=True)
        t3 = label("Theo dõi chương trình đào tạo 9 học kỳ, nhập điểm, tính GPA học kỳ & điểm tích lũy, "
                   "kiểm soát ràng buộc học phần – tất cả trong một ứng dụng.", size=14, color="#D6DBFF", wrap=True)
        tv.addWidget(t1)
        tv.addWidget(t2)
        tv.addWidget(t3)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        for t in (f"Mã ngành {PROGRAM['code']}", f"{PROGRAM['total_credits']} tín chỉ", f"{len(SEMESTERS)} học kỳ",
                  f"{len(COURSES)} học phần", FACULTY):
            chips.addWidget(chip(t, "white", "rgba(255,255,255,0.14)", 12, 600, "6px 12px"))
        chips.addStretch(1)
        tv.addSpacing(6)
        tv.addLayout(chips)
        tv.addSpacing(8)
        btn = QPushButton("  Bắt đầu sử dụng")
        btn.setIcon(icon("arrow", C["navy"], 18))
        btn.setLayoutDirection(Qt.RightToLeft)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background:{C['yellow']}; color:{C['navy']}; border:none; border-radius:14px;"
                          f" padding:0px 28px; font-size:15px; font-weight:800; }} QPushButton:hover {{ background:#FFE45C; }}")
        btn.setFixedHeight(50)
        btn.setMinimumWidth(btn.sizeHint().width() + 12)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.clicked.connect(self.start.emit)
        tv.addWidget(btn, 0, Qt.AlignLeft)
        hl.addLayout(tv, 1)
        root.addWidget(hero)

        if ADVISOR:
            root.addWidget(AdvisorCard())

        # Thanh vien
        mem_card = Card(pad=26)
        hh = QHBoxLayout()
        hh.addWidget(IconTile("users", C["primary"], C["primary_soft"], 40, 20, 12))
        tt = QVBoxLayout()
        tt.setSpacing(0)
        tt.addWidget(label("Thành viên nhóm thực hiện", "CardTitle"))
        tt.addWidget(label(f"{CLASS_LINE}  •  {FACULTY}", "Muted"))
        hh.addLayout(tt, 1)
        mem_card.lay.addLayout(hh)
        grid = QHBoxLayout()
        grid.setSpacing(16)
        grads = [("#1F3BFF", "#7C8BFF"), ("#E5383B", "#FF8A5B"), ("#10B981", "#5EE6B5"), ("#7C3AED", "#C084FC")]
        for i, name in enumerate(MEMBERS):
            grid.addWidget(MemberCard(i + 1, name, *grads[i], MEMBER_PHOTOS[i]))
        mem_card.lay.addLayout(grid)
        root.addWidget(mem_card)

        # Tinh nang
        feats = QHBoxLayout()
        feats.setSpacing(12)
        data = [
            ("layers", C["primary"], C["primary_soft"], "Chương trình 9 học kỳ",
             "Tên học phần, số tín chỉ, cấu trúc giờ học và mô tả tóm tắt."),
            ("calc", C["green"], C["green_soft"], "Điểm 20% – 20% – 60%",
             "Nhập điểm Thành phần, Giữa kỳ, Cuối kỳ. Tự động quy đổi chữ & hệ 4."),
            ("chart", C["amber"], C["amber_soft"], "GPA & điểm tích lũy",
             "Điểm trung bình từng học kỳ, CPA tích lũy và xếp loại học lực."),
            ("lock", C["red"], C["red_soft"], "Ràng buộc học phần",
             "Không cho lưu điểm khi học phần học trước chưa đạt yêu cầu."),
            ("sparkles", C["violet"], C["violet_soft"], "Trợ lý AI & tự động hoá",
             "Cảnh báo học tập, kế hoạch học lại, nhắc giờ học và tư vấn AI online."),
        ]
        for d in data:
            c = Card(pad=20, spacing=10)
            c.lay.addWidget(IconTile(d[0], d[1], d[2], 46, 22, 14))
            c.lay.addWidget(label(d[3], size=15, weight=700))
            c.lay.addWidget(label(d[4], size=12, color=C["muted"], wrap=True))
            c.lay.addStretch(1)
            feats.addWidget(c)
        root.addLayout(feats)
        root.addStretch(1)
        root.addWidget(label(f"© 2026 Nhóm thực hiện – {UNIVERSITY} – {FACULTY}  •  Phiên bản {APP_VERSION}",
                             size=11, color=C["faint"]), 0, Qt.AlignCenter)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))


# ====================================================================== Dashboard
class StatCard(Card):
    def __init__(self, title, ic, col, bg):
        super().__init__(pad=20, spacing=6)
        top = QHBoxLayout()
        top.addWidget(label(title, size=13, weight=600, color=C["muted"]), 1)
        top.addWidget(IconTile(ic, col, bg, 40, 20, 12))
        self.lay.addLayout(top)
        self.value = label("—", "Value")
        self.sub = label("", "Muted", wrap=True)
        self.lay.addWidget(self.value)
        self.lay.addWidget(self.sub)
        self.lay.addStretch(1)

    def set(self, value, sub=""):
        self.value.setText(value)
        self.sub.setText(sub)


class SemesterTile(Clickable):
    def __init__(self, sem):
        super().__init__()
        self.sem = sem
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("Tile")
        self.setStyleSheet(f"#Tile {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:16px; }}"
                           f"#Tile:hover {{ border-color:{C['primary']}; }}")
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(8)
        h = QHBoxLayout()
        h.addWidget(label(f"Học kỳ {sem}", size=14, weight=700), 1)
        self.badge = chip("", C["muted"], C["chip"], 10, 700, "3px 8px")
        h.addWidget(self.badge)
        v.addLayout(h)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        v.addWidget(self.bar)
        self.info = label("", size=12, color=C["muted"])
        v.addWidget(self.info)

    def update_from(self, st, is_next):
        self.bar.setMaximum(st["n_plan"])
        self.bar.setValue(st["n_done"])
        gpa = f"GPA {fmt(st['gpa4'])}" if st["gpa4"] is not None else "Chưa có điểm"
        self.info.setText(f"{st['n_done']}/{st['n_plan']} HP  •  {fmt_credits(st['credits_plan'])} TC  •  {gpa}")
        if st["completed"]:
            txt, fg, bg = "Hoàn thành", C["green"], C["green_soft"]
        elif is_next:
            txt, fg, bg = "Kỳ tiếp theo", C["primary"], C["primary_soft"]
        elif st["n_graded"]:
            txt, fg, bg = "Đang học", C["amber"], C["amber_soft"]
        else:
            txt, fg, bg = "Chưa học", C["muted"], C["chip"]
        self.badge.setText(txt)
        self.badge.setStyleSheet(f"background:{bg}; color:{fg}; border-radius:9px; padding:3px 8px; font-size:10px; font-weight:700;")


class DashboardPage(QWidget):
    open_semester = Signal(int)

    def __init__(self, book: GradeBook):
        super().__init__()
        self.book = book
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(22)
        root.addWidget(page_header("Tổng quan học tập", "Kết quả tích lũy, điểm trung bình các học kỳ và thông báo mới nhất"))

        row = QGridLayout()
        row.setSpacing(18)
        self.stat_row = row
        self.c_cpa4 = StatCard("Điểm tích lũy (hệ 4)", "award", C["primary"], C["primary_soft"])
        self.c_cpa10 = StatCard("Điểm tích lũy (hệ 10)", "star", C["amber"], C["amber_soft"])
        self.c_next = StatCard("Học kỳ tiếp theo", "calendar", C["green"], C["green_soft"])
        ring_card = Card(pad=20, spacing=6)
        rh = QHBoxLayout()
        rv = QVBoxLayout()
        rv.addWidget(label("Tín chỉ tích lũy", size=13, weight=600, color=C["muted"]))
        self.cred_val = label("0", "Value")
        self.cred_sub = label("", "Muted", wrap=True)
        rv.addWidget(self.cred_val)
        rv.addWidget(self.cred_sub)
        rv.addStretch(1)
        rh.addLayout(rv, 1)
        self.ring = Ring(104, 11)
        rh.addWidget(self.ring)
        ring_card.lay.addLayout(rh)
        self.stat_cards = [self.c_cpa4, self.c_cpa10, ring_card, self.c_next]
        root.addLayout(row)

        row2 = QBoxLayout(QBoxLayout.LeftToRight)
        self.row2 = row2
        row2.setSpacing(18)
        chart_card = Card()
        ch = QHBoxLayout()
        cv = QVBoxLayout()
        cv.setSpacing(2)
        cv.addWidget(label("Điểm trung bình theo học kỳ", "CardTitle"))
        cv.addWidget(label("Cột: GPA học kỳ (hệ 4)  •  Đường: CPA tích lũy", "Muted"))
        ch.addLayout(cv, 1)
        ch.addWidget(chip("■ GPA", C["primary"], C["primary_soft"], 11, 700))
        ch.addWidget(chip("● CPA", C["amber"], C["amber_soft"], 11, 700))
        chart_card.lay.addLayout(ch)
        self.chart = GpaChart()
        chart_card.lay.addWidget(self.chart, 1)
        row2.addWidget(chart_card, 3)

        noti = Card()
        nh = QHBoxLayout()
        nh.addWidget(IconTile("bell", C["red"], C["red_soft"], 36, 18, 10))
        nh.addWidget(label("Thông báo", "CardTitle"), 1)
        noti.lay.addLayout(nh)
        self.noti_box = QVBoxLayout()
        self.noti_box.setSpacing(10)
        noti.lay.addLayout(self.noti_box)
        noti.lay.addStretch(1)
        self.noti_card = noti
        row2.addWidget(noti, 2)
        root.addLayout(row2)

        tiles_card = Card()
        tiles_card.lay.addWidget(label("Tiến độ 9 học kỳ", "CardTitle"))
        grid = QGridLayout()
        grid.setSpacing(14)
        self.tile_grid = grid
        self.tiles = []
        for s in SEMESTERS:
            t = SemesterTile(s)
            t.clicked.connect(lambda s=s: self.open_semester.emit(s))
            self.tiles.append(t)
        tiles_card.lay.addLayout(grid)
        self._wide = None
        self._reflow(True)
        root.addWidget(tiles_card)
        root.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))

    def _reflow(self, wide):
        if wide == self._wide:
            return
        self._wide = wide
        cols = 4 if wide else 2
        for i, w in enumerate(self.stat_cards):
            self.stat_row.addWidget(w, i // cols, i % cols)
        for c in range(4):
            self.stat_row.setColumnStretch(c, 1 if c < cols else 0)
        self.row2.setDirection(QBoxLayout.LeftToRight if wide else QBoxLayout.TopToBottom)
        self.noti_card.setMinimumWidth(380 if wide else 0)
        tcols = 5 if wide else 3
        for i, t in enumerate(self.tiles):
            self.tile_grid.addWidget(t, i // tcols, i % tcols)
        for c in range(5):
            self.tile_grid.setColumnStretch(c, 1 if c < tcols else 0)

    def resizeEvent(self, e):
        self._reflow(self.width() >= 1300)
        super().resizeEvent(e)

    def _noti(self, ic, col, bg, title, body):
        f = QFrame()
        f.setStyleSheet(f"QFrame#N {{ background:{bg}; border-radius:14px; }}")
        f.setObjectName("N")
        h = QHBoxLayout(f)
        h.setContentsMargins(14, 12, 14, 12)
        h.setSpacing(12)
        ic_l = QLabel()
        ic_l.setPixmap(icon_pixmap(ic, col, 20))
        h.addWidget(ic_l, 0, Qt.AlignTop)
        v = QVBoxLayout()
        v.setSpacing(3)
        v.addWidget(label(title, size=13, weight=700, color=C["text"], wrap=True))
        b = label(body, size=12, color=C["text2"], wrap=True)
        b.setTextFormat(Qt.RichText)
        v.addWidget(b)
        h.addLayout(v, 1)
        self.noti_box.addWidget(f)

    def refresh(self):
        b = self.book
        cum = b.cumulative()
        self.c_cpa4.set(fmt(cum["cpa4"]), f"Xếp loại: {cum['rank']}  •  {cum['n_courses']} học phần đạt")
        self.c_cpa10.set(fmt(cum["cpa10"]), "Trung bình có trọng số theo tín chỉ các học phần đã đạt")
        total = PROGRAM["total_credits"]
        self.cred_val.setText(fmt_credits(cum["credits"]))
        self.cred_sub.setText(f"trên tổng {total} tín chỉ toàn khóa")
        self.ring.set(cum["credits"] / total, f"{cum['credits'] / total * 100:.0f}%")
        info = b.next_semester_info()
        if info:
            st = info["stats"]
            sub = f"{fmt_credits(st['credits_plan'])} tín chỉ"
            if st["electives_needed"]:
                sub += f"  •  {st['n_required']} bắt buộc + {st['electives_needed']} tự chọn"
            self.c_next.set(f"HK{info['semester']}: {st['n_plan']} HP", sub)
        else:
            self.c_next.set("Hoàn thành", "Bạn đã hoàn tất toàn bộ chương trình")

        gpa = [b.semester_stats(s)["gpa4"] for s in SEMESTERS]
        cpa = []
        for s in SEMESTERS:
            st = b.semester_stats(s)
            cpa.append(b.cumulative(s)["cpa4"] if st["n_graded"] else None)
        self.chart.set_data(gpa, cpa)

        while self.noti_box.count():
            it = self.noti_box.takeAt(0)
            if it.widget():
                it.widget().hide()
                it.widget().deleteLater()
        last = b.last_completed_semester()
        if last:
            c = b.cumulative(last)
            st = b.semester_stats(last)
            self._noti("award", C["primary"], C["primary_soft"], f"Điểm tích lũy sau Học kỳ {last}",
                       f"GPA HK{last}: <b>{fmt(st['gpa4'])}</b> (hệ 10: {fmt(st['gpa10'])})<br>"
                       f"CPA tích lũy: <b>{fmt(c['cpa4'])}</b> / 4 • <b>{fmt(c['cpa10'])}</b> / 10<br>"
                       f"Tín chỉ tích lũy: <b>{fmt_credits(c['credits'])}</b> • Xếp loại: <b>{c['rank']}</b>")
        else:
            self._noti("info", C["primary"], C["primary_soft"], "Chưa có học kỳ nào hoàn thành",
                       "Nhập đủ điểm các học phần của Học kỳ 1 để xem điểm tích lũy.")
        if info:
            st = info["stats"]
            body = f"Học kỳ {info['semester']} có <b>{st['n_plan']} học phần</b> ({fmt_credits(st['credits_plan'])} tín chỉ)"
            if st["electives_needed"]:
                body += f", gồm {st['n_required']} bắt buộc và {st['electives_needed']} tự chọn (chọn trong {st['n_electives']})"
            body += f".<br>Đã nhập điểm: {st['n_done']}/{st['n_plan']}."
            if info["locked"]:
                names = ", ".join(c["name"] for c in info["locked"][:4])
                more = f" và {len(info['locked']) - 4} HP khác" if len(info["locked"]) > 4 else ""
                body += f"<br><span style='color:{C['red']}'>Bị khóa ({len(info['locked'])}): {names}{more}</span>"
            self._noti("calendar", C["green"], C["green_soft"], f"Học kỳ tiếp theo: Học kỳ {info['semester']}", body)
        failed = [c for c in COURSES if (r := b.result(c["id"])) and not r.passed]
        if failed:
            self._noti("alert", C["red"], C["red_soft"], f"{len(failed)} học phần không đạt",
                       "Cần học lại: " + ", ".join(f"{c['name']}" for c in failed[:5]) + (" …" if len(failed) > 5 else ""))
        nxt = b.next_semester()
        for t in self.tiles:
            t.update_from(b.semester_stats(t.sem), t.sem == nxt)


# ====================================================================== Courses
SCORE_RE = QRegularExpression(r"^$|^(10([.,]0{0,2})?|\d([.,]\d{0,2})?)$")


class ScoreField(QWidget):
    def __init__(self, title, weight, color):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        h = QHBoxLayout()
        h.addWidget(label(title, size=12, weight=700, color=C["text2"]), 1)
        h.addWidget(chip(weight, color, C["surface"], 10, 800, "2px 6px"))
        v.addLayout(h)
        self.edit = QLineEdit()
        self.edit.setObjectName("ScoreInput")
        self.edit.setPlaceholderText("0 – 10")
        self.edit.setValidator(QRegularExpressionValidator(SCORE_RE, self.edit))
        self.edit.setMinimumHeight(50)
        v.addWidget(self.edit)


class CourseDetail(QFrame):
    saved = Signal(int)

    def __init__(self, book: GradeBook, host):
        super().__init__()
        self.book = book
        self.host = host
        self.cid = None
        self.setObjectName("Card")
        shadow(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(sa)
        body = QWidget()
        sa.setWidget(body)
        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)
        self.empty = label("Chọn một học phần trong bảng để xem chi tiết và nhập điểm.", size=13, color=C["muted"], wrap=True)
        lay.addWidget(self.empty)

        self.content = QWidget()
        cl = QVBoxLayout(self.content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(14)
        lay.addWidget(self.content)
        lay.addStretch(1)

        self.tags = QHBoxLayout()
        self.tags.setSpacing(6)
        cl.addLayout(self.tags)
        self.name = label("", size=20, weight=800, wrap=True)
        cl.addWidget(self.name)
        self.meta = label("", size=12, color=C["muted"], wrap=True)
        cl.addWidget(self.meta)

        self.lock_banner = QFrame()
        self.lock_banner.setStyleSheet(f"background:{C['red_soft']}; border-radius:12px;")
        lbh = QHBoxLayout(self.lock_banner)
        lbh.setContentsMargins(12, 10, 12, 10)
        li = QLabel()
        li.setPixmap(icon_pixmap("lock", C["red"], 18))
        lbh.addWidget(li, 0, Qt.AlignTop)
        self.lock_text = label("", size=12, color=C["red"], wrap=True)
        self.lock_text.setStyleSheet(f"color:{C['red']}; font-size:12px; font-weight:600;")
        lbh.addWidget(self.lock_text, 1)
        cl.addWidget(self.lock_banner)

        # Nhap diem
        sc = QFrame()
        sc.setStyleSheet(f"QFrame#SC {{ background:{C['surface2']}; border:1px solid {C['border']}; border-radius:16px; }}")
        sc.setObjectName("SC")
        sl = QVBoxLayout(sc)
        sl.setContentsMargins(16, 14, 16, 16)
        sl.setSpacing(12)
        sl.addWidget(label("Nhập điểm học phần", size=14, weight=700))
        fr = QHBoxLayout()
        fr.setSpacing(10)
        self.f_tp = ScoreField("Thành phần", "20%", C["primary"])
        self.f_gk = ScoreField("Giữa kỳ", "20%", C["violet"])
        self.f_ck = ScoreField("Cuối kỳ", "60%", C["amber"])
        for f in (self.f_tp, self.f_gk, self.f_ck):
            fr.addWidget(f)
            f.edit.textChanged.connect(self.preview)
            f.edit.returnPressed.connect(self.do_save)
        sl.addLayout(fr)

        res = QFrame()
        res.setStyleSheet(f"background:{C['surface']}; border-radius:14px;")
        rl = QHBoxLayout(res)
        rl.setContentsMargins(16, 12, 16, 12)
        rv = QVBoxLayout()
        rv.setSpacing(0)
        rv.addWidget(label("Điểm tổng kết (hệ 10)", size=11, weight=600, color=C["muted"]))
        self.r_total = label("—", size=32, weight=800, color=C["primary"])
        rv.addWidget(self.r_total)
        rl.addLayout(rv, 1)
        gv = QVBoxLayout()
        gv.setSpacing(4)
        self.r_letter = label("—", size=22, weight=800)
        self.r_letter.setAlignment(Qt.AlignCenter)
        self.r_letter.setFixedSize(64, 46)
        gv.addWidget(self.r_letter, 0, Qt.AlignRight)
        self.r_g4 = label("Hệ 4: —", size=11, weight=600, color=C["muted"])
        gv.addWidget(self.r_g4, 0, Qt.AlignRight)
        rl.addLayout(gv)
        sl.addWidget(res)
        self.formula = label("Tổng = 0.2 × TP + 0.2 × GK + 0.6 × CK", size=11, color=C["muted"])
        sl.addWidget(self.formula)
        br = QHBoxLayout()
        self.b_del = QPushButton("  Xoá điểm")
        self.b_del.setObjectName("Danger")
        self.b_del.setIcon(icon("trash", C["red"], 16))
        self.b_del.setCursor(Qt.PointingHandCursor)
        self.b_del.clicked.connect(self.do_delete)
        self.b_save = QPushButton("  Lưu điểm")
        self.b_save.setObjectName("Primary")
        self.b_save.setIcon(icon("save", "white", 16))
        self.b_save.setCursor(Qt.PointingHandCursor)
        self.b_save.clicked.connect(self.do_save)
        br.addWidget(self.b_del)
        br.addStretch(1)
        br.addWidget(self.b_save)
        sl.addLayout(br)
        cl.addWidget(sc)

        # Rang buoc
        cl.addWidget(label("Ràng buộc học phần", size=14, weight=700))
        self.pre_title = label("Học trước", size=12, weight=700, color=C["text2"])
        cl.addWidget(self.pre_title)
        self.pre_wrap = QWidget()
        self.pre_flow = ChipColumn(self.pre_wrap, 6)
        cl.addWidget(self.pre_wrap)
        cl.addWidget(label("Song hành", size=12, weight=700, color=C["text2"]))
        self.co_wrap = QWidget()
        self.co_flow = ChipColumn(self.co_wrap, 6)
        cl.addWidget(self.co_wrap)
        cl.addWidget(label("Là điều kiện học trước của", size=12, weight=700, color=C["text2"]))
        self.dep_wrap = QWidget()
        self.dep_flow = ChipColumn(self.dep_wrap, 6)
        cl.addWidget(self.dep_wrap)

        cl.addWidget(label("Mô tả tóm tắt", size=14, weight=700))
        self.desc = label("", size=12, color=C["text2"], wrap=True)
        self.desc.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cl.addWidget(self.desc)
        self.content.hide()

    def _fill_flow(self, flow, items):
        flow.clear()
        if not items:
            flow.addWidget(chip("Không có", C["muted"], C["chip"], 11, 600))
        for text, fg, bg in items:
            lb = chip(text, fg, bg, 11, 600, "4px 10px")
            flow.addWidget(lb)

    def _status_chip(self, cid):
        r = self.book.result(cid)
        name = COURSE_BY_ID[cid]["name"]
        if r is None:
            return (f"○ {name}", C["muted"], C["chip"])
        if r.passed:
            return (f"✓ {name}  {r.total:.1f}", C["green"], C["green_soft"])
        return (f"✕ {name}  {r.total:.1f}", C["red"], C["red_soft"])

    def show_course(self, cid):
        self.cid = cid
        if cid is None:
            self.content.hide()
            self.empty.show()
            return
        self.empty.hide()
        self.content.show()
        c = COURSE_BY_ID[cid]
        while self.tags.count():
            it = self.tags.takeAt(0)
            if it.widget():
                it.widget().hide()
                it.widget().deleteLater()
        self.tags.addWidget(chip(f"Học kỳ {c['semester']}", C["primary"], C["primary_soft"], 11, 700))
        self.tags.addWidget(chip(f"{fmt_credits(c['credits'])} tín chỉ", C["amber"], C["amber_soft"], 11, 700))
        self.tags.addWidget(chip("Tự chọn" if c["elective"] else "Bắt buộc", C["violet"] if c["elective"] else C["green"],
                                 C["violet_soft"] if c["elective"] else C["green_soft"], 11, 700))
        self.tags.addStretch(1)
        self.name.setText(c["name"])
        parts = []
        for k, lbl in (("lt", "Lý thuyết"), ("da", "Đồ án"), ("pbl", "PBL"), ("th", "Thực hành/TN"), ("tt", "Thực tập")):
            if c["hours"][k]:
                parts.append(f"{lbl}: {c['hours'][k]} TC")
        self.meta.setText("Cấu trúc: " + ("  •  ".join(parts) if parts else "—"))
        unmet = self.book.unmet_prereqs(cid)
        self.lock_banner.setVisible(bool(unmet))
        if unmet:
            self.lock_text.setText("Học phần đang bị khóa – không thể lưu điểm cho đến khi đạt: " + "; ".join(unmet[:6])
                                   + (" …" if len(unmet) > 6 else ""))
        g = self.book.grades.get(cid)
        for f, k in ((self.f_tp, "tp"), (self.f_gk, "gk"), (self.f_ck, "ck")):
            f.edit.blockSignals(True)
            f.edit.setText("" if not g else f"{g[k]:g}")
            f.edit.blockSignals(False)
        self.b_del.setEnabled(bool(g))
        self.preview()
        if "ALL" in c["prereq"]:
            req = [x for x in self.book.prereq_ids(cid)]
            n_ok = sum(1 for x in req if self.book.is_passed(x))
            el = len(self.book.passed_electives())
            items = [(f"Đã đạt {n_ok}/{len(req)} học phần bắt buộc", C["green"] if n_ok == len(req) else C["red"],
                      C["green_soft"] if n_ok == len(req) else C["red_soft"]),
                     (f"Tự chọn đạt {el}/{PROGRAM['elective_required']}",
                      C["green"] if el >= PROGRAM["elective_required"] else C["red"],
                      C["green_soft"] if el >= PROGRAM["elective_required"] else C["red_soft"])]
        else:
            items = [self._status_chip(p) for p in c["prereq"]]
        self._fill_flow(self.pre_flow, items)
        self._fill_flow(self.co_flow, [self._status_chip(p) for p in c["coreq"]])
        deps = [d for d in self.book.dependents(cid) if "ALL" not in COURSE_BY_ID[d]["prereq"]]
        self._fill_flow(self.dep_flow, [(f"HK{COURSE_BY_ID[d]['semester']} • {COURSE_BY_ID[d]['name']}", C["primary"],
                                         C["primary_soft"]) for d in deps])
        self.desc.setText(c["desc"] or "—")

    def _values(self):
        return [f.edit.text() for f in (self.f_tp, self.f_gk, self.f_ck)]

    def preview(self):
        try:
            vals = [core.parse_score(v) for v in self._values()]
        except ValueError:
            vals = [None]
        if None in vals:
            self.r_total.setText("—")
            self.r_total.setStyleSheet(f"font-size:32px; font-weight:800; color:{C['faint']};")
            self.r_letter.setText("—")
            self.r_letter.setStyleSheet(f"background:{C['chip']}; color:{C['muted']}; border-radius:12px; font-size:22px; font-weight:800;")
            self.r_g4.setText("Hệ 4: —")
            return
        t = total_score(*vals)
        letter, g4 = letter_of(t)
        col, bg = (C["green"], C["green_soft"]) if t >= core.PASS_MARK else (C["red"], C["red_soft"])
        if t >= 8.5:
            col, bg = C["primary"], C["primary_soft"]
        self.r_total.setText(f"{t:.1f}")
        self.r_total.setStyleSheet(f"font-size:32px; font-weight:800; color:{col};")
        self.r_letter.setText(letter)
        self.r_letter.setStyleSheet(f"background:{bg}; color:{col}; border-radius:12px; font-size:22px; font-weight:800;")
        self.r_g4.setText(f"Hệ 4: {g4:.1f}  •  {'Đạt' if t >= core.PASS_MARK else 'Không đạt'}")

    def do_save(self):
        if self.cid is None:
            return
        cid = self.cid
        sem = COURSE_BY_ID[cid]["semester"]
        was_complete = self.book.semester_stats(sem)["completed"]
        res = self.book.save(cid, *self._values())
        if not res.ok:
            kind = "warning" if res.problems and "học trước" in res.message else "error"
            MessageDialog.show_msg(self.window(), "Không thể lưu điểm", res.message, res.problems, kind)
            return
        r = self.book.result(cid)
        self.host.toast(f"Đã lưu: {COURSE_BY_ID[cid]['name']} — {r.total:.1f} ({r.letter})", "success")
        self.saved.emit(cid)
        st = self.book.semester_stats(sem)
        if st["completed"] and not was_complete:
            self.host.announce_semester(sem)

    def do_delete(self):
        if self.cid is None:
            return
        chk = self.book.check_delete(self.cid)
        if not chk.ok:
            MessageDialog.show_msg(self.window(), "Không thể xoá điểm", chk.message, chk.problems, "error")
            return
        if not MessageDialog.confirm(self.window(), "Xoá điểm học phần?",
                                     f"Điểm của “{COURSE_BY_ID[self.cid]['name']}” sẽ bị xoá.", "Xoá điểm"):
            return
        res = self.book.delete(self.cid)
        if res.ok:
            self.host.toast("Đã xoá điểm học phần", "info")
            self.saved.emit(self.cid)
        else:
            MessageDialog.show_msg(self.window(), "Lỗi", res.message, res.problems, "error")


class CoursesPage(QWidget):
    changed = Signal()
    COLS = ["#", "Tên học phần", "TC", "Học trước", "TP", "GK", "CK", "Tổng", "Chữ", "Trạng thái"]

    def __init__(self, book: GradeBook, host):
        super().__init__()
        self.book = book
        self.host = host
        self.sem = 1
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 24)
        root.setSpacing(18)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm học phần trong toàn chương trình…")
        self.search.addAction(icon("search", C["muted"], 18), QLineEdit.LeadingPosition)
        self.search.setMinimumWidth(220)
        self.search.setMaximumWidth(340)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        root.addWidget(page_header("Học phần & Nhập điểm",
                                   "Chương trình đào tạo 9 học kỳ • Điểm tổng kết = 20% Thành phần + 20% Giữa kỳ + 60% Cuối kỳ",
                                   [self.search]))

        pills = QHBoxLayout()
        pills.setSpacing(8)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.pill_btns = {}
        for s in SEMESTERS:
            b = QPushButton(f"Học kỳ {s}")
            b.setObjectName("Pill")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, s=s: self.set_semester(s))
            self.group.addButton(b)
            pills.addWidget(b)
            self.pill_btns[s] = b
        pills.addStretch(1)
        root.addLayout(pills)

        strip = QHBoxLayout()
        strip.setSpacing(14)
        self.m_courses = self._metric("layers", C["primary"], C["primary_soft"], "Số học phần")
        self.m_credits = self._metric("book", C["amber"], C["amber_soft"], "Số tín chỉ")
        self.m_done = self._metric("check", C["green"], C["green_soft"], "Đã nhập điểm")
        self.m_gpa = self._metric("chart", C["violet"], C["violet_soft"], "GPA học kỳ (hệ 4 / hệ 10)")
        for m in (self.m_courses, self.m_credits, self.m_done, self.m_gpa):
            strip.addWidget(m[0], 1)
        root.addLayout(strip)

        body = QHBoxLayout()
        body.setSpacing(18)
        tcard = Card(pad=8, spacing=0)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setDefaultSectionSize(52)
        hh = self.table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hh.setHighlightSections(False)
        widths = [40, 0, 44, 150, 46, 46, 46, 56, 48, 112]
        for i, w in enumerate(widths):
            if i == 1:
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table.setColumnWidth(i, w)
        self.delegate = StatusDelegate(self.table)
        self.table.setItemDelegateForColumn(9, self.delegate)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.itemSelectionChanged.connect(self._on_select)
        tcard.lay.addWidget(self.table)
        body.addWidget(tcard, 1)
        self.detail = CourseDetail(book, host)
        self.detail.setFixedWidth(410)
        self._compact = None
        self.detail.saved.connect(lambda _cid: self.changed.emit())
        body.addWidget(self.detail)
        root.addLayout(body, 1)
        self.pill_btns[1].setChecked(True)

    def _metric(self, ic, col, bg, title):
        f = QFrame()
        f.setObjectName("Card")
        shadow(f, 20, 4, 14)
        h = QHBoxLayout(f)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(12)
        h.addWidget(IconTile(ic, col, bg, 40, 20, 12))
        v = QVBoxLayout()
        v.setSpacing(0)
        v.addWidget(label(title, size=11, weight=600, color=C["muted"]))
        val = label("—", size=20, weight=800)
        v.addWidget(val)
        h.addLayout(v, 1)
        return f, val

    def set_semester(self, s):
        self.sem = s
        self.pill_btns[s].setChecked(True)
        if self.search.text():
            self.search.blockSignals(True)
            self.search.clear()
            self.search.blockSignals(False)
        self.refresh(select_first=True)

    def current_courses(self):
        q = self.search.text().strip().lower()
        if q:
            return [c for c in COURSES if q in c["name"].lower()]
        return [c for c in COURSES if c["semester"] == self.sem]

    def refresh(self, *_, select_first=False):
        st = self.book.semester_stats(self.sem)
        searching = bool(self.search.text().strip())
        for b in self.pill_btns.values():
            b.setEnabled(True)
        if searching:
            self.group.setExclusive(False)
            for b in self.pill_btns.values():
                b.setChecked(False)
            self.group.setExclusive(True)
        else:
            self.pill_btns[self.sem].setChecked(True)
        plan = f"{st['n_plan']}"
        if st["electives_needed"]:
            plan += f"  ({st['n_required']} BB + {st['electives_needed']}/{st['n_electives']} TC)"
        self.m_courses[1].setText(plan)
        self.m_credits[1].setText(fmt_credits(st["credits_plan"]))
        self.m_done[1].setText(f"{st['n_done']} / {st['n_plan']}")
        self.m_gpa[1].setText(f"{fmt(st['gpa4'])}  /  {fmt(st['gpa10'])}")

        keep = self.detail.cid
        courses = self.current_courses()
        self.table.blockSignals(True)
        self.table.setRowCount(len(courses))
        sel_row = None
        for r, c in enumerate(courses):
            g = self.book.grades.get(c["id"])
            res = self.book.result(c["id"])
            if res is not None:
                status = "Đạt" if res.passed else "Không đạt"
            elif self.book.is_locked(c["id"]):
                status = "Bị khóa"
            else:
                status = "Chưa nhập"
            pre = ", ".join(course_names(c["prereq"])) or "—"
            co = ", ".join(course_names(c["coreq"]))
            idx = f"{r + 1}" if not searching else f"K{c['semester']}"
            vals = [idx, c["name"], fmt_credits(c["credits"]), pre,
                    f"{g['tp']:g}" if g else "", f"{g['gk']:g}" if g else "", f"{g['ck']:g}" if g else "",
                    f"{res.total:.1f}" if res else "", res.letter if res else "", status]
            for ci, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if ci == 0:
                    it.setData(Qt.UserRole, c["id"])
                    it.setForeground(QColor(C["faint"]))
                if ci == 1:
                    f = it.font()
                    f.setWeight(QFont.DemiBold)
                    it.setFont(f)
                    tip = [c["name"], f"{fmt_credits(c['credits'])} tín chỉ • " + ("Tự chọn" if c["elective"] else "Bắt buộc")]
                    if co:
                        tip.append("Song hành: " + co)
                    if status == "Bị khóa":
                        it.setIcon(icon("lock", C["amber"], 14))
                        tip.append("Bị khóa: chưa đạt học phần học trước")
                    elif c["elective"]:
                        it.setIcon(icon("star", C["violet"], 14))
                    it.setToolTip("\n".join(tip))
                if ci == 3:
                    it.setForeground(QColor(C["muted"]))
                    it.setToolTip("Học trước: " + v)
                if ci in (7, 8) and res:
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
                    it.setForeground(QColor(C["green"] if res.passed else C["red"]))
                if ci in (2, 4, 5, 6, 7, 8):
                    it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, ci, it)
            if c["id"] == keep:
                sel_row = r
        self.table.blockSignals(False)
        if select_first or sel_row is None:
            sel_row = 0 if courses else None
        if sel_row is not None:
            self.table.selectRow(sel_row)
            self._on_select()
        else:
            self.detail.show_course(None)

    def _on_select(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        it = self.table.item(rows[0].row(), 0)
        if it:
            self.detail.show_course(it.data(Qt.UserRole))

    def resizeEvent(self, e):
        compact = self.width() < 1200
        if compact != self._compact:
            self._compact = compact
            self.detail.setFixedWidth(380 if compact else 410)
            self.table.setColumnHidden(3, compact)
        super().resizeEvent(e)

    def focus_course(self, cid):
        self.set_semester(COURSE_BY_ID[cid]["semester"])
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).data(Qt.UserRole) == cid:
                self.table.selectRow(r)


# ====================================================================== Results
class ResultsPage(QWidget):
    COLS = ["Học kỳ", "Số HP", "TC đã học", "TC đạt", "GPA hệ 10", "GPA hệ 4", "CPA hệ 10", "CPA hệ 4", "TC tích lũy",
            "Xếp loại", "Trạng thái"]

    def __init__(self, book: GradeBook, host):
        super().__init__()
        self.book = book
        self.host = host
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(20)
        b_exp = QPushButton("  Xuất bảng điểm (CSV)")
        b_exp.setObjectName("Ghost")
        b_exp.setIcon(icon("download", C["text2"], 16))
        b_exp.setCursor(Qt.PointingHandCursor)
        b_exp.clicked.connect(self.export_csv)
        b_reset = QPushButton("  Xoá toàn bộ dữ liệu")
        b_reset.setObjectName("Danger")
        b_reset.setIcon(icon("refresh", C["red"], 16))
        b_reset.setCursor(Qt.PointingHandCursor)
        b_reset.clicked.connect(self.reset_all)
        root.addWidget(page_header("Kết quả học tập & Tích lũy",
                                   "Điểm trung bình học kỳ (GPA) và điểm trung bình tích lũy (CPA) sau mỗi học kỳ",
                                   [b_exp, b_reset]))
        top = QGridLayout()
        self.top_grid = top
        top.setSpacing(18)
        self.big = Card()
        bh = QHBoxLayout()
        self.big_ring = Ring(150, 14, C["yellow"], C["amber"])
        bh.addWidget(self.big_ring)
        bv = QVBoxLayout()
        bv.setSpacing(4)
        bv.addWidget(label("Điểm trung bình tích lũy", size=13, weight=600, color=C["muted"]))
        self.big_val = label("—", size=44, weight=800, color=C["primary"])
        bv.addWidget(self.big_val)
        self.big_sub = label("", size=13, color=C["text2"], wrap=True)
        bv.addWidget(self.big_sub)
        self.big_rank = chip("—", C["navy"], C["yellow"], 13, 800, "6px 14px")
        bv.addWidget(self.big_rank, 0, Qt.AlignLeft)
        bv.addStretch(1)
        bh.addSpacing(10)
        bh.addLayout(bv, 1)
        self.big.lay.addLayout(bh)
        dist = Card()
        dist.lay.addWidget(label("Phân bố điểm chữ", "CardTitle"))
        self.dist_rows = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for i, (_, letter, _g) in enumerate(core.LETTER_SCALE):
            grid.addWidget(label(letter, size=12, weight=800), i, 0)
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            grid.addWidget(bar, i, 1)
            cnt = label("0", size=12, color=C["muted"])
            grid.addWidget(cnt, i, 2)
            self.dist_rows[letter] = (bar, cnt)
        grid.setColumnStretch(1, 1)
        dist.lay.addLayout(grid)
        self.dist_card = dist
        chart = Card()
        chart.lay.addWidget(label("Biểu đồ GPA / CPA", "CardTitle"))
        self.chart = GpaChart()
        self.chart.setMinimumHeight(220)
        chart.lay.addWidget(self.chart)
        self.chart_card = chart
        self._wide = None
        self._reflow(True)
        root.addLayout(top)

        tcard = Card(pad=8, spacing=0)
        self.table = QTableWidget(len(SEMESTERS) + 1, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFixedHeight(44 * (len(SEMESTERS) + 1) + 46)
        self.status_delegate = StatusDelegate(self.table)
        tcard.lay.addWidget(self.table)
        root.addWidget(tcard)
        root.addWidget(label("Ghi chú: GPA học kỳ và CPA đều tính trên tất cả học phần đã có điểm (kể cả không đạt), "
                             "nhờ vậy CPA của học kỳ đầu trùng GPA. Tín chỉ tích lũy chỉ cộng các học phần đạt (≥ 4.0). "
                             "Thang quy đổi: A ≥ 8.5 (4.0) • B+ ≥ 8.0 (3.5) • B ≥ 7.0 (3.0) • C+ ≥ 6.5 (2.5) • "
                             "C ≥ 5.5 (2.0) • D+ ≥ 5.0 (1.5) • D ≥ 4.0 (1.0) • F < 4.0 (0).",
                             size=11, color=C["muted"], wrap=True))
        root.addStretch(1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))

    def _reflow(self, wide):
        if wide == self._wide:
            return
        self._wide = wide
        g = self.top_grid
        if wide:
            g.addWidget(self.big, 0, 0)
            g.addWidget(self.dist_card, 0, 1)
            g.addWidget(self.chart_card, 0, 2)
            for c, st in enumerate((2, 2, 3)):
                g.setColumnStretch(c, st)
        else:
            g.addWidget(self.big, 0, 0)
            g.addWidget(self.dist_card, 0, 1)
            g.addWidget(self.chart_card, 1, 0, 1, 2)
            for c, st in enumerate((1, 1, 0)):
                g.setColumnStretch(c, st)

    def resizeEvent(self, e):
        self._reflow(self.width() >= 1180)
        super().resizeEvent(e)

    def refresh(self):
        b = self.book
        cum = b.cumulative()
        self.big_val.setText(f"{fmt(cum['cpa4'])} / 4")
        self.big_sub.setText(f"Hệ 10: {fmt(cum['cpa10'])}  •  {fmt_credits(cum['credits'])}/{PROGRAM['total_credits']} tín chỉ"
                             f"  •  {cum['n_courses']} học phần đạt")
        self.big_rank.setText(f"Xếp loại: {cum['rank']}")
        self.big_ring.set((cum["cpa4"] or 0) / 4, fmt(cum["cpa4"]), "CPA")
        counts = {l: 0 for _, l, _ in core.LETTER_SCALE}
        for c in COURSES:
            r = b.result(c["id"])
            if r:
                counts[r.letter] += 1
        mx = max(1, max(counts.values()))
        for l, (bar, cnt) in self.dist_rows.items():
            bar.setMaximum(mx)
            bar.setValue(counts[l])
            cnt.setText(str(counts[l]))
        gpa, cpa = [], []
        tot_hp = tot_tc = tot_pass = 0
        for i, s in enumerate(SEMESTERS):
            st = b.semester_stats(s)
            cu = b.cumulative(s)
            has = st["n_graded"] > 0
            gpa.append(st["gpa4"])
            cpa.append(cu["cpa4"] if has else None)
            tot_hp += st["n_graded"]
            tot_tc += st["credits_graded"]
            tot_pass += st["credits_passed"]
            status = "Hoàn thành" if st["completed"] else ("Đang học" if has else "Chưa học")
            vals = [f"Học kỳ {s}", f"{st['n_graded']}/{st['n_plan']}", fmt_credits(st["credits_graded"]),
                    fmt_credits(st["credits_passed"]), fmt(st["gpa10"]), fmt(st["gpa4"]),
                    fmt(cu["cpa10"]) if has else "—", fmt(cu["cpa4"]) if has else "—",
                    fmt_credits(cu["credits"]) if has else "—", cu["rank"] if has else "—", status]
            self._row(i, vals, status)
        vals = ["Toàn khóa", str(tot_hp), fmt_credits(tot_tc), fmt_credits(tot_pass), "", "", fmt(cum["cpa10"]),
                fmt(cum["cpa4"]), fmt_credits(cum["credits"]), cum["rank"], ""]
        self._row(len(SEMESTERS), vals, None, bold=True)
        self.chart.set_data(gpa, cpa)

    def _row(self, r, vals, status, bold=False):
        colors = {"Hoàn thành": C["green"], "Đang học": C["amber"], "Chưa học": C["faint"]}
        for ci, v in enumerate(vals):
            it = QTableWidgetItem(v)
            it.setTextAlignment(Qt.AlignCenter if ci else Qt.AlignLeft | Qt.AlignVCenter)
            f = it.font()
            if bold or ci in (0, 7):
                f.setBold(True)
            it.setFont(f)
            if ci == 7:
                it.setForeground(QColor(C["primary"]))
            if ci == 10 and status:
                it.setForeground(QColor(colors[status]))
            if bold:
                it.setBackground(QColor(C["primary_soft"]))
            self.table.setItem(r, ci, it)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Xuất bảng điểm", "BangDiem_TinHocXayDung.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Học kỳ", "Tên học phần", "Số TC", "Loại", "Thành phần", "Giữa kỳ", "Cuối kỳ", "Tổng kết",
                            "Điểm chữ", "Hệ 4", "Kết quả"])
                for c in COURSES:
                    g = self.book.grades.get(c["id"])
                    r = self.book.result(c["id"])
                    w.writerow([c["semester"], c["name"], fmt_credits(c["credits"]), "Tự chọn" if c["elective"] else "Bắt buộc",
                                g["tp"] if g else "", g["gk"] if g else "", g["ck"] if g else "",
                                f"{r.total:.1f}" if r else "", r.letter if r else "", f"{r.g4:.1f}" if r else "",
                                ("Đạt" if r.passed else "Không đạt") if r else "Chưa có điểm"])
                cum = self.book.cumulative()
                w.writerow([])
                w.writerow(["CPA hệ 4", fmt(cum["cpa4"]), "CPA hệ 10", fmt(cum["cpa10"]), "TC tích lũy",
                            fmt_credits(cum["credits"]), "Xếp loại", cum["rank"]])
            self.host.toast("Đã xuất bảng điểm ra tệp CSV", "success")
        except OSError as e:
            MessageDialog.show_msg(self.window(), "Không thể xuất tệp", str(e), None, "error")

    def reset_all(self):
        if MessageDialog.confirm(self.window(), "Xoá toàn bộ dữ liệu điểm?",
                                 "Tất cả điểm đã nhập của 9 học kỳ sẽ bị xoá vĩnh viễn. Bạn có chắc chắn?", "Xoá tất cả"):
            self.book.reset()
            self.host.refresh_all()
            self.host.toast("Đã xoá toàn bộ dữ liệu điểm", "info")


# ====================================================================== Main window
class MainWindow(QMainWindow):
    def __init__(self, book: GradeBook, theme="light"):
        super().__init__()
        self.book = book
        self.animate = True
        self.theme = apply_theme(theme)
        self._fade = None
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss())
        self.setWindowTitle(f"{APP_NAME} – Quản lý Học phần & Trợ lý AI")
        self.setWindowIcon(QIcon(LOGO))
        # Trợ lý AI dùng chung + bộ tự động hoá nhắc nhở
        self.session = ChatSession(book, self)
        self.reminders = ReminderStore()
        self.engine = AutomationEngine(book, self.reminders, parent=self)
        self._build()
        self.go(0)
        self._setup_tray()
        self._connect_automation()

    def _build(self):
        book = self.book
        central = QWidget()
        central.setObjectName("Content")
        self.setCentralWidget(central)
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(272)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(18, 24, 18, 20)
        sv.setSpacing(6)
        brand_box = QFrame()
        brand_box.setObjectName("BrandBox")
        brand_box.setStyleSheet("QFrame#BrandBox { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);"
                                " border-radius: 18px; }")
        brand = QVBoxLayout(brand_box)
        brand.setContentsMargins(14, 14, 14, 14)
        brand.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(logo_tile(52, 13, 4), 0, Qt.AlignVCenter)
        top.addWidget(label(UNIVERSITY, size=11, weight=800, color="white", wrap=True), 1, Qt.AlignVCenter)
        brand.addLayout(top)
        brand.addWidget(label(FACULTY, size=18, weight=800, color="white"))
        tag = label(CLASS_LINE, wrap=True)
        tag.setStyleSheet(f"background:{C['yellow']}; color:{C['navy']}; border-radius:7px; padding:3px 9px;"
                          " font-size:10px; font-weight:800;")
        brand.addWidget(tag)
        sv.addWidget(brand_box)
        sv.addSpacing(26)
        sv.addWidget(label("MENU", size=10, weight=700, color="#7E89C9"))
        sv.addSpacing(4)

        self.stack = QStackedWidget()
        self.intro = IntroPage()
        self.dash = DashboardPage(book)
        self.courses = CoursesPage(book, self)
        self.results = ResultsPage(book, self)
        self.ai = AIPage(book, self, self.engine, self.session)
        self.pages = [self.intro, self.dash, self.courses, self.results, self.ai]
        for p in self.pages:
            self.stack.addWidget(p)
        self.nav = QButtonGroup(self)
        self.nav_btns = []
        for i, (ic, text) in enumerate([("info", "Giới thiệu"), ("home", "Tổng quan"), ("book", "Học phần && Nhập điểm"),
                                        ("chart", "Kết quả tích lũy"), ("sparkles", "Trợ lý AI")]):
            b = QPushButton(f"   {text}")
            b.setObjectName("NavButton")
            b.setCheckable(True)
            b.setIcon(icon(ic, "#C7CEF5", 20))
            b.setIconSize(b.iconSize().expandedTo(b.iconSize()))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=i: self.go(i))
            self.nav.addButton(b, i)
            sv.addWidget(b)
            self.nav_btns.append((b, ic))
        sv.addStretch(1)

        ts = QFrame()
        ts.setObjectName("ThemeSwitch")
        tl = QHBoxLayout(ts)
        tl.setContentsMargins(5, 5, 5, 5)
        tl.setSpacing(4)
        self.theme_btns = {}
        for mode, ic, text in (("light", "sun", "Sáng"), ("dark", "moon", "Tối")):
            b = QPushButton(f" {text}")
            b.setObjectName("ThemeBtn")
            b.setCheckable(True)
            b.setChecked(mode == self.theme)
            b.setCursor(Qt.PointingHandCursor)
            b.setIcon(icon(ic, C["navy"] if mode == self.theme else "#C7CEF5", 16))
            b.clicked.connect(lambda _=False, m=mode: self.set_theme(m))
            tl.addWidget(b, 1)
            self.theme_btns[mode] = b
        sv.addWidget(ts)
        sv.addSpacing(10)

        sc = QFrame()
        sc.setObjectName("SideCard")
        scl = QVBoxLayout(sc)
        scl.setContentsMargins(16, 14, 16, 14)
        scl.setSpacing(4)
        scl.addWidget(label("CPA TÍCH LŨY", size=10, weight=700, color="#9AA5E0"))
        self.side_cpa = label("—", size=26, weight=800, color="white")
        scl.addWidget(self.side_cpa)
        self.side_bar = QProgressBar()
        self.side_bar.setTextVisible(False)
        self.side_bar.setFixedHeight(6)
        self.side_bar.setMaximum(PROGRAM["total_credits"] * 2)
        self.side_bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.12); border-radius:3px; }}"
                                    f"QProgressBar::chunk {{ background:{C['yellow']}; border-radius:3px; }}")
        scl.addWidget(self.side_bar)
        self.side_sub = label("", size=11, color="#C7CEF5")
        scl.addWidget(self.side_sub)
        sv.addWidget(sc)
        sv.addSpacing(10)
        sv.addWidget(label(f"ĐH BÁCH KHOA ĐÀ NẴNG  •  v{APP_VERSION}", size=10, color="#7E89C9"), 0, Qt.AlignCenter)

        h.addWidget(side)
        h.addWidget(self.stack, 1)

        # Bong bóng chat nổi ở góc dưới bên phải
        self.floating = FloatingChatBubble(self.session, central)
        self.floating.setParent(central)
        self.floating.open_page.connect(lambda: self.go(4))
        self.floating.show()
        self.floating.raise_()
        self._place_floating(central)
        # Layout chỉ cập nhật kích thước central SAU resizeEvent của cửa sổ, nên phải bám
        # theo chính vùng nội dung, nếu không bong bóng sẽ đứng giữa màn hình.
        central.installEventFilter(self)
        QTimer.singleShot(0, lambda: self._place_floating(self.centralWidget()))

        self.toast_w = Toast(central)
        self.intro.start.connect(lambda: self.go(1))
        self.dash.open_semester.connect(self.open_semester)
        self.courses.changed.connect(self.refresh_all)
        self.refresh_all()

    def set_theme(self, mode):
        if mode == self.theme:
            self.theme_btns[mode].setChecked(True)
            return
        idx = self.stack.currentIndex()
        sem = getattr(self.courses, "sem", None)
        self.theme = apply_theme(mode)
        save_settings({"theme": self.theme})
        QApplication.instance().setStyleSheet(qss())
        old = self.takeCentralWidget()
        self._build()
        old.deleteLater()
        if sem is not None and idx == 2:
            self.courses.set_semester(sem)
        self.go(idx)

    def go(self, i):
        prev = self.stack.currentIndex()
        self.stack.setCurrentIndex(i)
        if i == 4 and hasattr(self, "ai"):
            self.ai.refresh()
        # Trang AI đã có khung chat riêng → ẩn bong bóng để không che ô nhập
        if hasattr(self, "floating"):
            if prev != i:
                self.floating.close_popup()
            if i == 4:
                self.floating.hide()
            else:
                self.floating.show()
                self.floating.raise_()
                self._place_floating(self.centralWidget())
        if self.animate and prev != i:
            page = self.stack.currentWidget()
            eff = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(240)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda p=page: p.setGraphicsEffect(None))
            anim.start()
            self._fade = anim
        for j, (b, ic) in enumerate(self.nav_btns):
            b.setChecked(j == i)
            b.setIcon(icon(ic, "white" if j == i else "#C7CEF5", 20))

    def open_semester(self, s):
        self.go(2)
        self.courses.set_semester(s)

    def refresh_all(self):
        self.dash.refresh()
        self.courses.refresh()
        self.results.refresh()
        self.ai.refresh()
        cum = self.book.cumulative()
        self.side_cpa.setText(f"{fmt(cum['cpa4'])} / 4")
        self.side_bar.setValue(int(cum["credits"] * 2))
        self.side_sub.setText(f"{fmt_credits(cum['credits'])}/{PROGRAM['total_credits']} tín chỉ  •  {cum['rank']}")
        # Tự động hoá: quét cảnh báo sau mỗi thay đổi dữ liệu điểm
        if getattr(self, "engine", None):
            self.engine.refresh(force=True, notify=False)
            self._refresh_badge()

    # ------------------------------------------------------------- automation
    def _setup_tray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        try:
            tray = QSystemTrayIcon(QIcon(LOGO_BADGE), self)
            tray.setToolTip(f"{APP_NAME} – Trợ lý AI & nhắc nhở học tập")
            menu = QMenu()
            act_open = menu.addAction("Mở ứng dụng")
            act_open.triggered.connect(self._show_from_tray)
            act_ai = menu.addAction("Mở trợ lý AI")
            act_ai.triggered.connect(self._open_ai)
            act_check = menu.addAction("Kiểm tra nhắc nhở ngay")
            act_check.triggered.connect(lambda: self.engine.refresh(force=True))
            menu.addSeparator()
            act_quit = menu.addAction("Thoát")
            act_quit.triggered.connect(QApplication.instance().quit)
            tray.setContextMenu(menu)
            tray.activated.connect(self._tray_activated)
            tray.show()
            self.tray = tray
            self._tray_menu = menu
        except Exception:
            self.tray = None

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _open_ai(self):
        self._show_from_tray()
        self.go(4)

    def _connect_automation(self):
        self.engine.notify.connect(self._on_reminder)
        self.engine.changed.connect(self._refresh_badge)
        self.engine.digest_ready.connect(self._on_digest)
        self.engine.start()

    def _on_reminder(self, reminder):
        self._refresh_badge()
        # Lời khuyên AI có thông báo riêng (_on_digest) → tránh 2 toast chồng nhau
        if getattr(reminder, "type", "") == "coach":
            return
        kind = "warning" if reminder.level in ("danger", "warning") else "info"
        try:
            self.toast(f"AI: {reminder.title}", "error" if reminder.level == "danger" else kind)
        except Exception:
            pass
        if self.tray and self.engine.cfg.get("tray_notify", True):
            try:
                self.tray.showMessage(reminder.title, reminder.body[:220], QSystemTrayIcon.Information, 7000)
            except Exception:
                pass

    def _on_digest(self, text):
        self._refresh_badge()
        try:
            self.toast("AI đã gửi lời khuyên học tập hôm nay", "success")
        except Exception:
            pass

    def _refresh_badge(self):
        if hasattr(self, "floating"):
            self.floating.set_badge(self.engine.store.unseen_count())

    def _place_floating(self, parent):
        """Dua bong bop chat noi ve goc duoi ben phai cua vung noi dung."""
        if not hasattr(self, "floating"):
            return
        parent = parent or self.centralWidget()
        if not parent:
            return
        self.floating.place(parent.width(), parent.height())

    def toast(self, text, kind="success"):
        # Chống trùng: cùng một thông báo trong 8 giây chỉ hiện một lần
        now = time.time()
        last = getattr(self, "_last_toast", None)
        if last and last[0] == text and now - last[1] < 8:
            return
        self._last_toast = (text, now)
        self.toast_w.show_message(text, kind)

    def announce_semester(self, sem):
        st = self.book.semester_stats(sem)
        cum = self.book.cumulative(sem)
        items = [f"GPA Học kỳ {sem}: {fmt(st['gpa4'])} (hệ 4)  •  {fmt(st['gpa10'])} (hệ 10)",
                 f"CPA tích lũy: {fmt(cum['cpa4'])} (hệ 4)  •  {fmt(cum['cpa10'])} (hệ 10)",
                 f"Tín chỉ tích lũy: {fmt_credits(cum['credits'])}/{PROGRAM['total_credits']}  •  Xếp loại: {cum['rank']}"]
        if self.book.last_completed_semester() == sem and sem < SEMESTERS[-1]:
            info = self.book.next_semester_info()
            nst = info["stats"]
            line = f"Học kỳ {info['semester']} tiếp theo có {nst['n_plan']} học phần ({fmt_credits(nst['credits_plan'])} tín chỉ)"
            if nst["electives_needed"]:
                line += f" – {nst['n_required']} bắt buộc + {nst['electives_needed']} tự chọn"
            items.append(line)
            if info["locked"]:
                items.append(f"Cảnh báo: {len(info['locked'])} học phần kỳ tới đang bị khóa do học phần học trước chưa đạt")
        elif sem == SEMESTERS[-1]:
            items.append("Chúc mừng! Bạn đã hoàn thành toàn bộ chương trình đào tạo.")
        MessageDialog.show_msg(self, f"Hoàn thành Học kỳ {sem}!", "Kết quả học kỳ và điểm tích lũy của bạn:", items, "success")

    def eventFilter(self, obj, event):
        """Bám vị trí bong bóng chat khi vùng nội dung đổi kích thước thật."""
        if (event.type() == QEvent.Type.Resize and obj is self.centralWidget()
                and hasattr(self, "floating")):
            self._place_floating(obj)
        return super().eventFilter(obj, event)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        toast = getattr(self, "toast_w", None)
        if toast is not None and toast.isVisible():
            toast.reposition()
        self._place_floating(self.centralWidget())


def settings_path() -> Path:
    return core.default_data_path().with_name("settings.json")


def load_settings() -> dict:
    try:
        return json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(data: dict):
    try:
        p = settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        cur = load_settings()
        cur.update(data)
        p.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# ====================================================================== Cover
class CoverBanner(QWidget):
    NAVY = QColor("#0F2A78")

    def __init__(self):
        super().__init__()
        self._logo = QPixmap(LOGO)
        self._img = QImage(COVER_IMAGE)
        self._cache = None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = QRectF(self.rect())
        w, h = r.width(), r.height()
        clip = QPainterPath()
        clip.addRoundedRect(r, 14, 14)
        p.setClipPath(clip)
        p.fillRect(r, QColor("#0F2A78"))
        if not self._img.isNull():
            dpr = self.devicePixelRatioF()
            key = (int(w * dpr), int(h * dpr))
            if self._cache is None or self._cache[0] != key:
                sc = self._img.scaled(key[0], key[1], Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x = (sc.width() - key[0]) // 2
                y = int((sc.height() - key[1]) * 0.62)
                pm = QPixmap.fromImage(sc.copy(x, y, key[0], key[1]))
                pm.setDevicePixelRatio(dpr)
                self._cache = (key, pm)
            p.drawPixmap(QPointF(0, 0), self._cache[1])
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor(6, 16, 60, 200))
        g.setColorAt(0.45, QColor(6, 16, 60, 120))
        g.setColorAt(0.75, QColor(6, 16, 60, 0))
        p.fillRect(r, g)
        self._draw_text(p, w, h)

    def _draw_text(self, p, w, h):
        logo_h = h * 0.17
        f1 = ui_font(max(12, int(h * 0.058)), QFont.ExtraBold)
        f2 = ui_font(max(8, int(h * 0.030)), QFont.DemiBold)
        t1, t2 = UNIVERSITY, "THE UNIVERSITY OF DANANG – UNIVERSITY OF SCIENCE AND TECHNOLOGY"
        m1, m2 = QFontMetrics(f1), QFontMetrics(f2)
        tw = max(m1.horizontalAdvance(t1), m2.horizontalAdvance(t2))
        gap = h * 0.03
        total = logo_h + gap + tw
        x0, y0 = (w - total) / 2, h * 0.05
        if not self._logo.isNull():
            pm = self._logo.scaled(int(logo_h * 2), int(logo_h * 2), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("white"))
            p.drawRoundedRect(QRectF(x0 - 3, y0 - 3, logo_h + 6, logo_h + 6), 4, 4)
            p.drawPixmap(QRectF(x0, y0, logo_h, logo_h), pm, QRectF(pm.rect()))
        tx = x0 + logo_h + gap
        p.setPen(QColor("white"))
        p.setFont(f1)
        p.drawText(QRectF(tx, y0, tw + 4, logo_h * 0.55), Qt.AlignLeft | Qt.AlignBottom, t1)
        p.setPen(QPen(QColor("#FFD60A"), 1.4))
        p.drawLine(QPointF(tx, y0 + logo_h * 0.60), QPointF(tx + tw, y0 + logo_h * 0.60))
        p.setFont(f2)
        p.setPen(QColor("#DCE6FF"))
        p.drawText(QRectF(tx, y0 + logo_h * 0.64, tw + 4, logo_h * 0.36), Qt.AlignLeft | Qt.AlignTop, t2)

        tf = ui_font(max(24, int(h * 0.20)), QFont.ExtraBold)
        tf.setLetterSpacing(QFont.PercentageSpacing, 106)
        ty = y0 + logo_h + h * 0.02
        th = QFontMetrics(tf).height()
        p.setFont(tf)
        p.setPen(QColor(0, 0, 0, 120))
        p.drawText(QRectF(3, ty + 4, w, th), Qt.AlignHCenter | Qt.AlignVCenter, FACULTY)
        p.setPen(QColor("white"))
        p.drawText(QRectF(0, ty, w, th), Qt.AlignHCenter | Qt.AlignVCenter, FACULTY)


class SplashScreen(QWidget):
    STEPS = ((0, "Đang khởi động hệ thống…"), (25, "Đang tải dữ liệu chương trình đào tạo…"),
             (50, "Đang tải bảng điểm…"), (75, "Đang dựng giao diện…"), (100, "Hoàn tất"))

    def __init__(self, width=1040):
        super().__init__(None, Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(f"{APP_NAME} – {FACULTY}")
        self._value = 0.0
        self._build_cb = self._done_cb = None
        self._built = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        card = QFrame()
        card.setObjectName("CoverCard")
        card.setStyleSheet("QFrame#CoverCard { background:#FFFFFF; border-radius:20px; border:1px solid #DCE3F5; }"
                           " QLabel { background: transparent; }")
        shadow(card, 50, 12, 90)
        outer.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 18, 18, 20)
        lay.setSpacing(10)
        inner_w = width - 48 - 36
        self.banner = CoverBanner()
        self.banner.setFixedSize(inner_w, int(inner_w * 0.42))
        lay.addWidget(self.banner)

        self.status = label(self.STEPS[0][1], size=13, weight=600, color="#1E4FD0")
        self.status.setContentsMargins(6, 4, 0, 0)
        lay.addWidget(self.status)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.setFixedHeight(10)
        self.bar.setStyleSheet("QProgressBar { background:#E6EBF5; border:none; border-radius:5px; }"
                               "QProgressBar::chunk { border-radius:5px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                               " stop:0 #1E4FD0, stop:1 #4C7BFF); }")
        lay.addWidget(self.bar)
        lay.addSpacing(6)

        row = QHBoxLayout()
        row.setContentsMargins(6, 0, 6, 0)
        row.setSpacing(18)
        badge = QLabel()
        bp = QPixmap(LOGO_BADGE)
        if not bp.isNull():
            dpr = self.devicePixelRatioF()
            bp = bp.scaled(int(84 * dpr), int(84 * dpr), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            bp.setDevicePixelRatio(dpr)
            badge.setPixmap(bp)
        row.addWidget(badge, 0, Qt.AlignVCenter)
        if ADVISOR:
            av = QLabel()
            av.setPixmap(round_avatar(ADVISOR_PHOTO, 72, "#FFD60A", 3, self.devicePixelRatioF()))
            av.setFixedSize(72, 72)
            row.addWidget(av, 0, Qt.AlignVCenter)
            adv = QVBoxLayout()
            adv.setSpacing(2)
            adv.addStretch(1)
            adv.addWidget(label("GIẢNG VIÊN HƯỚNG DẪN", size=11, weight=800, color="#1E4FD0"))
            adv.addWidget(label(ADVISOR, size=17, weight=800, color="#0F2A78"))
            adv.addStretch(1)
            row.addLayout(adv)
        info = QVBoxLayout()
        info.setSpacing(3)
        info.addWidget(label("PHẦN MỀM QUẢN LÝ HỌC PHẦN", size=20, weight=800, color="#0F2A78"), 0, Qt.AlignRight)
        info.addWidget(label(CLASS_LINE, size=13, weight=800, color="#1E4FD0"), 0, Qt.AlignRight)
        info.addWidget(label("Nhóm thực hiện: " + " • ".join(MEMBERS), size=12, color="#5B6478"), 0, Qt.AlignRight)
        meta = [f"Ngày xây dựng: {BUILD_DATE}", f"v{APP_VERSION}"]
        info.addWidget(label("  |  ".join(meta), size=12, color="#5B6478"), 0, Qt.AlignRight)
        row.addLayout(info, 1)
        lay.addLayout(row)

        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._tick)

    def run(self, build_cb, done_cb):
        self._build_cb, self._done_cb = build_cb, done_cb
        self._timer.start()

    def _tick(self):
        self._value = min(100.0, self._value + 1.2)
        v = int(self._value)
        self.bar.setValue(v)
        text = [t for lim, t in self.STEPS if v >= lim][-1]
        if self.status.text() != text:
            self.status.setText(text)
        if v >= 40 and not self._built:
            self._built = True
            QApplication.processEvents()
            self._build_cb()
        if v >= 100:
            self._timer.stop()
            QTimer.singleShot(250, self._done_cb)

    def mousePressEvent(self, e):
        if self._built:
            self._value = 99.0
        super().mousePressEvent(e)


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DUT.TinHocXayDung.QuanLyHocPhan")
        except Exception:
            pass
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    fam = load_fonts()
    f = QFont(fam, 10)
    f.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(f)
    app.setStyleSheet(qss())
    app.setWindowIcon(QIcon(LOGO))
    scr = app.primaryScreen().availableGeometry()
    splash = SplashScreen(max(720, min(1040, scr.width() - 80)))
    splash.adjustSize()
    splash.move(scr.center() - splash.rect().center())
    splash.show()
    app.processEvents()
    state = {}

    def build():
        w = MainWindow(GradeBook(), load_settings().get("theme", "light"))
        w.resize(min(1560, scr.width() - 40), min(960, scr.height() - 40))
        w.setMinimumSize(min(1280, scr.width()), min(680, scr.height()))
        w.move(scr.center() - w.rect().center())
        state["w"] = w

    def done():
        w = state["w"]
        w.show()
        w.raise_()
        w.activateWindow()
        splash.close()

    splash.run(build, done)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
