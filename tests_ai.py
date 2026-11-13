"""Kiểm thử AI engine, phân tích học tập và tư vấn (chạy: python tests_ai.py)."""
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent / "app"))

import ai_engine
import core
from ai_engine import (AI_BASE_URL, AI_MODEL, AIClient, AIError, LocalAnalytics, StudyAdvisor,
                       build_messages, chat_endpoint, load_api_config, mask_key, reset_api_config,
                       save_api_config)
from core import COURSES, GradeBook, PROGRAM, SEMESTERS

FAILED = []
TMP = pathlib.Path(tempfile.mkdtemp())


def check(cond, msg):
    if cond:
        print(f"  [OK]   {msg}")
    else:
        print(f"  [FAIL] {msg}")
        FAILED.append(msg)


def section(title):
    print(f"\n=== {title} ===")


def book(name="g.json"):
    return GradeBook(TMP / name)


def fill(book_, semesters, score=8.0):
    for s in semesters:
        for c in book_.courses_in(s):
            if c["elective"] or "ALL" in c["prereq"]:
                continue
            book_.save(c["id"], score, score, score)


# ------------------------------------------------------------------ 1. config
section("1. Cấu hình ONLINE API mặc định")
cfg = load_api_config()
check(cfg["base_url"] == "http://127.0.0.1:31415/v1", f"BASE_URL = {cfg['base_url']}")
check(cfg["model"] == "auto:smart", f"MODEL = {cfg['model']}")
check("freellmapi-" not in open(ai_engine.__file__, encoding="utf-8").read(),
      "Mã nguồn không nhúng khoá API")
check(cfg["api_key"] == ai_engine.AI_API_KEY,
      "Khoá lấy từ biến môi trường / tệp cục bộ" + ("" if ai_engine.AI_API_KEY else " (chưa cấu hình — bỏ qua phần gọi API thật)"))
check(chat_endpoint("http://127.0.0.1:31415/v1") == "http://127.0.0.1:31415/v1/chat/completions",
      "Chuẩn hoá endpoint khi base kết thúc /v1")
check(chat_endpoint("http://host:1234") == "http://host:1234/v1/chat/completions",
      "Chuẩn hoá endpoint khi base không có /v1")
check(chat_endpoint("http://host/v1/chat/completions") == "http://host/v1/chat/completions",
      "Giữ nguyên endpoint đầy đủ")
check("…" in mask_key("demo-key-1234567890abcdef"), "Che API key khi hiển thị")

old_path = ai_engine.API_CONFIG_PATH
ai_engine.API_CONFIG_PATH = TMP / "ai.json"
save_api_config({"model": "auto", "base_url": "http://x/v1", "api_key": "k-1234567890"})
c2 = load_api_config()
check(c2["model"] == "auto" and c2["base_url"] == "http://x/v1", "Lưu/đọc cấu hình")
reset_api_config()
c3 = load_api_config()
check(c3["model"] == AI_MODEL and c3["base_url"] == AI_BASE_URL, "Khôi phục mặc định")
ai_engine.API_CONFIG_PATH = old_path

client = AIClient({"api_key": "k-test-1234567890"})
check(client.configured(), "AIClient.configured() = True khi có khoá")
check(client.endpoint.endswith("/chat/completions"), f"endpoint = {client.endpoint}")
check(AIClient({"api_key": ""}).configured() is False, "Thiếu API key → configured() False")

# ------------------------------------------------------------------ 2. analytics
section("2. Phân tích học tập cơ bản")
gb = book()
fill(gb, [1], 8.0)
rep = LocalAnalytics(gb).report()
check(rep.cpa4 is not None and 3.5 <= rep.cpa4 <= 4.0, f"CPA hệ 4 = {rep.cpa4}")
check(rep.credits_passed > 0, f"Tín chỉ tích lũy = {rep.credits_passed}")
check(rep.graduation["total"] == PROGRAM["total_credits"], "Tổng tín chỉ = 156")
check(rep.graduation["pace"] in ("Đúng tiến độ", "Nhanh tiến độ", "Chậm tiến độ", "Chưa có dữ liệu"),
      f"Tốc độ = {rep.graduation['pace']}")
