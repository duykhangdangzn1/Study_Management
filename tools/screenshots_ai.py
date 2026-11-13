"""Chụp ảnh các trang AI (offscreen) để kiểm tra giao diện.

Chạy:  python tools/screenshots_ai.py
Ảnh lưu vào  artifacts/*.png
"""
import os
import pathlib
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from PySide6.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

import ai_page
import automation
from core import GradeBook

TMP = pathlib.Path(tempfile.mkdtemp())
ai_page.CHAT_PATH = TMP / "chat.json"
automation.CONFIG_PATH = TMP / "automation.json"
automation.STORE_PATH = TMP / "reminders.json"
automation.load_config = lambda: dict(automation.DEFAULT_CONFIG, ai_coach=False, study_time="00:00")

OUT = ROOT / "artifacts"
OUT.mkdir(exist_ok=True)


def demo_book() -> GradeBook:
    book = GradeBook(TMP / "demo.json")
    scores = {1: (7.5, 8.0, 8.5), 2: (7.0, 7.5, 8.0), 3: (8.0, 8.5, 9.0)}
    for sem, (tp, gk, ck) in scores.items():
        for c in book.courses_in(sem):
            if c["elective"] or "ALL" in c["prereq"]:
                continue
            book.save(c["id"], tp, gk, ck)
    candidates = [c for c in book.courses_in(3) if not c["elective"] and not book.dependents(c["id"])]
    if candidates:
        book.save(candidates[0]["id"], 3.5, 3.0, 3.2)
    return book


def main():
    import ui_kit
    import main as main_mod
    from main import MainWindow

    ui_kit.load_fonts()
    main_mod.save_settings = lambda data: None

    book = demo_book()
    w = MainWindow(book)
    w.animate = False   # tránh ảnh chụp bị trong suốt do hiệu ứng fade
    w.resize(1500, 940)
    w.show()
    for _ in range(6):
        APP.processEvents()
    w.engine.refresh(force=True, notify=False)
    for _ in range(4):
        APP.processEvents()

    failed = sum(1 for s in (1, 2, 3) for c in book.courses_in(s)
                 if book.result(c["id"]) and not book.result(c["id"]).passed)
    cum = book.cumulative()
    fail_note = "Cần học lại" if failed else "Đạt tất cả"
    w.session.append("user", "Thống kê tình hình học tập của tôi sau Học kỳ 3?")
    w.session.append("assistant",
        "### BẢNG THỐNG KÊ HỌC TẬP\n\n"
        "| Chỉ tiêu | Giá trị | Ghi chú |\n"
        "| --- | --- | --- |\n"
        f"| CPA (hệ 4) | {ai_page.fmt(cum['cpa4'])} | Xếp loại: {cum['rank']} |\n"
        f"| CPA (hệ 10) | {ai_page.fmt(cum['cpa10'])} | Thang 10 |\n"
        f"| Tín chỉ tích lũy | {cum['credits']:g} / 156 TC | Còn {156 - cum['credits']:g} TC |\n"
        f"| Học phần không đạt | {failed} môn | {fail_note} |\n\n"
        "**Việc cần làm ngay:**\n"
        "1. Đăng ký học lại học phần chưa đạt ở HK4.\n"
        "2. Dành 2 buổi/tuần ôn lại môn nền tảng.\n"
        "3. Cập nhật điểm đúng hạn để theo dõi tiến độ.")
    for _ in range(4):
        APP.processEvents()

    shots = [("01_dashboard", lambda: w.go(1)),
             ("02_ai_overview", lambda: (w.go(4), w.ai.open_tab("overview"))),
             ("03_ai_chat", lambda: (w.go(4), w.ai.open_tab("chat"))),
             ("04_ai_plan", lambda: (w.go(4), w.ai.open_tab("plan"))),
             ("05_ai_automation", lambda: (w.go(4), w.ai.open_tab("automation"))),
             ("06_ai_settings", lambda: (w.go(4), w.ai.open_tab("settings"))),
             ("07_bubble", lambda: (w.go(1), w._place_floating(w.centralWidget()),
                                    w.floating.show_popup())),
             ("08_results", lambda: w.go(3)),
             ("09_toast", lambda: (w.go(3), w.toast("AI: Lời khuyên AI hôm nay", "info")))]
    for name, action in shots:
        action()
        for _ in range(5):
            APP.processEvents()
        path = OUT / f"{name}.png"
        w.grab().save(str(path))
        print("saved", path)
    w.floating.close_popup()
    w.toast_w.hide_now(immediate=True)
    w.engine.stop()
    w.close()


if __name__ == "__main__":
    main()
