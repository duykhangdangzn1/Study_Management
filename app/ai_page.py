"""Giao diện AI: trang trợ lý AI riêng + bong bóng chat nổi.

Trang AI gồm 5 tab:
- Tổng quan AI   : cảnh báo học tập, tiến độ tốt nghiệp, kế hoạch học lại, việc cần làm.
- Trò chuyện AI  : chat online API, có toàn bộ ngữ cảnh học tập.
- Phương pháp & Kế hoạch: thời khoá biểu tuần, phương pháp học cá nhân hoá,
                   lịch học lại + AI soạn kế hoạch chi tiết.
- Tự động hoá    : nhắc nhở, giờ học, AI coach hằng ngày, kho nhắc nhở.
- Cài đặt AI     : endpoint/model online API, kiểm tra kết nối.
"""
from __future__ import annotations

import html
import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QObject, QPoint, QPropertyAnimation, QSize, QTime, QTimer, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
                           QTextDocument)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
                               QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QScrollArea, QSizePolicy, QTabWidget, QTextBrowser, QTimeEdit,
                               QVBoxLayout, QWidget)

import ai_engine
import core
from ai_engine import (AI_BASE_URL, AI_MODE, AI_MODEL, AIClient, AIError, LocalAnalytics, StudyAdvisor,
                       build_messages, load_api_config, mask_key, reset_api_config, save_api_config)
from automation import DEFAULT_CONFIG as AUTO_DEFAULT, AutomationEngine, Reminder, parse_hhmm
from ui_kit import (C, FONT_FAMILY, Card, IconTile, MessageDialog, Ring, SegmentedTabBar, SoftRow, chip, icon,
                    icon_pixmap, label, resource_path, shadow, tint)

APP_ICON = resource_path("assets/logo_badge.png")


def fmt(v, nd=2, dash="—"):
    return dash if v is None else f"{v:.{nd}f}"


def scroll_page(inner: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.NoFrame)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
    v.addWidget(label(sub, "PageSub", wrap=True))
    h.addLayout(v, 1)
    if right:
        for r in right:
            h.addWidget(r, 0, Qt.AlignBottom)
    return w


def clear_layout(box):
    """Xoá sạch widget VÀ layout con (tránh widget cũ còn nổi trên giao diện)."""
    while box.count():
        item = box.takeAt(0)
        w = item.widget()
        if w:
            w.hide()
            w.deleteLater()
        elif item.layout() is not None:
            sub = item.layout()
            clear_layout(sub)
            sub.deleteLater()


_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in s.split("|")]


def _inline_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`\n]+)`",
               lambda m: f"<code style='background:{C['chip']}; padding:0 3px;'>{m.group(1)}</code>", s)
    return s


def _table_html(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    parts = ["<table width='100%' cellspacing='0' cellpadding='5' style='border-collapse:collapse; margin:6px 0;'>"]
    for ri, row in enumerate(rows):
        cells = []
        for cell in row:
            body = _inline_md(html.escape(cell))
            if ri == 0:
                cells.append(f"<td bgcolor='{C['primary_soft']}' style='border:1px solid {C['border']};"
                             f" font-weight:700;'>{body}</td>")
            else:
                cells.append(f"<td style='border:1px solid {C['border']};'>{body}</td>")
        parts.append("<tr>" + "".join(cells) + "</tr>")
    parts.append("</table>")
    return "".join(parts)


def to_rich(text: str) -> str:
    """Markdown → HTML an toàn (dùng cho QLabel); hỗ trợ bảng, tiêu đề, danh sách."""
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if "|" in s and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1].strip()):
            rows = [_split_row(line)]
            i += 2
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                rows.append(_split_row(lines[i]))
                i += 1
            out.append(_table_html(rows))
            continue
        if not s:
            out.append("<div style='height:6px'></div>")
        elif re.match(r"^#{1,4}\s*", s):
            out.append("<div style='font-weight:800; font-size:14px; margin:6px 0 2px;'>" +
                       _inline_md(html.escape(re.sub(r"^#{1,4}\s*", "", s))) + "</div>")
        elif re.match(r"^[-*•]\s+", s):
            out.append("<div style='margin-left:8px;'>• " +
                       _inline_md(html.escape(re.sub(r"^[-*•]\s+", "", s))) + "</div>")
        elif re.match(r"^\d+[.)]\s+", s):
            out.append("<div style='margin-left:8px;'>" + _inline_md(html.escape(s)) + "</div>")
        elif s.startswith(">"):
            out.append(f"<div style='border-left:3px solid {C['primary_border']}; padding-left:8px; color:{C['muted']};'>" +
                       _inline_md(html.escape(s.lstrip("> "))) + "</div>")
        else:
            out.append("<div>" + _inline_md(html.escape(s)) + "</div>")
        i += 1
    return "".join(out)


