import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import main as M, core, ui_kit
app = QApplication(sys.argv); app.setStyle("Fusion")
fam = ui_kit.load_fonts(); app.setFont(QFont(fam, 10)); app.setStyleSheet(ui_kit.qss())
book = core.GradeBook(pathlib.Path(tempfile.mkdtemp()) / "g.json")
import random; random.seed(3)
for s in (1, 2, 3):
    for c in book.courses_in(s):
        r = book.save(c["id"], random.choice([7,8,9,6.5,10]), random.choice([6,7,8,9]), random.choice([5,6.5,7,8,9.5]))
book.save(24, 2, 3, 3)  # TN thuy luc fail
for c in book.courses_in(4)[:3]: book.save(c["id"], 8, 8, 8)
w = M.MainWindow(book); w.animate = False; w.resize(1560, 960); w.show()
def snap(name):
    for _ in range(5): app.processEvents()
    w.grab().save(f"shots/{name}.png")
snap("1_intro"); w.go(1); snap("2_dash"); w.open_semester(4); snap("3_courses")
w.courses.focus_course(34); snap("4_locked"); w.go(3); snap("5_results")
w.go(2); w.courses.focus_course(40); snap("6_locked")
d = w.courses.detail
for f, v in zip((d.f_tp, d.f_gk, d.f_ck), ("8", "7,5", "9")): f.edit.setText(v)
app.processEvents(); snap("7_preview")
res = book.save(40, 8, 7.5, 9)
dlg = M.MessageDialog(w, "Không thể lưu điểm", res.message, res.problems, "warning"); dlg.show(); app.processEvents(); dlg.grab().save("shots/8_block.png"); dlg.close()
w.announce_semester = lambda s: None
dlg2 = M.MessageDialog(w, "Hoàn thành Học kỳ 3!", "Kết quả học kỳ và điểm tích lũy của bạn:", ["GPA Học kỳ 3: 3.03", "CPA tích lũy: 3.03", "Học kỳ 4 tiếp theo có 10 học phần (17 tín chỉ)"], "success"); dlg2.show(); app.processEvents(); dlg2.grab().save("shots/9_done.png")
w.toast("Đã lưu: Giải tích — 8.4 (B+)"); 
import time
for _ in range(40): app.processEvents(); time.sleep(0.02)
snap("10_toast")
