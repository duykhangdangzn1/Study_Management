"""Video demo: quay CHÍNH ỨNG DỤNG — gõ câu hỏi vào khung chat, bấm gửi, AI trả lời.

Timeline mỗi cảnh chia theo tỉ lệ cố định (gõ chữ → bấm gửi → chờ AI → đọc câu trả lời)
để động tác gõ khớp nhịp với lời thuyết minh, không bị trôi hay giật.

Chạy: python tools/make_chat_video.py [--check]
Kết quả: video/Demo_ChatTroLyAI.mp4
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tools"))

from PySide6.QtWidgets import QApplication, QScrollArea   # noqa: E402

import core                                        # noqa: E402
import ai_page                                     # noqa: E402
import automation                                  # noqa: E402
import ui_kit                                      # noqa: E402
import main as main_mod                            # noqa: E402
import make_intro_video as base                    # noqa: E402
import make_demo_video as slides                   # noqa: E402

W, H, FPS, APP_H = base.W, base.H, base.FPS, base.APP_H
OUT = ROOT / "video"
APP = QApplication.instance() or QApplication([])

# Tỉ lệ thời lượng từng đoạn trong một cảnh (khớp với nhịp đọc).
SEG = (("typing", 0.36), ("send", 0.05), ("wait", 0.09), ("answer", 0.50))

# Ống kính cho từng đoạn: phóng vào ô nhập khi gõ, vào câu trả lời khi đọc.
# Giữ nguyên toàn khung: phóng vào sẽ cắt mất mép sidebar và trông xộc xệch.
CAM = {"typing": (1.0, 960, 476), "send": (1.0, 960, 476),
       "wait": (1.0, 960, 476), "answer": (1.0, 960, 476),
       "slide": (1.0, 960, 476)}

QUESTIONS = [
    ("01_f_chkc1", "Nếu em bị điểm F môn Cơ học kết cấu 1 thì chuyện gì xảy ra?",
     "Câu thứ nhất, cũng là câu thầy đặt: nếu Cơ học kết cấu một bị điểm F. "
     "AI trả lời trong khung chat rằng hai tín chỉ không được tích lũy, phải học lại, "
     "và bảy học phần phía sau bị khóa, trong đó có Cơ học kết cấu hai.",
     "Hỏi: “Nếu em bị điểm F môn Cơ học kết cấu 1…”",
     "AI đọc bảng điểm và trả lời ngay trong khung chat"),
    ("02_f_clt", "Bị F Cơ lý thuyết thì những môn nào bị ảnh hưởng?",
     "Tiếp theo là Cơ lý thuyết. AI chỉ ra hai nhánh bị khóa ngay sau nó: "
     "Sức bền vật liệu và Thủy lực, rồi kéo theo Cơ học kết cấu một, Cơ học đất, Vật liệu xây dựng.",
     "Hỏi: “Bị F Cơ lý thuyết thì môn nào bị ảnh hưởng?”",
     "AI liệt kê đúng hai nhánh bị khóa"),
    ("03_sbvl", "Đã qua Cơ lý thuyết nhưng F Sức bền thì sao?",
     "Câu thứ ba, trường hợp dễ trả lời sai nhất. AI khẳng định: chưa được học Cơ học kết cấu một, "
     "vì học phần này yêu cầu đạt cả hai môn tiên quyết. Đã qua Cơ lý thuyết vẫn chưa đủ.",
     "Hỏi: “Đã qua Cơ lý thuyết nhưng F Sức bền…”",
     "Trả lời đúng từng mắt xích tiên quyết"),
    ("04_canh_bao", "Em có đang bị cảnh báo kết quả học tập không?",
     "Sang chủ đề cảnh báo học tập. AI đối chiếu điểm trung bình tích lũy với bốn ngưỡng của Điều mười hai, "
     "rồi khẳng định em chưa thuộc diện cảnh báo, kèm con số cụ thể.",
     "Hỏi: “Em có đang bị cảnh báo kết quả học tập không?”",
     "Đối chiếu Điều 12 và trả lời kèm con số"),
    ("05_tin_chi", "Học kỳ tới em được đăng ký tối đa bao nhiêu tín chỉ?",
     "Câu về giới hạn đăng ký. AI áp đúng Điều bảy khoản sáu: vì chưa đạt chuẩn tiếng Anh, "
     "em chỉ được đăng ký tối đa mười bốn tín chỉ, thay vì hai mươi lăm.",
     "Hỏi: “Học kỳ tới em được đăng ký tối đa bao nhiêu tín chỉ?”",
     "Áp đúng giới hạn 14 tín chỉ"),
    ("06_toeic", "Em cần TOEIC bao nhiêu để đủ điều kiện tốt nghiệp?",
     "Chủ đề chuẩn đầu ra ngoại ngữ. AI trích Quyết định bốn năm một một: TOEIC bốn trăm năm mươi, "
     "hoặc IELTS năm phẩy năm, hoặc TOEFL iBT bốn mươi sáu.",
     "Hỏi: “Em cần TOEIC bao nhiêu để tốt nghiệp?”",
     "Trích QĐ 4511/2022"),
    ("07_do_an", "Điều kiện để được làm đồ án tốt nghiệp là gì?",
     "Về đồ án tốt nghiệp. AI nêu đúng hai điều kiện của Điều mười lăm: "
     "còn không quá bốn tín chỉ chưa tích lũy và điểm trung bình tích lũy từ một phẩy chín trở lên.",
     "Hỏi: “Điều kiện để được làm đồ án tốt nghiệp?”",
     "Nêu đúng Điều 15: CPA ≥ 1,90 và còn ≤ 4 TC"),
    ("08_hoc_bong", "Điều kiện xét học bổng loại B là gì?",
     "Chủ đề học bổng. AI trích Quyết định một bốn một bốn: loại B cần điểm trung bình từ tám phẩy không "
     "và điểm rèn luyện từ tám mươi, mức thưởng một trăm hai mươi phần trăm học phí.",
     "Hỏi: “Điều kiện xét học bổng loại B?”",
     "Trích QĐ 1414/2021 và mức 120% học phí"),
    ("09_liem_chinh", "Nếu em chép bài của bạn rồi nộp thì bị xử lý thế nào?",
     "Chủ đề liêm chính học thuật. AI chỉ rõ hành vi chép bài thuộc nhóm đạo văn và gian lận, "
     "bị xử lý theo Quyết định không hai chín, và hồ sơ vi phạm được xét trước khi công nhận tốt nghiệp.",
     "Hỏi: “Nếu em chép bài của bạn rồi nộp thì sao?”",
     "Trích QĐ 029/2017 về liêm chính học thuật"),
    ("10_tot_nghiep", "Với kết quả hiện tại, em còn thiếu gì để tốt nghiệp?",
     "Cuối cùng là câu tổng hợp: còn thiếu gì để tốt nghiệp. AI đối chiếu bốn điều kiện của Điều mười bảy: "
     "tín chỉ, điểm trung bình tích lũy, chuẩn ngoại ngữ và chuẩn công nghệ thông tin, "
     "rồi chỉ ra việc cần làm trước.",
     "Hỏi: “Với kết quả hiện tại, em còn thiếu gì để tốt nghiệp?”",
     "Đối chiếu đủ 4 điều kiện tốt nghiệp"),
]


def make_book(tmp: Path) -> core.GradeBook:
    book = core.GradeBook(tmp / "grades.json")
    for sem in (1, 2, 3):
        for c in book.courses_in(sem):
            if c["elective"] or "ALL" in str(c["prereq"]):
                continue
            book.save(c["id"], 8, 8, 8)
    book.save(29, 1, 0, 2.0)
    return book


def shot(win):
    APP.processEvents()
    return win.grab()


def capture(win, chat, question: str) -> dict:
    """Quay 4 đoạn: gõ chữ (mượt, 1 khung/2 ký tự), gửi, chờ AI, cuộn câu trả lời."""
    typing: list = []
    chat.input.clear()
    APP.processEvents()
    for i in range(0, len(question) + 1, 2):
        chat.input.setText(question[:i])
        APP.processEvents()
        typing.append(shot(win))
    chat.input.setText(question)
    APP.processEvents()
    typing.append(shot(win))
    typing.append(shot(win))

    chat._on_send()
    TIME_SEND = time.time()
    wait_frame = None
    while getattr(chat.session, "busy", False) and time.time() - TIME_SEND < 240:
        APP.processEvents()
        if wait_frame is None and time.time() - TIME_SEND > 0.5:
            wait_frame = shot(win)          # trạng thái "AI đang soạn câu trả lời…"
        time.sleep(0.05)
    APP.processEvents()
    if wait_frame is None:
        wait_frame = shot(win)

    answer: list = [shot(win)]
    area = chat.findChild(QScrollArea)
    if area is not None:
        bar = area.verticalScrollBar()
        top = bar.value()
        span = max(1, bar.maximum() - top)
        for k in range(1, 9):
            bar.setValue(int(top + span * k / 8))
            APP.processEvents()
            time.sleep(0.06)
            answer.append(shot(win))
    else:
        answer.append(shot(win))
    return dict(typing=typing, wait=wait_frame, answer=answer)


def main(check: bool = False) -> int:
    OUT.mkdir(exist_ok=True)
    base.OUT.mkdir(parents=True, exist_ok=True)
    base.AUD.mkdir(parents=True, exist_ok=True)
    base.SENT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="chatvideo_"))
    ui_kit.load_fonts()
    main_mod.save_settings = lambda data: None
    ui_kit.MessageDialog.exec = lambda self, *a, **k: 0
    ai_page.CHAT_PATH = tmp / "chat.json"
    automation.CONFIG_PATH = tmp / "automation.json"
    automation.STORE_PATH = tmp / "reminders.json"

    book = make_book(tmp)
    win = main_mod.MainWindow(book)
    win.animate = False
    win.toast = lambda text, kind="info": None
    win.resize(int(round(W * APP_H / H)), APP_H)
    win.show()
    for _ in range(8):
        APP.processEvents()
    try:
        win.engine.stop()
    except Exception:
        pass
    win.go(4)
    win.ai.tabs.setCurrentWidget(win.ai.chat_tab)
    for _ in range(8):
        APP.processEvents()
    chat = win.ai.chat_tab

    print(f"[1/3] Quay {len(QUESTIONS)} câu hỏi trên ứng dụng…")
    scenes: list[dict] = []
    for name, question, narration, cap, capsub in QUESTIONS:
        print(f"  · {name}")
        frames = capture(win, chat, question)
        print(f"    gõ {len(frames['typing'])} khung · trả lời {len(frames['answer'])} khung")
        frames.update(name=name, cap=cap, capsub=capsub, narration=narration)
        scenes.append(frames)

    intro = dict(name="00_mo_dau", typing=[slides.slide(slides.SCENES[0])], wait=None,
                 answer=[slides.slide(slides.SCENES[0])],
                 cap="Gõ câu hỏi – AI trả lời trong khung chat",
                 capsub="Demo thao tác thật · 10 câu hỏi nhiều chủ đề · Quản lý Học phần – Tin học Xây dựng",
                 narration="Kính chào thầy Nguyễn Thanh Hải.\n"
                           "Đây là demo thao tác thật: em gõ từng câu hỏi vào khung chat, bấm gửi, "
                           "và trợ lý AI trả lời ngay trong khung chat.\n"
                           "Mười câu hỏi trải trên nhiều chủ đề: môn tiên quyết, cảnh báo học tập, "
                           "tín chỉ, chuẩn ngoại ngữ, đồ án, học bổng, liêm chính và tốt nghiệp.")
    outro = dict(name="99_ket", typing=[slides.slide(slides.SCENES[-1])], wait=None,
                 answer=[slides.slide(slides.SCENES[-1])],
                 cap="10 câu hỏi · câu trả lời có căn cứ điều khoản",
                 capsub="Bộ kiểm thử tự động: 56/56 bài đạt · 35/35 kiểm tra qua khung chat",
                 narration="Cả mười câu đều được trả lời ngay trong khung chat, kèm căn cứ điều khoản. "
                           "Bộ kiểm thử tự động năm mươi sáu bài đều đạt, trong đó ba mươi lăm kiểm tra "
                           "đi qua chính khung chat này.\n"
                           "Em xin cảm ơn thầy Nguyễn Thanh Hải đã theo dõi.")
    scenes = [intro] + scenes + [outro]

    print("[2/3] Dựng lời thuyết minh…")
    audio_parts: list = []
    for sc in scenes:
        nar = base.Narration(sc["name"], sc["narration"])
        wav = nar.build()
        sc["dur"] = nar.duration + 0.7
        audio_parts.append(wav)
        audio_parts.append(base._gap_wav(0.7))
    total_dur = sum(s["dur"] for s in scenes)
    print(f"  tổng thời lượng: {total_dur:.1f}s")
    if check:
        return 0

    print("[3/3] Mã hoá video…")
    silent = OUT / "chat_silent.mp4"
    enc = base.Encoder(silent)
    total = int(total_dur * FPS)
    done = 0
    for sc in scenes:
        n = int(sc["dur"] * FPS)
        caps = []
        for label, share in SEG:
            if label == "typing":
                caps.append((sc["typing"], max(1, int(n * share))))
            elif label == "send":
                caps.append(([sc["typing"][-1]], max(1, int(n * share))))
            elif label == "wait":
                caps.append(([sc["wait"] or sc["typing"][-1]], max(1, int(n * share))))
            else:
                caps.append((sc["answer"], max(1, n - sum(c[1] for c in caps))))
        for label, (frames, cnt) in zip([s[0] for s in SEG], caps):
            cam = CAM["slide"] if sc["name"][:2] in ("00", "99") else CAM[label]
            pix = [base.compose(f, cam) for f in frames]
            for f in pix:
                base.draw_caption(f, sc["cap"], sc["capsub"])
            for k in range(cnt):
                idx = min(len(pix) - 1, int(k * len(pix) / cnt))
                base.draw_progress(pix[idx], done / max(1, total))
                enc.write(pix[idx])
                done += 1
        print(f"  {sc['name']}: {n} khung ({done}/{total})")
    enc.close()

    narration = OUT / "chat_narration.wav"
    base.concat_wavs(audio_parts, narration)
    dur = base.media_duration(narration)
    music = OUT / "chat_music.wav"
    base.build_music(dur, music)
    final = OUT / "Demo_ChatTroLyAI.mp4"
    base.ff("-i", str(silent), "-i", str(narration), "-i", str(music),
            "-filter_complex",
            "[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(final))
    print(f"XONG: {final} ({final.stat().st_size / 1e6:.2f} MB, {dur:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
