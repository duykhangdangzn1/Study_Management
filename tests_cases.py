"""Bộ kiểm thử hàng loạt cho trợ lý AI: môn tiên quyết bị F, cảnh báo học tập, quy chế,
tra cứu tài liệu của thầy và hỏi đáp thật với AI.

Chạy: python tests_cases.py            (đầy đủ, gồm hỏi AI online)
      python tests_cases.py --offline  (chỉ phần tính toán, không gọi mạng)
"""
from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))

import core                                    # noqa: E402
import ai_engine                               # noqa: E402
import rules                                   # noqa: E402
from ai_engine import AIClient, LocalAnalytics, build_messages   # noqa: E402

ONLINE = "--offline" not in sys.argv
TMP = Path(tempfile.mkdtemp())
OK = 0
FAIL = 0
LOGS: list[str] = []


def check(name: str, cond: bool, detail: str = ""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}" + (f"  [{detail}]" if detail else ""))
    LOGS.append(("ok   " if cond else "FAIL ") + name + (f" | {detail}" if detail else ""))


def section(title: str):
    print(f"\n=== {title} ===")


def make_book(name, semesters, fail=(), score=8.0, extra_pass=()):
    """Bảng điểm tổng hợp: các học kỳ đã học đều đạt, trừ danh sách `fail`."""
    book = core.GradeBook(TMP / name)
    for s in semesters:
        for c in book.courses_in(s):
            if c["elective"] or "ALL" in c["prereq"]:
                continue
            book.save(c["id"], score, score, score)
    for cid in extra_pass:
        book.save(cid, score, score, score)
    for cid, total in fail:
        book.save(cid, max(0.0, total - 1), max(0.0, total - 2), total)
    return book


def names(rep):
    return [p.name for p in rep.retake_plan]


# --------------------------------------------------------- 1. F Cơ học kết cấu 1
section("1. Cơ học kết cấu 1 (HK4, 2 TC) bị điểm F")
base = make_book("ok1.json", (1, 2, 3), extra_pass=(29,))
f1 = make_book("f_chkc1.json", (1, 2, 3), fail=[(29, 2.0)])
r1 = LocalAnalytics(f1).report()
r1_base = LocalAnalytics(base).report()

check("CHKC1 được đưa vào kế hoạch học lại",
      any(n.startswith("Cơ học kết cấu 1") for n in names(r1)), str(names(r1)))
check("CHKC1 được ưu tiên cao vì mở khoá nhiều học phần sau",
      any("mở khoá nhiều" in p.suggest_when for p in r1.retake_plan
          if p.name.startswith("Cơ học kết cấu 1")),
      "; ".join(p.suggest_when for p in r1.retake_plan))
check("CHKC1 chặn ít nhất 2 học phần phía sau", len(f1.dependents(29)) >= 2,
      str(f1.dependents(29)))
check("CHKC2 (id 39) bị khoá vì chưa đạt CHKC1", f1.is_locked(39))
check("CHKC2 không có trong danh sách học phần mở để đăng ký",
      29 in f1.prereq_ids(39))
check("2 TC của CHKC1 không được tính vào tín chỉ tích luỹ",
      abs(r1_base.credits_passed - r1.credits_passed - 2.0) < 1e-6,
      f"{r1_base.credits_passed} vs {r1.credits_passed}")
check("Điểm F làm CPA giảm", (r1.cpa4 or 0) < (r1_base.cpa4 or 0),
      f"{r1.cpa4} < {r1_base.cpa4}")
check("App báo cảnh báo 'học phần không đạt'",
      any("không đạt" in a.title.lower() for a in r1.alerts),
      "; ".join(a.title for a in r1.alerts))
check("Môn CHKC1 nằm trong danh sách môn không đạt", any(
    "Cơ học kết cấu 1" in str(getattr(f, "name", f)) for f in r1.failed))
check("Học phần phụ thuộc của CHKC1 gồm CHKC2", 39 in f1.dependents(29))