check(gb.last_completed_semester() == 1 and gb.next_semester() == 2, "HK1 xong → kỳ tới = 2")
check(len(rep.next_plan) > 0, f"Có {len(rep.next_plan)} học phần kỳ tới")

# ------------------------------------------------------------------ 3. warnings
section("3. Cảnh báo học tập")
low = book("low.json")
fill(low, [1], 4.0)            # tất cả điểm D → CPA 1.0
rep_low = LocalAnalytics(low).report()
levels = {a.level for a in rep_low.alerts}
check("danger" in levels, f"CPA thấp sinh cảnh báo nguy hiểm ({sorted(levels)})")
check(any("CPA" in a.title or "CPA" in a.detail for a in rep_low.alerts), "Cảnh báo nêu CPA")
check(rep_low.cpa4 is not None and rep_low.cpa4 < 2.0, f"CPA = {rep_low.cpa4} < 2.0")

fail_book = book("fail.json")
fail_book.save(1, 3, 3, 3)
rep_fail = LocalAnalytics(fail_book).report()
check(len(rep_fail.failed) == 1, "Nhận diện 1 học phần không đạt")
check(len(rep_fail.retake_plan) >= 1, "Sinh kế hoạch học lại")
check(rep_fail.retake_plan[0].name == "Giải tích", "Kế hoạch nêu đúng môn")
check("Học kỳ" in rep_fail.retake_plan[0].suggest_when, f"Thời điểm: {rep_fail.retake_plan[0].suggest_when}")

no_grades = LocalAnalytics(book("empty.json")).report()
check(any(a.level == "info" for a in no_grades.alerts), "Chưa có điểm → hướng dẫn nhập điểm")

# ------------------------------------------------------------------ 4. graduation
section("4. Tiến độ tốt nghiệp & mục tiêu CPA")
an = LocalAnalytics(gb)
need20 = an.required_future_gpa(2.0)
need25 = an.required_future_gpa(2.5)
check(need20 is not None and 0 <= need20 <= 4, f"GPA cần cho CPA 2.0 = {need20}")
check(need25 is not None and need25 >= (need20 or 0), f"GPA cần cho CPA 2.5 = {need25}")
targets = an.targets()
check(len(targets) == 3 and all("needed_gpa" in t for t in targets), "Bảng mục tiêu CPA có 3 mốc")
check(rep.graduation["credits_left"] == PROGRAM["total_credits"] - rep.credits_passed, "Tín chỉ còn thiếu đúng")

full = book("full.json")
fill(full, SEMESTERS, 9.0)
for c in COURSES:
    if c["elective"]:
        full.save(c["id"], 8, 8, 8)
for c in COURSES:
    if "ALL" in c["prereq"]:
        r = full.save(c["id"], 9, 9, 9)
        check(r.ok, f"Lưu học phần tốt nghiệp: {c['name']}")
rep_full = LocalAnalytics(full).report()
check(rep_full.credits_passed == PROGRAM["total_credits"], f"Tín chỉ = {rep_full.credits_passed}/156")
check(rep_full.graduation["graduation_ok"], "Đủ điều kiện tốt nghiệp")
check(len(rep_full.retake_plan) == 0, "Không còn môn học lại")
check(any(a.level == "good" for a in rep_full.alerts), "Có thông báo kết quả tốt")

# ------------------------------------------------------------------ 5. advisor
section("5. StudyAdvisor – phương pháp & kế hoạch")
adv = StudyAdvisor(gb)
methods = adv.methods()
check(len(methods) >= 4, f"Có {len(methods)} phương pháp")
check(all(m.get("title") and m.get("detail") for m in methods), "Mọi phương pháp có tiêu đề + nội dung")

week = adv.weekly_plan()
check(len(week) == 7, f"Thời khoá biểu 7 ngày ({[d['day'] for d in week][:3]}…)")
check(all(d["tasks"] for d in week), "Mỗi ngày có việc cụ thể")

adv_low = StudyAdvisor(low)
check(any("CPA" in m["title"] or "cứu" in m["title"].lower() for m in adv_low.methods()),
      "Sinh viên CPA thấp nhận phương pháp cứu CPA")

