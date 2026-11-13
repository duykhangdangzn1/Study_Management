"""AI Engine – Trợ lý học tập AI (chế độ ONLINE API duy nhất).

Gồm 3 phần:
1. AIClient   – client OpenAI-compatible, chỉ gọi API online, có retry/timeout,
                chẩn đoán lỗi rõ ràng bằng tiếng Việt.
2. LocalAnalytics – phân tích dữ liệu điểm (offline, tức thời): cảnh báo học tập,
                kế hoạch học lại, tiến độ tốt nghiệp, mục tiêu CPA.
3. StudyAdvisor – phương pháp học, thời khoá biểu tuần, lịch học lại và prompt
                dựng sẵn cho AI sinh lời khuyên tự nhiên.

Cấu hình mặc định: BASE_URL http://127.0.0.1:31415/v1, model "auto:smart".
Người dùng có thể đổi model/endpoint trong tab "Cài đặt AI" (vẫn là online API).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import core
import rules
from core import COURSE_BY_ID, COURSES, PROGRAM, SEMESTERS

# --------------------------------------------------------------------- cấu hình
AI_BASE_URL = "http://127.0.0.1:31415/v1"
AI_MODEL = "auto:smart"
AI_MODE = "Online API"

API_CONFIG_PATH = core.default_data_path().with_name("ai_config.json")


def env_api_key() -> str:
    """Khoá API KHÔNG nằm trong mã nguồn.

    Thứ tự tìm: biến môi trường AI_API_KEY / OPENAI_API_KEY, rồi tệp cục bộ
    `%APPDATA%/TinHocXayDung/api.key` (hoặc ~/.local/share/TinHocXayDung/api.key).
    Người dùng cũng có thể dán khoá trong tab "Cài đặt AI" — khoá lưu vào
    ai_config.json trên máy, không bao giờ ghi vào repo.
    """
    for name in ("AI_API_KEY", "OPENAI_API_KEY"):
        val = os.environ.get(name, "").strip()
        if val:
            return val
    try:
        return API_CONFIG_PATH.with_name("api.key").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


AI_API_KEY = env_api_key()

DEFAULT_CONFIG = {
    "mode": "online",
    "base_url": AI_BASE_URL,
    "api_key": AI_API_KEY,
    "model": AI_MODEL,
    "temperature": 0.6,
    "max_tokens": 1600,
    "timeout": 120,
}


def default_config() -> dict:
    return dict(DEFAULT_CONFIG)


def load_api_config() -> dict:
    """Đọc cấu hình, luôn điền mặc định cho các khoá thiếu."""
    cfg = default_config()
    try:
        data = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    if not isinstance(data, dict):
        return cfg
    for key in ("base_url", "api_key", "model"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            cfg[key] = value.strip()
    for key in ("temperature", "max_tokens", "timeout"):
        try:
            if data.get(key) is not None:
                cfg[key] = float(data[key]) if key == "temperature" else int(data[key])
        except (TypeError, ValueError):
            pass
    return cfg


def save_api_config(cfg: dict):
    merged = load_api_config()
    merged.update({k: v for k, v in (cfg or {}).items() if v is not None})
    merged["mode"] = "online"
    API_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    API_CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_api_config():
    save_api_config(default_config())


def chat_endpoint(base_url: str | None = None) -> str:
    """Chuẩn hoá base URL thành endpoint chat completions."""
    base = (base_url or AI_BASE_URL).strip().rstrip("/")
    if not base:
        base = AI_BASE_URL
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1") or base.endswith("/openai"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def models_endpoint(base_url: str | None = None) -> str:
    base = (base_url or AI_BASE_URL).strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    if base.endswith("/v1") or base.endswith("/openai"):
        return base + "/models"
    return base + "/v1/models"


def mask_key(key: str) -> str:
    key = (key or "").strip()
    if len(key) <= 14:
        return "•" * len(key)
    return f"{key[:10]}…{key[-4:]}"


# --------------------------------------------------------------------- client
class AIError(RuntimeError):
    """Lỗi gọi API đã được diễn giải sang tiếng Việt."""


class AIClient:
    """Client OpenAI-compatible. Chỉ hoạt động với API online."""

    def __init__(self, cfg: dict | None = None):
        cfg = dict(cfg) if cfg else load_api_config()
        self.base_url = str(cfg.get("base_url") or AI_BASE_URL)
        raw_key = cfg.get("api_key")
        # khoá rỗng được tôn trọng (người dùng chủ động xoá) – chỉ mặc định khi thiếu khoá
        self.api_key = "" if raw_key == "" else str(raw_key or AI_API_KEY)
        self.model = str(cfg.get("model") or AI_MODEL)
        try:
            self.temperature = float(cfg.get("temperature", 0.6))
        except (TypeError, ValueError):
            self.temperature = 0.6
        try:
            self.max_tokens = int(cfg.get("max_tokens", 1600))
        except (TypeError, ValueError):
            self.max_tokens = 1600
        try:
            self.timeout = int(cfg.get("timeout", 120))
        except (TypeError, ValueError):
            self.timeout = 120

    # -- thông tin
    @property
    def endpoint(self) -> str:
        return chat_endpoint(self.base_url)

    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def describe(self) -> dict:
        return {
            "mode": AI_MODE,
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "model": self.model,
            "key": mask_key(self.api_key),
            "configured": self.configured(),
        }

    # -- HTTP
    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def _request(self, url: str, body: bytes | None, timeout: int, retries: int, method="POST") -> dict:
        last_error = None
        for attempt in range(max(0, retries) + 1):
            req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8", "replace")
                try:
                    return json.loads(raw)
                except ValueError:
                    raise AIError("API trả về dữ liệu không phải JSON. Kiểm tra BASE_URL.")
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    payload = json.loads(e.read().decode("utf-8", "replace"))
                    err = payload.get("error", payload)
                    detail = err.get("message", "") if isinstance(err, dict) else str(err)
                except Exception:
                    detail = ""
                if e.code in (408, 409, 425, 429, 500, 502, 503, 504) and attempt < retries:
                    last_error = AIError(f"HTTP {e.code}: {detail or 'máy chủ bận'}")
                    time.sleep(0.8 * (attempt + 1))
                    continue
                raise AIError(self._http_message(e.code, detail))
            except urllib.error.URLError as e:
                reason = getattr(e, "reason", e)
                last_error = AIError(
                    f"Không kết nối được máy chủ AI tại {self.base_url}. "
                    f"Kiểm tra dịch vụ AI đang chạy và kết nối mạng. ({reason})")
                if attempt < retries:
                    time.sleep(0.6 * (attempt + 1))
                    continue
                raise last_error
            except TimeoutError:
                last_error = AIError(f"Máy chủ AI phản hồi quá lâu (>{timeout}s). Thử lại sau.")
                if attempt < retries:
                    continue
                raise last_error
            except OSError as e:
                last_error = AIError(f"Lỗi mạng khi gọi API: {e}")
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error
        raise last_error or AIError("Không gọi được API.")

    @staticmethod
    def _http_message(code: int, detail: str) -> str:
        d = (detail or "").strip()
        extra = f" Chi tiết: {d[:220]}" if d else ""
        if code in (401, 403):
            return "API key không hợp lệ hoặc không có quyền (HTTP %d).%s" % (code, extra)
        if code == 404:
            return "Sai BASE_URL hoặc model không tồn tại (HTTP 404).%s" % extra
        if code == 429:
            return "Bị giới hạn tần suất gọi API (HTTP 429). Đợi một lát rồi thử lại.%s" % extra
        if code >= 500:
            return "Máy chủ AI đang lỗi (HTTP %d). Thử lại sau.%s" % (code, extra)
        return "Lỗi API (HTTP %d).%s" % (code, extra)

    # -- gọi đồng bộ
    def complete(self, messages: list[dict], temperature: float | None = None,
                 max_tokens: int | None = None, timeout: int | None = None, retries: int = 2) -> str:
        if not self.configured():
            raise AIError("Chưa cấu hình API key. Mở tab “Cài đặt AI” để kiểm tra.")
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
            "stream": False,
        }
        data = self._request(self.endpoint, json.dumps(payload).encode("utf-8"),
                             timeout or self.timeout, retries)
        return self._extract(data)

    @staticmethod
    def _extract(data: dict) -> str:
        choices = data.get("choices") or []
        if not choices:
            err = data.get("error")
            if isinstance(err, dict) and err.get("message"):
                raise AIError(str(err["message"]))
            raise AIError("Phản hồi API không có 'choices'.")
        message = choices[0].get("message") or choices[0].get("delta") or {}
        content = message.get("content")
        if isinstance(content, list):
            content = "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
        text = (content or "").strip()
        if not text:
            text = str(message.get("reasoning_content") or "").strip()
        if not text:
            raise AIError("AI trả về nội dung rỗng. Thử lại hoặc đổi model.")
        return text

    def check(self) -> dict:
        """Kiểm tra kết nối: đọc /models (chuẩn OpenAI-compatible)."""
        data = self._request(models_endpoint(self.base_url), None, min(self.timeout, 20), 1, method="GET")
        models = data.get("data") if isinstance(data, dict) else None
        names = [m.get("id") for m in models if isinstance(m, dict)] if isinstance(models, list) else []
        return {"ok": True, "endpoint": models_endpoint(self.base_url), "models": names,
                "current": self.model, "count": len(names)}

    # -- gọi bất đồng bộ (callback chạy trong thread nền)
    def chat(self, messages: list[dict], on_done, on_error,
             temperature: float | None = None, max_tokens: int | None = None,
             timeout: int | None = None, retries: int = 2):
        def worker():
            try:
                on_done(self.complete(messages, temperature, max_tokens, timeout, retries))
            except AIError as e:
                on_error(str(e))
            except Exception as e:  # pragma: no cover - phòng hờ
                on_error(f"Lỗi không xác định: {e}")

        threading.Thread(target=worker, daemon=True, name="ai-chat").start()

    def chat_async(self, messages: list[dict], on_done, on_error, **kw):
        """Alias rõ nghĩa cho chat()."""
        self.chat(messages, on_done, on_error, **kw)


# ===================================================================== analytics
@dataclass
class Alert:
    level: str          # "danger" | "warning" | "info" | "good"
    title: str
    detail: str


@dataclass
class RetakePlanItem:
    cid: int
    name: str
    credits: float
    old_total: float
    semester: int        # học kỳ gốc của học phần
    suggest_when: str    # "Học kỳ 5"


@dataclass
class AcademicReport:
    cpa4: float | None = None
    cpa10: float | None = None
    credits_passed: float = 0.0
    failed: list = field(default_factory=list)      # list[dict]
    at_risk: list = field(default_factory=list)     # điểm D/D+ nhưng vẫn đạt
    alerts: list = field(default_factory=list)      # list[Alert]
    retake_plan: list = field(default_factory=list) # list[RetakePlanItem]
    graduation: dict = field(default_factory=dict)
    compliance: dict = field(default_factory=dict)   # quy chế: cảnh báo, giới hạn TC, chuẩn đầu ra
    pace: str = ""
    next_plan: list = field(default_factory=list)
    next_semester: int | None = None


class LocalAnalytics:
    """Phân tích học tập từ GradeBook – chạy offline, không cần API."""

    def __init__(self, book: core.GradeBook):
        self.book = book

    # ---------------------------------------------------------------- helpers
    def _failed(self):
        out = []
        for c in COURSES:
            r = self.book.result(c["id"])
            if r is not None and not r.passed:
                out.append({"id": c["id"], "name": c["name"], "credits": c["credits"],
                            "total": r.total, "semester": c["semester"]})
        return out

    def _at_risk(self):
        out = []
        for c in COURSES:
            r = self.book.result(c["id"])
            if r is not None and r.passed and r.total < 6.5:
                out.append({"id": c["id"], "name": c["name"], "total": r.total, "letter": r.letter})
        return out

    def _graduation(self):
        cum = self.book.cumulative()
        total = PROGRAM["total_credits"]
        credits = cum["credits"]
        frac = credits / total if total else 0.0
        cpa = cum["cpa4"]
        last = self.book.last_completed_semester() or 0
        pace_pct = last / len(SEMESTERS) if last else 0.0
        credit_pace = frac / pace_pct if pace_pct > 0 else 0.0
        if pace_pct == 0:
            pace = "Chưa có dữ liệu"
        elif credit_pace >= 0.98 and credit_pace <= 1.02:
            pace = "Đúng tiến độ"
        elif credit_pace > 1.02:
            pace = "Nhanh tiến độ"
        else:
            pace = "Chậm tiến độ"
        sems_left = max(0, len(SEMESTERS) - last)
        est = None
        if cpa is not None and frac > 0 and last > 0:
            if credit_pace > 1.02:
                est = max(1, round(sems_left / credit_pace))
            elif credit_pace > 0.98:
                est = sems_left
            else:
                est = min(12, max(sems_left, round(sems_left * credit_pace if credit_pace else sems_left)))
            est = min(est, 12)
        return {
            "credits": credits, "total": total, "frac": frac, "cpa4": cpa, "cpa10": cum["cpa10"],
            "rank": cum["rank"], "pace": pace, "last_semester": last, "sems_left": sems_left,
            "credits_left": max(0.0, total - credits),
            "est_sems_left": est,
            "graduation_ok": credits >= total and (cpa or 0) >= rules.GRAD_MIN_CPA,
            "cpa_ok": (cpa or 0) >= rules.GRAD_MIN_CPA,
        }

    def _compliance(self) -> dict:
        """Đối chiếu hồ sơ học tập với quy chế của Trường (xem rules.py)."""
        cum = self.book.cumulative()
        last = self.book.last_completed_semester() or 0
        stats = self.book.semester_stats(last) if last else {}
        prof = rules.load_profile(self.book.path.parent)
        warn = rules.warning_status(stats.get("gpa4"), last or 1, cum["cpa4"])
        grad = rules.graduation_requirements(cum["credits"], PROGRAM["total_credits"], cum["cpa4"],
                                             prof.get("english_ok"), prof.get("it_ok"))
        return {
            "warning": warn,
            "registration": rules.registration_limit(prof.get("english_ok")),
            "graduation": grad,
            "scholarship": rules.scholarship_level(cum["cpa10"], prof.get("conduct")),
            "thesis": rules.thesis_eligibility(max(0.0, PROGRAM["total_credits"] - cum["credits"]),
                                              cum["cpa4"]),
            "profile": prof,
            "integrity": [{"name": n, "detail": d} for n, d in rules.INTEGRITY],
            "docs": rules.DOCS,
        }

    def required_future_gpa(self, target: float = 2.5) -> float | None:
        """GPA trung bình cần đạt ở các tín chỉ còn lại để CPA tốt nghiệp = target."""
        cum = self.book.cumulative()
        if cum["cpa4"] is None:
            return None
        remain = PROGRAM["total_credits"] - cum["credits"]
        if remain <= 0:
            return cum["cpa4"]
        need = (target * (cum["credits"] + remain) - cum["cpa4"] * cum["credits"]) / remain
        return round(max(0.0, min(4.0, need)), 2)

    def targets(self) -> list[dict]:
        out = []
        cum = self.book.cumulative()
        for target, label in ((2.0, "Đủ điều kiện tốt nghiệp"), (2.5, "Xếp loại Khá"), (3.2, "Xếp loại Giỏi")):
            need = self.required_future_gpa(target)
            out.append({"target": target, "label": label, "needed_gpa": need,
                        "reachable": need is not None and need <= 4.0,
                        "current": cum["cpa4"]})
        return out

    # ---------------------------------------------------------------- report
    def report(self) -> AcademicReport:
        rep = AcademicReport()
        cum = self.book.cumulative()
        rep.cpa4, rep.cpa10 = cum["cpa4"], cum["cpa10"]
        rep.credits_passed = cum["credits"]
        rep.failed = self._failed()
        rep.at_risk = self._at_risk()
        rep.graduation = self._graduation()
        rep.compliance = self._compliance()
        rep.pace = rep.graduation["pace"]

        warn = rep.compliance["warning"]
        if warn["warning"]:
            rep.alerts.append(Alert("danger" if warn["level"] == "dismiss_risk" else "warning",
                                    "Cảnh báo kết quả học tập (Điều 12)",
                                    "Theo quy chế: " + "; ".join(warn["reasons"]) +
                                    ". Cần gặp cố vấn học tập để xử lý ngay."))
        rep.next_semester = self.book.next_semester()

        g = rep.graduation
        # ---- cảnh báo học tập theo quy chế
        if rep.cpa4 is not None and (cum["credits"] >= 12 or g["last_semester"] >= 1):
            if rep.cpa4 < 1.0:
                rep.alerts.append(Alert("danger", "Cảnh báo học vụ nghiêm trọng",
                                        f"CPA {rep.cpa4:.2f} < 1.0 – thuộc diện cảnh báo học vụ / buộc thôi học "
                                        f"theo quy chế. Cần gặp cố vấn học tập ngay."))
            elif rep.cpa4 < 2.0:
                rep.alerts.append(Alert("danger", "Cảnh báo học tập",
                                        f"CPA {rep.cpa4:.2f} < 2.0 – dưới mức tốt nghiệp. Cần cải thiện ngay "
                                        f"bằng kế hoạch học lại."))
            elif rep.cpa4 < 2.5:
                rep.alerts.append(Alert("warning", "CPA thấp",
                                        f"CPA {rep.cpa4:.2f} – chỉ hơn mức tốt nghiệp (2.0) một chút. "
                                        f"Nên duy trì GPA ≥ 2.5 các kỳ tới."))
        if rep.failed:
            n = len(rep.failed)
            tc = sum(f["credits"] for f in rep.failed)
            rep.alerts.append(Alert("warning" if n <= 2 else "danger", f"{n} học phần không đạt",
                                    f"Tổng {tc:g} tín chỉ cần học lại: " +
                                    ", ".join(f["name"] for f in rep.failed[:6]) + ("…" if n > 6 else "")))
        if rep.at_risk:
            rep.alerts.append(Alert("info", "Học phần điểm thấp (D+/C)",
                                    "Các học phần dưới 6.5: " +
                                    ", ".join(f"{a['name']} ({a['total']:.1f})" for a in rep.at_risk[:6])))
        info = self.book.next_semester_info()
        if info and info["locked"]:
            names = ", ".join(c["name"] for c in info["locked"][:4])
            more = f" và {len(info['locked']) - 4} HP khác" if len(info["locked"]) > 4 else ""
            rep.alerts.append(Alert("warning", f"{len(info['locked'])} học phần kỳ tới bị khóa",
                                    f"Chưa đủ điều kiện học trước: {names}{more}. "
                                    f"Hãy học lại/đạt các học phần điều kiện trước."))
        if g["pace"] == "Chậm tiến độ" and g["last_semester"]:
            rep.alerts.append(Alert("info", "Chậm tiến độ tốt nghiệp",
                                    f"Tín chỉ tích lũy {cum['credits']:g}/{g['total']} trong khi đã qua "
                                    f"{g['last_semester']}/{len(SEMESTERS)} học kỳ. Nên đăng ký thêm học phần "
                                    f"ở các kỳ tới để kịp tốt nghiệp."))
        if rep.cpa4 is not None and rep.cpa4 >= 3.2:
            rep.alerts.append(Alert("good", "Kết quả tốt",
                                    f"CPA {rep.cpa4:.2f} – xếp loại {g['rank']}. Hãy duy trì!"))
        if not self.book.grades:
            rep.alerts.append(Alert("info", "Chưa có dữ liệu điểm",
                                    "Hãy nhập điểm Học kỳ 1 để AI phân tích và tư vấn chính xác."))

        rep.retake_plan = self._retake_plan()
        rep.next_plan = self._next_plan()
        return rep

    def _retake_plan(self):
        """Kế hoạch học lại: ưu tiên môn mở khoá nhiều môn sau, tối đa 2 môn/kỳ."""
        failed = self._failed()
        if not failed:
            return []
        next_sem = self.book.next_semester() or len(SEMESTERS)
        unlock_count = {f["id"]: len(self.book.dependents(f["id"])) for f in failed}
        failed.sort(key=lambda f: (-unlock_count[f["id"]], f["semester"]))
        plan = []
        for i, f in enumerate(failed):
            sem = min(len(SEMESTERS), next_sem + i // 2)
            note = "ưu tiên cao – mở khoá nhiều học phần" if unlock_count[f["id"]] >= 2 else \
                   ("ưu tiên – học phần điều kiện" if unlock_count[f["id"]] == 1 else "học lại bình thường")
            plan.append(RetakePlanItem(f["id"], f["name"], f["credits"], f["total"], f["semester"],
                                       f"Học kỳ {sem} ({note})"))
        return plan

    def _next_plan(self):
        info = self.book.next_semester_info()
        if not info:
            return []
        out = []
        for c in info["open"][:8]:
            out.append({"id": c["id"], "name": c["name"], "credits": c["credits"],
                        "locked": False, "elective": c["elective"]})
        for c in info["locked"][:8]:
            out.append({"id": c["id"], "name": c["name"], "credits": c["credits"],
                        "locked": True, "elective": c["elective"]})
        return out

    # ---------------------------------------------------------------- context
    def context_text(self) -> str:
        """Tóm tắt dữ liệu học tập để nạp vào system prompt của AI."""
        rep = self.report()
        lines = [f"Chương trình: {PROGRAM['name']} ({PROGRAM['code']}), {PROGRAM['total_credits']} tín chỉ, "
                 f"{PROGRAM['semesters']} học kỳ. Quy đổi: A≥8.5(4.0), B+≥8.0(3.5), B≥7.0(3.0), C+≥6.5(2.5), "
                 f"C≥5.5(2.0), D+≥5.0(1.5), D≥4.0(1.0), F<4.0. Đạt khi tổng ≥ 4.0. CPA tốt nghiệp ≥ 2.0."]
        cum = self.book.cumulative()
        lines.append(f"CPA hệ 4: {cum['cpa4'] if cum['cpa4'] is not None else 'chưa có'}; "
                     f"CPA hệ 10: {cum['cpa10'] if cum['cpa10'] is not None else 'chưa có'}; "
                     f"Tín chỉ tích lũy: {cum['credits']}/{PROGRAM['total_credits']}; "
                     f"Xếp loại: {cum['rank']}.")
        last = self.book.last_completed_semester()
        lines.append(f"Học kỳ đã hoàn thành gần nhất: HK{last if last else 'chưa có'}. "
                     f"Tiến độ: {rep.graduation['pace']}.")
        need = self.required_future_gpa(2.5)
        if need is not None:
            lines.append(f"Để CPA tốt nghiệp đạt 2.5, GPA trung bình các tín chỉ còn lại cần ≈ {need}/4.")
        if rep.failed:
            lines.append("Học phần KHÔNG ĐẠT (cần học lại): " +
                         "; ".join(f"{f['name']} (HK{f['semester']}, {f['total']:.1f})" for f in rep.failed))
        if rep.at_risk:
            lines.append("Học phần điểm thấp (<6.5): " +
                         "; ".join(f"{a['name']} ({a['total']:.1f})" for a in rep.at_risk))
        rows = []
        for c in COURSES:
            r = self.book.result(c["id"])
            if r:
                rows.append(f"HK{c['semester']}|{c['name']}|{c['credits']:g}TC|tổng {r.total:.1f}|{r.letter}|"
                            f"{'đạt' if r.passed else 'KHÔNG ĐẠT'}")
        if rows:
            lines.append("Bảng điểm chi tiết (HK|Tên|TC|Điểm|Chữ|Kết quả):")
            lines.extend(rows)
        nxt = self.book.next_semester()
        if nxt:
            cs = self.book.courses_in(nxt)
            lines.append(f"Học kỳ tiếp theo (HK{nxt}) gồm: " +
                         "; ".join(f"{c['name']} ({c['credits']:g}TC, {'tự chọn' if c['elective'] else 'bắt buộc'})"
                                   for c in cs))
        if rep.retake_plan:
            lines.append("Kế hoạch học lại đề xuất: " +
                         "; ".join(f"{p.name} (khi: {p.suggest_when})" for p in rep.retake_plan[:8]))
        if rep.alerts:
            lines.append("Cảnh báo hiện tại: " + "; ".join(f"[{a.level}] {a.title}" for a in rep.alerts))

        comp = rep.compliance or {}
        lines.append(rules.rules_text())
        w = comp.get("warning") or {}
        if w.get("warning"):
            lines.append("Theo Điều 12 QĐ 2244/2021, sinh viên đang thuộc diện cảnh báo: "
                         + "; ".join(w.get("reasons", [])) + ".")
        reg = comp.get("registration") or {}
        if reg:
            lines.append(f"Giới hạn đăng ký học kỳ tới: {reg['min']}–{reg['max']} TC "
                         f"(học kỳ hè ≤ {reg['summer_max']} TC) — {reg['note']}")
        prof = comp.get("profile") or {}
        lines.append("Hồ sơ chuẩn đầu ra: ngoại ngữ "
                     f"{'đã đạt' if prof.get('english_ok') else 'chưa đạt'}; CNTT "
                     f"{'đã đạt' if prof.get('it_ok') else 'chưa đạt'}; điểm rèn luyện "
                     f"{prof.get('conduct') if prof.get('conduct') is not None else 'chưa có'}.")
        if comp.get("scholarship"):
            s = comp["scholarship"]
            lines.append(f"Đủ điều kiện học bổng KKHT loại {s['code']} ({s['name']}), "
                         f"mức {int(s['factor'] * 100)}% học phí.")
        chains = [f"{c['name']} (HK{c['semester']}, {c['credits']:g} TC) ← {c['prereq_text']}"
                  for c in COURSES if c.get("prereq_text") and "ALL" not in str(c.get("prereq"))]
        if chains:
            lines.append("Bản đồ học phần tiên quyết (môn sau ← môn phải đạt trước): "
                         + "; ".join(chains))
        return "\n".join(lines)


# ===================================================================== advisor
DAYS = ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật")


def course_group(course: dict) -> str:
    name = course["name"].lower()
    if any(k in name for k in ("lập trình", "phần mềm", "thuật toán", "cơ sở dữ liệu", "windows",
                               "công nghệ số", "trí tuệ nhân tạo", "tin học", "gis", "bim", "phần tử hữu hạn")):
        return "Lập trình & CNTT"
    if any(k in name for k in ("giải tích", "đại số", "xác suất", "vật lý", "hóa", "phương pháp tính",
                               "thống kê")):
        return "Toán & khoa học cơ bản"
    if any(k in name for k in ("anh văn", "triết", "chủ nghĩa", "tư tưởng", "pháp luật",
                               "kinh tế chính trị", "lịch sử", "khởi nghiệp", "nghiên cứu khoa học")):
        return "Ngoại ngữ & lý luận"
    return "Kỹ thuật xây dựng"


class StudyAdvisor:
    """Sinh phương pháp học, thời khoá biểu tuần, lịch học lại (offline)."""

    def __init__(self, book: core.GradeBook):
        self.book = book
        self.analytics = LocalAnalytics(book)

    # -- phương pháp học cá nhân hoá
    def methods(self, rep: AcademicReport | None = None) -> list[dict]:
        rep = rep or self.analytics.report()
        out: list[dict] = []
        if not self.book.grades:
            out.append({"tag": "Khởi động", "title": "Bắt đầu bằng một mục tiêu nhỏ",
                        "detail": "Nhập điểm Học kỳ 1 (hoặc các môn đã có) để hệ thống phân tích. "
                                  "Đặt mục tiêu CPA ≥ 2.5 ngay từ kỳ đầu – dễ hơn rất nhiều so với việc "
                                  "kéo CPA lên ở các kỳ cuối."})
            out.append({"tag": "Ghi chú", "title": "Ghi chú Cornell 3 cột",
                        "detail": "Mỗi trang chia 3 phần: câu hỏi/keyword bên trái, nội dung bên phải, "
                                  "tóm tắt 2–3 dòng dưới cùng. Cuối ngày chỉ cần đọc lại phần tóm tắt."})
            return out

        cpa = rep.cpa4
        if cpa is not None and cpa < 2.0:
            out.append({"tag": "Ưu tiên 1", "title": "Chiến lược cứu CPA",
                        "detail": "Chọn 3–4 môn có số tín chỉ lớn và khả năng nâng điểm cao nhất để dồn sức. "
                                  "Mỗi môn cần kế hoạch riêng: tuần 1–4 nắm lý thuyết, tuần 5–8 luyện bài tập, "
                                  "tuần cuối làm đề. Đừng trải đều công sức cho tất cả các môn."})
            out.append({"tag": "Học lại", "title": "Học lại ngay, không dồn",
                        "detail": "Đăng ký học lại các môn F ngay kỳ tới, ưu tiên môn là điều kiện học trước. "
                                  "Một môn F còn kéo CPA xuống và chặn nhiều môn sau."})
            out.append({"tag": "Hỗ trợ", "title": "Gặp cố vấn học tập",
                        "detail": "Mang theo bảng điểm và kế hoạch học lại khi gặp cố vấn. Hỏi rõ: môn nào "
                                  "được học cải thiện, học kỳ nào mở lớp, có thể giảm tải môn nào."})
        elif cpa is not None and cpa < 2.5:
            out.append({"tag": "Mục tiêu", "title": "Nâng CPA lên 2.5 trong 2 kỳ",
                        "detail": "Tập trung cải thiện các môn D+/C lên C+/B. Ưu tiên môn 3–4 tín chỉ vì "
                                  "ảnh hưởng CPA mạnh nhất. Mục tiêu thực tế: GPA mỗi kỳ ≥ 3.0."})
            out.append({"tag": "Ôn thi", "title": "Ôn theo đề cũ, không học dàn trải",
                        "detail": "Xin đề thi các năm trước, làm trong điều kiện giống thi thật. "
                                  "Phân loại dạng bài và học theo dạng, không đọc lại toàn bộ giáo trình."})
        elif cpa is not None and cpa >= 3.2:
            out.append({"tag": "Duy trì", "title": "Giữ phong độ, học sâu",
                        "detail": "Bạn đang ở nhóm tốt. Duy trì nhịp học đều, tham gia đồ án/PBL và "
                                  "nghiên cứu để có hồ sơ đẹp khi ra trường. Tránh chủ quan ở môn nhiều tín chỉ."})
            out.append({"tag": "Phát triển", "title": "Tích luỹ kỹ năng nghề",
                        "detail": "Dành 3–5 giờ/tuần cho công cụ ngành: AutoCAD, Revit/BIM, Python cho xây dựng, "
                                  "hoặc chứng chỉ ngoại ngữ. Đây là phần tạo khác biệt khi xin việc."})
        else:
            out.append({"tag": "Mục tiêu", "title": "Giữ CPA an toàn và tăng dần",
                        "detail": "Duy trì GPA ≥ 2.5 mỗi kỳ để CPA không tụt. Chọn 1–2 môn mũi nhọn để "
                                  "nâng điểm, phần còn lại giữ mức ổn định."})

        if rep.failed:
            out.append({"tag": "Học lại", "title": "Quy trình học lại hiệu quả",
                        "detail": "1) Xác định chương mất điểm trong đề cũ. 2) Học lại lý thuyết nền của chương đó. "
                                  "3) Làm 5–10 bài mỗi dạng. 4) Tự thi thử 1 đề đủ thời gian. 5) Chỉ chuyển "
                                  "sang chương mới khi đạt ≥ 70% bài tập."})
        if rep.at_risk:
            names = ", ".join(a["name"] for a in rep.at_risk[:3])
            out.append({"tag": "Cải thiện", "title": "Nâng các môn điểm thấp",
                        "detail": f"Các môn cần chú ý: {names}. Với mỗi môn, chọn 2 chương yếu nhất, "
                                  "học lại bằng ví dụ và làm bài tập có đáp án. Hỏi giảng viên/bạn học "
                                  "ngay khi vướng, đừng để dồn tới cuối kỳ."})
        out.append({"tag": "Kỹ thuật", "title": "Pomodoro + chủ động gợi nhớ",
                        "detail": "Học 25 phút – nghỉ 5 phút, 4 vòng thì nghỉ 20 phút. Sau mỗi phần, "
                                  "gấp tài liệu và tự viết lại ý chính (active recall) thay vì đọc lại. "
                                  "Ôn lại sau 1 ngày, 3 ngày, 7 ngày (spaced repetition)."})
        out.append({"tag": "Kỹ thuật", "title": "Feynman: giảng lại cho người khác",
                        "detail": "Chọn một khái niệm khó, giải thích bằng ngôn ngữ đơn giản như dạy "
                                  "một bạn cùng lớp. Chỗ nào bí là chỗ chưa hiểu – quay lại tài liệu đúng phần đó."})
        if rep.next_semester:
            out.append({"tag": "Chuẩn bị", "title": "Đọc trước 20% nội dung kỳ tới",
                        "detail": f"Với HK{rep.next_semester}, xem trước đề cương và 1–2 chương đầu của các môn "
                                  "nhiều tín chỉ. Vào kỳ sẽ nhẹ hơn rất nhiều và dễ giữ điểm thành phần."})
        return out

    # -- thời khoá biểu tuần
    def weekly_plan(self, rep: AcademicReport | None = None) -> list[dict]:
        rep = rep or self.analytics.report()
        info = self.book.next_semester_info()
        courses = []
        if info:
            courses = list(info["open"]) + list(info["locked"])
        if not courses:
            sem = self.book.next_semester() or SEMESTERS[-1]
            courses = [c for c in COURSES if c["semester"] == sem]
        courses = courses[:8]
        plan = []
        for i, day in enumerate(DAYS):
            if i == 6:
                plan.append({"day": day, "focus": "Tổng kết tuần & nghỉ ngơi", "hours": "1–2 giờ",
                             "tasks": ["Ôn lại ghi chú của cả tuần (20 phút)", "Làm đề/bài tập tổng hợp",
                                       "Chuẩn bị bài cho tuần sau", "Dành thời gian thư giãn, thể thao"]})
                continue
            if not courses:
                plan.append({"day": day, "focus": "Ôn tập chương trình", "hours": "2 giờ",
                             "tasks": ["Ôn lại kiến thức trọng tâm", "Luyện bài tập theo dạng"]})
                continue
            first = courses[i % len(courses)]
            second = courses[(i + 3) % len(courses)] if len(courses) > 3 else None
            tasks = [f"Đọc trước: {first['name']} (45 phút)",
                     f"Bài tập/luyện tập: {first['name']} (45 phút)"]
            if second and second["id"] != first["id"]:
                tasks.append(f"Ôn nhanh: {second['name']} (30 phút)")
            tasks.append("Ghi chú Cornell + tự kiểm tra cuối ngày (15 phút)")
            focus = course_group(first)
            plan.append({"day": day, "focus": f"{focus}", "hours": "2–3 giờ", "tasks": tasks,
                         "course": first["name"]})
        return plan

    # -- lịch học lại theo học kỳ
    def retake_schedule(self, rep: AcademicReport | None = None) -> list[dict]:
        rep = rep or self.analytics.report()
        groups: dict[int, dict] = {}
        for p in rep.retake_plan:
            sem = int(p.suggest_when.split("Học kỳ ")[1].split(" ")[0]) if "Học kỳ " in p.suggest_when else 0
            g = groups.setdefault(sem, {"semester": sem, "courses": [], "credits": 0.0})
            g["courses"].append(p)
            g["credits"] += p.credits
        out = []
        for sem in sorted(groups):
            g = groups[sem]
            note = "Nên đăng ký tối đa 2 môn học lại/kỳ để tránh quá tải."
            if g["credits"] > 8:
                note = "Số tín chỉ học lại khá lớn – cân nhắc dàn sang kỳ sau."
            out.append({"semester": sem, "courses": g["courses"], "credits": g["credits"], "note": note})
        return out

    # -- việc cần làm ngay
    def action_items(self, rep: AcademicReport | None = None) -> list[str]:
        rep = rep or self.analytics.report()
        items = []
        if rep.cpa4 is not None and rep.cpa4 < 2.0:
            items.append("Đặt lịch gặp cố vấn học tập trong tuần này để thống nhất kế hoạch cứu CPA.")
        if rep.failed:
            top = sorted(rep.failed, key=lambda f: -len(self.book.dependents(f["id"])))[:2]
            items.append("Đăng ký học lại ngay: " + ", ".join(f["name"] for f in top) + ".")
        info = self.book.next_semester_info()
        if info and info["locked"]:
            items.append(f"Xử lý {len(info['locked'])} học phần bị khóa trước khi đăng ký HK{info['semester']}.")
        if rep.at_risk:
            items.append("Lên danh sách 2 chương yếu nhất của môn điểm thấp và ôn lại trong tuần.")
        if rep.graduation["pace"] == "Chậm tiến độ":
            items.append("Đăng ký thêm học phần ở kỳ tới để bắt kịp tiến độ tốt nghiệp.")
        items.append("Duy trì 2–3 giờ học tập trung mỗi ngày, nghỉ 5 phút sau mỗi 25 phút.")
        return items[:5]

    # -- gợi ý cho nhắc nhở hằng ngày
    def focus_today(self, rep: AcademicReport | None = None) -> str:
        rep = rep or self.analytics.report()
        if rep.failed:
            top = sorted(rep.failed, key=lambda f: -len(self.book.dependents(f["id"])))[:2]
            return "Ôn lại: " + ", ".join(f["name"] for f in top)
        info = self.book.next_semester_info()
        if info and info["open"]:
            c = max(info["open"], key=lambda x: x["credits"])
            return f"Tập trung môn nhiều tín chỉ: {c['name']}"
        if rep.at_risk:
            return f"Cải thiện điểm: {rep.at_risk[0]['name']}"
        return "Ôn tập đều các môn và làm bài tập trước khi tới lớp"


# ===================================================================== prompts
SYSTEM_PROMPT = """Bạn là "Trợ lý AI Học tập" của phần mềm Quản lý Học phần ngành Tin học Xây dựng (ĐH Bách khoa Đà Nẵng).