def prepare_markdown(text: str) -> str:
    """Chuẩn hoá câu trả lời AI trước khi render Markdown.

    Bổ sung dòng phân cách cho bảng do AI quên, đổi bullet • thành -, gộp dòng
    trống thừa và bỏ khối ``` bao quanh cả câu trả lời.
    """
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u200b", "").replace("\ufeff", "").strip()
    text = re.sub(r"^```(?:markdown|md)?\s*\n(.*?)\n```\s*$", r"\1", text, flags=re.S)
    text = re.sub(r"(?m)^\s*[•·]\s+", "- ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if "|" in s and not _TABLE_SEP_RE.match(s):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if _TABLE_SEP_RE.match(nxt):
                if out and out[-1].strip():
                    out.append("")
                out.append(line)
                out.append(lines[i + 1])
                i += 2
                while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                    out.append(lines[i])
                    i += 1
                out.append("")
                continue
            if s.startswith("|") and nxt.startswith("|") and "|" in nxt:
                cols = max(1, len(_split_row(line)))
                if out and out[-1].strip():
                    out.append("")
                out.append(line)
                out.append("| " + " | ".join(["---"] * cols) + " |")
                i += 1
                while i < len(lines) and lines[i].strip().startswith("|"):
                    out.append(lines[i])
                    i += 1
                out.append("")
                continue
        if s.startswith("#") and out and out[-1].strip():
            out.append("")
        out.append(line)
        i += 1
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def default_chat_path() -> Path:
    return core.default_data_path().with_name("chat_history.json")


CHAT_PATH = default_chat_path()


def _title_from(text: str) -> str:
    line = re.sub(r"[#*`>|]", "", (text or "").strip().split("\n")[0]).strip()
    line = re.sub(r"\s+", " ", line)
    if not line:
        return "Đoạn chat mới"
    return line[:46] + ("…" if len(line) > 46 else "")


class ChatStore:
    """Lưu lịch sử trò chuyện bền vững (mặc định .../TinHocXayDung/chat_history.json)."""

    MAX_SESSIONS = 100

    def __init__(self, path=None):
        self.path = Path(path) if path else Path(CHAT_PATH)
        self.sessions: list[dict] = []
        self.load()

    def load(self):
        self.sessions = []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        raw = data.get("sessions", []) if isinstance(data, dict) else data
        if not isinstance(raw, list):
            return
        for s in raw:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("id") or "")
            if not sid:
                continue
            msgs = []
            for m in s.get("messages") or []:
                if isinstance(m, dict) and m.get("role") in ("user", "assistant") and m.get("content"):
                    msgs.append({"role": m["role"], "content": str(m["content"])})
            try:
                updated = float(s.get("updated") or 0)
            except (TypeError, ValueError):
                updated = 0.0
            self.sessions.append({"id": sid, "title": str(s.get("title") or "Đoạn chat"),
                                  "updated": updated, "messages": msgs})
        self.sessions.sort(key=lambda x: x["updated"], reverse=True)

    def persist(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            payload = {"version": 1, "sessions": self.sessions[:self.MAX_SESSIONS]}
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass

    def get(self, sid: str) -> dict | None:
        return next((s for s in self.sessions if s["id"] == sid), None)

    def create(self, title: str = "Đoạn chat mới") -> dict:
        s = {"id": datetime.now().strftime("%Y%m%d%H%M%S%f"), "title": title,
             "updated": time.time(), "messages": []}
        self.sessions.insert(0, s)
        self.persist()
        return s

    def add_message(self, sid: str, role: str, content: str):
        s = self.get(sid)
        if s is None:
            return
        s["messages"].append({"role": role, "content": content})
        if role == "user" and s["title"] in ("Đoạn chat mới", "Đoạn chat đầu tiên", ""):
            s["title"] = _title_from(content)
        s["updated"] = time.time()
        self.sessions.sort(key=lambda x: x["updated"], reverse=True)
        self.persist()

    def rename(self, sid: str, title: str):
        s = self.get(sid)
        if s is None:
            return
        s["title"] = (title or "").strip()[:80] or s["title"]
        s["updated"] = time.time()
        self.persist()

    def delete(self, sid: str):
        self.sessions = [s for s in self.sessions if s["id"] != sid]
        self.persist()


class _Bridge(QObject):
    ok = Signal(str)
    err = Signal(str)
    obj = Signal(object)


# ==================================================================== chat state
WELCOME_TEXT = ("Xin chào! Mình là Trợ lý AI học tập. Mình đọc trực tiếp bảng điểm của bạn để cảnh báo học tập, "
                "lập kế hoạch học lại và dự báo tốt nghiệp. Hỏi mình nhé!")


class ChatSession(QObject):
    """Phiên chat dùng chung cho trang AI và bong bóng nổi, có lịch sử bền vững."""

    appended = Signal(str, str)   # role, text
    busy_changed = Signal(bool)
    failed = Signal(str)
    switched = Signal(str)        # đổi cuộc trò chuyện
    history_changed = Signal()

    def __init__(self, book, parent=None, store: ChatStore | None = None):
        super().__init__(parent)
        self.book = book
        self.store = store or ChatStore()
        if not self.store.sessions:
            self.store.create("Đoạn chat đầu tiên")
        self.session_id: str = self.store.sessions[0]["id"]
        self.busy = False
        self._bridge = None

    # ---------------------------------------------------------- lịch sử
    @property
    def messages(self) -> list[dict]:
        s = self.store.get(self.session_id)
        return s["messages"] if s else []

    @property
    def current_title(self) -> str:
        s = self.store.get(self.session_id)
        return s["title"] if s else ""

    def new_chat(self) -> str:
        s = self.store.create()
        self.session_id = s["id"]
        self.switched.emit(self.session_id)
        self.history_changed.emit()
        return self.session_id

    def switch(self, sid: str):
        if sid == self.session_id or self.store.get(sid) is None:
            return
        self.session_id = sid
        self.switched.emit(sid)

    def delete_chat(self, sid: str):
        self.store.delete(sid)
        if self.store.get(self.session_id) is None:
            if not self.store.sessions:
                self.store.create("Đoạn chat đầu tiên")
            self.session_id = self.store.sessions[0]["id"]
            self.switched.emit(self.session_id)
        self.history_changed.emit()

    def rename_chat(self, sid: str, title: str):
        self.store.rename(sid, title)
        self.history_changed.emit()

    def clear(self):
        self.new_chat()

    # ---------------------------------------------------------- hội thoại
    def append(self, role: str, text: str):
        text = (text or "").strip()
        if not text:
            return
        if role in ("user", "assistant"):
            if self.store.get(self.session_id) is None:
                self.new_chat()
            self.store.add_message(self.session_id, role, text)
            self.history_changed.emit()
        self.appended.emit(role, text)

    def send(self, text: str) -> bool:
        text = (text or "").strip()
        if not text or self.busy:
            return False
        self.append("user", text)
        self.busy = True
        self.busy_changed.emit(True)
        context = LocalAnalytics(self.book).context_text()
        history = [m for m in self.messages if m["role"] in ("user", "assistant")]
        if history and history[-1]["role"] == "user" and history[-1]["content"] == text:
            history = history[:-1]          # câu hỏi hiện tại do build_messages chèn vào cuối
        # build_messages("qa") nạp quy chế + trích văn bản luật của Trường theo đúng câu hỏi,
        # nên câu trả lời trong khung chat có căn cứ điều/khoản thay vì tự suy diễn.
        messages = build_messages("qa", context, extra=text, history=history[-10:])
        bridge = _Bridge(self)
        bridge.ok.connect(self._done)
        bridge.err.connect(self._error)
        self._bridge = bridge
        AIClient().chat(messages, bridge.ok.emit, bridge.err.emit, temperature=0.55, max_tokens=2200)
        return True

    def _done(self, text: str):
        self.busy = False
        self.busy_changed.emit(False)
        text = (text or "").strip()
        self.append("assistant", text or "Mình chưa nhận được nội dung trả lời. Bạn thử lại giúp mình nhé.")

    def _error(self, message: str):
        self.busy = False
        self.busy_changed.emit(False)
        self.append("error", "⚠ " + message)
        self.failed.emit(message)


# ==================================================================== chat widgets
class _ChatBody(QTextBrowser):
    """QTextBrowser không cuộn riêng để bánh xe chuột vẫn cuộn khung chat."""

    def wheelEvent(self, e):
        e.ignore()


def _chat_css(color: str, user: bool = False) -> str:
    border = "rgba(255,255,255,0.38)" if user else C["border"]
    th_bg = "rgba(255,255,255,0.16)" if user else C["primary_soft"]
    code_bg = "rgba(255,255,255,0.18)" if user else C["chip"]
    link = "#EAF0FF" if user else C["primary"]
    return (f"body {{ color: {color}; }}"
            f"p {{ margin: 0 0 7px 0; color: {color}; }}"
            f"li {{ margin: 2px 0; color: {color}; }}"
            f"h1, h2, h3, h4 {{ color: {color}; margin: 2px 0 5px 0; font-weight: 800; }}"
            f"table {{ border-collapse: collapse; margin: 6px 0 8px 0; }}"
            f"th, td {{ border: 1px solid {border}; padding: 6px 10px; }}"
            f"th {{ background: {th_bg}; font-weight: 700; }}"
            f"code {{ background: {code_bg}; padding: 1px 4px; }}"
            f"a {{ color: {link}; }}")


class ChatBubble(QFrame):
    """Một tin nhắn: avatar + bong bóng bo tròn, không có khung lồng bên trong.

    Mọi stylesheet đều kèm selector (#BubbleAI/#BubbleUser/#BubbleErr) để không
    rò border/background xuống QTextBrowser con.
    """

    PAD_X, PAD_TOP, PAD_BOTTOM = 16, 12, 13

    def __init__(self, text, role):
        super().__init__()
        self._text = str(text)
        self._max = 760
        is_user = role == "user"
        is_error = role == "error"

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)
        if is_user:
            h.addStretch(1)
        else:
            h.addWidget(IconTile("alert" if is_error else "sparkles",
                                 C["red"] if is_error else C["primary"],
                                 C["red_soft"] if is_error else C["primary_soft"],
                                 30, 15, 15), 0, Qt.AlignTop)

        box = QFrame()
        if is_user:
            box.setObjectName("BubbleUser")
            box.setStyleSheet(
                f"QFrame#BubbleUser {{ background: {C['primary']}; border: none; border-radius: 16px;"
                " border-bottom-right-radius: 6px; }"
                "QFrame#BubbleUser QLabel { background: transparent; }")
        elif is_error:
            box.setObjectName("BubbleErr")
            box.setStyleSheet(
                f"QFrame#BubbleErr {{ background: {C['red_soft']}; border: 1px solid {C['red_border']};"
                " border-radius: 16px; border-bottom-left-radius: 6px; }"
                "QFrame#BubbleErr QLabel { background: transparent; }")
        else:
            box.setObjectName("BubbleAI")
            box.setStyleSheet(
                f"QFrame#BubbleAI {{ background: {C['surface']}; border: 1px solid {C['border']};"
                " border-radius: 16px; border-bottom-left-radius: 6px; }"
                "QFrame#BubbleAI QLabel { background: transparent; }")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(self.PAD_X, self.PAD_TOP, self.PAD_X, self.PAD_BOTTOM)
        bl.setSpacing(0)

        self.body = _ChatBody()
        self.body.setFrameShape(QFrame.NoFrame)
        self.body.setOpenExternalLinks(True)
        self.body.setReadOnly(True)
        self.body.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body.setFocusPolicy(Qt.NoFocus)
        self.body.setContentsMargins(0, 0, 0, 0)
        color = "white" if is_user else C["text"]
        self.body.setStyleSheet(f"QTextBrowser {{ background: transparent; border: none; color: {color}; }}")
        doc = self.body.document()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(QFont(FONT_FAMILY, 10))
        doc.setDefaultStyleSheet(_chat_css(color, is_user))
        doc.setMarkdown(prepare_markdown(self._text), QTextDocument.MarkdownDialectGitHub)
        bl.addWidget(self.body)
        h.addWidget(box, 0)
        if not is_user:
            h.addStretch(1)
        self.box = box

    def _chrome(self) -> int:
        return 2 * self.PAD_X + 2  # padding + viền

    def set_max_width(self, px):
        """Bề rộng bong bóng vừa khít nội dung, không kéo dài hết khung chat."""
        self._max = max(220, int(px))
        doc = self.body.document()
        doc.setTextWidth(10000)
        natural = doc.idealWidth()
        has_table = any(line.strip().startswith("|") for line in self._text.split("\n"))
        if natural <= 0:
            longest = max((len(line) for line in self._text.split("\n")), default=0)
            natural = longest * 7.2
        floor = self._max * (0.72 if has_table else 0.46)
        ideal = int(min(self._max, max(floor, natural + self._chrome() + 4)))
        self.box.setFixedWidth(ideal)
        self._fit()

    def _fit(self):
        inner = max(140, self.box.width() - self._chrome())
        doc = self.body.document()
        doc.setTextWidth(inner)
        # Làm tròn LÊN: int() cắt cụt từng làm mất dòng cuối của câu trả lời dài.
        height = int(doc.size().height() + 0.999) + 4
        self.body.setFixedSize(inner, height)


