"""Nghiep vu: tinh diem, rang buoc hoc phan, GPA/CPA, luu tru."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from courses_data import COURSES, PROGRAM

WEIGHTS = (Decimal("0.2"), Decimal("0.2"), Decimal("0.6"))
PASS_MARK = 4.0
COMPONENT_LABELS = ("Thành phần", "Giữa kỳ", "Cuối kỳ")

# (nguong hệ 10, chu, hệ 4)
LETTER_SCALE = [
    (8.5, "A", 4.0),
    (8.0, "B+", 3.5),
    (7.0, "B", 3.0),
    (6.5, "C+", 2.5),
    (5.5, "C", 2.0),
    (5.0, "D+", 1.5),
    (4.0, "D", 1.0),
    (0.0, "F", 0.0),
]

COURSE_BY_ID = {c["id"]: c for c in COURSES}
SEMESTERS = list(range(1, PROGRAM["semesters"] + 1))


def round1(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def round2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def parse_score(text) -> float | None:
    """Chuyen chuoi -> diem [0,10]. Tra ve None neu rong; raise ValueError neu sai."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        value = float(text)
    else:
        s = str(text).strip().replace(",", ".")
        if not s:
            return None
        value = float(s)
    if not 0.0 <= value <= 10.0:
        raise ValueError("Điểm phải nằm trong khoảng 0 – 10")
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total_score(tp: float, gk: float, ck: float) -> float:
    d = sum(Decimal(str(v)) * w for v, w in zip((tp, gk, ck), WEIGHTS))
    return round1(d)


def letter_of(total: float) -> tuple[str, float]:
    for threshold, letter, g4 in LETTER_SCALE:
        if total >= threshold:
            return letter, g4
    return "F", 0.0


def classify(cpa4: float | None) -> str:
    if cpa4 is None:
        return "—"
    if cpa4 >= 3.6:
        return "Xuất sắc"
    if cpa4 >= 3.2:
        return "Giỏi"
    if cpa4 >= 2.5:
        return "Khá"
    if cpa4 >= 2.0:
        return "Trung bình"
    if cpa4 >= 1.0:
        return "Yếu"
    return "Kém"


def fmt_credits(x: float) -> str:
    return f"{x:g}"


def default_data_path() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "TinHocXayDung" / "grades.json"


@dataclass
class Result:
    total: float
    letter: str
    g4: float

    @property
    def passed(self) -> bool:
        return self.total >= PASS_MARK


@dataclass
class CheckResult:
    ok: bool
    message: str = ""
    problems: list | None = None