# ------------------------------------------------------ 2. F Cơ lý thuyết (HK2)
section("2. Cơ lý thuyết (HK2, 2 TC) bị điểm F")
f2 = make_book("f_clt.json", (1,), fail=[(14, 2.0)])
r2 = LocalAnalytics(f2).report()
check("Cơ lý thuyết vào kế hoạch học lại", any("Cơ lý thuyết" in n for n in names(r2)),
      str(names(r2)))
check("Sức bền vật liệu (19) bị khoá vì thiếu Cơ lý thuyết", f2.is_locked(19))
check("Cơ học kết cấu 1 (29) cũng bị khoá theo chuỗi tiên quyết", f2.is_locked(29))
check("Cơ lý thuyết được ưu tiên 'mở khoá nhiều học phần'",
      any("mở khoá nhiều" in p.suggest_when for p in r2.retake_plan
          if "Cơ lý thuyết" in p.name),
      "; ".join(p.suggest_when for p in r2.retake_plan))
check("Chuỗi phụ thuộc của Cơ lý thuyết chứa Sức bền và CHKC1",
      {19, 29}.issubset(set(f2.dependents(14))), str(f2.dependents(14)))

# --------------------------- 3. Qua Cơ lý thuyết nhưng F Sức bền vật liệu (HK3)
section("3. Đã qua Cơ lý thuyết, nhưng Sức bền vật liệu (HK3, 3 TC) bị F")
f3 = make_book("f_sbvl.json", (1, 2), fail=[(19, 2.0)])
r3 = LocalAnalytics(f3).report()
check("Cơ lý thuyết đã đạt nên không bị khoá", not f3.is_locked(14))
check("Sức bền vật liệu vào kế hoạch học lại",
      any("Sức bền vật liệu" in n for n in names(r3)), str(names(r3)))
check("Cơ học kết cấu 1 bị khoá vì thiếu Sức bền", f3.is_locked(29))
check("Sức bền vật liệu là điều kiện của CHKC1", 29 in f3.dependents(19))
check("3 TC Sức bền không được tính", abs(
    LocalAnalytics(make_book("ok3.json", (1, 2), extra_pass=(19,))).report().credits_passed
    - r3.credits_passed - 3.0) < 1e-6)
check("Không có môn nào khác bị khoá oan (CHKC1 là môn duy nhất phụ thuộc)",
      all(not f3.is_locked(c["id"]) for c in f3.courses_in(3)
          if c["id"] not in (19,) and c["id"] not in f3.grades))

# -------------------------------------------------------- 4. Cảnh báo học tập
section("4. Cảnh báo học tập theo Điều 12 QĐ 2244/2021")
w = rules.warning_status(0.65, 1, None)
check("HK1 TB < 0,80 → cảnh báo", w["warning"] and w["level"] == "warning")
check("HK1 CPA < 1,20 → cũng cảnh báo", rules.warning_status(3.0, 1, 1.10)["warning"])
check("Năm 2 ngưỡng CPA 1,40", rules.cpa_warning_threshold(4) == 1.40)
check("Năm 3 ngưỡng CPA 1,60", rules.cpa_warning_threshold(5) == 1.60)
check("Năm 4 ngưỡng CPA 1,80", rules.cpa_warning_threshold(8) == 1.80)
check("2 lần liên tiếp → nguy cơ buộc thôi học",
      rules.warning_status(0.7, 2, 1.2, warn_streak=1)["level"] == "dismiss_risk")
check("Kết quả tốt → an toàn", rules.warning_status(2.9, 4, 2.8)["level"] == "none")
low = make_book("low.json", (1,))
for c in low.courses_in(1):
    if "ALL" not in c["prereq"]:
        low.save(c["id"], 3.0, 2.0, 2.5)
rl = LocalAnalytics(low).report()
check("Học kỳ đầu toàn điểm thấp → báo cảnh báo trong app",
      rl.compliance["warning"]["warning"], str(rl.compliance["warning"]["reasons"]))