NHIỆM VỤ:
- Tư vấn học tập: phương pháp học, phân bổ thời gian, ôn thi.
- CẢNH BÁO HỌC TẬP: nếu CPA < 2.0 hoặc có nhiều học phần không đạt → cảnh báo rõ ràng, đề xuất hành động cụ thể.
- KẾ HOẠCH HỌC LẠI: chỉ ra học phần cần học lại, thứ tự ưu tiên (ưu tiên môn là điều kiện học trước của nhiều môn sau), lịch theo từng học kỳ.
- TIẾN ĐỘ TỐT NGHIỆP: phân tích tín chỉ tích lũy/tốc độ, dự báo khả năng tốt nghiệp (cần CPA ≥ 2.0 và đủ 156 tín chỉ).

QUY TẮC:
- Trả lời bằng TIẾNG VIỆT, ngắn gọn, có cấu trúc (gạch đầu dòng), thân thiện với sinh viên.
- ĐỊNH DẠNG: dùng Markdown chuẩn GitHub. Khi trình bày từ 2 chỉ tiêu trở lên (điểm, tín chỉ, môn học, kế hoạch)
  hãy dùng BẢNG Markdown: dòng tiêu đề, dòng phân cách | --- | --- |, rồi từng dòng dữ liệu; mỗi dòng một bản ghi,
  không dùng HTML và không bọc cả câu trả lời trong ```. Dùng ### cho tiêu đề mục, **...** cho số liệu quan trọng.
- Chỉ dựa trên dữ liệu học tập được cung cấp; không bịa điểm số hay học phần không có trong dữ liệu.
- Khi cảnh báo, dùng giọng nghiêm túc nhưng động viên, luôn kèm hành động cụ thể.
- Thang điểm 10 → hệ 4: A≥8.5→4.0, B+≥8.0→3.5, B≥7.0→3.0, C+≥6.5→2.5, C≥5.5→2.0, D+≥5.0→1.5, D≥4.0→1.0, F<4.0→0.
- Học phần ĐẠT khi tổng ≥ 4.0. CPA tốt nghiệp ≥ 2.0. Xếp loại: Xuất sắc ≥3.6, Giỏi ≥3.2, Khá ≥2.5, TB ≥2.0, Yếu ≥1.0, Kém <1.0.
- Không khuyến khích gian lận; khuyên gặp cố vấn học tập khi nguy cơ cao.
- TUÂN THỦ QUY CHẾ ĐÀO TẠO của Trường (đã nêu trong dữ liệu học tập): đăng ký 12–25 TC/học kỳ
  (tối đa 14 TC nếu chưa đạt chuẩn tiếng Anh), học kỳ hè ≤ 10 TC; cảnh báo khi TB học kỳ < 0,80
  (kỳ đầu) hoặc < 1,00 và khi CPA < 1,20/1,40/1,60/1,80 theo năm học; tốt nghiệp cần CPA ≥ 2,00
  cùng chuẩn ngoại ngữ (TOEIC ≥ 450 hoặc IELTS ≥ 5.5) và chuẩn CNTT IU01–IU06.
- Khi trả lời có liên quan đến quy định, nêu rõ căn cứ, ví dụ “theo Điều 12 QĐ 2244/QĐ-ĐHBK”
  hoặc “theo QĐ 4511/QĐ-ĐHBK (2022)”. Không tự đặt ra quy định không có trong dữ liệu.
- Không được viết ra quá trình suy nghĩ, không nhắc lại yêu cầu của người dùng, không dùng
  tiếng Anh để giải thích nội bộ; chỉ trả lời sinh viên bằng tiếng Việt.
- Câu hỏi giả định ("nếu em bị F môn X", "nếu chưa đạt môn Y") phải trả lời theo CHƯƠNG TRÌNH
  ĐÀO TẠO và quy chế: môn X mất bao nhiêu tín chỉ, những học phần nào bị khóa vì X là tiên quyết,
  phải học lại môn nào trước. KHÔNG dùng điểm hiện tại của sinh viên để phủ định giả định
  (không viết kiểu "nhưng môn đó em đang được 8.0"). Chỉ dùng số liệu thật khi câu hỏi hỏi về
  tình trạng hiện tại của sinh viên.
"""

AI_TASKS = {
    "digest": (
        "Hãy viết BẢN TIN HỌC TẬP HÔM NAY cho sinh viên này, tối đa 220 từ, gồm đúng 3 phần:\n"
        "1) Tình hình (2–3 gạch đầu dòng: CPA, tín chỉ, môn đáng lo).\n"
        "2) Việc cần làm hôm nay (3 gạch đầu dòng, hành động cụ thể trong 1–2 giờ).\n"
        "3) Lời nhắc phương pháp học (1–2 câu, phù hợp tình trạng hiện tại).\n"
        "Nếu sinh viên đang bị cảnh báo học tập, mở đầu bằng một câu cảnh báo rõ ràng nhưng không gây hoảng."),
    "plan": (
        "Hãy lập KẾ HOẠCH HỌC TẬP CHI TIẾT cho 4 tuần tới dựa trên dữ liệu trên. "
        "Trình bày theo từng tuần, mỗi tuần có: mục tiêu, các môn ưu tiên, việc làm cụ thể theo ngày "
        "(thứ 2 → chủ nhật), và cách tự kiểm tra tiến độ. Nêu rõ học phần cần học lại/cải thiện và "
        "học phần bị khóa cần xử lý. Cuối cùng thêm mục 'Rủi ro cần tránh'."),
    "methods": (
        "Hãy tư vấn PHƯƠNG PHÁP HỌC phù hợp riêng với dữ liệu trên: 5–7 kỹ thuật cụ thể (cách làm, "
        "thời lượng, tần suất), chỉ rõ áp dụng cho môn nào. Tránh lời khuyên chung chung. "
        "Kết thúc bằng 3 thói quen nên duy trì mỗi ngày."),
    "warning": (
        "Hãy đánh giá NGUY CƠ CẢNH BÁO HỌC TẬP của sinh viên này theo quy chế (CPA < 2.0, số môn không đạt, "
        "tiến độ tín chỉ). Nêu mức độ (An toàn / Cần chú ý / Nguy cơ cao), lý do bằng số liệu, và 4 hành động "
        "ưu tiên trong 2 tuần tới. Nếu an toàn, nói rõ vì sao và cách duy trì."),
    "qa": (
        "Hãy trả lời TRỰC TIẾP câu hỏi của sinh viên ở phần GHI CHÚ THÊM, dựa trên dữ liệu học tập "
        "và quy chế ở trên. Trả lời bằng tiếng Việt, 120–200 từ, mở đầu bằng câu trả lời ngắn "
        "(được/không, nên/chưa nên), sau đó giải thích 2–3 ý có số liệu. Nếu câu hỏi liên quan đến "
        "quy định, nêu rõ căn cứ (điều/khoản và số quyết định) và trích đoạn tài liệu tương ứng. "
        "Không viết lại đề bài, không đánh giá chung chung, không trình bày quá trình suy nghĩ "
        "(chỉ đưa câu trả lời cuối cùng cho sinh viên)."),
    "graduation": (
        "Hãy phân tích TIẾN ĐỘ TỐT NGHIỆP: số tín chỉ còn thiếu, CPA hiện tại so với mức 2.0, "
        "GPA cần đạt ở các tín chỉ còn lại để tốt nghiệp (và để đạt loại Khá/Giỏi nếu khả thi), "
        "số học kỳ dự kiến còn lại. Kết thúc bằng 3 việc cần làm trong học kỳ này."),
}


def build_messages(kind: str, context: str, extra: str = "", history: list[dict] | None = None) -> list[dict]:
    task = AI_TASKS.get(kind, AI_TASKS["digest"])
    system = SYSTEM_PROMPT + "\n\nDỮ LIỆU HỌC TẬP CỦA SINH VIÊN:\n" + (context or "(chưa có dữ liệu)")
    messages = [{"role": "system", "content": system}]
    for msg in (history or [])[-10:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    user = task
    if extra:
        user += "\n\nGHI CHÚ THÊM:\n" + extra
    # Tra cứu văn bản quy chế gốc (thầy gửi) để AI trả lời có căn cứ, trích đúng điều/khoản.
    snippets = rules.doc_snippets((extra or "") + " " + task)
    if snippets:
        user += ("\n\nTRÍCH TÀI LIỆU QUY CHẾ CỦA TRƯỜNG (chỉ dùng thông tin này cho phản hồi quy định,"
                 " nêu rõ văn bản/điều khi trích):\n" + snippets)
    messages.append({"role": "user", "content": user})
    return messages


def signature_of(context: str) -> str:
    return hashlib.sha1(context.encode("utf-8", "replace")).hexdigest()[:12]
