"""Kiểm thử bộ tự động hoá nhắc nhở.

Chạy:  python tests_automation.py
"""
import pathlib
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent / "app"))

from PySide6.QtCore import QCoreApplication

APP = QCoreApplication.instance() or QCoreApplication([])

import automation
import core
from automation import (DEFAULT_CONFIG, AutomationEngine, ReminderStore, build_reminders,
                        parse_hhmm)
from core import COURSES, GradeBook, SEMESTERS

FAILED = []
TMP = pathlib.Path(tempfile.mkdtemp())
automation.CONFIG_PATH = TMP / "automation.json"


def check(cond, msg):
    if cond:
        print(f"  [OK]   {msg}")
    else:
        print(f"  [FAIL] {msg}")
        FAILED.append(msg)


def section(title):
    print(f"\n=== {title} ===")


def make_book(name="g.json"):
    return GradeBook(TMP / name)


def cfg(**kw):
    base = dict(DEFAULT_CONFIG)
    base.update({"study_time": "00:00", "ai_coach": False})
    base.update(kw)
    return base


# ------------------------------------------------------------------ 1. parsing
section("1. Cấu hình & thời gian")
check(parse_hhmm("19:30") == (19, 30), "parse 19:30")
check(parse_hhmm("bad", (7, 5)) == (7, 5), "fallback khi chuỗi sai")
check(parse_hhmm("25:99", (8, 0)) == (8, 0), "fallback khi giờ không hợp lệ")
check(automation.load_config()["enabled"] is True, "config mặc định có enabled=True")

# ------------------------------------------------------------------ 2. builder
section("2. Sinh nhắc nhở từ dữ liệu điểm")
book = make_book()
r = book.save(1, 3, 3, 3)          # Giải tích: không đạt
check(r.ok, "Lưu điểm không đạt cho Giải tích")
items = build_reminders(book, cfg(), now=datetime(2026, 11, 10, 20, 0))
kinds = {i.kind for i in items}
check("retake" in kinds, f"Có nhắc học lại ({sorted(kinds)})")
check(any(i.level in ("warning", "danger") for i in items), "Có nhắc mức cảnh báo")
check(any(i.rid.startswith("study-") for i in items), "Có nhắc giờ học hằng ngày")
check(any("Giải tích" in i.body for i in items if i.kind == "retake"), "Nội dung nhắc nêu tên môn không đạt")
check(all(i.title for i in items), "Mọi nhắc nhở đều có tiêu đề")

early = build_reminders(book, cfg(study_time="23:59"), now=datetime(2026, 11, 10, 8, 0))
check(not any(i.rid.startswith("study-") for i in early), "Chưa tới giờ học → không nhắc giờ học")

off = build_reminders(book, cfg(enabled=False), now=datetime(2026, 11, 10, 20, 0))
check(off == [], "Tắt tự động hoá → không sinh nhắc nhở")

no_warn = build_reminders(book, cfg(academic_warning=False, failed_course=False,
                                    graduation_risk=False, daily_study_reminder=False,
                                    weekly_review=False, locked_course=False),
                          now=datetime(2026, 11, 10, 20, 0))
check(no_warn == [], "Tắt từng loại → không sinh nhắc nhở tương ứng")

# ------------------------------------------------------------------ 3. store
section("3. Kho nhắc nhở (chống trùng, trạng thái)")
store = ReminderStore(TMP / "r.json")
first = store.add(items[0])
second = store.add(items[0])
check(first is True and second is False, "Thêm lần đầu = True, thêm trùng = False")
check(len(store.items) == 1, "Chống trùng theo rid")
check(store.unseen_count() == 1, "Đếm chưa đọc = 1")

rid = items[0].rid
store.mark_read(rid)
check(store.unseen_count() == 0, "Đánh dấu đã đọc → chưa đọc = 0")
check(store.active() and store.active()[0].rid == rid, "Đã đọc vẫn còn trong danh sách hoạt động")

store.snooze(rid, hours=24)
check(not any(i.rid == rid for i in store.active()), "Hoãn 1 ngày → không còn hoạt động")

store2 = ReminderStore(TMP / "r.json")
check(len(store2.items) == 1 and store2.items[rid].snooze_until > 0, "Lưu/đọc lại giữ trạng thái hoãn")

store.mark_done(rid)
check(store.unseen_count() == 0 and not any(i.rid == rid for i in store.active()), "Đánh dấu xong → không hoạt động")
store.clear_done()
check(not store.items, "Dọn đã xong → kho rỗng")

# ------------------------------------------------------------------ 4. engine
section("4. AutomationEngine – refresh, notify, quiet hours")
book2 = make_book("g2.json")
book2.save(1, 8, 8, 8)
book2.save(2, 4, 4, 4)   # Vật lý: D (đạt, điểm thấp)
notified = []
eng = AutomationEngine(book2, ReminderStore(TMP / "e1.json"), cfg(),
                       client_factory=lambda: None)
