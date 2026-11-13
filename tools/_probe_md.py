import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))

from PySide6.QtWidgets import QApplication, QTextBrowser
from PySide6.QtGui import QTextDocument

app = QApplication([])
md = """Dưới đây là bảng thống kê:

### BẢNG THỐNG KÊ HỌC TẬP

| Chỉ tiêu | Trạng thái / Giá trị | Ghi chú |
| --- | --- | --- |
| Tổng tín chỉ chương trình | 156 TC | 9 học kỳ |
| Tín chỉ đã tích lũy | 11.0 / 156 TC | ⚠ Chậm tiến độ |
| CPA (Hệ 4) | 4.0 | ✅ Xuất sắc |
| Số môn không đạt | 2 môn | ⚠ Cần học lại ngay |

**Kết luận:** cần cải thiện ngay.
"""
doc = QTextDocument()
doc.setDefaultStyleSheet("table { border-collapse: collapse; } td, th { padding: 5px 8px; border: 1px solid #E6EAF3; }")
doc.setMarkdown(md, QTextDocument.MarkdownDialectGitHub)
doc.setTextWidth(560)
print("SIZE", doc.size().width(), doc.size().height())
print("TABLES", len([f for f in doc.rootFrame().childFrames()]))
print(doc.toHtml()[:900])
b = QTextBrowser()
b.setFrameShape(QTextBrowser.NoFrame)
b.setStyleSheet("background: white;")
b.setMarkdown(md, QTextDocument.MarkdownDialectGitHub)
b.resize(600, 320)
b.grab().save("artifacts/_probe_md.png")
print("saved probe")
