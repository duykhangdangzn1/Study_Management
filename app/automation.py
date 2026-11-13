"""Tự động hoá nhắc nhở học tập.

Gồm 2 tầng:
1. Hàm thuần (không Qt): Reminder, ReminderStore, build_reminders() – kiểm thử được
   không cần giao diện. Sinh nhắc nhở từ dữ liệu điểm: cảnh báo học tập, học lại,
   học phần bị khoá, tiến độ tốt nghiệp, giờ học hằng ngày, tổng kết tuần.
2. AutomationEngine(QObject): bộ điều phối theo thời gian (QTimer), chống trùng lặp,
   giờ yên tĩnh, tự gọi AI tạo "lời khuyên hôm nay", phát signal cho giao diện/tray.

Dữ liệu lưu tại %APPDATA%\\TinHocXayDung\\reminders.json + automation.json
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

import ai_engine
import core
from ai_engine import LocalAnalytics, StudyAdvisor, build_messages

CONFIG_PATH = core.default_data_path().with_name("automation.json")
STORE_PATH = core.default_data_path().with_name("reminders.json")

DEFAULT_CONFIG = {
    "enabled": True,
    "check_interval_min": 30,
    "daily_study_reminder": True,
    "study_time": "19:30",
    "weekly_review": True,
    "academic_warning": True,
    "failed_course": True,
    "locked_course": True,
    "graduation_risk": True,
    "ai_coach": True,
    "ai_coach_time": "08:00",
    "tray_notify": True,
    "quiet_enabled": False,
    "quiet_from": "22:00",
    "quiet_to": "07:00",
    "max_notify_per_check": 2,
    "last_check": 0.0,
}

LEVELS = ("danger", "warning", "info", "good")


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    if isinstance(data, dict):
        for key, value in data.items():
            if key in cfg:
                cfg[key] = value
    return cfg


def save_config(cfg: dict) -> dict:
    merged = load_config()
    merged.update({k: v for k, v in (cfg or {}).items() if k in DEFAULT_CONFIG})
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def parse_hhmm(text: str, fallback=(19, 30)) -> tuple[int, int]:
    try:
        hh, mm = str(text).strip().split(":")
        h, m = int(hh), int(mm)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except (ValueError, AttributeError):
        pass
    return fallback


def _stable_id(prefix: str, key: str) -> str:
    return f"{prefix}-{hashlib.sha1(key.encode('utf-8', 'replace')).hexdigest()[:10]}"


@dataclass
class Reminder:
    rid: str
    kind: str
    level: str
    title: str
    body: str
    created: float = field(default_factory=time.time)
    due: float | None = None
    read: bool = False
    done: bool = False
    snooze_until: float = 0.0
    action: str = ""

    def active(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return not self.done and self.snooze_until <= now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder | None":
        try:
            rid = str(data["rid"])
            return cls(rid=rid, kind=str(data.get("kind", "info")), level=str(data.get("level", "info")),
                       title=str(data.get("title", "")), body=str(data.get("body", "")),
                       created=float(data.get("created") or time.time()),
                       due=float(data["due"]) if data.get("due") else None,
                       read=bool(data.get("read", False)), done=bool(data.get("done", False)),
                       snooze_until=float(data.get("snooze_until") or 0.0),
                       action=str(data.get("action", "")))
        except (KeyError, TypeError, ValueError):
            return None


class ReminderStore:
    """Kho nhắc nhở bền vững, tự chống trùng theo rid."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else STORE_PATH
        self.items: dict[str, Reminder] = {}
        self.load()

    # -- io
    def load(self):
        self.items = {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for raw in data.get("items", []) if isinstance(data, dict) else []:
            r = Reminder.from_dict(raw)
            if r:
                self.items[r.rid] = r

    def persist(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"version": 1, "items": [r.to_dict() for r in self.items.values()]}
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
            return True
        except OSError:
            return False

    # -- ghi
    def add(self, reminder: Reminder, persist: bool = True) -> bool:
        old = self.items.get(reminder.rid)
        if old:
            old.title, old.body, old.level = reminder.title, reminder.body, reminder.level
            old.kind, old.action = reminder.kind, reminder.action
            if old.done:
                return False
            if persist:
                self.persist()
            return False
        self.items[reminder.rid] = reminder
        self.prune()
        if persist:
            self.persist()
        return True

    def mark_read(self, rid: str, read: bool = True):
        r = self.items.get(rid)
        if r:
            r.read = read
            self.persist()

    def mark_all_read(self):
        for r in self.items.values():
            if r.active():
                r.read = True
        self.persist()

    def mark_done(self, rid: str):
        r = self.items.get(rid)
        if r:
            r.done = True
            r.read = True
            self.persist()

    def snooze(self, rid: str, hours: float = 24.0):
        r = self.items.get(rid)
        if r:
            r.snooze_until = time.time() + hours * 3600
            r.read = True
            self.persist()

    def remove(self, rid: str):
        if self.items.pop(rid, None):
            self.persist()

    def clear_done(self):
        self.items = {k: v for k, v in self.items.items() if not v.done}
        self.persist()

    def prune(self, max_age_days: int = 60, limit: int = 300):
        now = time.time()
        drop = [k for k, v in self.items.items()
                if (v.done or v.created < now - max_age_days * 86400) and v.created < now - 86400]
        for k in drop:
            self.items.pop(k, None)
        if len(self.items) > limit:
            for k, _ in sorted(self.items.items(), key=lambda kv: kv[1].created)[: len(self.items) - limit]:
                self.items.pop(k, None)

    # -- đọc
    def unseen_count(self) -> int:
        return sum(1 for r in self.items.values() if r.active() and not r.read)

    def active(self, limit: int | None = None) -> list[Reminder]:
        now = time.time()
        items = [r for r in self.items.values() if r.active(now)]
        items.sort(key=lambda r: (r.read, -r.created))
        return items[:limit] if limit else items

    def history(self, limit: int = 60) -> list[Reminder]:
        items = sorted(self.items.values(), key=lambda r: -r.created)
        return items[:limit]

    def find(self, rid: str) -> Reminder | None:
        return self.items.get(rid)


# --------------------------------------------------------------------- builders
def build_reminders(book: core.GradeBook, cfg: dict | None = None,
                    now: datetime | None = None, analytics: LocalAnalytics | None = None) -> list[Reminder]:
    """Sinh danh sách nhắc nhở từ dữ liệu học tập (không phụ thuộc Qt)."""
    cfg = dict(DEFAULT_CONFIG, **(cfg or {}))
    if not cfg.get("enabled", True):
        return []
    now = now or datetime.now()
    an = analytics or LocalAnalytics(book)
    rep = an.report()
    advisor = StudyAdvisor(book)
    out: list[Reminder] = []
    stamp = now.timestamp()

    # 1) cảnh báo học tập (CPA, học vụ, cảnh báo kỳ tới)
    if cfg.get("academic_warning", True):
        for a in rep.alerts:
            if a.level in ("danger", "warning"):
                out.append(Reminder(_stable_id("warn", a.title), "warning", a.level, a.title, a.detail,
                                    created=stamp, due=stamp, action="Xem tổng quan AI"))

    # 2) học phần không đạt + kế hoạch học lại
    if cfg.get("failed_course", True) and rep.failed:
        names = ", ".join(f"{f['name']} ({f['total']:.1f})" for f in rep.failed[:6])
        more = f" và {len(rep.failed) - 6} học phần khác" if len(rep.failed) > 6 else ""
        body = f"Cần học lại {len(rep.failed)} học phần: {names}{more}."
        if rep.retake_plan:
            body += "\nƯu tiên: " + "; ".join(f"{p.name} – {p.suggest_when}" for p in rep.retake_plan[:3])
        out.append(Reminder("failed-summary", "retake",
                            "danger" if len(rep.failed) >= 3 else "warning",
                            f"{len(rep.failed)} học phần chưa đạt", body, created=stamp, due=stamp,
                            action="Xem kế hoạch học lại"))

    # 3) học phần bị khoá ở kỳ tới
    if cfg.get("locked_course", True):
        info = book.next_semester_info()
        if info and info["locked"]:
            names = ", ".join(c["name"] for c in info["locked"][:4])
            more = f" và {len(info['locked']) - 4} HP khác" if len(info["locked"]) > 4 else ""
            out.append(Reminder(_stable_id("locked", str(info["semester"])), "locked", "warning",
                                f"{len(info['locked'])} học phần HK{info['semester']} bị khoá",
                                f"Chưa đạt học phần học trước: {names}{more}. Cần xử lý trước khi đăng ký.",
                                created=stamp, due=stamp, action="Xem học phần"))

    # 4) rủi ro tiến độ tốt nghiệp
    if cfg.get("graduation_risk", True):
        g = rep.graduation
        if g["pace"] == "Chậm tiến độ" or (g["cpa4"] is not None and g["cpa4"] < 2.0):
            need = an.required_future_gpa(2.0)
            body = (f"Đã tích lũy {core.fmt_credits(g['credits'])}/{g['total']} tín chỉ sau "
                    f"{g['last_semester']} học kỳ. CPA hiện tại {g['cpa4'] if g['cpa4'] is not None else '—'}.")
            if need is not None:
                body += f" Cần GPA trung bình {need}/4 ở các tín chỉ còn lại để đủ điều kiện tốt nghiệp."
            out.append(Reminder(_stable_id("grad", "risk"), "graduation", "danger" if not g["cpa_ok"] else "info",
                                "Tiến độ tốt nghiệp cần chú ý", body, created=stamp, due=stamp,
                                action="Xem tiến độ tốt nghiệp"))

    # 5) nhắc học hằng ngày
    if cfg.get("daily_study_reminder", True):
        hh, mm = parse_hhmm(cfg.get("study_time", "19:30"))
        if now.hour * 60 + now.minute >= hh * 60 + mm:
            focus = advisor.focus_today(rep)
            tip = advisor.methods(rep)[0]["title"] if advisor.methods(rep) else "Pomodoro 25/5"
            body = (f"Hôm nay: {focus}.\nHọc 2–3 hiệp Pomodoro (25 phút tập trung – 5 phút nghỉ). "
                    f"Kỹ thuật gợi ý: {tip}.")
            out.append(Reminder(f"study-{now.date()}", "study", "info", "Đến giờ học tập", body,
                                created=stamp, due=stamp, action="Mở phương pháp học"))

    # 6) tổng kết tuần (Chủ nhật)
    if cfg.get("weekly_review", True) and now.weekday() == 6:
        out.append(Reminder(f"weekly-{now.date()}", "weekly", "info", "Tổng kết tuần học",
                            "Dành 30 phút xem lại điểm, tiến độ tín chỉ và đặt mục tiêu cho tuần tới. "
                            "Kiểm tra các học phần sắp thi/kiểm tra.", created=stamp, due=stamp,
                            action="Xem tổng quan AI"))

    # 7) vừa hoàn thành học kỳ → nhắc đăng ký kỳ tới
    last = book.last_completed_semester()
    if last and last < len(core.SEMESTERS):
        info = book.next_semester_info()
        if info:
            st = info["stats"]
            out.append(Reminder(_stable_id("nextsem", str(last)), "semester", "good",
                                f"Đã xong HK{last} – chuẩn bị HK{info['semester']}",
                                f"HK{info['semester']} có {st['n_plan']} học phần "
                                f"({core.fmt_credits(st['credits_plan'])} tín chỉ). "
                                f"Xem trước đề cương và đọc 1–2 chương đầu.",
                                created=stamp, due=stamp, action="Xem học kỳ tiếp theo"))
    return out


class _Bridge(QObject):
    ok = Signal(str)
    err = Signal(str)


class AutomationEngine(QObject):
    """Điều phối nhắc nhở + AI coach theo thời gian thực."""

    changed = Signal()          # danh sách nhắc nhở thay đổi
    notify = Signal(object)     # Reminder cần hiện thông báo
    digest_ready = Signal(str)  # nội dung AI vừa tạo
    ai_error = Signal(str)
    status = Signal(str)

    def __init__(self, book: core.GradeBook, store: ReminderStore | None = None,
                 cfg: dict | None = None, client_factory=None, parent=None):
        super().__init__(parent)
        self.book = book
        self.store = store or ReminderStore()
        self.cfg = dict(DEFAULT_CONFIG, **(cfg or load_config()))
        self._factory = client_factory or (lambda: ai_engine.AIClient())
        self._last_check = float(self.cfg.get("last_check") or 0.0)
        self._ai_busy = False
        self._ai_fail_until = 0.0
        self._coach_date = ""
        self._running = False
        self._timer = QTimer(self)
        self._timer.setInterval(60_000)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------- vòng đời
    def start(self, initial_delay_ms: int = 1200):
        if self._running:
            return
        self._running = True
        self._timer.start()
        QTimer.singleShot(initial_delay_ms, lambda: self.refresh(force=True, notify=False))

    def stop(self):
        self._running = False
        self._timer.stop()

    @property
    def running(self) -> bool:
        return self._running

    # ------------------------------------------------------------- cấu hình
    def update(self, cfg: dict, persist: bool = True):
        self.cfg = dict(self.cfg, **(cfg or {}))
        if persist:
            self.cfg = save_config(self.cfg)
            self.cfg["last_check"] = self._last_check
        self.status.emit("Đã lưu cài đặt tự động hoá")

    def _quiet(self, now: datetime) -> bool:
        if not self.cfg.get("quiet_enabled"):
            return False
        start = parse_hhmm(self.cfg.get("quiet_from", "22:00"), (22, 0))
        end = parse_hhmm(self.cfg.get("quiet_to", "07:00"), (7, 0))
        cur = now.hour * 60 + now.minute
        a, b = start[0] * 60 + start[1], end[0] * 60 + end[1]
        return (a <= cur or cur < b) if a > b else (a <= cur < b)

    # ------------------------------------------------------------- kiểm tra
    def _interval_sec(self) -> float:
        try:
            return max(5, int(self.cfg.get("check_interval_min", 30))) * 60
        except (TypeError, ValueError):
            return 30 * 60

    def refresh(self, force: bool = False, notify: bool = True) -> list[Reminder]:
        now = datetime.now()
        if not force and self._last_check and (time.time() - self._last_check) < self._interval_sec():
            return []
        self._last_check = time.time()
        self.cfg["last_check"] = self._last_check
        try:
            candidates = build_reminders(self.book, self.cfg, now)
        except Exception as e:  # pragma: no cover - bảo vệ UI
            self.status.emit(f"Không phân tích được dữ liệu: {e}")
            return []
        fresh: list[Reminder] = []
        for r in candidates:
            if self.store.add(r, persist=False):
                fresh.append(r)
        self.store.persist()
        save_config({**self.cfg, "last_check": self._last_check})
        self.changed.emit()
        if notify and fresh and not self._quiet(now):
            limit = max(1, int(self.cfg.get("max_notify_per_check", 2) or 2))
            for r in fresh[:limit]:
                self.notify.emit(r)
        if self.cfg.get("ai_coach") and self._coach_due(now):
            self.request_digest()
        return fresh

    def _coach_due(self, now: datetime) -> bool:
        if not self.cfg.get("ai_coach"):
            return False
        hh, mm = parse_hhmm(self.cfg.get("ai_coach_time", "08:00"), (8, 0))
        if now.hour * 60 + now.minute < hh * 60 + mm:
            return False
        if self._coach_date == str(now.date()):
            return False
        if time.time() < self._ai_fail_until:
            return False
        return f"coach-{now.date()}" not in self.store.items

    def _tick(self):
        if not self.cfg.get("enabled", True):
            return
        now = datetime.now()
        # nhắc giờ học: chỉ cần kiểm tra đúng ngày/đúng mốc
        if self.cfg.get("daily_study_reminder", True):
            hh, mm = parse_hhmm(self.cfg.get("study_time", "19:30"))
            if now.hour * 60 + now.minute >= hh * 60 + mm and f"study-{now.date()}" not in self.store.items:
                self.refresh(force=True)
                return
        self.refresh(force=False)
        if self._coach_due(now):
            self.request_digest()

    # ------------------------------------------------------------- AI coach
    def request_digest(self, force: bool = False) -> bool:
        if self._ai_busy:
            return False
        client = self._factory()
        if not client.configured():
            self.ai_error.emit("Chưa cấu hình API key cho trợ lý AI.")
            return False
        if not force and time.time() < self._ai_fail_until:
            return False
        context = LocalAnalytics(self.book).context_text()
        messages = build_messages("digest", context)
        bridge = _Bridge(self)
        bridge.ok.connect(self._on_digest_ok)
        bridge.err.connect(self._on_digest_err)
        self._busy_bridge = bridge
        self._ai_busy = True
        self._coach_date = str(datetime.now().date())
        self.status.emit("AI đang tạo lời khuyên học tập…")
        client.chat(messages, bridge.ok.emit, bridge.err.emit, temperature=0.5, max_tokens=900)
        return True

    def _on_digest_ok(self, text: str):
        self._ai_busy = False
        now = datetime.now()
        r = Reminder(f"coach-{now.date()}", "coach", "coach", "Lời khuyên AI hôm nay", text,
                     created=time.time(), due=time.time(), action="Mở trò chuyện AI")
        is_new = self.store.add(r)
        self.changed.emit()
        self.status.emit("Đã cập nhật lời khuyên AI hôm nay")
        self.digest_ready.emit(text)
        if is_new and not self._quiet(now):
            self.notify.emit(r)

    def _on_digest_err(self, message: str):
        self._ai_busy = False
        self._ai_fail_until = time.time() + 1800
        self.status.emit(f"Không tạo được lời khuyên AI: {message}")
        self.ai_error.emit(message)

    # ------------------------------------------------------------- tiện ích
    def next_check_text(self) -> str:
        if not self.cfg.get("enabled", True):
            return "Tự động hoá đang tắt"
        remaining = self._interval_sec() - (time.time() - self._last_check)
        if self._last_check and remaining > 60:
            return f"Kiểm tra tiếp sau {int(remaining // 60)} phút"
        return "Đang kiểm tra…"

    def summary(self) -> dict:
        items = self.store.active()
        return {
            "active": len(items),
            "unseen": self.store.unseen_count(),
            "danger": sum(1 for r in items if r.level == "danger"),
            "last_check": self._last_check,
        }
