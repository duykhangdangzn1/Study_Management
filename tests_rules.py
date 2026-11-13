"""Kiểm thử quy chế đào tạo (rules.py) và tích hợp vào phân tích AI.

Chạy: python tests_rules.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))

import rules                                  # noqa: E402
import core                                   # noqa: E402
import ai_engine                              # noqa: E402

OK, FAIL = 0, 0


def check(name, cond, info=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {info}")


print("[1] Ngưỡng cảnh báo kết quả học tập – Điều 12 QĐ 2244/2021")
w = rules.warning_status(0.70, 1, None)
check("HK1 TB 0,70 < 0,80 → cảnh báo", w["warning"] and w["level"] == "warning")
check("ngưỡng HK đầu = 0,80", w["semester_threshold"] == 0.80)
w = rules.warning_status(0.95, 3, 2.5)
check("HK3 TB 0,95 < 1,00 → cảnh báo", w["warning"])
check("ngưỡng HK sau = 1,00", w["semester_threshold"] == 1.00)
check("HK3–4 là năm 2 → ngưỡng CPA 1,40", rules.cpa_warning_threshold(3) == 1.40)
w = rules.warning_status(3.0, 3, 1.35)
check("năm 2 CPA 1,35 < 1,40 → cảnh báo", w["warning"])
check("ngưỡng CPA năm 2 = 1,40", w["cpa_threshold"] == 1.40)
w = rules.warning_status(3.0, 5, 1.55)
check("CPA 1,55 < 1,60 (năm 3) → cảnh báo", w["warning"])
check("ngưỡng CPA năm 3 = 1,60", w["cpa_threshold"] == 1.60)
w = rules.warning_status(3.0, 7, 1.75)
check("năm 4 trở đi CPA < 1,80 → cảnh báo", w["warning"] and w["cpa_threshold"] == 1.80)
w = rules.warning_status(2.8, 5, 2.6)
check("KQ tốt → không cảnh báo", not w["warning"] and w["level"] == "none")
w = rules.warning_status(0.9, 2, 1.3, warn_streak=1)
check("cảnh báo lần 2 liên tiếp → nguy cơ buộc thôi học", w["level"] == "dismiss_risk")

print("[2] Giới hạn đăng ký – Điều 7 khoản 6")
check("chưa đạt chuẩn NN → tối đa 14 TC", rules.registration_limit(False)["max"] == 14)
check("đạt chuẩn NN → tối đa 25 TC", rules.registration_limit(True)["max"] == 25)
check("tối thiểu 12 TC", rules.registration_limit(True)["min"] == 12)
check("học kỳ hè ≤ 10 TC", rules.registration_limit(True)["summer_max"] == 10)

print("[3] Điều kiện tốt nghiệp")
items = rules.graduation_requirements(156, 156, 2.4, True, False)
check("đủ 4 điều kiện mặc định", len(items) == 4)
check("có mục ngoại ngữ và CNTT", {i["key"] for i in items} == {"credits", "cpa", "english", "it"})
by = {i["key"]: i for i in items}
check("đủ tín chỉ → ok", by["credits"]["ok"])
check("chưa có chuẩn CNTT → chưa đạt", by["it"]["ok"] is False)
check("CPA 2,4 ≥ 2,0 → đạt", by["cpa"]["ok"])
items = rules.graduation_requirements(100, 156, 1.9, False, False)
check("thiếu tín chỉ + CPA thấp → chưa đạt", not any(i["ok"] for i in items))

print("[4] Đồ án tốt nghiệp – Điều 15")
check("CPA 1,95 + còn 4 TC → đủ điều kiện",
      rules.thesis_eligibility(4, 1.95)["ok"])
check("CPA 1,80 → không đủ", not rules.thesis_eligibility(4, 1.80)["ok"])
check("còn 6 TC → không đủ", not rules.thesis_eligibility(6, 2.5)["ok"])

print("[5] Học bổng khuyến khích học tập – QĐ 1414/2021")
check("GPA 9,2 + RL 95 → loại A", rules.scholarship_level(9.2, 95)["code"] == "A")
check("GPA 8,3 + RL 85 → loại B", rules.scholarship_level(8.3, 85)["code"] == "B")
check("GPA 8,3 + RL 70 → tụt xuống loại C", rules.scholarship_level(8.3, 70)["code"] == "C")
check("GPA 6,5 → không có học bổng", rules.scholarship_level(6.5, 90) is None)
check("chưa có điểm rèn luyện → None", rules.scholarship_level(9.0, None) is None)
check("mức loại A = 150%", rules.scholarship_level(9.2, 95)["factor"] == 1.5)

print("[6] Hồ sơ chuẩn đầu ra (profile.json)")
tmp = Path(tempfile.mkdtemp())
prof = rules.load_profile(tmp)
check("mặc định chưa đạt chuẩn", prof["english_ok"] is False and prof["it_ok"] is False)
rules.save_profile(tmp, {"english_ok": True, "it_ok": False, "conduct": 82})
prof = rules.load_profile(tmp)
check("lưu/đọc lại đúng", prof["english_ok"] is True and prof["conduct"] == 82)
check("khoá lạ bị bỏ qua", set(prof) == set(rules.DEFAULT_PROFILE))

print("[7] Văn bản luật cho AI")
txt = rules.rules_text()
for kw in ("Điều 12", "Điều 7", "TOEIC", "IU01", "1414"):
    check(f"rules_text có '{kw}'", kw in txt)
check("docs_summary liệt kê văn bản", "2244" in rules.docs_summary() and "4511" in rules.docs_summary())

print("[8] Tích hợp LocalAnalytics")
book = core.GradeBook(tmp / "g.json")
book.save(book.courses_in(1)[0]["id"], 8, 9, 8.5)
rep = ai_engine.LocalAnalytics(book).report()
comp = rep.compliance
check("report có compliance", isinstance(comp, dict) and bool(comp))
check("compliance có warning/registration/graduation/scholarship",
      all(k in comp for k in ("warning", "registration", "graduation", "scholarship")))
check("bảng điểm 1 môn → cảnh báo học kỳ (TB học kỳ < 1,0 hoặc CPA thấp)",
      "warning" in comp["warning"])
ctx = ai_engine.LocalAnalytics(book).context_text()
check("context_text nạp luật cho AI", "QUY CHẾ ÁP DỤNG" in ctx and "Điều 12" in ctx)
check("context có giới hạn đăng ký", "12–25 TC" in ctx or "12–14 TC" in ctx or "14 TC" in ctx)

print(f"\nKẾT QUẢ: {OK} đạt, {FAIL} lỗi")
sys.exit(1 if FAIL else 0)
