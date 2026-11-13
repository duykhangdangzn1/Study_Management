"""Kiểm thử giao diện (offscreen): tất cả trang, tab AI, bong bóng, tự động hoá.

Chạy:  python tests_gui.py
"""
import os
import pathlib
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(pathlib.Path(__file__).parent / "app"))

from PySide6.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

import ai_page
import automation
import ui_kit
from ai_page import ChatBubble, ChatStore, prepare_markdown, to_rich
from core import GradeBook, SEMESTERS

FAILED = []
TMP = pathlib.Path(tempfile.mkdtemp())
ai_page.CHAT_PATH = TMP / "chat.json"
automation.CONFIG_PATH = TMP / "automation.json"
automation.STORE_PATH = TMP / "reminders.json"
automation.load_config = lambda: dict(automation.DEFAULT_CONFIG, ai_coach=False,
                                      check_interval_min=30, study_time="00:00")


def check(cond, msg):
    if cond:
        print(f"  [OK]   {msg}")
    else:
        print(f"  [FAIL] {msg}")
        FAILED.append(msg)


def section(title):
    print(f"\n=== {title} ===")


# ------------------------------------------------------------------ 0. helpers
section("0. Tiện ích hiển thị")
rich = to_rich("**Đậm** và `code`\n- gạch đầu dòng\n1. mục số\n<script>alert(1)</script>")
check("<b>Đậm</b>" in rich, "Markdown **đậm** → HTML")
check("&lt;script&gt;" in rich and "<script>" not in rich, "HTML được escape an toàn")
check("• gạch đầu dòng" in rich, "Gạch đầu dòng được định dạng")
table_md = "| Chỉ tiêu | Giá trị |\n| --- | --- |\n| CPA | 2.44 |"
rich_table = to_rich(table_md)
check("<table" in rich_table and "| --- |" not in rich_table, "Markdown table → HTML table")
bubble = ChatBubble(table_md, "assistant")
bubble.set_max_width(700)
APP.processEvents()
html_doc = bubble.body.document().toHtml().lower()
check("<table" in html_doc and "cpa" in bubble.body.toPlainText().lower(), "Bong bóng chat render bảng thật")
check(bubble.body.height() > 40, "Chiều cao bong bóng khớp nội dung bảng")
broken = prepare_markdown("| A | B |\n| 1 | 2 |")
check("| --- | --- |" in broken, "Tự bổ sung dòng phân cách cho bảng AI viết thiếu")

# ------------------------------------------------------------------ 1. data
section("1. Chuẩn bị dữ liệu mẫu")
book = GradeBook(TMP / "g.json")
for sem in (1, 2, 3):
    for c in book.courses_in(sem):
        if c["elective"] or "ALL" in c["prereq"]:
            continue
        book.save(c["id"], 8, 8, 8)
# một môn trượt ở HK3 để có cảnh báo + kế hoạch học lại
candidates = [c for c in book.courses_in(3) if not c["elective"] and not book.dependents(c["id"])]
if candidates:
    fail_id = candidates[0]["id"]
    r = book.save(fail_id, 3, 3, 3)
    check(r.ok, f"Tạo điểm không đạt cho học phần {fail_id}")
else:
    print("  [SKIP] Không tìm được học phần không có môn phụ thuộc")

# ------------------------------------------------------------------ 2. window
section("2. Khởi tạo cửa sổ chính")
ui_kit.load_fonts()
import main as main_mod
from main import MainWindow

main_mod.save_settings = lambda data: None   # không ghi đè cài đặt người dùng
w = MainWindow(book)
w.resize(1440, 900)
w.show()
for _ in range(3):
    APP.processEvents()
check(w.stack.count() == 5, f"Có {w.stack.count()} trang")
check(w.ai.tabs.count() == 5, f"Trang AI có {w.ai.tabs.count()} tab")
check(type(w.ai.tabs.tabBar()).__name__ == "SegmentedTabBar", "Tab bar dùng segmented control mới")

# ------------------------------------------------------------------ 3. pages
section("3. Điều hướng toàn bộ trang")
for i in range(5):
    w.go(i)
    APP.processEvents()
    check(w.stack.currentIndex() == i, f"Mở trang {i}")
w.dash.refresh()
w.courses.refresh()
w.results.refresh()
APP.processEvents()
check(w.courses.table.rowCount() > 0, f"Bảng học phần có {w.courses.table.rowCount()} dòng")
check(w.side_cpa.text() != "—", f"Sidebar CPA = {w.side_cpa.text()}")

# ------------------------------------------------------------------ 4. AI tabs
section("4. Trang AI – 5 tab")
w.go(4)
for idx in range(w.ai.tabs.count()):
    w.ai.tabs.setCurrentIndex(idx)
    APP.processEvents()
    check(w.ai.tabs.currentIndex() == idx, f"Tab AI {idx} hiển thị")
w.ai.refresh()
APP.processEvents()
check(w.ai.analysis.alert_box.count() > 0, "Tab tổng quan có cảnh báo")
check(w.ai.analysis.retake_box.count() > 0, "Tab tổng quan có kế hoạch học lại")
check(w.ai.analysis.todo_box.count() > 0, "Tab tổng quan có việc cần làm")

w.ai.tabs.setCurrentWidget(w.ai.plan)
w.ai.plan.refresh()
APP.processEvents()
check(w.ai.plan.week_box.count() > 0, "Tab kế hoạch có thời khoá biểu")
check(w.ai.plan.methods_box.count() > 0, "Tab kế hoạch có phương pháp học")
check(w.ai.plan.retake_box.count() > 0, "Tab kế hoạch có lịch học lại")