class HistoryPanel(QWidget):
    """Danh sách cuộc trò chuyện: tạo mới, tìm, đổi tên, xoá."""

    def __init__(self, session: ChatSession, host=None):
        super().__init__()
        self.session = session
        self.host = host
        self._loading = False
        self.setFixedWidth(250)
        self.setObjectName("HistoryPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(
            f"#HistoryPanel {{ background: {C['surface2']}; border: none; border-radius: 18px; }}"
            "#HistoryPanel QLabel { background: transparent; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(6)
        head.addWidget(label("Lịch sử trò chuyện", size=11, weight=800, color=C["muted"]), 1)
        self.count = chip("0", C["muted"], C["chip"], 10, 700, "1px 7px")
        head.addWidget(self.count)
        root.addLayout(head)

        self.new_btn = QPushButton("＋  Đoạn chat mới")
        self.new_btn.setObjectName("Primary")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.setFixedHeight(38)
        self.new_btn.clicked.connect(self.session.new_chat)
        root.addWidget(self.new_btn)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm cuộc trò chuyện…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedHeight(36)
        self.search.textChanged.connect(self.refresh)
        root.addWidget(self.search)

        self.list = QListWidget()
        self.list.setFrameShape(QFrame.NoFrame)
        self.list.setWordWrap(False)
        self.list.setTextElideMode(Qt.ElideRight)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setStyleSheet(
            "QListWidget { background: transparent; border: none; outline: 0; }"
            f"QListWidget::item {{ padding: 10px 12px; border-radius: 10px; color: {C['text2']}; }}"
            f"QListWidget::item:hover {{ background: {C['chip']}; }}"
            f"QListWidget::item:selected {{ background: {C['primary_soft']}; color: {C['primary']}; font-weight: 700; }}")
        self.list.currentItemChanged.connect(self._pick)
        root.addWidget(self.list, 1)

        self.empty = label("Chưa có cuộc trò chuyện nào.", size=11, color=C["muted"], wrap=True)
        self.empty.hide()
        root.addWidget(self.empty)

        acts = QHBoxLayout()
        acts.setSpacing(6)
        self.rename_btn = QPushButton("Đổi tên")
        self.rename_btn.setObjectName("Ghost")
        self.rename_btn.setCursor(Qt.PointingHandCursor)
        self.rename_btn.clicked.connect(self._rename)
        self.del_btn = QPushButton("Xoá")
        self.del_btn.setObjectName("Danger")
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.clicked.connect(self._delete)
        for b in (self.rename_btn, self.del_btn):
            b.setStyleSheet("padding: 6px 8px; font-size: 12px;")
        acts.addWidget(self.rename_btn, 1)
        acts.addWidget(self.del_btn, 1)
        root.addLayout(acts)

        self.session.history_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self._loading = True
        cur = self.session.session_id
        q = self.search.text().strip().lower()
        self.list.clear()
        shown = 0
        for s in self.session.store.sessions:
            preview = self._preview(s)
            if q and q not in s["title"].lower() and q not in preview.lower():
                continue
            it = QListWidgetItem(s["title"])
            it.setSizeHint(QSize(0, 42))
            it.setData(Qt.UserRole, s["id"])
            it.setToolTip(f"{self._when(s.get('updated'))}\n{len(s['messages'])} tin nhắn\n{preview}")
            self.list.addItem(it)
            if s["id"] == cur:
                self.list.setCurrentItem(it)
            shown += 1
        self.count.setText(str(len(self.session.store.sessions)))
        self.empty.setVisible(shown == 0)
        self._loading = False

    def _pick(self, cur, _prev=None):
        if self._loading or cur is None:
            return
        sid = cur.data(Qt.UserRole)
        if sid and sid != self.session.session_id:
            self.session.switch(sid)

    def _selected(self) -> str | None:
        it = self.list.currentItem()
        return it.data(Qt.UserRole) if it else None

    def _rename(self):
        sid = self._selected()
        if not sid:
            return
        s = self.session.store.get(sid)
        title, ok = QInputDialog.getText(self, "Đổi tên cuộc trò chuyện", "Tên mới:",
                                         text=s["title"] if s else "")
        if ok and title.strip():
            self.session.rename_chat(sid, title.strip()[:80])

    def _delete(self):
        sid = self._selected()
        s = self.session.store.get(sid) if sid else None
        if not s:
            return
        if MessageDialog.confirm(self, "Xoá cuộc trò chuyện",
                                 f'Xoá "{s["title"]}" và toàn bộ tin nhắn trong đó?', "Xoá"):
            self.session.delete_chat(sid)
            if self.host and hasattr(self.host, "toast"):
                self.host.toast("Đã xoá cuộc trò chuyện", "info")

    @staticmethod
    def _when(ts):
        try:
            dt = datetime.fromtimestamp(float(ts))
        except (TypeError, ValueError, OSError):
            return ""
        if dt.date() == datetime.now().date():
            return dt.strftime("Hôm nay %H:%M")
        return dt.strftime("%d/%m/%Y %H:%M")

    @staticmethod
    def _preview(s) -> str:
        for m in reversed(s.get("messages") or []):
            return re.sub(r"\s+", " ", str(m.get("content") or ""))[:90]
        return "Chưa có tin nhắn"


QUICK_PROMPTS = [
    ("Phân tích tiến độ", "Hãy phân tích tổng quan tiến độ học tập của tôi, dự báo khả năng tốt nghiệp và xếp loại."),
    ("Cảnh báo học tập", "Tôi có thuộc diện cảnh báo học tập không? Nếu có, hãy nêu mức độ và 4 việc cần làm ngay."),
    ("Kế hoạch học lại", "Lập kế hoạch học lại chi tiết cho các học phần tôi không đạt, ưu tiên môn mở khoá nhiều môn sau."),
    ("Phương pháp học", "Đề xuất phương pháp học phù hợp với điểm số hiện tại của tôi, nêu môn áp dụng cụ thể."),
]


class _ComposerInput(QLineEdit):
    """Ô nhập có báo focus để khung soạn thảo đổi màu viền."""

    focused = Signal(bool)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.focused.emit(True)

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.focused.emit(False)


class SuggestionBlock(QWidget):
    """Gợi ý câu hỏi nhanh, chỉ hiện khi cuộc trò chuyện chưa có tin nhắn nào."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setMaximumWidth(640)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 2, 4, 6)
        outer.setSpacing(8)
        outer.addWidget(label("Gợi ý nhanh", size=11, weight=700, color=C["muted"]))
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        for i, (text, prompt) in enumerate(QUICK_PROMPTS):
            b = QPushButton(text)
            b.setObjectName("Suggest")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, p=prompt: self.session.send(p))
            grid.addWidget(b, i // 2, i % 2)
        for col in range(2):
            grid.setColumnStretch(col, 1)
        outer.addLayout(grid)


class ChatWidget(QWidget):
    """Khung chat (dùng cho tab Trò chuyện và bong bóng nổi)."""

    QUICK = QUICK_PROMPTS

    def __init__(self, session: ChatSession, host=None, compact=False):
        super().__init__()
        self.session = session
        self.host = host
        self.compact = compact
        self._suggest = None
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)
        self.history = None
        if not compact:
            self.history = HistoryPanel(session, host)
            outer.addWidget(self.history)
        col = QWidget()
        col.setObjectName("ChatCol")
        col.setStyleSheet("#ChatCol { background: transparent; }")
        root = QVBoxLayout(col)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        outer.addWidget(col, 1)

        # Khung "canvas" bo tròn bao trọn vùng tin nhắn + ô soạn thảo. Bản compact nằm
        # trong popup đã có viền riêng nên không lồng thêm khung (tránh ô vuông lồng nhau).
        if compact:
            canvas_lay = root
            self.canvas = None
        else:
            self.canvas = QFrame()
            self.canvas.setObjectName("ChatCanvas")
            self.canvas.setAttribute(Qt.WA_StyledBackground, True)
            canvas_box = QVBoxLayout(self.canvas)
            canvas_box.setContentsMargins(12, 12, 12, 12)
            canvas_box.setSpacing(8)
            root.addWidget(self.canvas, 1)
            canvas_lay = canvas_box

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        self.msg_host = QWidget()
        self.msg_host.setStyleSheet("background: transparent;")
        self.msgs = QVBoxLayout(self.msg_host)
        self.msgs.setContentsMargins(2, 2, 8, 2)
        self.msgs.setSpacing(14)
        self.msgs.addStretch(1)
        self.scroll.setWidget(self.msg_host)
        canvas_lay.addWidget(self.scroll, 1)

        self.typing = label("AI đang soạn câu trả lời…", size=11, color=C["muted"])
        self.typing.setContentsMargins(40, 0, 0, 0)
        self.typing.hide()
        canvas_lay.addWidget(self.typing)

        self.composer = QFrame()
        self.composer.setObjectName("Composer")
        self.composer.setProperty("focus", False)
        self.composer.setProperty("onCanvas", "false" if compact else "true")
        self.composer.setAttribute(Qt.WA_StyledBackground, True)
        crow = QHBoxLayout(self.composer)
        crow.setContentsMargins(14, 5, 5, 5)
        crow.setSpacing(8)
        self.input = _ComposerInput()
        self.input.setObjectName("ComposerInput")
        self.input.setPlaceholderText("Hỏi AI về học tập, cảnh báo, học lại, tốt nghiệp…")
        self.input.setMinimumHeight(38)
        self.input.returnPressed.connect(self._on_send)
        self.input.focused.connect(self._set_focus)
        crow.addWidget(self.input, 1)
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setIcon(icon("arrow", "white", 17))
        self.send_btn.setIconSize(QSize(18, 18))
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setToolTip("Gửi câu hỏi (Enter)")
        self.send_btn.clicked.connect(self._on_send)
        crow.addWidget(self.send_btn)
        canvas_lay.addWidget(self.composer)

        self.bubbles: list[ChatBubble] = []
        self.session.appended.connect(self._on_appended)
        self.session.busy_changed.connect(self._on_busy)
        self.session.switched.connect(self._on_switched)
        self._reset_messages()

    # -- render
    def _on_appended(self, role, text):
        self._render(role, text)

    def _on_switched(self, _sid):
        self._reset_messages()

    def _set_focus(self, on):
        self.composer.setProperty("focus", bool(on))
        st = self.composer.style()
        st.unpolish(self.composer)
        st.polish(self.composer)
        self.composer.update()

    def _add_suggestions(self):
        if self.compact or self._suggest is not None:
            return
        self._suggest = SuggestionBlock(self.session)
        self.msgs.insertWidget(self.msgs.count() - 1, self._suggest)

    def _reset_messages(self):
        while self.msgs.count():
            item = self.msgs.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.deleteLater()
        self.bubbles.clear()
        self._suggest = None
        self.msgs.addStretch(1)
        msgs = self.session.messages
        if msgs:
            for m in msgs:
                self._render(m["role"], m["content"])
        else:
            self._render("assistant", WELCOME_TEXT)
            self._add_suggestions()
        QTimer.singleShot(0, self.reflow)
        QTimer.singleShot(0, self._scroll_bottom)

    def bubble_width(self) -> int:
        """Bề rộng tối đa của bong bóng, luôn nằm trong vùng nhìn thấy của khung chat.

        Bản compact (popup 460px) từng rơi vào nhánh dự phòng 700px nên nội dung bị
        cắt ngang và mất dòng cuối.
        """
        vp = self.scroll.viewport().width()
        if vp <= 0:
            vp = max(280, self.width() - 40)
        return max(220, int(vp) - 46)

    def _render(self, role, text):
        if role in ("user", "error") and self._suggest is not None:
            self._suggest.hide()
            self._suggest.deleteLater()
            self._suggest = None
        b = ChatBubble(text, role)
        b.set_max_width(self.bubble_width())
        self.msgs.insertWidget(self.msgs.count() - 1, b)
        self.bubbles.append(b)
        # Bong bóng có thể được vẽ lúc khung chat chưa có kích thước thật (popup đang ẩn,
        # tab chưa mở) → luôn tính lại bề rộng sau khi vòng lặp sự kiện chạy.
        QTimer.singleShot(0, self.reflow)
        QTimer.singleShot(0, self._scroll_bottom)

    def _scroll_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self.reflow)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.reflow()

    def reflow(self):
        """Tính lại bề rộng/chiều cao bong bóng khi khung chat đã có kích thước thật."""
        if self.scroll.viewport().width() <= 0:
            return
        w = self.bubble_width()
        for b in self.bubbles:
            b.set_max_width(w)

    # -- send
    def _on_send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        if not self.session.send(text):
            if self.host and hasattr(self.host, "toast"):
                self.host.toast("AI đang trả lời, vui lòng đợi…", "info")

    def _on_busy(self, busy):
        self.send_btn.setEnabled(not busy)
        self.input.setEnabled(not busy)
        self.typing.setVisible(busy)
        if not busy:
            self.input.setFocus()
        else:
            QTimer.singleShot(0, self._scroll_bottom)

    def focus_input(self):
        self.input.setFocus()


# ==================================================================== alert rows
class AlertRow(SoftRow):
    """Một cảnh báo học tập: nền pha màu nhấn rất nhẹ, đọc rõ trong cả theme sáng và tối."""

    ICONS = {"danger": "alert", "warning": "alert", "info": "bell", "good": "award", "coach": "sparkles"}
    COLORS = {"danger": "red", "warning": "amber", "info": "primary", "good": "green",
              "coach": "violet"}

    def __init__(self, alert):
        ic = self.ICONS.get(alert.level, "bell")
        col = C[self.COLORS.get(alert.level, "primary")]
        super().__init__(col, radius=14, fill=34, bar=True)
        h = QHBoxLayout(self)
        h.setContentsMargins(16, 12, 14, 12)
        h.setSpacing(12)
        h.addWidget(IconTile(ic, col, tint(col, 42), 32, 17, 16), 0, Qt.AlignTop)
        v = QVBoxLayout()
        v.setSpacing(3)
        v.addWidget(label(alert.title, size=13, weight=800, color=C["text"], wrap=True))
        detail = label(alert.detail, size=12, color=C["text2"], wrap=True)
        detail.setTextFormat(Qt.PlainText)
        v.addWidget(detail)
        h.addLayout(v, 1)


# ==================================================================== overview tab
class AnalysisTab(QWidget):
    ask = Signal(str)
    open_courses = Signal()

    def __init__(self, book, host=None, session=None):
        super().__init__()
        self.book = book
        self.host = host
        self.session = session
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(16)

        b_refresh = QPushButton("  Làm mới phân tích")
        b_refresh.setObjectName("Ghost")
        b_refresh.setIcon(icon("refresh", C["text2"], 16))
        b_refresh.setCursor(Qt.PointingHandCursor)
        b_refresh.clicked.connect(self.refresh)
        b_warn = QPushButton("  AI đánh giá nguy cơ")
        b_warn.setObjectName("Primary")
        b_warn.setIcon(icon("sparkles", "white", 16))
        b_warn.setCursor(Qt.PointingHandCursor)
        b_warn.clicked.connect(lambda: self.ask.emit(
            "Hãy đánh giá nguy cơ cảnh báo học tập của tôi theo quy chế: nêu mức độ, lý do bằng số liệu "
            "và 4 hành động ưu tiên trong 2 tuần tới."))
        root.addWidget(page_header("Tổng quan AI",
                                   "Phân tích tự động từ bảng điểm: cảnh báo học tập, tiến độ tốt nghiệp, "
                                   "kế hoạch học lại – cập nhật ngay sau mỗi lần lưu điểm",
                                   [b_refresh, b_warn]))

        row = QHBoxLayout()
        row.setSpacing(12)
        self.card_cpa = self._stat("CPA tích lũy (hệ 4)", "target", C["primary"], C["primary_soft"])
        self.card_credits = self._stat("Tín chỉ tích lũy", "cap", C["amber"], C["amber_soft"])
        self.card_failed = self._stat("Học phần không đạt", "alert", C["red"], C["red_soft"])
        self.card_risk = self._stat("Mức cảnh báo", "bell", C["violet"], C["violet_soft"])
        for c in (self.card_cpa, self.card_credits, self.card_failed, self.card_risk):
            row.addWidget(c[0], 1)
        root.addLayout(row)

        alerts = Card()
        head = QHBoxLayout()
        head.addWidget(IconTile("bell", C["red"], C["red_soft"], 38, 20, 11))
        head.addWidget(label("Cảnh báo học tập", "CardTitle"), 1)
        self.alert_chip = chip("0", C["red"], C["red_soft"], 11, 800)
        head.addWidget(self.alert_chip)
        alerts.lay.addLayout(head)
        self.alert_box = QVBoxLayout()
        self.alert_box.setSpacing(8)
        alerts.lay.addLayout(self.alert_box)
        root.addWidget(alerts)

        # Hai cột độc lập (kiểu masonry): mỗi thẻ ôm đúng nội dung, không thẻ nào bị kéo
        # cao theo thẻ bên cạnh nên không còn khoảng trống thừa bên trong hay giữa các thẻ.
        cols = QHBoxLayout()
        cols.setSpacing(14)
        left_col = QVBoxLayout()
        left_col.setSpacing(14)
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        grad = Card()
        gh = QHBoxLayout()
        gh.addWidget(IconTile("award", C["green"], C["green_soft"], 38, 20, 11))
        gh.addWidget(label("Tiến độ tốt nghiệp", "CardTitle"), 1)
        self.pace_chip = chip("—", C["muted"], C["chip"], 11, 700)
        gh.addWidget(self.pace_chip)
        grad.lay.addLayout(gh)
        gr = QHBoxLayout()
        self.grad_ring = Ring(112, 11, C["green"], "#34D399")
        gr.addWidget(self.grad_ring)
        gv = QVBoxLayout()
        gv.setSpacing(3)
        self.grad_pct = label("0 / 156 tín chỉ", size=20, weight=800, color=C["primary"])
        self.grad_detail = label("", size=12, color=C["text2"], wrap=True)
        self.grad_detail.setTextFormat(Qt.RichText)
        gv.addWidget(self.grad_pct)
        gv.addWidget(self.grad_detail)
        gv.addStretch(1)
        gr.addLayout(gv, 1)
        grad.lay.addLayout(gr)
        left_col.addWidget(grad)

        retake = Card()
        rh = QHBoxLayout()
        rh.addWidget(IconTile("refresh", C["amber"], C["amber_soft"], 38, 20, 11))
        rh.addWidget(label("Kế hoạch học lại", "CardTitle"), 1)
        self.retake_chip = chip("0", C["amber"], C["amber_soft"], 11, 800)
        rh.addWidget(self.retake_chip)
        retake.lay.addLayout(rh)
        self.retake_box = QVBoxLayout()
        self.retake_box.setSpacing(7)
        # Nhận toàn bộ chiều cao còn lại của thẻ để không còn mảng trắng dưới nội dung.
        retake.lay.addLayout(self.retake_box, 1)
        right_col.addWidget(retake)

        nxt = Card()
        nh = QHBoxLayout()
        nh.addWidget(IconTile("calendar", C["primary"], C["primary_soft"], 38, 20, 11))
        nh.addWidget(label("Học kỳ tiếp theo", "CardTitle"), 1)
        nxt.lay.addLayout(nh)
        self.next_box = QVBoxLayout()
        self.next_box.setSpacing(6)
        nxt.lay.addLayout(self.next_box)
        right_col.addWidget(nxt)

        # ---- Quy chế & chuẩn đầu ra (QĐ 2244/2021, 4511/2022, 417/2016, 1414/2021)
        policy = Card()
        ph = QHBoxLayout()
        ph.addWidget(IconTile("check", C["green"], C["green_soft"], 38, 20, 11))
        ph.addWidget(label("Quy chế & chuẩn đầu ra", "CardTitle"), 1)
        self.policy_chip = chip("—", C["muted"], C["chip"], 11, 700)
        ph.addWidget(self.policy_chip)
        policy.lay.addLayout(ph)
        self.policy_box = QVBoxLayout()
        self.policy_box.setSpacing(5)
        policy.lay.addLayout(self.policy_box)
        self.cb_english = QCheckBox("Đã có chứng chỉ ngoại ngữ chuẩn đầu ra")
        self.cb_it = QCheckBox("Đã có chứng nhận CNTT IU01–IU06")
        for cb in (self.cb_english, self.cb_it):
            cb.setCursor(Qt.PointingHandCursor)
            cb.toggled.connect(self._save_profile)
            policy.lay.addWidget(cb)
        self.policy_saved = label("", size=10, color=C["faint"], wrap=True)
        policy.lay.addWidget(self.policy_saved)
        right_col.addWidget(policy)

        todo = Card()
        th = QHBoxLayout()
        th.addWidget(IconTile("check", C["violet"], C["violet_soft"], 38, 20, 11))
        th.addWidget(label("Việc cần làm tuần này", "CardTitle"), 1)
        todo.lay.addLayout(th)
        self.todo_box = QVBoxLayout()
        self.todo_box.setSpacing(6)
        todo.lay.addLayout(self.todo_box)
        left_col.addWidget(todo)
        # Cân chiều cao hai cột: trái (tiến độ + việc tuần này) ~ phải (học lại + học kỳ tới).
        left_col.addStretch(1)
        right_col.addStretch(1)
        cols.addLayout(left_col, 1)
        cols.addLayout(right_col, 1)
        root.addLayout(cols)
        root.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))

    def _profile_dir(self):
        from pathlib import Path
        return Path(self.book.path).parent

    def _save_profile(self, *_):
        """Lưu hồ sơ chuẩn đầu ra để kiểm tra tốt nghiệp/học bổng theo quy chế."""
        import rules as rules_mod
        prof = rules_mod.load_profile(self._profile_dir())
        prof["english_ok"] = self.cb_english.isChecked()
        prof["it_ok"] = self.cb_it.isChecked()
        rules_mod.save_profile(self._profile_dir(), prof)
        self.policy_saved.setText("Đã lưu hồ sơ – các mục tốt nghiệp đã cập nhật.")
        self.refresh()

    def _stat(self, title, ic, col, bg):
        f = QFrame()
        f.setObjectName("Card")
        shadow(f, 20, 4, 14)
        h = QHBoxLayout(f)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(11)
        h.addWidget(IconTile(ic, col, bg, 42, 21, 12))
        v = QVBoxLayout()
        v.setSpacing(0)
        v.addWidget(label(title, size=11, weight=600, color=C["muted"]))
        val = label("—", size=21, weight=800)
        v.addWidget(val)
        h.addLayout(v, 1)
        return f, val

    # -- refresh
    def refresh(self):
        an = LocalAnalytics(self.book)
        rep = an.report()
        g = rep.graduation

        self.card_cpa[1].setText(fmt(rep.cpa4))
        self.card_credits[1].setText(f"{core.fmt_credits(rep.credits_passed)} / {core.PROGRAM['total_credits']}")
        self.card_failed[1].setText(str(len(rep.failed)))
        dangerous = [a for a in rep.alerts if a.level == "danger"]
        warning = [a for a in rep.alerts if a.level == "warning"]
        self.card_risk[1].setText("Cao" if dangerous else ("Trung bình" if warning else "Thấp"))

        clear_layout(self.alert_box)
        if rep.alerts:
            for a in rep.alerts:
                self.alert_box.addWidget(AlertRow(a))
        else:
            self.alert_box.addWidget(label("Chưa có cảnh báo. Hãy nhập điểm để AI phân tích.",
                                           size=12, color=C["muted"]))
        self.alert_chip.setText(f"{len(rep.alerts)}")

        self.grad_ring.set(min(1.0, g["frac"]), f"{g['frac'] * 100:.0f}%", "hoàn thành")
        self.grad_pct.setText(f"{core.fmt_credits(g['credits'])} / {g['total']} tín chỉ")
        lines = [f"Còn <b>{core.fmt_credits(g['credits_left'])}</b> tín chỉ để đủ điều kiện tốt nghiệp."]
        lines.append(f"CPA tốt nghiệp cần <b>≥ 2.00</b> — hiện tại <b>{fmt(g['cpa4'])}</b> "
                     f"({'đạt' if g['cpa_ok'] else 'chưa đạt'}).")
        need25 = an.required_future_gpa(2.5)
        if need25 is not None and g["credits_left"] > 0:
            verdict = "khả thi" if need25 <= 3.5 else ("khó" if need25 <= 4.0 else "rất khó")
            lines.append(f"Để CPA tốt nghiệp đạt 2.5 (loại Khá): GPA các tín chỉ còn lại cần ≈ "
                         f"<b>{need25:.2f}/4</b> ({verdict}).")
        if g["est_sems_left"]:
            lines.append(f"Dự kiến còn <b>{g['est_sems_left']} học kỳ</b> nếu giữ tốc độ hiện tại.")
        self.grad_detail.setText("<br>".join(lines))
        pace = g["pace"]
        col, bg = (C["green"], C["green_soft"]) if pace in ("Đúng tiến độ", "Nhanh tiến độ") else \
                  ((C["red"], C["red_soft"]) if pace == "Chậm tiến độ" else (C["muted"], C["chip"]))
        self.pace_chip.setText(pace)
        self.pace_chip.setStyleSheet(f"background:{bg}; color:{col}; border-radius:9px; padding:4px 10px;"
                                     f" font-size:11px; font-weight:700;")

        clear_layout(self.retake_box)
        self.retake_chip.setText(str(len(rep.retake_plan)))
        if rep.retake_plan:
            for i, p in enumerate(rep.retake_plan[:6]):
                f = SoftRow(None, radius=12)
                # Giữ đúng chiều cao tự nhiên của hàng: nếu để hàng giãn kín thẻ, khoảng
                # cách giữa tên môn và dòng chi tiết bị kéo rộng và số thứ tự trôi lệch.
                f.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
                h = QHBoxLayout(f)
                h.setContentsMargins(14, 10, 14, 11)
                h.setSpacing(10)
                num = label(str(i + 1), size=17, weight=800, color=C["primary"])
                num.setFixedWidth(22)
                num.setAlignment(Qt.AlignCenter)
                h.addWidget(num, 0, Qt.AlignVCenter)
                v = QVBoxLayout()
                v.setSpacing(2)
                v.addWidget(label(p.name, size=12, weight=700, wrap=True))
                v.addWidget(label(f"{p.credits:g} TC • điểm cũ {p.old_total:.1f} • HK{p.semester}",
                                  size=11, color=C["muted"]))
                h.addLayout(v, 1)
                h.addWidget(chip(p.suggest_when.split(" (")[0], C["amber"], C["amber_soft"], 10, 800, "3px 8px"),
                            0, Qt.AlignVCenter)
                self.retake_box.addWidget(f)
            # Chỗ trống còn lại nằm dưới danh sách, không nhồi vào bên trong hàng.
            self.retake_box.addStretch(1)
        else:
            good = SoftRow(C["green"], radius=12, bar=True)
            good.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            gh = QHBoxLayout(good)
            gh.setContentsMargins(16, 11, 14, 11)
            ic = QLabel()
            ic.setPixmap(icon_pixmap("check", C["green"], 18))
            gh.addWidget(ic, 0, Qt.AlignVCenter)
            gh.addWidget(label("Không có học phần không đạt – tuyệt vời!", size=12, weight=700,
                               color=C["green"]), 1, Qt.AlignVCenter)
            self.retake_box.addWidget(good)

        clear_layout(self.next_box)
        info = self.book.next_semester_info()
        if info:
            st = info["stats"]
            body = (f"HK{info['semester']}: <b>{st['n_plan']} học phần</b> "
                    f"({core.fmt_credits(st['credits_plan'])} tín chỉ)")
            if st["electives_needed"]:
                body += f" — {st['n_required']} bắt buộc + {st['electives_needed']} tự chọn"
            self.next_box.addWidget(label(body, size=13, color=C["text"], wrap=True))
            self.next_box.addWidget(label(f"Đã có điểm: {st['n_done']}/{st['n_plan']}"
                                          + (f" • Bị khoá: {len(info['locked'])}" if info["locked"] else ""),
                                          size=12, color=C["muted"], wrap=True))
            for c in (info["open"] or info["locked"])[:4]:
                row = QHBoxLayout()
                li = QLabel()
                ic = "lock" if c in info["locked"] else ("star" if c["elective"] else "book")
                col = C["amber"] if c in info["locked"] else (C["violet"] if c["elective"] else C["primary"])
                li.setPixmap(icon_pixmap(ic, col, 16))
                row.addWidget(li)
                row.addWidget(label(f"{c['name']} ({c['credits']:g} TC)", size=12, color=C["text2"], wrap=True), 1)
                self.next_box.addLayout(row)
        else:
            self.next_box.addWidget(label("Bạn đã hoàn thành toàn bộ chương trình hoặc chưa xong kỳ hiện tại.",
                                          size=12, color=C["muted"], wrap=True))

        clear_layout(self.todo_box)
        for i, text in enumerate(StudyAdvisor(self.book).action_items(rep), 1):
            row = QHBoxLayout()
            bullet = QLabel(str(i))
            bullet.setFixedSize(20, 20)
            bullet.setAlignment(Qt.AlignCenter)
            bullet.setStyleSheet(f"background:{C['primary_soft']}; color:{C['primary']}; border-radius:10px;"
                                 f" font-size:11px; font-weight:800;")
            row.addWidget(bullet, 0, Qt.AlignTop)
            txt = label(text, size=12, color=C["text2"], wrap=True)
            txt.setMinimumWidth(0)
            row.addWidget(txt, 1)
            self.todo_box.addLayout(row)
        self.todo_box.addStretch(1)

        # ---- mục quy chế (cảnh báo, giới hạn đăng ký, điều kiện tốt nghiệp, học bổng)
        clear_layout(self.policy_box)
        comp = rep.compliance or {}
        warn = comp.get("warning") or {}
        reg = comp.get("registration") or {}
        prof = comp.get("profile") or {}
        for cb, key in ((self.cb_english, "english_ok"), (self.cb_it, "it_ok")):
            cb.blockSignals(True)
            cb.setChecked(bool(prof.get(key)))
            cb.blockSignals(False)

        lvl = warn.get("level", "none")
        if lvl == "dismiss_risk":
            text, col, bg = "Nguy cơ buộc thôi học", C["red"], C["red_soft"]
        elif lvl == "warning":
            text, col, bg = "Bị cảnh báo", C["amber"], C["amber_soft"]
        else:
            text, col, bg = "An toàn", C["green"], C["green_soft"]
        self.policy_chip.setText(text)
        self.policy_chip.setStyleSheet(f"background:{bg}; color:{col}; border-radius:9px;"
                                       f" padding:4px 10px; font-size:11px; font-weight:700;")

        if warn.get("reasons"):
            for r in warn["reasons"]:
                self.policy_box.addWidget(label(f"• {r}", size=12, color=C["red"], wrap=True))
            self.policy_box.addWidget(label(warn.get("source", ""), size=10, color=C["faint"], wrap=True))
        else:
            self.policy_box.addWidget(label(
                f"Không thuộc diện cảnh báo: TB học kỳ ≥ {warn.get('semester_threshold', 1.0):.2f}, "
                f"CPA ≥ {warn.get('cpa_threshold', 1.8):.2f} (năm {warn.get('year', 1)}).",
                size=12, color=C["text2"], wrap=True))
        if reg:
            self.policy_box.addWidget(label(
                f"Đăng ký học kỳ tới: {reg['min']}–{reg['max']} TC (hè ≤ {reg['summer_max']} TC). "
                f"{reg['note']}", size=12, color=C["text2"], wrap=True))
        gitems = comp.get("graduation") or []
        if gitems:
            done = sum(1 for it in gitems if it["ok"])
            self.policy_box.addWidget(label(f"Điều kiện tốt nghiệp: {done}/{len(gitems)} đạt",
                                           size=12, weight=700, color=C["text"]))
            for it in gitems:
                row = QHBoxLayout()
                row.setSpacing(7)
                mark = QLabel("✓" if it["ok"] else "✗")
                mark.setStyleSheet(f"color:{C['green'] if it['ok'] else C['red']};"
                                   f" font-size:13px; font-weight:900;")
                mark.setFixedWidth(14)
                row.addWidget(mark, 0, Qt.AlignTop)
                row.addWidget(label(f"{it['label']} — {it['detail']}", size=11,
                                    color=C["text2"], wrap=True), 1)
                self.policy_box.addLayout(row)
        sch = comp.get("scholarship")
        if sch:
            self.policy_box.addWidget(label(
                f"Học bổng KKHT: đủ điều kiện loại {sch['code']} ({sch['name']}), "
                f"mức {int(sch['factor'] * 100)}% học phí.", size=12, color=C["green"], wrap=True))


# ==================================================================== plan tab
class PlanTab(QWidget):
    def __init__(self, book, host=None):
        super().__init__()
        self.book = book
        self.host = host
        self._raw = ""
        self._bridge = None
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(16)
        root.addWidget(page_header("Phương pháp học & Kế hoạch",
                                   "Gợi ý cá nhân hoá theo điểm số, học phần bị khoá và tiến độ tốt nghiệp"))

        # --- lịch tuần
        week = Card()
        wh = QHBoxLayout()
        wh.addWidget(IconTile("calendar", C["primary"], C["primary_soft"], 38, 20, 11))
        wh.addWidget(label("Thời khoá biểu tuần gợi ý", "CardTitle"), 1)
        self.week_chip = chip("2–3 giờ/ngày", C["primary"], C["primary_soft"], 11, 700)
        wh.addWidget(self.week_chip)
        week.lay.addLayout(wh)
        self.week_box = QVBoxLayout()
        self.week_box.setSpacing(8)
        week.lay.addLayout(self.week_box)
        root.addWidget(week)

        # --- phương pháp
        methods = Card()
        mh = QHBoxLayout()
        mh.addWidget(IconTile("sparkles", C["violet"], C["violet_soft"], 38, 20, 11))
        mh.addWidget(label("Phương pháp học phù hợp", "CardTitle"), 1)
        methods.lay.addLayout(mh)
        self.methods_box = QVBoxLayout()
        self.methods_box.setSpacing(8)
        methods.lay.addLayout(self.methods_box)
        root.addWidget(methods)

        # --- lịch học lại
        retake = Card()
        rh = QHBoxLayout()
        rh.addWidget(IconTile("refresh", C["amber"], C["amber_soft"], 38, 20, 11))
        rh.addWidget(label("Lịch học lại theo học kỳ", "CardTitle"), 1)
        retake.lay.addLayout(rh)
        self.retake_box = QVBoxLayout()
        self.retake_box.setSpacing(8)
        retake.lay.addLayout(self.retake_box)
        root.addWidget(retake)

        # --- AI soạn kế hoạch
        ai = Card()
        ah = QHBoxLayout()
        ah.addWidget(IconTile("target", C["green"], C["green_soft"], 38, 20, 11))
        ah.addWidget(label("AI soạn kế hoạch chi tiết", "CardTitle"), 1)
        self.ai_status = chip("Online API", C["green"], C["green_soft"], 11, 700)
        ah.addWidget(self.ai_status)
        ai.lay.addLayout(ah)
        btns = QHBoxLayout()
        btns.setSpacing(8)
        self.b_plan = self._ai_button("Kế hoạch 4 tuần", "plan")
        self.b_method = self._ai_button("Phương pháp cá nhân hoá", "methods")
        self.b_warn = self._ai_button("Đánh giá cảnh báo", "warning")
        self.b_grad = self._ai_button("Phân tích tốt nghiệp", "graduation")
        for b in (self.b_plan, self.b_method, self.b_warn, self.b_grad):
            btns.addWidget(b)
        btns.addStretch(1)
        self.b_copy = QPushButton("  Sao chép")
        self.b_copy.setObjectName("Ghost")
        self.b_copy.setIcon(icon("download", C["text2"], 15))
        self.b_copy.setCursor(Qt.PointingHandCursor)
        self.b_copy.clicked.connect(self._copy)
        self.b_copy.setEnabled(False)
        btns.addWidget(self.b_copy)
        ai.lay.addLayout(btns)

        out_box = SoftRow(None, radius=14)
        out_lay = QVBoxLayout(out_box)
        out_lay.setContentsMargins(16, 14, 16, 14)
        self.output = QLabel("Chọn một nút phía trên để AI soạn nội dung dựa trên bảng điểm thật của bạn.")
        self.output.setWordWrap(True)
        self.output.setTextFormat(Qt.RichText)
        self.output.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.output.setStyleSheet(f"background: transparent; border: none; color: {C['text2']}; font-size: 13px;")
        self.output.setMinimumHeight(70)
        out_lay.addWidget(self.output)
        ai.lay.addWidget(out_box)
        root.addWidget(ai)
        root.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))

    def _ai_button(self, text, kind):
        b = QPushButton("  " + text)
        b.setObjectName("Ghost")
        b.setIcon(icon("sparkles", C["violet"], 15))
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda _=False, k=kind: self._generate(k))
        return b

    # -- data driven
    def refresh(self):
        advisor = StudyAdvisor(self.book)
        rep = LocalAnalytics(self.book).report()

        clear_layout(self.week_box)
        plan = advisor.weekly_plan(rep)
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, day in enumerate(plan):
            box = SoftRow(None, radius=12)
            v = QVBoxLayout(box)
            v.setContentsMargins(13, 11, 13, 12)
            v.setSpacing(4)
            top = QHBoxLayout()
            top.addWidget(label(day["day"], size=12, weight=800, color=C["primary"]), 1)
            top.addWidget(label(day["hours"], size=10, weight=700, color=C["muted"]))
            v.addLayout(top)
            v.addWidget(label(day["focus"], size=11, weight=700, color=C["text"], wrap=True))
            for task in day["tasks"][:3]:
                task_lbl = label("• " + task, size=10, color=C["text2"], wrap=True)
                task_lbl.setMinimumWidth(0)
                task_lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                v.addWidget(task_lbl)
            box.setMinimumWidth(0)
            for child in box.findChildren(QLabel):
                child.setMinimumWidth(0)
            grid.addWidget(box, i // 3, i % 3)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        self.week_box.addLayout(grid)

        clear_layout(self.methods_box)
        for m in advisor.methods(rep):
            row = SoftRow(None, radius=12)
            h = QHBoxLayout(row)
            h.setContentsMargins(14, 11, 14, 11)
            h.setSpacing(10)
            h.addWidget(chip(m.get("tag", "Gợi ý"), C["violet"], C["violet_soft"], 10, 800, "3px 8px"), 0, Qt.AlignTop)
            v = QVBoxLayout()
            v.setSpacing(2)
            v.addWidget(label(m["title"], size=12, weight=800, color=C["text"], wrap=True))
            v.addWidget(label(m["detail"], size=12, color=C["text2"], wrap=True))
            h.addLayout(v, 1)
            self.methods_box.addWidget(row)

        clear_layout(self.retake_box)
        schedule = advisor.retake_schedule(rep)
        if not schedule:
            self.retake_box.addWidget(label("Không có học phần cần học lại.", size=12, color=C["green"]))
        for g in schedule:
            box = SoftRow(C["amber"], radius=12, bar=True)
            v = QVBoxLayout(box)
            v.setContentsMargins(16, 11, 14, 12)
            v.setSpacing(4)
            top = QHBoxLayout()
            top.addWidget(label(f"Học kỳ {g['semester']}", size=12, weight=800, color=C["amber"]), 1)
            top.addWidget(label(f"{g['credits']:g} tín chỉ", size=11, weight=700, color=C["amber"]))
            v.addLayout(top)
            for p in g["courses"]:
                v.addWidget(label(f"• {p.name} — điểm cũ {p.old_total:.1f} ({p.credits:g} TC)",
                                  size=12, color=C["text2"], wrap=True))
            v.addWidget(label(g["note"], size=11, color=C["muted"], wrap=True))
            self.retake_box.addWidget(box)

        cfg = load_api_config()
        self.ai_status.setText(f"Online API • {cfg.get('model') or AI_MODEL}")

    # -- AI generation
    def _generate(self, kind):
        if self._bridge is not None:
            if self.host and hasattr(self.host, "toast"):
                self.host.toast("AI đang soạn nội dung, vui lòng đợi…", "info")
            return
        client = AIClient()
        if not client.configured():
            self.output.setText("⚠ Chưa cấu hình API key. Mở tab “Cài đặt AI” để kiểm tra.")
            return
        context = LocalAnalytics(self.book).context_text()
        messages = build_messages(kind, context)
        self._raw = ""
        self.b_copy.setEnabled(False)
        for b in (self.b_plan, self.b_method, self.b_warn, self.b_grad):
            b.setEnabled(False)
        self.output.setText("AI đang phân tích bảng điểm và soạn nội dung… (có thể mất 10–40 giây)")
        bridge = _Bridge(self)
        bridge.ok.connect(self._on_ok)
        bridge.err.connect(self._on_err)
        self._bridge = bridge
        client.chat(messages, bridge.ok.emit, bridge.err.emit, temperature=0.55, max_tokens=1800)

    def _reset_buttons(self):
        self._bridge = None
        for b in (self.b_plan, self.b_method, self.b_warn, self.b_grad):
            b.setEnabled(True)

    def _on_ok(self, text):
        self._reset_buttons()
        self._raw = text
        self.output.setText(to_rich(text))
        self.b_copy.setEnabled(True)
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("AI đã soạn xong nội dung", "success")

    def _on_err(self, message):
        self._reset_buttons()
        self._raw = ""
        self.output.setText("⚠ " + html.escape(message))
        self.b_copy.setEnabled(False)

    def _copy(self):
        if not self._raw:
            return
        QApplication.clipboard().setText(self._raw)
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("Đã sao chép nội dung AI", "success")


# ==================================================================== automation tab
class AutomationTab(QWidget):
    def __init__(self, book, engine: AutomationEngine | None = None, host=None):
        super().__init__()
        self.book = book
        self.engine = engine
        self.host = host
        self._rows: list[Reminder] = []
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)

        b_now = QPushButton("  Chạy kiểm tra ngay")
        b_now.setObjectName("Ghost")
        b_now.setIcon(icon("refresh", C["primary"], 16))
        b_now.setCursor(Qt.PointingHandCursor)
        b_now.clicked.connect(self._run_now)
        b_coach = QPushButton("  AI lời khuyên hôm nay")
        b_coach.setObjectName("Primary")
        b_coach.setIcon(icon("sparkles", "white", 16))
        b_coach.setCursor(Qt.PointingHandCursor)
        b_coach.clicked.connect(self._ask_coach)
        root.addWidget(page_header("Tự động hoá nhắc nhở",
                                   "Tự động cảnh báo học tập, nhắc giờ học và gửi lời khuyên AI – "
                                   "chạy nền ngay cả khi bạn đang ở trang khác",
                                   [b_now, b_coach]))

        status = Card()
        sh = QHBoxLayout()
        sh.addWidget(IconTile("bell", C["amber"], C["amber_soft"], 38, 20, 11))
        sv = QVBoxLayout()
        sv.setSpacing(1)
        sv.addWidget(label("Trạng thái tự động hoá", "CardTitle"))
        self.status_lbl = label("Đang khởi động…", size=12, color=C["muted"], wrap=True)
        sv.addWidget(self.status_lbl)
        sh.addLayout(sv, 1)
        self.count_chip = chip("0 nhắc nhở", C["primary"], C["primary_soft"], 11, 700)
        sh.addWidget(self.count_chip)
        status.lay.addLayout(sh)
        root.addWidget(status)

        # ---- cài đặt
        cfg_card = Card()
        ch = QHBoxLayout()
        ch.addWidget(IconTile("settings", C["primary"], C["primary_soft"], 38, 20, 11))
        ch.addWidget(label("Cài đặt nhắc nhở", "CardTitle"), 1)
        cfg_card.lay.addLayout(ch)

        self.cb_enabled = QCheckBox("Bật tự động hoá")
        self.cb_study = QCheckBox("Nhắc giờ học hằng ngày")
        self.cb_warn = QCheckBox("Cảnh báo học tập")
        self.cb_failed = QCheckBox("Học phần không đạt")
        self.cb_locked = QCheckBox("Học phần bị khoá")
        self.cb_grad = QCheckBox("Rủi ro tốt nghiệp")
        self.cb_coach = QCheckBox("AI coach hằng ngày")
        self.cb_weekly = QCheckBox("Tổng kết tuần (Chủ nhật)")
        self.cb_tray = QCheckBox("Thông báo qua khay hệ thống")
        self.cb_quiet = QCheckBox("Giờ yên tĩnh")
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        for i, cb in enumerate((self.cb_enabled, self.cb_warn, self.cb_failed, self.cb_locked,
                                self.cb_grad, self.cb_study, self.cb_coach, self.cb_weekly,
                                self.cb_tray, self.cb_quiet)):
            grid.addWidget(cb, i // 3, i % 3)
        cfg_card.lay.addLayout(grid)

        times = QHBoxLayout()
        times.setSpacing(14)
        times.addWidget(label("Giờ học:", size=12, weight=600, color=C["text2"]))
        self.time_study = QTimeEdit()
        self.time_study.setDisplayFormat("HH:mm")
        times.addWidget(self.time_study)
        times.addSpacing(10)
        times.addWidget(label("Giờ AI coach:", size=12, weight=600, color=C["text2"]))
        self.time_coach = QTimeEdit()
        self.time_coach.setDisplayFormat("HH:mm")
        times.addWidget(self.time_coach)
        times.addSpacing(10)
        times.addWidget(label("Tần suất kiểm tra:", size=12, weight=600, color=C["text2"]))
        self.interval = QComboBox()
        for minutes in (15, 30, 60, 120, 240):
            self.interval.addItem(f"{minutes} phút", minutes)
        times.addWidget(self.interval)
        times.addStretch(1)
        self.save_btn = QPushButton("  Lưu cài đặt")
        self.save_btn.setObjectName("Primary")
        self.save_btn.setIcon(icon("save", "white", 15))
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)
        times.addWidget(self.save_btn)
        cfg_card.lay.addLayout(times)
        root.addWidget(cfg_card)

        # ---- danh sách nhắc nhở
        list_card = Card()
        lh = QHBoxLayout()
        lh.addWidget(IconTile("bell", C["red"], C["red_soft"], 38, 20, 11))
        lh.addWidget(label("Hộp nhắc nhở", "CardTitle"), 1)
        self.b_read = QPushButton("Đã đọc tất cả")
        self.b_read.setObjectName("Ghost")
        self.b_read.setCursor(Qt.PointingHandCursor)
        self.b_read.clicked.connect(self._read_all)
        lh.addWidget(self.b_read)
        self.b_clear = QPushButton("Dọn đã xong")
        self.b_clear.setObjectName("Ghost")
        self.b_clear.setCursor(Qt.PointingHandCursor)
        self.b_clear.clicked.connect(self._clear_done)
        lh.addWidget(self.b_clear)
        list_card.lay.addLayout(lh)
        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(8)
        list_card.lay.addLayout(self.list_box)
        root.addWidget(list_card)
        root.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))

        self._load()
        if self.engine:
            self.engine.changed.connect(self.refresh_list)
        self.refresh_list()

    # -- config
    def _load(self):
        cfg = self.engine.cfg if self.engine else AUTO_DEFAULT
        self.cb_enabled.setChecked(bool(cfg.get("enabled", True)))
        self.cb_study.setChecked(bool(cfg.get("daily_study_reminder", True)))
        self.cb_warn.setChecked(bool(cfg.get("academic_warning", True)))
        self.cb_failed.setChecked(bool(cfg.get("failed_course", True)))
        self.cb_locked.setChecked(bool(cfg.get("locked_course", True)))
        self.cb_grad.setChecked(bool(cfg.get("graduation_risk", True)))
        self.cb_coach.setChecked(bool(cfg.get("ai_coach", True)))
        self.cb_weekly.setChecked(bool(cfg.get("weekly_review", True)))
        self.cb_tray.setChecked(bool(cfg.get("tray_notify", True)))
        self.cb_quiet.setChecked(bool(cfg.get("quiet_enabled", False)))
        for widget, key, fallback in ((self.time_study, "study_time", (19, 30)),
                                      (self.time_coach, "ai_coach_time", (8, 0))):
            h, m = parse_hhmm(cfg.get(key, ""), fallback)
            widget.setTime(QTime(h, m))
        idx = self.interval.findData(int(cfg.get("check_interval_min", 30) or 30))
        self.interval.setCurrentIndex(idx if idx >= 0 else 1)

    def _save(self):
        if not self.engine:
            return
        cfg = {
            "enabled": self.cb_enabled.isChecked(),
            "daily_study_reminder": self.cb_study.isChecked(),
            "academic_warning": self.cb_warn.isChecked(),
            "failed_course": self.cb_failed.isChecked(),
            "locked_course": self.cb_locked.isChecked(),
            "graduation_risk": self.cb_grad.isChecked(),
            "ai_coach": self.cb_coach.isChecked(),
            "weekly_review": self.cb_weekly.isChecked(),
            "tray_notify": self.cb_tray.isChecked(),
            "quiet_enabled": self.cb_quiet.isChecked(),
            "study_time": self.time_study.time().toString("HH:mm"),
            "ai_coach_time": self.time_coach.time().toString("HH:mm"),
            "check_interval_min": int(self.interval.currentData() or 30),
        }
        self.engine.update(cfg)
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("Đã lưu cài đặt tự động hoá", "success")
        self.refresh_status()
        self.engine.refresh(force=True, notify=False)

    def _run_now(self):
        if not self.engine:
            return
        new = self.engine.refresh(force=True)
        if self.host and hasattr(self.host, "toast"):
            self.host.toast(f"Đã kiểm tra xong – {len(new)} nhắc nhở mới", "info" if not new else "warning")
        self.refresh_status()
        self.refresh_list()

    def _ask_coach(self):
        if not self.engine:
            return
        if not self.engine.request_digest(force=True):
            if self.host and hasattr(self.host, "toast"):
                self.host.toast("AI đang bận hoặc chưa cấu hình API", "warning")

    def _read_all(self):
        if self.engine:
            self.engine.store.mark_all_read()
            self.engine.changed.emit()

    def _clear_done(self):
        if self.engine:
            self.engine.store.clear_done()
            self.engine.changed.emit()

    # -- list
    def refresh_status(self):
        if not self.engine:
            self.status_lbl.setText("Chưa khởi tạo bộ tự động hoá.")
            return
        s = self.engine.summary()
        state = "đang bật" if self.engine.cfg.get("enabled", True) else "đang tắt"
        self.status_lbl.setText(f"Tự động hoá {state} • {self.engine.next_check_text()} • "
                                f"{s['unseen']} chưa đọc, {s['danger']} mức nguy hiểm")
        self.count_chip.setText(f"{s['active']} nhắc nhở")

    def refresh_list(self):
        self.refresh_status()
        clear_layout(self.list_box)
        if not self.engine:
            self.list_box.addWidget(label("Chưa có bộ tự động hoá.", size=12, color=C["muted"]))
            return
        items = self.engine.store.active(limit=30)
        if not items:
            self.list_box.addWidget(label("Chưa có nhắc nhở nào. Hệ thống sẽ tự tạo khi cần.",
                                          size=12, color=C["muted"]))
            return
        for r in items:
            self.list_box.addWidget(self._row_widget(r))

    def _row_widget(self, r: Reminder) -> QFrame:
        palette = {"danger": (C["red"], C["red_soft"]), "warning": (C["amber"], C["amber_soft"]),
                   "good": (C["green"], C["green_soft"]), "coach": (C["violet"], C["violet_soft"])}
        col, bg = palette.get(r.level, (C["primary"], C["primary_soft"]))
        f = QFrame()
        f.setStyleSheet(f"QFrame#R {{ background:{C['surface2']}; border:1px solid {C['border']}; border-radius:12px; }}"
                        f" QFrame#R[unread='true'] {{ border-color:{col}; background:{bg}; }}")
        f.setObjectName("R")
        f.setProperty("unread", "true" if not r.read else "false")
        h = QHBoxLayout(f)
        h.setContentsMargins(11, 9, 11, 9)
        h.setSpacing(10)
        icon_name = "sparkles" if r.kind == "coach" else ("refresh" if r.kind == "retake" else
                                                          ("calendar" if r.kind in ("semester", "weekly") else "bell"))
        tile = QLabel()
        tile.setPixmap(icon_pixmap(icon_name, col, 19))
        h.addWidget(tile, 0, Qt.AlignTop)
        v = QVBoxLayout()
        v.setSpacing(2)
        top = QHBoxLayout()
        top.addWidget(label(r.title, size=12, weight=800, color=C["text"], wrap=True), 1)
        top.addWidget(chip("MỚI" if not r.read else "ĐÃ ĐỌC", col if not r.read else C["muted"],
                           bg if not r.read else C["chip"], 9, 800, "2px 6px"), 0, Qt.AlignTop)
        v.addLayout(top)
        body = QLabel()
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        body.setText(to_rich(r.body))
        body.setStyleSheet(f"background:transparent; color:{C['text2']}; font-size:12px;")
        v.addWidget(body)
        actions = QHBoxLayout()
        actions.setSpacing(6)
        if not r.read:
            b = QPushButton("Đã đọc")
            b.setObjectName("Pill")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, rid=r.rid: self._mark_read(rid))
            actions.addWidget(b)
        b2 = QPushButton("Xong")
        b2.setObjectName("Pill")
        b2.setCursor(Qt.PointingHandCursor)
        b2.clicked.connect(lambda _=False, rid=r.rid: self._mark_done(rid))
        actions.addWidget(b2)
        b3 = QPushButton("Hoãn 1 ngày")
        b3.setObjectName("Pill")
        b3.setCursor(Qt.PointingHandCursor)
        b3.clicked.connect(lambda _=False, rid=r.rid: self._snooze(rid))
        actions.addWidget(b3)
        actions.addStretch(1)
        v.addLayout(actions)
        h.addLayout(v, 1)
        return f

    def _mark_read(self, rid):
        if self.engine:
            self.engine.store.mark_read(rid)
            self.engine.changed.emit()

    def _mark_done(self, rid):
        if self.engine:
            self.engine.store.mark_done(rid)
            self.engine.changed.emit()

    def _snooze(self, rid):
        if self.engine:
            self.engine.store.snooze(rid, 24)
            self.engine.changed.emit()


# ==================================================================== settings tab
class SettingsTab(QWidget):
    def __init__(self, host=None):
        super().__init__()
        self.host = host
        self._bridge = None
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)
        root.addWidget(page_header("Cài đặt AI", "Chế độ ONLINE API – trợ lý luôn gọi máy chủ AI, không dùng model offline"))

        mode = Card()
        mh = QHBoxLayout()
        mh.addWidget(IconTile("sparkles", C["green"], C["green_soft"], 42, 22, 12))
        mv = QVBoxLayout()
        mv.setSpacing(2)
        mv.addWidget(label("Chế độ AI", "CardTitle"))
        mv.addWidget(label("Chỉ online API: mọi câu trả lời, kế hoạch và lời khuyên đều do AI online tạo. "
                           "Phân tích cảnh báo/kế hoạch học lại cơ bản vẫn chạy offline để luôn sẵn sàng.",
                           size=12, color=C["muted"], wrap=True))
        mh.addLayout(mv, 1)
        mh.addWidget(chip("ONLINE API", C["green"], C["green_soft"], 11, 800, "5px 11px"), 0, Qt.AlignTop)
        mode.lay.addLayout(mh)
        info = QGridLayout()
        info.setHorizontalSpacing(14)
        info.setVerticalSpacing(6)
        self.lbl_endpoint = label(AI_BASE_URL, size=12, color=C["text2"], wrap=True)
        self.lbl_model = label(AI_MODEL, size=12, weight=700, color=C["primary"])
        self.lbl_key = label(mask_key(load_api_config().get("api_key", "")), size=12, color=C["text2"])
        for row, (title, widget) in enumerate((("BASE_URL", self.lbl_endpoint),
                                               ("MODEL", self.lbl_model),
                                               ("API KEY", self.lbl_key))):
            info.addWidget(label(title, size=10, weight=800, color=C["muted"]), row, 0)
            info.addWidget(widget, row, 1)
        info.setColumnStretch(1, 1)
        mode.lay.addLayout(info)
        root.addWidget(mode)

        conn = Card()
        ch = QHBoxLayout()
        ch.addWidget(IconTile("link", C["primary"], C["primary_soft"], 38, 20, 11))
        ch.addWidget(label("Kiểm tra kết nối", "CardTitle"), 1)
        self.test_btn = QPushButton("  Kiểm tra")
        self.test_btn.setObjectName("Primary")
        self.test_btn.setIcon(icon("link", "white", 15))
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.clicked.connect(self._test)
        ch.addWidget(self.test_btn)
        conn.lay.addLayout(ch)
        self.test_result = label("Chưa kiểm tra. Bấm “Kiểm tra” để xác nhận máy chủ AI đang chạy.",
                                 size=12, color=C["muted"], wrap=True)
        conn.lay.addWidget(self.test_result)
        root.addWidget(conn)

        edit = Card()
        eh = QHBoxLayout()
        eh.addWidget(IconTile("settings", C["violet"], C["violet_soft"], 38, 20, 11))
        eh.addWidget(label("Tuỳ chỉnh kết nối (nâng cao)", "CardTitle"), 1)
        edit.lay.addLayout(eh)
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.inp_url = QLineEdit()
        self.inp_url.setPlaceholderText(AI_BASE_URL)
        self.inp_model = QLineEdit()
        self.inp_model.setPlaceholderText(AI_MODEL)
        self.inp_key = QLineEdit()
        self.inp_key.setEchoMode(QLineEdit.Password)
        self.inp_key.setClearButtonEnabled(True)
        for row, (title, widget, hint) in enumerate((
                ("BASE_URL", self.inp_url, "Ví dụ: http://127.0.0.1:31415/v1"),
                ("MODEL", self.inp_model, "Mặc định: auto:smart (router tự chọn model tốt nhất)"),
                ("API KEY", self.inp_key, "Để trống nếu giữ khoá hiện tại; dán khoá mới để thay đổi"))):
            form.addWidget(label(title, size=10, weight=800, color=C["muted"]), row * 2, 0)
            form.addWidget(widget, row * 2, 1)
            form.addWidget(label(hint, size=10, color=C["faint"]), row * 2 + 1, 1)
        form.setColumnStretch(1, 1)
        edit.lay.addLayout(form)
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_reset = QPushButton("  Khôi phục mặc định")
        self.btn_reset.setObjectName("Ghost")
        self.btn_reset.setIcon(icon("refresh", C["text2"], 15))
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self._reset)
        btns.addWidget(self.btn_reset)
        self.btn_save = QPushButton("  Lưu cài đặt")
        self.btn_save.setObjectName("Primary")
        self.btn_save.setIcon(icon("save", "white", 15))
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._save)
        btns.addWidget(self.btn_save)
        edit.lay.addLayout(btns)
        root.addWidget(edit)

        tips = Card()
        tips.lay.addWidget(label("Lưu ý", "CardTitle"))
        for text in ("Trợ lý chỉ hoạt động với API online. Khi mất mạng, phần cảnh báo học tập và kế hoạch "
                     "học lại cơ bản vẫn phân tích được từ dữ liệu điểm.",
                     "Không chia sẻ API key. Khoá được lưu cục bộ trong %APPDATA%\\TinHocXayDung.",
                     "Nếu kết nối lỗi: kiểm tra dịch vụ AI đang chạy, đúng BASE_URL và model tồn tại."):
            tips.lay.addWidget(label("• " + text, size=12, color=C["text2"], wrap=True))
        root.addWidget(tips)
        root.addStretch(1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll_page(inner))
        self._load()

    def _load(self):
        cfg = load_api_config()
        self.inp_url.setText(cfg.get("base_url", AI_BASE_URL))
        self.inp_model.setText(cfg.get("model", AI_MODEL))
        key = cfg.get("api_key", "")
        # Không đổ khoá vào ô (Password echo hiển thị kém); placeholder cho biết đã có khoá.
        self.inp_key.clear()
        self.inp_key.setPlaceholderText(
            f"Đã lưu: {mask_key(key)} — nhập khoá mới để thay đổi" if key
            else "Chưa có API key — dán khoá vào đây")
        self.lbl_endpoint.setText(cfg.get("base_url", AI_BASE_URL))
        self.lbl_model.setText(cfg.get("model", AI_MODEL))
        self.lbl_key.setText(mask_key(cfg.get("api_key", "")))

    def _save(self):
        cfg = {
            "base_url": self.inp_url.text().strip() or AI_BASE_URL,
            "model": self.inp_model.text().strip() or AI_MODEL,
            "api_key": self.inp_key.text().strip() or load_api_config().get("api_key", ""),
        }
        save_api_config(cfg)
        self._load()
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("Đã lưu cài đặt AI online", "success")

    def _reset(self):
        reset_api_config()
        self._load()
        self.test_result.setText("Đã khôi phục cấu hình mặc định (BASE_URL, API key, model auto:smart).")
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("Đã khôi phục cài đặt AI mặc định", "info")

    def _test(self):
        if self._bridge is not None:
            return
        cfg = {
            "base_url": self.inp_url.text().strip() or AI_BASE_URL,
            "model": self.inp_model.text().strip() or AI_MODEL,
            "api_key": self.inp_key.text().strip(),
        }
        if not cfg["api_key"]:
            self.test_result.setText("⚠ Chưa nhập API key.")
            return
        client = AIClient(cfg)
        self.test_btn.setEnabled(False)
        self.test_result.setText("Đang kiểm tra kết nối tới máy chủ AI…")
        bridge = _Bridge(self)
        bridge.obj.connect(self._test_ok)
        bridge.err.connect(self._test_err)
        self._bridge = bridge

        def worker():
            try:
                bridge.obj.emit(client.check())
            except AIError as e:
                bridge.err.emit(str(e))
            except Exception as e:  # pragma: no cover
                bridge.err.emit(f"Lỗi không xác định: {e}")

        threading.Thread(target=worker, daemon=True, name="ai-check").start()

    def _test_ok(self, info):
        self._bridge = None
        self.test_btn.setEnabled(True)
        models = info.get("models") or []
        found = info.get("current") in models
        text = f"✓ Kết nối thành công – máy chủ có {info.get('count', len(models))} model."
        if models:
            text += " Model hiện tại: " + (f"{info.get('current')} (có sẵn)" if found else
                                           f"{info.get('current')} (không thấy trong danh sách, vẫn có thể dùng)")
        self.test_result.setText(text)
        self.test_result.setStyleSheet(f"color:{C['green']}; font-size:12px;")
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("Kết nối AI thành công", "success")

    def _test_err(self, message):
        self._bridge = None
        self.test_btn.setEnabled(True)
        self.test_result.setText("✗ " + message)
        self.test_result.setStyleSheet(f"color:{C['red']}; font-size:12px;")
        if self.host and hasattr(self.host, "toast"):
            self.host.toast("Không kết nối được AI", "error")


# ==================================================================== AI page
class AIPage(QWidget):
    #: (khoá, nhãn) của 5 khu vực trợ lý AI
    TABS = (("overview", "Tổng quan AI"), ("chat", "Trò chuyện AI"),
            ("plan", "Kế hoạch học tập"), ("automation", "Tự động hoá"),
            ("settings", "Cài đặt AI"))

    def __init__(self, book, host=None, engine: AutomationEngine | None = None, session: ChatSession | None = None):
        super().__init__()
        self.book = book
        self.host = host
        self.engine = engine
        self.session = session or ChatSession(book, self)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 14)
        root.setSpacing(12)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabBar(SegmentedTabBar())
        self.tabs.setStyleSheet("QTabWidget::pane { border: none; background: transparent; }"
                                "QTabBar { background: transparent; border: none; }")
        self.tabs.setFocusPolicy(Qt.NoFocus)

        self.analysis = AnalysisTab(book, host, self.session)
        self.chat_tab = ChatWidget(self.session, host, compact=False)
        self.plan = PlanTab(book, host)
        self.automation = AutomationTab(book, engine, host)
        self.settings = SettingsTab(host)

        for (_, title), widget in zip(self.TABS, (self.analysis, self.chat_tab, self.plan,
                                                  self.automation, self.settings)):
            self.tabs.addTab(widget, title)
        # Thanh tab mặc định được thay bằng segmented nav tự vẽ: bo tròn chuẩn và
        # không bao giờ đè lên nội dung (QTabWidget vẫn giữ nguyên API tab).
        self.tabs.tabBar().hide()

        nav = QFrame()
        nav.setObjectName("SegNav")
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(5, 4, 5, 4)
        nav_lay.setSpacing(2)
        group = QButtonGroup(self)
        group.setExclusive(True)
        self.nav_btns = []
        for i, (_, title) in enumerate(self.TABS):
            b = QPushButton(title)
            b.setObjectName("SegBtn")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(lambda _=False, i=i: self.tabs.setCurrentIndex(i))
            group.addButton(b, i)
            nav_lay.addWidget(b)
            self.nav_btns.append(b)
        self.nav_btns[0].setChecked(True)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(nav, 0)
        top.addStretch(1)
        cfg = load_api_config()
        self.mode_chip = chip(f"Online API • {cfg.get('model') or AI_MODEL}",
                              C["green"], C["green_soft"], 11, 700, "5px 11px")
        top.addWidget(self.mode_chip, 0, Qt.AlignVCenter)
        root.addLayout(top)
        root.addWidget(self.tabs, 1)

        self.analysis.ask.connect(self.ask_ai)
        self.tabs.currentChanged.connect(self._on_tab)

    def _on_tab(self, index):
        if 0 <= index < len(self.nav_btns):
            self.nav_btns[index].setChecked(True)
        widget = self.tabs.widget(index)
        if widget is self.chat_tab:
            QTimer.singleShot(0, self.chat_tab.reflow)
            QTimer.singleShot(80, self.chat_tab.focus_input)
        elif widget is self.plan:
            self.plan.refresh()
        elif widget is self.automation:
            self.automation.refresh_status()
            self.automation.refresh_list()
        elif widget is self.analysis:
            self.analysis.refresh()

    def refresh(self):
        self.analysis.refresh()
        self.plan.refresh()
        self.automation.refresh_status()

    def ask_ai(self, text: str):
        self.tabs.setCurrentWidget(self.chat_tab)
        self.session.send(text)

    def open_tab(self, name: str):
        mapping = {"overview": self.analysis, "chat": self.chat_tab, "plan": self.plan,
                   "automation": self.automation, "settings": self.settings}
        widget = mapping.get(name)
        if widget:
            self.tabs.setCurrentWidget(widget)


# ==================================================================== floating
class ChatPopup(QFrame):
    """Cửa sổ chat nổi (con của cửa sổ chính)."""

    def __init__(self, session: ChatSession, open_page=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ChatPopup")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"#ChatPopup {{ background:{C['surface']}; border:1px solid {C['border']};"
                           f" border-radius:18px; }}")
        self.setFixedSize(460, 620)
        shadow(self, 44, 10, 70)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(9)
        head.addWidget(IconTile("sparkles", C["primary"], C["primary_soft"], 38, 20, 12))
        tv = QVBoxLayout()
        tv.setSpacing(0)
        tv.addWidget(label("Trợ lý AI học tập", size=14, weight=800, color=C["text"]))
        cfg = load_api_config()
        tv.addWidget(label(f"Online API • {cfg.get('model') or AI_MODEL}", size=10,
                           color=C["muted"]))
        head.addLayout(tv, 1)
        b_page = QPushButton("Trang AI")
        b_page.setObjectName("Pill")
        b_page.setCursor(Qt.PointingHandCursor)
        if open_page:
            b_page.clicked.connect(open_page)
        head.addWidget(b_page)
        b_close = QPushButton("×")
        b_close.setFixedSize(28, 28)
        b_close.setCursor(Qt.PointingHandCursor)
        b_close.setStyleSheet(f"QPushButton {{ background:{C['chip']}; color:{C['muted']}; border:none;"
                              f" border-radius:14px; font-size:13px; font-weight:800; }}"
                              f"QPushButton:hover {{ background:{C['red_soft']}; color:{C['red']}; }}")
        b_close.clicked.connect(self.hide)
        head.addWidget(b_close)
        lay.addLayout(head)

        self.chat = ChatWidget(session, None, compact=True)
        lay.addWidget(self.chat, 1)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(e)


class FloatingChatBubble(QFrame):
    """Bong bóng chat nổi ở góc dưới-phải, có badge số nhắc nhở chưa đọc."""

    open_page = Signal()

    def __init__(self, session: ChatSession, parent=None):
        super().__init__(parent)
        self.setFixedSize(66, 66)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Trợ lý AI học tập – bấm để hỏi nhanh")
        self.setAttribute(Qt.WA_Hover)
        self._badge = 0
        self._hover = False
        self._popup = ChatPopup(session, self._goto_page, None)
        self._popup.hide()
        shadow(self, 38, 10, 70)

    # -- paint
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing)
        r = self.rect().adjusted(5, 5, -5, -5)
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, QColor("#1427B8" if not self._hover else "#1F3BFF"))
        grad.setColorAt(1, QColor("#1F3BFF" if not self._hover else "#4C66FF"))
        p.setPen(QPen(QColor("#FFFFFF" if not self._hover else C["yellow"]), 2.4))
        p.setBrush(QBrush(grad))
        p.drawEllipse(r)
        pm = icon_pixmap("sparkles", C["yellow"], 27)
        p.drawPixmap(int(r.center().x() - 13), int(r.center().y() - 13), pm)
        if self._badge > 0:
            d = 22
            bx, by = self.width() - d - 1, 1
            p.setPen(QPen(QColor("white"), 2))
            p.setBrush(QColor(C["red"]))
            p.drawEllipse(bx, by, d, d)
            p.setPen(QColor("white"))
            f = p.font()
            f.setPixelSize(10)
            f.setBold(True)
            p.setFont(f)
            p.drawText(bx, by, d, d, Qt.AlignCenter, "9+" if self._badge > 9 else str(self._badge))

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    # -- behaviour
    def set_badge(self, count: int):
        if int(count) != self._badge:
            self._badge = max(0, int(count))
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle()
        super().mousePressEvent(e)

    def _goto_page(self):
        self.close_popup()
        self.open_page.emit()

    def toggle(self):
        if self._popup.isVisible():
            self.close_popup()
        else:
            self.show_popup()

    def show_popup(self):
        par = self.parentWidget()
        if par:
            # popup phải là con của vùng nội dung (không phải bubble) để không bị cắt
            self._popup.setParent(par)
            self._popup.move(self._target_pos(par))
        self._popup.show()
        self._popup.raise_()
        self._popup.chat.focus_input()

    def close_popup(self):
        self._popup.hide()

    def _target_pos(self, parent) -> QPoint:
        size = self._popup.size()
        x = self.x() + self.width() - size.width()
        y = self.y() - size.height() - 10
        x = max(10, min(x, parent.width() - size.width() - 10))
        y = max(10, y)
        return QPoint(x, y)

    def place(self, parent_w: int, parent_h: int):
        self.move(max(0, parent_w - self.width() - 26), max(0, parent_h - self.height() - 26))
        if self._popup.isVisible() and self.parentWidget():
            self._popup.move(self._target_pos(self.parentWidget()))
        self.raise_()
