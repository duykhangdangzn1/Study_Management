"""Kiểm thử đúng luồng người dùng: GÕ CÂU HỎI VÀO KHUNG CHAT CỦA APP rồi bấm gửi.

Không gọi thẳng engine: test dựng trang AI thật, đặt chữ vào ô nhập, kích hoạt nút gửi,
đợi AI trả lời và đọc lại bong bóng chat + lịch sử phiên.

Chạy: python tests_chat_ui.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))

import core                       # noqa: E402
import ai_page                    # noqa: E402
import ui_kit                     # noqa: E402
from PySide6.QtWidgets import QApplication   # noqa: E402

OK = 0
FAIL = 0
LOGS: list[str] = []


def check(name, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}" + (f"  [{detail}]" if detail else ""))
    LOGS.append(("ok   " if cond else "FAIL ") + name + (f" | {detail}" if detail else ""))


def make_book(tmp: Path) -> core.GradeBook:
    """Bảng điểm tổng hợp: HK1–3 đã học, Cơ học kết cấu 1 (HK4) bị F."""
    book = core.GradeBook(tmp / "grades.json")
    for sem in (1, 2, 3):
        for c in book.courses_in(sem):
            if c["elective"] or "ALL" in str(c["prereq"]):
                continue
            book.save(c["id"], 8, 8, 8)
    book.save(29, 1, 0, 2.0)
    return book


def main() -> int:
    app = QApplication.instance() or QApplication([])
    ui_kit.load_fonts()
    tmp = Path(tempfile.mkdtemp(prefix="chatui_"))
    ai_page.CHAT_PATH = tmp / "chat.json"
    old_dialog = ui_kit.MessageDialog.exec
    ui_kit.MessageDialog.exec = lambda self, *a, **k: 0

    book = make_book(tmp)
    page = ai_page.AIPage(book)
    page.resize(1500, 960)
    page.show()
    page.tabs.setCurrentWidget(page.chat_tab)
    app.processEvents()

    print("=== Mở khung chat của app ===")
    check("Có ô nhập chat", page.chat_tab.input is not None)
    check("Có nút gửi", page.chat_tab.send_btn is not None)
    check("Có vùng bong bóng hội thoại", page.chat_tab.msgs is not None)
    check("Ô nhập có placeholder hướng dẫn",
          "Hỏi AI" in page.chat_tab.input.placeholderText(),
          page.chat_tab.input.placeholderText())

    CASES = [
        ("F Cơ học kết cấu 1",
         "Nếu em bị điểm F môn Cơ học kết cấu 1 thì chuyện gì xảy ra với em?",
         ["học lại", "kết cấu 2", "khóa", "khoá", "tiên quyết"]),
        ("F Cơ lý thuyết",
         "Nếu em bị F môn Cơ lý thuyết ở học kỳ 2 thì môn nào bị ảnh hưởng?",
         ["sức bền", "thủy lực", "khóa"]),
        ("Qua Cơ lý thuyết, F Sức bền",
         "Em đã qua Cơ lý thuyết nhưng bị F Sức bền vật liệu, có được học Cơ học kết cấu 1 không?",
         ["không", "kết cấu 1"]),
        ("Cảnh báo học tập",
         "Em có đang bị cảnh báo kết quả học tập không? Nêu căn cứ.",
         ["điều 12", "2244", "cảnh báo"]),
        ("Giới hạn tín chỉ",
         "Học kỳ tới em được đăng ký tối đa bao nhiêu tín chỉ?",
         ["14", "25"]),
    ]

    answers: list[str] = []
    for label, question, keys in CASES:
        print(f"\n=== Gõ vào khung chat: {label} ===")
        before = len(page.chat_tab.bubbles)
        page.chat_tab.input.setText(question)
        app.processEvents()
        check("Câu hỏi đã nằm trong ô nhập", page.chat_tab.input.text() == question)
        page.chat_tab._on_send()          # đúng hành động bấm nút gửi
        app.processEvents()
        check("Ô nhập được xoá sau khi gửi", page.chat_tab.input.text() == "")

        t0 = time.time()
        while page.session.busy and time.time() - t0 < 200:
            app.processEvents()
            time.sleep(0.05)
        app.processEvents()

        msgs = page.session.messages
        answer = msgs[-1]["content"] if msgs and msgs[-1]["role"] == "assistant" else ""
        answers.append(answer)
        low = answer.lower()
        hit = [k for k in keys if k.lower() in low]
        check(f"AI trả lời ({time.time() - t0:.0f}s)", bool(answer) and not answer.startswith("["),
              answer[:120])
        check(f"Trả lời đúng trọng tâm: {label}", bool(hit),
              f"khớp {hit}" if hit else answer[:140])
        check("Chat hiển thị thêm bong bóng hỏi + đáp",
              len(page.chat_tab.bubbles) >= before + 2,
              f"{before} → {len(page.chat_tab.bubbles)}")
        check("Lịch sử phiên có câu hỏi của người dùng",
              any(m["role"] == "user" and m["content"] == question for m in msgs))

    print("\n=== Lịch sử hội thoại ===")
    check("Lịch sử lưu đủ 5 câu hỏi + 5 câu trả lời",
          len([m for m in page.session.messages if m["role"] == "user"]) == len(CASES))

    ai_page.CHAT_PATH = ROOT / "video" / "chat_ui_answers.md"
    with open(ai_page.CHAT_PATH, "w", encoding="utf-8") as fh:
        fh.write("# Trả lời qua khung chat của ứng dụng\n\n")
        for (label, question, _), ans in zip(CASES, answers):
            fh.write(f"## {label}\n\n**Hỏi (gõ vào khung chat):** {question}\n\n"
                     f"**AI trả lời:**\n\n{ans}\n\n---\n\n")

    ui_kit.MessageDialog.exec = old_dialog
    print(f"\nKẾT QUẢ: {OK} đạt, {FAIL} lỗi")
    (ROOT / "video" / "chat_ui_results.txt").write_text("\n".join(LOGS), encoding="utf-8")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
