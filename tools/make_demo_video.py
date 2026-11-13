"""Video demo trợ lý AI + bộ kiểm thử (1920x1080, phụ đề ở dải riêng).

Dùng lại hạ tầng của make_intro_video.py (TTS VieNeu, ffmpeg, nhạc nền, Encoder).
Chạy: python tools/make_demo_video.py [--check]
Kết quả: video/Demo_TroLyAI_TestBo.mp4
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tools"))

from PySide6.QtCore import QRectF, Qt                       # noqa: E402
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap   # noqa: E402
from PySide6.QtWidgets import QApplication                  # noqa: E402

import core                                                 # noqa: E402
import ai_engine                                            # noqa: E402
import rules                                                # noqa: E402
import ui_kit                                               # noqa: E402
import make_intro_video as base                             # noqa: E402

_FONTS_READY = False

W, H, FPS = base.W, base.H, base.FPS
APP_H = base.APP_H
OUT = ROOT / "video"
AUD = OUT / "demo_audio"
SENT = OUT / "demo_sent"
INK, INK2 = base.INK, base.INK2
YEL, BLU, WHITE, MUT = base.YELLOW, base.BLUE, base.WHITE, base.MUTED
RED = QColor("#FF5A6E")
GRN = QColor("#37D67A")
CARD = QColor("#111C3C")

SCENES: list[dict] = []

# Câu chốt cho từng cảnh (in lớn ở nửa dưới khung hình)
TAKE = {
    "01_chao": "Một trợ lý biết đọc bảng điểm, biết luật của Trường, và biết trích dẫn nguồn.",
    "02_bo_test": "56 bài kiểm thử: 48 bài tính toán quy chế và 8 câu hỏi thật gửi cho AI.",
    "03_f_chkc1": "F một môn tiên quyết không chỉ mất 2 tín chỉ: nó chặn 7 học phần phía sau.",
    "04_f_clt": "F Cơ lý thuyết làm đứt chuỗi tiên quyết ngay từ mắt xích gốc.",
    "05_f_sbvl": "Đã qua Cơ lý thuyết vẫn chưa đủ: Sức bền vật liệu chặn Cơ học kết cấu 1.",
    "06_canh_bao": "Ngưỡng cảnh báo khác nhau theo từng năm học – phần mềm kiểm tra đúng ngưỡng.",
    "07_luat_ai": "AI trích đúng điều, khoản và số quyết định trong từng câu trả lời.",
    "08_ket": "56/56 bài đạt · ba câu hỏi của thầy đều có câu trả lời kèm số liệu.",
}


def add(name, text, cap, capsub, heading, sub, blocks, accent=YEL):
    SCENES.append(dict(name=name, text=text, cap=cap, capsub=capsub, heading=heading,
                       sub=sub, blocks=blocks, accent=accent))


# ------------------------------------------------------------------ nội dung
add("01_chao",
    "Kính chào thầy Nguyễn Thanh Hải.\n"
    "Em xin trình bày bản demo trợ lý AI của phần mềm Quản lý Học phần, "
    "ngành Tin học Xây dựng, Trường Đại học Bách khoa, Đại học Đà Nẵng.\n"
    "Toàn bộ số liệu trong video này do chính phần mềm tính ra, "
    "và đã được kiểm chứng bằng bộ kiểm thử tự động.",
    "Trợ lý AI học tập – bản demo kiểm thử",
    "Kính chào thầy Nguyễn Thanh Hải · Đồ án Quản lý Học phần – Tin học Xây dựng · ĐH Bách khoa – ĐH Đà Nẵng",
    "Kính chào thầy Nguyễn Thanh Hải",
    "Demo trợ lý AI thông minh · 56 bài kiểm thử tự động · số liệu thật từ phần mềm",
    [("chip", ["Đọc bảng điểm", "Đối chiếu quy chế", "Trả lời có căn cứ"]),
     ("big", ("56/56", "bài kiểm thử đạt")),
     ("note", "QĐ 2244/2021 · QĐ 4511/2022 · QĐ 417/2016 · QĐ 029/2017 · QĐ 1414/2021")])

add("02_bo_test",
    "Thầy đặt ba câu hỏi rất cụ thể.\n"
    "Một: nếu Cơ học kết cấu một bị điểm F thì sao.\n"
    "Hai: nếu Cơ lý thuyết bị F thì sao.\n"
    "Ba: nếu đã qua Cơ lý thuyết, nhưng Sức bền vật liệu bị F thì sao.\n"
    "Em đã đưa cả ba câu hỏi này, cùng bốn mươi tám trường hợp khác, vào bộ kiểm thử tự động. "
    "Kết quả: năm mươi sáu bài đạt, không có bài lỗi.",
    "Bộ kiểm thử: 56 bài",
    "48 bài tính toán quy chế + 8 câu hỏi thật gửi cho trợ lý AI",
    "Bộ kiểm thử hệ thống",
    "Chạy bằng một lệnh: python tests_cases.py",
    [("big", ("56 / 56", "đạt · 0 lỗi")),
     ("cols", [("Phần tính toán", ["Cảnh báo Điều 12", "Giới hạn 12–25 TC",
                                   "Tốt nghiệp, học bổng", "Chuỗi tiên quyết"]),
               ("Phần hỏi AI", ["F Cơ học kết cấu 1", "F Cơ lý thuyết",
                                "F Sức bền vật liệu", "Cảnh báo, TOEIC, đồ án"])])])

add("03_f_chkc1",
    "Câu hỏi thứ nhất: Cơ học kết cấu một bị điểm F.\n"
    "Đây là học phần hai tín chỉ, học kỳ bốn.\n"
    "Phần mềm trả lời bằng số liệu, không bằng cảm tính.\n"
    "Thứ nhất, hai tín chỉ này không được tính vào tín chỉ tích lũy, "
    "và điểm trung bình tích lũy bị kéo xuống.\n"
    "Thứ hai, sinh viên bắt buộc học lại, và được xếp ưu tiên cao, "
    "vì học phần này mở khóa cho bảy học phần phía sau.\n"
    "Thứ ba, Cơ học kết cấu hai ở học kỳ năm bị khóa, "
    "vì chưa đạt học phần tiên quyết.",
    "F Cơ học kết cấu 1 (HK4, 2 TC)",
    "Kết quả do phần mềm tính: 2 TC không tích lũy · 7 học phần bị khóa · phải học lại",
    "Nếu Cơ học kết cấu 1 bị điểm F",
    "Học phần tiên quyết của 7 học phần phía sau",
    [("kv", [("2 TC", "không được tính tích lũy"),
             ("7", "học phần phía sau bị khóa"),
             ("Học lại", "ưu tiên cao – mở khóa nhiều môn")]),
     ("flow", ["Cơ học kết cấu 1 (F)", "Cơ học kết cấu 2 (HK5)", "… 6 học phần khác"])],
    accent=RED)

add("04_f_clt",
    "Câu hỏi thứ hai: Cơ lý thuyết bị điểm F ở học kỳ hai.\n"
    "Chuỗi tiên quyết bị đứt ngay từ gốc.\n"
    "Sức bền vật liệu ở học kỳ ba bị khóa, "
    "và kéo theo Cơ học kết cấu một ở học kỳ bốn cũng bị khóa.\n"
    "Phần mềm ghi nhận đây là học phần điều kiện, "
    "và xếp lịch học lại sớm nhất có thể.",
    "F Cơ lý thuyết (HK2)",
    "Đứt chuỗi tiên quyết: Sức bền vật liệu và Cơ học kết cấu 1 đều bị khóa",
    "Nếu Cơ lý thuyết bị điểm F",
    "Một môn nền tảng, hai môn phía sau bị chặn",
    [("flow", ["Vật lý Cơ và Nhiệt", "Cơ lý thuyết (F)", "Sức bền vật liệu",
               "Cơ học kết cấu 1"]),
     ("note", "Hệ thống đề xuất: học lại Cơ lý thuyết ngay học kỳ kế tiếp để mở khóa chuỗi.")],
    accent=RED)

add("05_f_sbvl",
    "Câu hỏi thứ ba: đã qua Cơ lý thuyết, nhưng Sức bền vật liệu bị F.\n"
    "Lúc này Cơ học kết cấu một vẫn bị khóa, vì Sức bền vật liệu "
    "là điều kiện trực tiếp của nó.\n"
    "Phần mềm phân biệt rất rõ: Cơ lý thuyết đã đạt nên không còn bị chặn, "
    "chỉ còn Sức bền vật liệu chặn Cơ học kết cấu một.\n"
    "Đây chính là điểm mà tư vấn thủ công hay trả lời sai.",
    "Qua Cơ lý thuyết, F Sức bền vật liệu",
    "Cơ học kết cấu 1 vẫn bị khóa vì thiếu đúng học phần tiên quyết trực tiếp",
    "Đã qua Cơ lý thuyết, nhưng F Sức bền vật liệu",
    "Trả lời đúng từng mắt xích, không suy diễn",
    [("flow", ["Cơ lý thuyết (đạt)", "Sức bền vật liệu (F)", "Cơ học kết cấu 1 (khóa)"]),
     ("kv", [("3 TC", "Sức bền không tích lũy"),
             ("1", "học phần bị chặn trực tiếp"),
             ("Điều 9", "học lại học phần không đạt")])],
    accent=RED)

add("06_canh_bao",
    "Ngoài môn tiên quyết, phần mềm tự đối chiếu Điều mười hai "
    "của Quyết định hai hai bốn bốn về cảnh báo kết quả học tập.\n"
    "Cảnh báo khi điểm trung bình học kỳ dưới không phẩy tám mươi ở học kỳ đầu, "
    "hoặc dưới một phẩy không không ở các học kỳ sau.\n"
    "Hoặc khi điểm trung bình tích lũy dưới một phẩy hai đối với năm nhất, "
    "một phẩy bốn năm hai, một phẩy sáu năm ba, và một phẩy tám từ năm tư.\n"
    "Bị cảnh báo hai lần liên tiếp thì thuộc diện xét buộc thôi học.",
    "Cảnh báo học tập – Điều 12 QĐ 2244/2021",
    "Ngưỡng cảnh báo được kiểm thử cho từng năm học",
    "Cảnh báo học tập theo quy chế",
    "Bốn ngưỡng CPA cho bốn năm học, đã kiểm thử riêng",
    [("table", [("Học kỳ đầu", "TB học kỳ < 0,80"),
                ("Các học kỳ sau", "TB học kỳ < 1,00"),
                ("Năm 1 – 2 – 3", "CPA < 1,20 · 1,40 · 1,60"),
                ("Năm 4 trở đi", "CPA < 1,80"),
                ("Hai lần liên tiếp", "xét buộc thôi học")])],
    accent=QColor("#FFC53D"))

add("07_luat_ai",
    "Để trả lời đúng luật, em đã nhúng năm văn bản thầy gửi vào phần mềm.\n"
    "Quyết định hai hai bốn bốn về đào tạo, bốn năm một một về ngoại ngữ, "
    "bốn một bảy về kỹ năng công nghệ thông tin, không hai chín về liêm chính học thuật, "
    "và một bốn một bốn về học bổng.\n"
    "Khi sinh viên hỏi, trợ lý tra đúng đoạn văn bản, "
    "rồi trích dẫn điều khoản ngay trong câu trả lời.\n"
    "Ví dụ: theo Điều mười hai Quyết định hai hai bốn bốn, "
    "hoặc theo Quyết định bốn năm một một, chuẩn đầu ra là TOEIC bốn trăm năm mươi.",
    "Trợ lý AI đọc tài liệu của thầy",
    "5 văn bản quy chế được nhúng trong phần mềm và tra cứu theo câu hỏi",
    "AI hiểu luật và trích dẫn nguồn",
    "Trả lời kèm căn cứ: điều, khoản, số quyết định",
    [("docs", [("QĐ 2244/2021", "Đào tạo đại học"),
               ("QĐ 4511/2022", "Năng lực ngoại ngữ"),
               ("QĐ 417/2016", "Kỹ năng CNTT IU01–IU06"),
               ("QĐ 029/2017", "Liêm chính học thuật"),
               ("QĐ 1414/2021", "Học bổng khuyến khích")])])

add("08_ket",
    "Tổng kết lại. Bộ kiểm thử năm mươi sáu bài, đạt toàn bộ.\n"
    "Ba câu hỏi của thầy đều được trả lời bằng số liệu, "
    "có chỉ rõ môn nào bị khóa, vì sao, và cần học lại môn nào trước.\n"
    "Toàn bộ câu trả lời được lưu trong tệp kết quả để thầy đối chiếu.\n"
    "Em xin cảm ơn thầy đã xem. Kính chúc thầy nhiều sức khỏe.",
    "Kết quả: 56/56 bài kiểm thử đạt",
    "Cảm ơn thầy Nguyễn Thanh Hải đã theo dõi phần demo",
    "56/56 bài kiểm thử đạt",
    "Sẵn sàng cho phần phản biện của thầy",
    [("big", ("56 / 56", "đạt · 0 lỗi")),
     ("chip", ["F tiên quyết", "Cảnh báo Điều 12", "Chuẩn đầu ra", "Học bổng"]),
     ("note", "Kết quả chi tiết: video/case_results.txt · câu trả lời: video/case_answers.md")],
    accent=GRN)


# ------------------------------------------------------------------ vẽ slide
def _ensure_fonts():
    """Nạp bộ font Be Vietnam Pro của ứng dụng (nếu chưa nạp)."""
    global _FONTS_READY
    if not _FONTS_READY:
        ui_kit.load_fonts()
        _FONTS_READY = True


def _f(size: int, bold=False) -> QFont:
    _ensure_fonts()
    f = QFont(ui_kit.FONT_FAMILY)
    f.setPixelSize(size)
    f.setWeight(QFont.DemiBold if bold else QFont.Normal)
    return f


def _wrap(p: QPainter, text: str, x: float, y: float, width: float, size: int,
          color=WHITE, bold=False, lh: float = 1.45) -> float:
    """Vẽ chữ có tự xuống dòng, trả về toạ độ y sau khi vẽ."""
    f = _f(size, bold)
    p.setFont(f)
    p.setPen(color)
    fm = p.fontMetrics()
    words, line, lines = text.split(), "", []
    for w in words:
        trial = (line + " " + w).strip()
        if fm.horizontalAdvance(trial) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    for ln in lines:
        p.drawText(QRectF(x, y, width, fm.height() * 1.6), Qt.AlignLeft | Qt.AlignTop, ln)
        y += fm.height() * lh
    return y


def _card(p: QPainter, x, y, w, h, accent=WHITE, alpha=26):
    p.setBrush(QColor(255, 255, 255, alpha))
    p.setPen(QPen(QColor(255, 255, 255, 34), 1))
    p.drawRoundedRect(QRectF(x, y, w, h), 22, 22)
    p.setPen(Qt.NoPen)
    p.setBrush(accent)
    p.drawRoundedRect(QRectF(x, y, 6, h), 3, 3)


def slide(scene: dict) -> QPixmap:
    _ensure_fonts()
    pm = QPixmap(W, H)
    pm.fill(INK)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)

    g = QLinearGradient(0, 0, W, APP_H)
    g.setColorAt(0, INK)
    g.setColorAt(0.55, INK2)
    g.setColorAt(1, QColor("#070D20"))
    p.fillRect(QRectF(0, 0, W, APP_H), g)
    p.setBrush(QColor(76, 102, 255, 30))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(W - 520, -260, 720, 720))
    p.setBrush(QColor(255, 214, 10, 22))
    p.drawEllipse(QRectF(-180, 520, 460, 460))

    p.setPen(QColor("#8FA0C8"))
    p.setFont(_f(11, True))
    p.drawText(QRectF(70, 44, 1000, 24), Qt.AlignLeft,
               "QUẢN LÝ HỌC PHẦN · TIN HỌC XÂY DỰNG · ĐH BÁCH KHOA – ĐH ĐÀ NẴNG")
    p.setPen(QColor(255, 255, 255, 40))
    p.drawLine(70, 82, W - 70, 82)

    acc = scene["accent"]
    y = _wrap(p, scene["heading"], 70, 118, W - 240, 24, acc, bold=True, lh=1.2)
    y = _wrap(p, scene["sub"], 70, y + 8, W - 320, 13, MUT, lh=1.35) + 30

    left_w = 1080
    for kind, payload in scene["blocks"]:
        if kind == "big":
            value, label = payload
            _card(p, 70, y, left_w, 158, acc)
            p.setFont(_f(34, True))
            p.setPen(WHITE)
            p.drawText(QRectF(100, y + 28, left_w - 60, 62), Qt.AlignLeft, value)
            _wrap(p, label, 100, y + 98, left_w - 60, 12, MUT, lh=1.2)
            y += 186
        elif kind == "kv":
            h = 74 * len(payload) + 22
            _card(p, 70, y, left_w, h, acc)
            yy = y + 14
            for k, v in payload:
                p.setFont(_f(16, True))
                p.setPen(acc)
                p.drawText(QRectF(100, yy, 230, 52), Qt.AlignLeft | Qt.AlignVCenter, k)
                p.setFont(_f(13))
                p.setPen(WHITE)
                p.drawText(QRectF(340, yy, left_w - 290, 52), Qt.AlignLeft | Qt.AlignVCenter, v)
                yy += 74
            y += h + 20
        elif kind == "chip":
            x = 70
            for t in payload:
                p.setBrush(QColor(255, 255, 255, 26))
                p.setPen(Qt.NoPen)
                f = _f(10, True)
                p.setFont(f)
                wd = p.fontMetrics().horizontalAdvance(t) + 34
                p.drawRoundedRect(QRectF(x, y, wd, 40), 20, 20)
                p.setPen(WHITE)
                p.drawText(QRectF(x, y, wd, 40), Qt.AlignCenter, t)
                x += wd + 12
            y += 62
        elif kind == "flow":
            parts = payload
            bw = (left_w - 20 * (len(parts) - 1)) / len(parts)
            for i, t in enumerate(parts):
                bx = 70 + i * (bw + 20)
                hot = "F" in t or "khóa" in t
                _card(p, bx, y, bw, 96, RED if hot else GRN)
                _wrap(p, t, bx + 18, y + 26, bw - 34, 12, WHITE, bold=True, lh=1.3)
            y += 120
        elif kind == "table":
            rh = 58
            _card(p, 70, y, left_w, rh * len(payload) + 18, acc)
            yy = y + 9
            for k, v in payload:
                p.setFont(_f(14, True))
                p.setPen(acc)
                p.drawText(QRectF(100, yy, 300, rh), Qt.AlignLeft | Qt.AlignVCenter, k)
                p.setFont(_f(13))
                p.setPen(WHITE)
                p.drawText(QRectF(410, yy, left_w - 360, rh), Qt.AlignLeft | Qt.AlignVCenter, v)
                p.setPen(QColor(255, 255, 255, 22))
                if yy > y + 12:
                    p.drawLine(100, yy, 70 + left_w - 30, yy)
                yy += rh
            y += rh * len(payload) + 30
        elif kind == "docs":
            h = 52 * len(payload) + 16
            _card(p, 70, y, left_w, h, acc)
            yy = y + 8
            for k, v in payload:
                p.setFont(_f(14, True))
                p.setPen(acc)
                p.drawText(QRectF(100, yy, 240, 46), Qt.AlignLeft | Qt.AlignVCenter, k)
                p.setFont(_f(13))
                p.setPen(WHITE)
                p.drawText(QRectF(350, yy, left_w - 290, 46), Qt.AlignLeft | Qt.AlignVCenter, v)
                yy += 52
            y += h + 18
        elif kind == "cols":
            cw = (left_w - 24) / 2
            for ci, (title, items) in enumerate(payload):
                cx = 70 + ci * (cw + 24)
                _card(p, cx, y, cw, 44 * len(items) + 60, acc)
                p.setFont(_f(11, True))
                p.setPen(acc)
                p.drawText(QRectF(cx + 22, y + 14, cw - 40, 26), Qt.AlignLeft, title)
                yy = y + 46
                for it in items:
                    p.setFont(_f(10))
                    p.setPen(WHITE)
                    p.drawText(QRectF(cx + 22, yy, cw - 40, 36), Qt.AlignLeft | Qt.AlignVCenter,
                               "•  " + it)
                    yy += 44
            y += 44 * max(len(a) for _, a in payload) + 78
        elif kind == "note":
            y = _wrap(p, payload, 70, y, left_w, 12, QColor("#9FB0D4")) + 8

    take = TAKE.get(scene["name"])
    if take:
        ty = max(y + 24, 596)
        _card(p, 70, ty, left_w, 118, acc, alpha=24)
        _wrap(p, take, 100, ty + 34, left_w - 70, 17, WHITE, bold=True, lh=1.3)

    # thẻ minh hoạ bên phải
    bx, by, bw, bh = 1204, 150, W - 1274, APP_H - 210
    _card(p, bx, by, bw, bh, acc, alpha=20)
    p.setFont(_f(12, True))
    p.setPen(acc)
    p.drawText(QRectF(bx + 24, by + 20, bw - 48, 26), Qt.AlignLeft, "TRỢ LÝ AI TRẢ LỜI")
    items = ["Trả lời trực tiếp, không lan man",
             "Nêu rõ điều, khoản, số quyết định",
             "Chỉ rõ môn bị khóa và môn phải học lại",
             "Đề xuất bước tiếp theo trong học kỳ",
             "Số liệu lấy từ bảng điểm thật"]
    yy = by + 62
    for it in items:
        p.setBrush(acc)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(bx + 26, yy + 7, 7, 7))
        yy = _wrap(p, it, bx + 46, yy, bw - 76, 10, WHITE, lh=1.25) + 12
    p.setPen(QColor(255, 255, 255, 40))
    p.drawLine(bx + 24, APP_H - 96, bx + bw - 24, APP_H - 96)
    _wrap(p, "python tests_cases.py · 56 bài · 0 lỗi", bx + 24, APP_H - 78, bw - 48, 10, acc, bold=True)

    p.end()
    base.draw_caption(pm, scene["cap"], scene["capsub"])
    base.draw_progress(pm, 0.0)
    return pm


# ------------------------------------------------------------------ dựng video
def build_narration(scene: dict) -> tuple[Path, float]:
    AUD.mkdir(parents=True, exist_ok=True)
    SENT.mkdir(parents=True, exist_ok=True)
    wavs: list[Path] = []
    for para in [p.strip() for p in scene["text"].split("\n") if p.strip()]:
        for sent in [x.strip() for x in para.replace("!", ".").replace("?", ".").split(".") if x.strip()]:
            wavs.append(base.synth_sentence(sent + "."))
            wavs.append(base._gap_wav(0.34))
        wavs.append(base._gap_wav(0.45))
    out = AUD / f"{scene['name']}.wav"
    base.concat_wavs(wavs, out)
    dur = base.media_duration(out)
    print(f"  [TTS] {scene['name']}: {dur:.1f}s")
    return out, dur


def render(check: bool = False):
    app = QApplication.instance() or QApplication([])      # noqa: F841
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"[1/4] Dựng lời thuyết minh cho {len(SCENES)} cảnh…")
    audio_parts: list[Path] = []
    durations: list[float] = []
    for sc in SCENES:
        wav, dur = build_narration(sc)
        audio_parts.append(wav)
        audio_parts.append(base._gap_wav(0.7))
        durations.append(dur + 0.7)
    if check:
        print(f"  tổng thời lượng dự kiến: {sum(durations):.1f}s")
        return

    print("[2/4] Vẽ slide…")
    frames = [slide(sc) for sc in SCENES]
    for sc, fr in zip(SCENES, frames):
        fr.save(str(OUT / f"slide_{sc['name']}.png"))

    print("[3/4] Mã hoá video…")
    video = OUT / "demo_silent.mp4"
    enc = base.Encoder(video)
    total = sum(int(d * FPS) for d in durations)
    done = 0
    for sc, fr, dur in zip(SCENES, frames, durations):
        n = int(dur * FPS)
        for _ in range(n):
            enc.write(fr)
        done += n
        print(f"  {sc['name']}: {n} khung ({done}/{total})")
    enc.close()

    print("[4/4] Trộn âm thanh + video…")
    narration = OUT / "demo_narration.wav"
    base.concat_wavs(audio_parts, narration)
    dur_all = base.media_duration(narration)
    music = OUT / "demo_music.wav"
    base.build_music(dur_all, music)
    final = OUT / "Demo_TroLyAI_TestBo.mp4"
    base.ff("-i", str(video), "-i", str(narration), "-i", str(music),
            "-filter_complex",
            "[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(final))
    print(f"XONG: {final}  ({final.stat().st_size / 1e6:.2f} MB, "
          f"{dur_all:.1f}s, {time.time() - t0:.0f}s)")


if __name__ == "__main__":
    render(check="--check" in sys.argv)