eng.notify.connect(lambda r: notified.append(r))
fresh = eng.refresh(force=True)
check(len(fresh) >= 1, f"refresh() tạo {len(fresh)} nhắc nhở mới")
check(len(eng.store.active()) >= 1, "Kho có nhắc nhở hoạt động")
check(eng.summary()["active"] >= 1, "summary() đếm đúng")
check("phút" in eng.next_check_text() or "Đang" in eng.next_check_text(), "Có mô tả lần kiểm tra tới")

# quiet hours: chặn thông báo nhưng vẫn lưu
notified.clear()
eng_q = AutomationEngine(make_book("g3.json"), ReminderStore(TMP / "e2.json"),
                         cfg(quiet_enabled=True, quiet_from="00:00", quiet_to="23:59"),
                         client_factory=lambda: None)
eng_q.book.save(1, 3, 3, 3)
eng_q.notify.connect(lambda r: notified.append(r))
eng_q.refresh(force=True)
check(notified == [], "Giờ yên tĩnh → không phát thông báo")
check(len(eng_q.store.active()) >= 1, "Giờ yên tĩnh → vẫn lưu nhắc nhở")

# interval gate
eng_calls = []
eng_g = AutomationEngine(make_book("g4.json"), ReminderStore(TMP / "e3.json"), cfg(),
                         client_factory=lambda: None)
eng_g.changed.connect(lambda: eng_calls.append(1))
eng_g.refresh(force=True)
n1 = len(eng_calls)
eng_g.refresh(force=False)
check(len(eng_calls) == n1, "Chưa tới hạn kiểm tra → không quét lại")

# ------------------------------------------------------------------ 5. AI coach
section("5. AI coach tự động (client giả lập)")


class FakeClient:
    calls = []

    def configured(self):
        return True

    def chat(self, messages, on_done, on_error, temperature=0.5, max_tokens=900):
        FakeClient.calls.append(messages)
        on_done("**Tình hình**: CPA 3.9 – tốt.\n- Học 2 giờ hôm nay\n1. Ôn Giải tích")


eng_ai = AutomationEngine(make_book("g5.json"), ReminderStore(TMP / "e4.json"),
                          cfg(ai_coach=True, ai_coach_time="00:00"),
                          client_factory=lambda: FakeClient())
eng_ai.book.save(1, 8, 8, 8)
digests = []
eng_ai.digest_ready.connect(lambda t: digests.append(t))
ok = eng_ai.request_digest(force=True)
check(ok, "request_digest() khởi chạy")
check(len(FakeClient.calls) == 1, "AI được gọi đúng 1 lần")
check(any(r.kind == "coach" for r in eng_ai.store.items.values()), "Lời khuyên AI được lưu thành nhắc nhở")
check(digests and "CPA" in digests[0], "Signal digest_ready phát nội dung")

# lỗi AI không làm treo
class BadClient:
    def configured(self):
        return True

    def chat(self, messages, on_done, on_error, **kw):
        on_error("Lỗi thử nghiệm")


eng_bad = AutomationEngine(make_book("g6.json"), ReminderStore(TMP / "e5.json"),
                           cfg(ai_coach=True), client_factory=lambda: BadClient())
errors = []
eng_bad.ai_error.connect(lambda m: errors.append(m))
eng_bad.request_digest(force=True)
check(errors and "Lỗi thử nghiệm" in errors[0], "Lỗi API được báo qua signal ai_error")
check(eng_bad._coach_due(datetime.now()) is False, "Sau lỗi → tạm hoãn gọi AI (không spam)")

# ------------------------------------------------------------------ 6. cấu hình
section("6. Lưu cấu hình tự động hoá")
eng.set_cfg = None
eng.update({"study_time": "06:15", "check_interval_min": 15, "ai_coach": False})
check(eng.cfg["study_time"] == "06:15", "update() đổi giờ học")
check(automation.load_config()["study_time"] == "06:15", "Cấu hình được ghi ra tệp")

# ------------------------------------------------------------------ 7. tích hợp cảnh báo
section("7. Nhắc nhở khớp với phân tích học tập")
low = make_book("low.json")
for c in low.courses_in(1):
    low.save(c["id"], 4, 4, 4)
low_items = build_reminders(low, cfg(), now=datetime(2026, 11, 10, 20, 0))
check(any(i.kind == "warning" and "CPA" in i.body for i in low_items), "CPA thấp sinh nhắc cảnh báo")
check(any(i.kind == "retake" for i in low_items) is False,
      "Không có môn F (điểm 4.0 vẫn đạt) → không có nhắc học lại")

print("\n" + "=" * 60)
if FAILED:
    print(f"FAILED {len(FAILED)} test(s):")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("ALL AUTOMATION TESTS PASSED")