# ------------------------------------------------------------------ 5. automation
section("5. Tab tự động hoá")
w.ai.tabs.setCurrentWidget(w.ai.automation)
eng = w.engine
eng.refresh(force=True, notify=False)
APP.processEvents()
w.ai.automation.refresh_list()
APP.processEvents()
check(len(eng.store.active()) > 0, f"Có {len(eng.store.active())} nhắc nhở hoạt động")
check(w.ai.automation.list_box.count() > 0, "Hộp nhắc nhở hiển thị")
check(w.ai.automation.cb_enabled.isChecked(), "Cài đặt tự động hoá được nạp")
w.ai.automation._save()
APP.processEvents()
check(eng.cfg["study_time"] == w.ai.automation.time_study.time().toString("HH:mm"),
      "Lưu cài đặt tự động hoá")
w.ai.automation._read_all()
APP.processEvents()
check(eng.store.unseen_count() == 0, "Đánh dấu đã đọc tất cả")
w.ai.automation._run_now()
APP.processEvents()
check(w.ai.automation.status_lbl.text() != "", "Thanh trạng thái có nội dung")

# ------------------------------------------------------------------ 6. bubble
section("6. Bong bóng chat & cửa sổ nổi")
w.go(1)   # bong bóng chỉ hiện ngoài trang AI
w._place_floating(w.centralWidget())
APP.processEvents()
check(w.floating.isVisible(), "Bong bóng hiển thị")
w.floating.set_badge(4)
APP.processEvents()
check(w.floating._badge == 4, "Badge cập nhật")
w.floating.show_popup()
APP.processEvents()
check(w.floating._popup.isVisible(), "Popup chat mở")
w.session._done("Kết quả phân tích thử nghiệm")
APP.processEvents()
check(any("Kết quả phân tích" in m["content"] for m in w.session.messages), "Tin nhắn AI vào phiên chat")
w.floating.close_popup()
APP.processEvents()
check(not w.floating._popup.isVisible(), "Popup chat đóng")
w.go(4)
APP.processEvents()
check(not w.floating.isVisible(), "Trang AI ẩn bong bóng để không che ô nhập")

# ------------------------------------------------------------------ 6b. history
section("6b. Lịch sử trò chuyện")
w.session.append("user", "Phân tích điểm HK1 giúp mình")
first = w.session.session_id
w.session.new_chat()
w.session.append("user", "Lập kế hoạch học lại cho HK4")
second = w.session.session_id
check(first != second and len(w.session.store.sessions) >= 2, "Tạo cuộc trò chuyện mới")
w.session.rename_chat(second, "Kế hoạch HK4")
check(w.session.store.get(second)["title"] == "Kế hoạch HK4", "Đổi tên cuộc trò chuyện")
w.session.switch(first)
APP.processEvents()
check(any("Phân tích điểm HK1" in m["content"] for m in w.session.messages), "Chuyển lại lịch sử cũ")
check(len(w.ai.chat_tab.bubbles) >= 1, "Khung chat vẽ lại theo lịch sử")
w.session.delete_chat(second)
check(w.session.store.get(second) is None, "Xoá cuộc trò chuyện")
reloaded = ChatStore(TMP / "chat.json")
check(any(s["id"] == first for s in reloaded.sessions), "Lịch sử được lưu ra đĩa và nạp lại")

# ------------------------------------------------------------------ 6c. toast
section("6c. Thông báo có nút đóng")
w.toast("Thông báo kiểm thử", "info")
APP.processEvents()
check(w.toast_w.isVisible() and w.toast_w.close_btn.isVisible(), "Toast hiển thị kèm nút ×")
check(w.toast_w._timer.isActive(), "Toast tự ẩn theo hẹn giờ")
w.toast("Thông báo kiểm thử", "info")
check(w.toast_w._text == "Thông báo kiểm thử", "Chống trùng thông báo")
w.toast_w.close_btn.click()
w.toast_w.hide_now(immediate=True)
check(not w.toast_w.isVisible(), "Nút × đóng được thông báo")

# ------------------------------------------------------------------ 7. settings
section("7. Cài đặt AI")
w.ai.tabs.setCurrentWidget(w.ai.settings)
APP.processEvents()
check(w.ai.settings.lbl_endpoint.text() != "", "Hiển thị BASE_URL")
check(w.ai.settings.inp_key.placeholderText() != "", "Ô API key có gợi ý khoá đã lưu")
check(w.ai.settings.lbl_model.text() != "", "Hiển thị MODEL")
w.ai.settings._test_err("Lỗi thử nghiệm")
check("Lỗi thử nghiệm" in w.ai.settings.test_result.text(), "Hiển thị lỗi kết nối")
w.ai.settings._test_ok({"ok": True, "models": ["auto:smart", "auto"], "current": "auto:smart", "count": 2})
check("thành công" in w.ai.settings.test_result.text(), "Hiển thị kết nối thành công")

# ------------------------------------------------------------------ 8. theme
section("8. Chuyển giao diện Sáng/Tối")
w.set_theme("dark")
APP.processEvents()
w.go(4)
APP.processEvents()
check(ui_kit.THEME == "dark", "Chuyển sang tối")
w.set_theme("light")
APP.processEvents()
w.go(4)
APP.processEvents()
check(ui_kit.THEME == "light", "Chuyển lại sáng")
check(w.ai.tabs.count() == 5, "Trang AI dựng lại đủ tab sau khi đổi giao diện")

# ------------------------------------------------------------------ 9. teardown
section("9. Đóng ứng dụng")
w.engine.stop()
w.close()
APP.processEvents()
check(not w.engine.running, "Bộ tự động hoá dừng khi đóng")

print("\n" + "=" * 60)
if FAILED:
    print(f"FAILED {len(FAILED)} test(s):")
    for f in FAILED:
        print("  -", f)
    sys.exit(1)
print("ALL GUI TESTS PASSED")