adv_fail = StudyAdvisor(fail_book)
check(any("học lại" in m["title"].lower() for m in adv_fail.methods()), "Sinh viên trượt nhận phương pháp học lại")
acts = adv_fail.action_items()
check(1 <= len(acts) <= 5, f"Việc cần làm: {len(acts)} mục")
check(bool(adv.focus_today()), "Có trọng tâm học hôm nay")

# full-time student: lịch học lại trống
check(StudyAdvisor(full).retake_schedule() == [], "Đã đạt hết → lịch học lại trống")

# ------------------------------------------------------------------ 6. prompts
section("6. Prompt & ngữ cảnh cho AI")
ctx = LocalAnalytics(gb).context_text()
for kw in ("CPA", "Tín chỉ tích lũy", "Bảng điểm chi tiết", "Học kỳ tiếp theo"):
    check(kw in ctx, f"Ngữ cảnh có '{kw}'")
check(len(ctx) > 400, f"Độ dài ngữ cảnh = {len(ctx)} ký tự")

msgs = build_messages("plan", ctx, extra="ưu tiên môn nhiều tín chỉ")
check(len(msgs) == 2 and msgs[0]["role"] == "system", "build_messages: system + user")
check(ctx in msgs[0]["content"], "Ngữ cảnh nằm trong system prompt")
check("KẾ HOẠCH HỌC TẬP CHI TIẾT" in msgs[1]["content"], "Prompt kế hoạch đúng nhiệm vụ")
check("ưu tiên môn nhiều tín chỉ" in msgs[1]["content"], "Ghi chú thêm được nối vào prompt")
for kind in ("digest", "methods", "warning", "graduation"):
    check(kind in ai_engine.AI_TASKS, f"Có prompt '{kind}'")
sp = ai_engine.SYSTEM_PROMPT
for kw in ("CẢNH BÁO HỌC TẬP", "KẾ HOẠCH HỌC LẠI", "TIẾN ĐỘ TỐT NGHIỆP", "TIẾNG VIỆT"):
    check(kw in sp, f"System prompt có '{kw}'")

# ------------------------------------------------------------------ 7. error path
section("7. Xử lý lỗi API (không treo, không crash)")
got = {}


def boom(*a, **k):
    raise AIError("Lỗi mô phỏng")


client_bad = AIClient({"api_key": "k-test-123", "base_url": ai_engine.AI_BASE_URL})
client_bad._request = boom
client_bad.chat([{"role": "user", "content": "x"}], lambda t: got.setdefault("ok", t),
                lambda e: got.setdefault("err", e))
for _ in range(200):
    if got:
        break
    time.sleep(0.02)
check("err" in got and "Lỗi mô phỏng" in got["err"], f"on_error nhận: {got.get('err', '')[:50]}")

got.clear()
no_key = AIClient({"api_key": ""})
no_key.chat([{"role": "user", "content": "x"}], lambda t: got.setdefault("ok", t),
            lambda e: got.setdefault("err", e))
for _ in range(100):
    if got:
        break
    time.sleep(0.01)
check("err" in got, "Thiếu API key → báo lỗi ngay")

check("Không kết nối" in AIClient._http_message(0, "") or "Lỗi API" in AIClient._http_message(0, ""),
      "Thông điệp lỗi HTTP có tiếng Việt")
check("API key" in AIClient._http_message(401, ""), "Lỗi 401 hướng dẫn kiểm tra API key")
check("429" in AIClient._http_message(429, ""), "Lỗi 429 báo giới hạn tần suất")

# ------------------------------------------------------------------ 8. live API
section("8. Gọi API ONLINE thật")
try:
    live = AIClient()
    info = live.check()
    check(info["ok"] and info["count"] >= 1, f"Máy chủ AI hoạt động – {info['count']} model khả dụng")
    check(AI_MODEL in info["models"] or any(m.startswith("auto") for m in info["models"]),
          f"Có model '{AI_MODEL}'")
    text = live.complete([{"role": "user", "content": "Trả lời đúng ba từ: xin chào bạn"}],
                         max_tokens=40, retries=0)
    check(bool(text.strip()), f"API trả lời: {text.strip()[:70]!r}")
except AIError as e:
    print(f"  [SKIP] Không gọi được API online: {e}")

print("\n" + "=" * 60)
if FAILED:
    print(f"FAILED {len(FAILED)} test(s):")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("ALL AI TESTS PASSED")