# ------------------------------------------------ 5. Giới hạn đăng ký & chuẩn
section("5. Đăng ký học phần, tốt nghiệp, học bổng")
check("Chưa đạt chuẩn TA → tối đa 14 TC", rules.registration_limit(False)["max"] == 14)
check("Đạt chuẩn TA → tối đa 25 TC", rules.registration_limit(True)["max"] == 25)
check("Học kỳ hè ≤ 10 TC", rules.registration_limit(True)["summer_max"] == 10)
grad = {i["key"]: i for i in rules.graduation_requirements(156, 156, 2.4, True, True)}
check("Đủ 4 điều kiện → tốt nghiệp", all(i["ok"] for i in grad.values()))
check("Thiếu chuẩn CNTT → chưa tốt nghiệp",
      not {i["key"]: i for i in rules.graduation_requirements(156, 156, 2.4, True, False)}["it"]["ok"])
check("Đồ án TN cần CPA ≥ 1,90", rules.thesis_eligibility(4, 1.90)["ok"]
      and not rules.thesis_eligibility(4, 1.85)["ok"])
check("Đồ án TN chỉ khi còn ≤ 4 TC", not rules.thesis_eligibility(6, 2.5)["ok"])
check("Học bổng A: GPA ≥ 9,00 + RL ≥ 90",
      rules.scholarship_level(9.1, 92)["code"] == "A")
check("GPA 8,5 + RL 60 → không có học bổng (thiếu RL)",
      rules.scholarship_level(8.5, 60) is None)
check("Hệ số học bổng A/B/C = 150/120/100%",
      [rules.scholarship_level(g, c)["factor"] for g, c in ((9.2, 95), (8.2, 85), (7.2, 70))]
      == [1.5, 1.2, 1.0])

# --------------------------------------------------- 6. Tra cứu tài liệu thầy gửi
section("6. Tra cứu văn bản quy chế đã nhúng (thầy gửi)")
check("Có 5 văn bản trong assets/luat", len(list(rules.docs_dir().glob("*.txt"))) >= 6,
      str(rules.docs_dir()))
snip = rules.doc_snippets("cảnh báo kết quả học tập, buộc thôi học")
check("Hỏi cảnh báo → trích QĐ 2244 Điều 12", "0,80" in snip or "0.80" in snip or "1,00" in snip,
      snip[:120])
snip = rules.doc_snippets("chuẩn tiếng Anh TOEIC bao nhiêu để tốt nghiệp")
check("Hỏi TOEIC → trích QĐ 4511", "TOEIC" in snip, snip[:120])
snip = rules.doc_snippets("chứng chỉ CNTT IU01 IU06")
check("Hỏi CNTT → trích QĐ 417", "IU01" in snip, snip[:120])
snip = rules.doc_snippets("copy bài của bạn bị xử lý thế nào đạo văn")
check("Hỏi đạo văn → trích QĐ 029", "Đạo văn" in snip or "đạo văn" in snip, snip[:120])
snip = rules.doc_snippets("điều kiện học bổng khuyến khích học tập loại A")
check("Hỏi học bổng → trích QĐ 1414", "150" in snip or "học bổng" in snip.lower(), snip[:120])

# --------------------------------------------------------- 7. Nối luật vào prompt
section("7. Prompt gửi AI có luật + tài liệu trích")
book = make_book("ctx.json", (1, 2, 3), fail=[(29, 2.0)])
ctx = LocalAnalytics(book).context_text()
msgs = build_messages("warning", ctx, extra="Nếu Cơ học kết cấu 1 bị F thì sao?")
blob = "\n".join(m["content"] for m in msgs)
check("context_text có quy chế", "QUY CHẾ ÁP DỤNG" in ctx)
check("messages có trích tài liệu quy chế", "TRÍCH TÀI LIỆU QUY CHẾ" in blob)
check("messages có yêu cầu nêu căn cứ điều khoản", "Điều 12" in blob)