class GradeBook:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_data_path()
        self.grades: dict[int, dict] = {}
        self.load()

    # ---------- luu tru ----------
    def load(self):
        self.grades = {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for k, v in data.get("grades", {}).items():
                cid = int(k)
                if cid in COURSE_BY_ID and all(x in v for x in ("tp", "gk", "ck")):
                    self.grades[cid] = {
                        "tp": parse_score(v["tp"]),
                        "gk": parse_score(v["gk"]),
                        "ck": parse_score(v["ck"]),
                        "saved_at": v.get("saved_at", ""),
                    }
        except (OSError, ValueError, TypeError, AttributeError):
            self.grades = {}

    def persist(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        payload = {"version": 1, "grades": {str(k): v for k, v in sorted(self.grades.items())}}
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    # ---------- truy van ----------
    def result(self, cid: int) -> Result | None:
        g = self.grades.get(cid)
        if not g:
            return None
        t = total_score(g["tp"], g["gk"], g["ck"])
        letter, g4 = letter_of(t)
        return Result(t, letter, g4)

    def is_passed(self, cid: int) -> bool:
        r = self.result(cid)
        return bool(r and r.passed)

    def prereq_ids(self, cid: int) -> list[int]:
        c = COURSE_BY_ID[cid]
        if "ALL" in c["prereq"]:
            return [x["id"] for x in COURSES if x["id"] != cid and not x["elective"]]
        return list(c["prereq"])

    def passed_electives(self, exclude: int | None = None) -> list[int]:
        return [c["id"] for c in COURSES if c["elective"] and c["id"] != exclude and self.is_passed(c["id"])]

    def unmet_prereqs(self, cid: int) -> list[str]:
        """Danh sach mo ta cac dieu kien hoc truoc chua dat."""
        problems = []
        for pid in self.prereq_ids(cid):
            r = self.result(pid)
            name = COURSE_BY_ID[pid]["name"]
            if r is None:
                problems.append(f"{name} (chưa có điểm)")
            elif not r.passed:
                problems.append(f"{name} (không đạt: {r.total:.1f})")
        if "ALL" in COURSE_BY_ID[cid]["prereq"]:
            need = PROGRAM["elective_required"]
            have = len(self.passed_electives())
            if have < need:
                problems.append(f"Học phần tự chọn: mới đạt {have}/{need}")
        return problems

    def is_locked(self, cid: int) -> bool:
        return bool(self.unmet_prereqs(cid))

    def dependents(self, cid: int) -> list[int]:
        out = []
        for c in COURSES:
            if c["id"] == cid:
                continue
            if cid in self.prereq_ids(c["id"]) or ("ALL" in c["prereq"] and COURSE_BY_ID[cid]["elective"]):
                out.append(c["id"])
        return out

    def graded_dependents(self, cid: int) -> list[int]:
        deps = [d for d in self.dependents(cid) if d in self.grades]
        if COURSE_BY_ID[cid]["elective"]:
            # Mot hoc phan tu chon chi rang buoc DATN khi khong con du so tu chon dat khac
            need = PROGRAM["elective_required"]
            if len(self.passed_electives(exclude=cid)) >= need:
                deps = [d for d in deps if "ALL" not in COURSE_BY_ID[d]["prereq"]]
        return deps

    # ---------- ghi ----------
    def check_save(self, cid: int, tp, gk, ck) -> CheckResult:
        try:
            vals = [parse_score(v) for v in (tp, gk, ck)]
        except ValueError as e:
            return CheckResult(False, f"Điểm không hợp lệ: {e}")
        missing = [lbl for lbl, v in zip(COMPONENT_LABELS, vals) if v is None]
        if missing:
            return CheckResult(False, "Vui lòng nhập đủ điểm: " + ", ".join(missing))
        unmet = self.unmet_prereqs(cid)
        if unmet:
            return CheckResult(False, "Không thể lưu điểm vì học phần học trước chưa đạt yêu cầu.", unmet)
        course = COURSE_BY_ID[cid]
        if course["elective"] and not self.is_passed(cid):
            need = PROGRAM["elective_required"]
            if len(self.passed_electives(exclude=cid)) >= need:
                return CheckResult(False, f"Bạn đã đạt đủ {need} học phần tự chọn. Không thể lưu thêm học phần tự chọn khác.")
        new_total = total_score(*vals)
        if new_total < PASS_MARK:
            deps = self.graded_dependents(cid)
            if deps:
                return CheckResult(False, "Không thể lưu điểm không đạt vì các học phần sau đã có điểm dựa trên học phần này:",
                                   [COURSE_BY_ID[d]["name"] for d in deps])
        return CheckResult(True)

    def save(self, cid: int, tp, gk, ck) -> CheckResult:
        chk = self.check_save(cid, tp, gk, ck)
        if not chk.ok:
            return chk
        tp, gk, ck = (parse_score(v) for v in (tp, gk, ck))
        old = self.grades.get(cid)
        self.grades[cid] = {"tp": tp, "gk": gk, "ck": ck, "saved_at": datetime.now().isoformat(timespec="seconds")}
        try:
            self.persist()
        except OSError as e:
            if old is None:
                self.grades.pop(cid, None)
            else:
                self.grades[cid] = old
            return CheckResult(False, f"Không ghi được tệp dữ liệu: {e}")
        return CheckResult(True, "Đã lưu điểm thành công.")

    def check_delete(self, cid: int) -> CheckResult:
        if cid not in self.grades:
            return CheckResult(False, "Học phần này chưa có điểm.")
        deps = self.graded_dependents(cid)
        if deps:
            return CheckResult(False, "Không thể xoá điểm vì các học phần sau đã có điểm dựa trên học phần này:",
                               [COURSE_BY_ID[d]["name"] for d in deps])
        return CheckResult(True)

    def delete(self, cid: int) -> CheckResult:
        chk = self.check_delete(cid)
        if not chk.ok:
            return chk
        old = self.grades.pop(cid)
        try:
            self.persist()
        except OSError as e:
            self.grades[cid] = old
            return CheckResult(False, f"Không ghi được tệp dữ liệu: {e}")
        return CheckResult(True, "Đã xoá điểm.")

    def reset(self):
        self.grades = {}
        self.persist()

    # ---------- thong ke ----------
    def courses_in(self, sem: int) -> list[dict]:
        return [c for c in COURSES if c["semester"] == sem]

    def semester_stats(self, sem: int) -> dict:
        cs = self.courses_in(sem)
        required = [c for c in cs if not c["elective"]]
        electives = [c for c in cs if c["elective"]]
        graded = [(c, self.result(c["id"])) for c in cs if c["id"] in self.grades]
        credits_graded = sum(c["credits"] for c, _ in graded)
        gpa10 = gpa4 = None
        if credits_graded:
            gpa10 = round2(sum(r.total * c["credits"] for c, r in graded) / credits_graded)
            gpa4 = round2(sum(r.g4 * c["credits"] for c, r in graded) / credits_graded)
        need_el = PROGRAM["elective_required"] if electives else 0
        graded_el = sum(1 for c in electives if c["id"] in self.grades)
        req_graded = sum(1 for c in required if c["id"] in self.grades)
        n_plan = len(required) + need_el
        n_done = req_graded + min(graded_el, need_el)
        credits_plan = sum(c["credits"] for c in required) + need_el * (electives[0]["credits"] if electives else 0)
        return {
            "semester": sem,
            "n_courses": len(cs),
            "n_required": len(required),
            "n_electives": len(electives),
            "electives_needed": need_el,
            "n_plan": n_plan,
            "n_done": n_done,
            "credits_plan": credits_plan,
            "n_graded": len(graded),
            "credits_graded": credits_graded,
            "credits_passed": sum(c["credits"] for c, r in graded if r.passed),
            "n_failed": sum(1 for _, r in graded if not r.passed),
            "gpa10": gpa10,
            "gpa4": gpa4,
            "completed": n_done >= n_plan,
        }

    def cumulative(self, upto: int | None = None) -> dict:
        """CPA tính trên TẤT CẢ học phần đã có điểm (kể cả không đạt).

        Nhờ vậy CPA luôn khớp GPA khi chỉ có một học kỳ, và môn F thực sự kéo
        điểm tích lũy xuống đúng như quy chế. Tín chỉ tích lũy (credits) vẫn
        chỉ cộng các học phần đạt.
        """
        upto = upto or SEMESTERS[-1]
        graded = [(c, self.result(c["id"])) for c in COURSES if c["semester"] <= upto]
        graded = [(c, r) for c, r in graded if r is not None]
        passed = [(c, r) for c, r in graded if r.passed]
        credits = sum(c["credits"] for c, _ in passed)
        attempted = sum(c["credits"] for c, _ in graded)
        cpa10 = cpa4 = None
        if attempted:
            cpa10 = round2(sum(r.total * c["credits"] for c, r in graded) / attempted)
            cpa4 = round2(sum(r.g4 * c["credits"] for c, r in graded) / attempted)
        return {"upto": upto, "credits": credits, "attempted_credits": attempted, "n_courses": len(passed),
                "n_graded": len(graded), "cpa10": cpa10, "cpa4": cpa4, "rank": classify(cpa4)}

    def completed_semesters(self) -> list[int]:
        return [s for s in SEMESTERS if self.semester_stats(s)["completed"]]

    def last_completed_semester(self) -> int | None:
        """Hoc ky da qua gan nhat: hoc ky lien tiep cuoi cung da nhap du diem."""
        last = None
        for s in SEMESTERS:
            if self.semester_stats(s)["completed"]:
                last = s
            else:
                break
        return last

    def next_semester(self) -> int | None:
        last = self.last_completed_semester()
        if last is None:
            return SEMESTERS[0]
        return last + 1 if last < SEMESTERS[-1] else None

    def next_semester_info(self) -> dict | None:
        sem = self.next_semester()
        if sem is None:
            return None
        st = self.semester_stats(sem)
        cs = self.courses_in(sem)
        locked = [c for c in cs if c["id"] not in self.grades and self.is_locked(c["id"])]
        open_ = [c for c in cs if c["id"] not in self.grades and not self.is_locked(c["id"])]
        return {"semester": sem, "stats": st, "locked": locked, "open": open_}