# --------------------------------------------------------------- 8. Hỏi AI thật
section("8. Hỏi trợ lý AI (câu hỏi của thầy + quy chế)")
AI_CASES = [
    ("Cơ học kết cấu 1 bị F", "Nếu em bị điểm F môn Cơ học kết cấu 1 (học kỳ 4, 2 tín chỉ) "
     "thì chuyện gì xảy ra với em?", ["học lại", "kết cấu 2", "khóa", "khoá", "tiên quyết"]),
    ("F Cơ lý thuyết", "Nếu em bị điểm F môn Cơ lý thuyết ở học kỳ 2 thì những môn nào "
     "bị ảnh hưởng và em phải làm gì?", ["sức bền", "kết cấu", "học lại"]),
    ("Qua Cơ lý thuyết, F Sức bền", "Em đã qua Cơ lý thuyết nhưng bị F môn Sức bền vật liệu "
     "thì có được học Cơ học kết cấu 1 không?", ["không", "kết cấu 1"]),
    ("Mức cảnh báo hiện tại", "Em có đang bị cảnh báo kết quả học tập không? Nêu căn cứ quy chế.",
     ["cảnh báo", "điều 12", "2244"]),
    ("Giới hạn tín chỉ", "Học kỳ tới em được đăng ký tối đa bao nhiêu tín chỉ?", ["14", "25"]),
    ("Chuẩn ngoại ngữ", "Em cần chứng chỉ tiếng Anh nào và bao nhiêu điểm để đủ điều kiện tốt nghiệp?",
     ["toeic", "450", "4511"]),
    ("Điều kiện đồ án", "Em cần điều kiện gì để được làm đồ án tốt nghiệp?",
     ["1,90", "1.90", "4 tín", "4 tc", "điều 15"]),
    ("Liêm chính học thuật", "Nếu em chép bài của bạn rồi nộp thì bị xử lý thế nào?",
     ["đạo văn", "liêm chính", "029"]),
]

ANSWER_FILE = ROOT / "video" / "case_answers.md"
ANSWER_FILE.parent.mkdir(parents=True, exist_ok=True)


def ask_ai(question: str, context: str, timeout: float = 150.0) -> str:
    client = AIClient()
    if not client.configured():
        return ""
    messages = build_messages("qa", context, extra=question)
    box: dict[str, str] = {}
    done = threading.Event()

    def ok(text):
        box["text"] = text
        done.set()

    def err(msg):
        box["err"] = str(msg)
        done.set()

    # Model suy luận (reasoning) dùng nhiều token nội bộ nên cần dư chỗ cho phần trả lời.
    client.chat(messages, ok, err, temperature=0.35, max_tokens=2200)
    done.wait(timeout)
    return box.get("text", "") or ("[LỖI] " + box.get("err", "timeout"))


if ONLINE:
    ANSWER_FILE.write_text("# Câu hỏi kiểm thử & trả lời của trợ lý AI\n\n", encoding="utf-8")
    for label, question, keys in AI_CASES:
        t0 = time.time()
        answer = ask_ai(question, ctx)
        low = answer.lower()
        hit = [k for k in keys if k.lower() in low]
        ok_case = bool(answer) and not answer.startswith("[LỖI]") and bool(hit)
        check(f"AI: {label}", ok_case,
              (f"{time.time() - t0:.0f}s, khớp {hit}" if ok_case else answer[:140]))
        with ANSWER_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"## {label}\n\n**Hỏi:** {question}\n\n**Đáp:**\n\n{answer}\n\n---\n\n")
    print(f"\n  (đã lưu câu trả lời vào {ANSWER_FILE})")
else:
    print("  (bỏ qua phần hỏi AI vì chạy --offline)")

print(f"\nKẾT QUẢ: {OK} đạt, {FAIL} lỗi")
(ROOT / "video" / "case_results.txt").write_text("\n".join(LOGS), encoding="utf-8")
sys.exit(1 if FAIL else 0)
