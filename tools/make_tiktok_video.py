"""Video TikTok dọc (1080x1920) giới thiệu phần mềm — giọng kể tâm sự, GenZ.

- Giọng đọc: VieNeu-TTS (tiếng Việt tự nhiên), dự phòng Piper.
- Nhịp: caption bắt đúng câu đang đọc, hình trượt lên + zoom nhẹ (Ken Burns).
- Chạy:  python tools/make_tiktok_video.py            (dựng đầy đủ)
         python tools/make_tiktok_video.py --check    (chỉ in thời lượng)
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tools"))

from PySide6.QtCore import QRectF, Qt                                    # noqa: E402
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage, QLinearGradient,  # noqa: E402
                           QPainter, QPainterPath, QPixmap, QRadialGradient)
from PySide6.QtWidgets import QApplication                              # noqa: E402

import ui_kit                                                          # noqa: E402
import make_intro_video as base                                        # noqa: E402

APP = QApplication.instance() or QApplication([])
FAMILY = ui_kit.load_fonts()

# ------------------------------------------------------------------- khung hình
W, H, FPS = 1080, 1920, 30
OUT = ROOT / "video"
AUD = OUT / "audio"
OUT.mkdir(parents=True, exist_ok=True)
AUD.mkdir(parents=True, exist_ok=True)
SHOT = ROOT / "docs" / "screenshots"

INK_TOP = "#0B1230"
INK_BOT = "#04060F"
YELLOW = QColor("#FFD60A")
WHITE = QColor("#FFFFFF")
MUTED = QColor("#9FAAC8")
BLUE = QColor("#4C66FF")

CARD_W, CARD_H = 1044, 587
CARD_X, CARD_Y = (W - CARD_W) // 2, 790


def font(size: int, weight=QFont.Normal) -> QFont:
    f = QFont(FAMILY, 12)
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ------------------------------------------------------------------- kịch bản
# Giọng kể tâm sự, xưng "mình", nói với người xem như bạn cùng khoá.
SCENES = [
    dict(name="01_hook", kind="hook", image=None,
         text="Bài tập dự án đầu tiên ở DUT, mình làm một app quản lý học phần. "
              "Kèm luôn một trợ lý AI."),
    dict(name="02_ngop", kind="image", image="01_dashboard.png",
         text="Năm nhất mở app của trường ra là mình ngơ luôn: bảy mươi chín học phần, "
              "chín học kỳ, tiên quyết chằng chịt."),
    dict(name="03_diem", kind="image", image="08_results.png",
         text="Nên mình tự code một app desktop bằng Python. Nhập điểm ba cột, "
              "GPA với CPA tự tính."),
    dict(name="04_quyche", kind="image", image="03_ai_chat.png",
         text="Cái mình thích nhất là app hiểu quy chế thật của trường. "
              "Hỏi bị F môn Cơ học kết cấu một thì sao, nó trả lời kèm điều khoản."),
    dict(name="05_canhbao", kind="image", image="02_ai_overview.png",
         text="Nó đọc bảng điểm, cảnh báo môn nào sắp toang, "
              "và chỉ ra môn nào đang khoá môn nào."),
    dict(name="06_kehoach", kind="image", image="04_ai_plan.png",
         text="Có cả kế hoạch bốn tuần với thời khoá biểu, "
              "kiểu một anh khoá trên ngồi cạnh."),
    dict(name="07_nhacnho", kind="image", image="05_ai_automation.png",
         text="Nó nhắc mình học mỗi ngày, không cho mình trốn."),
    dict(name="08_bongbong", kind="image", image="07_bubble.png",
         text="Bong bóng chat nổi, đang ở trang nào cũng hỏi được."),
    dict(name="09_ket", kind="end", image=None,
         text="Bài học của mình: bài tập dự án đầu tiên không cần hoàn hảo, chỉ cần hiểu mình làm gì. "
              "Code mình để trên GitHub, link ở comment nha."),
]

TAIL = 0.35          # giây lặng cuối mỗi cảnh


# ------------------------------------------------------------------- caption
def chunk(sentence: str, max_words: int = 7, max_chars: int = 40) -> list[str]:
    out, cur = [], []
    for w in sentence.split():
        cur.append(w)
        if len(cur) >= max_words or len(" ".join(cur)) >= max_chars:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out or [sentence]


def captions(narr: "base.Narration") -> list[tuple[float, float, str]]:
    """Chia từng câu thành cụm ngắn, thời lượng theo độ dài chữ -> khớp giọng đọc."""
    out: list[tuple[float, float, str]] = []
    for i, sent in enumerate(narr.sents):
        t0, dur = narr.offsets[i], narr.durs[i]
        parts = chunk(sent)
        total = sum(len(p) for p in parts) or 1
        acc = 0.0
        for p in parts:
            share = dur * len(p) / total
            out.append((t0 + acc, t0 + acc + share, p.rstrip(".!?;:")))
            acc += share
    return out


# ------------------------------------------------------------------- nền & chữ
def background(p: QPainter, t: float):
    g = QLinearGradient(0, 0, W * 0.4, H)
    g.setColorAt(0, QColor(INK_TOP))
    g.setColorAt(1, QColor(INK_BOT))
    p.fillRect(QRectF(0, 0, W, H), g)
    for (cx, cy, r, color, ph) in ((140, 320, 620, BLUE, 0.0),
                                   (940, 1280, 700, QColor("#7A3BFF"), 1.7),
                                   (520, 1700, 520, QColor("#0E7B6B"), 3.1)):
        x = cx + 40 * math.sin(t * 0.35 + ph)
        y = cy + 30 * math.cos(t * 0.28 + ph)
        rg = QRadialGradient(x, y, r)
        c = QColor(color)
        c.setAlpha(46)
        rg.setColorAt(0, c)
        c2 = QColor(color)
        c2.setAlpha(0)
        rg.setColorAt(1, c2)
        p.fillRect(QRectF(0, 0, W, H), rg)


def wrap(text: str, f: QFont, max_w: float) -> list[str]:
    fm = QFontMetrics(f)
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if fm.horizontalAdvance(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_caption(p: QPainter, text: str, alpha: float = 1.0):
    if not text:
        return
    size = 62
    while size > 40:
        f = font(size, QFont.Bold)
        lines = wrap(text, f, W - 150)
        if len(lines) <= 3:
            break
        size -= 4
    f = font(size, QFont.Bold)
    lines = wrap(text, f, W - 150)
    fm = QFontMetrics(f)
    lh = int(fm.height() * 1.12)
    total = lh * len(lines)
    top = 470 - total / 2
    # nền mờ cho dễ đọc
    box = QPainterPath()
    box.addRoundedRect(QRectF(46, top - 34, W - 92, total + 68), 30, 30)
    p.fillPath(box, QColor(4, 8, 22, int(150 * alpha)))
    # thanh vàng bên trái
    p.fillRect(QRectF(74, top - 10, 7, total + 20), QColor(255, 214, 10, int(255 * alpha)))
    p.setFont(f)
    for i, line in enumerate(lines):
        c = QColor(WHITE)
        c.setAlpha(int(255 * alpha))
        p.setPen(c)
        p.drawText(QRectF(104, top + i * lh, W - 190, lh), Qt.AlignLeft | Qt.AlignVCenter, line)


def draw_pill(p: QPainter, x: float, y: float, text: str, fg=QColor("#0A1020"),
              bg=YELLOW, size: int = 26, pad: float = 26):
    f = font(size, QFont.Bold)
    fm = QFontMetrics(f)
    w = fm.horizontalAdvance(text) + pad * 2
    h = size + 26
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
    p.fillPath(path, bg)
    p.setFont(f)
    p.setPen(fg)
    p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, text)
    return w


def draw_progress(p: QPainter, frac: float):
    y = H - 10
    p.fillRect(QRectF(0, y, W, 10), QColor(255, 255, 255, 30))
    p.fillRect(QRectF(0, y, W * max(0.0, min(1.0, frac)), 10), YELLOW)


# ------------------------------------------------------------------- thẻ app
def draw_card(p: QPainter, img: QPixmap, t: float, dur: float):
    dy = (1 - ease_out(t / 0.55)) * 90
    alpha = ease_out(t / 0.55)
    zoom = 1.0 + 0.06 * ease(min(1.0, t / max(0.1, dur)))
    rct = QRectF(CARD_X, CARD_Y + dy, CARD_W, CARD_H)

    p.save()
    p.setOpacity(alpha)
    # bóng đổ nhiều lớp
    for i in range(10, 0, -1):
        sh = QPainterPath()
        sh.addRoundedRect(rct.adjusted(-i, -i + 16, i, i + 16), 30 + i, 30 + i)
        p.fillPath(sh, QColor(0, 0, 0, 7))
    clip = QPainterPath()
    clip.addRoundedRect(rct, 26, 26)
    p.setClipPath(clip)
    sw, sh_ = img.width() / zoom, img.height() / zoom
    sx, sy = (img.width() - sw) / 2, (img.height() - sh_) / 2
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.drawPixmap(rct, img, QRectF(sx, sy, sw, sh_))
    p.setClipping(False)
    pen = QColor(255, 255, 255, 34)
    p.setPen(pen)
    p.drawPath(clip)
    p.restore()


# ------------------------------------------------------------------- khung hình
def frame(scene: dict, narr: "base.Narration", caps, t: float, dur: float,
          idx: int, total: int) -> QPixmap:
    pm = QPixmap(W, H)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    background(p, t)

    if scene["kind"] == "hook":
        draw_hook(p, narr, t)
    elif scene["kind"] == "end":
        draw_end(p, narr, t)
    else:
        draw_pill(p, 56, 96, "BÀI TẬP DỰ ÁN ĐẦU TIÊN Ở DUT")
        draw_card(p, scene["pix"], t, dur)
        cur = next((c[2] for c in caps if c[0] <= t < c[1] + 0.02), "")
        draw_caption(p, cur)

    p.setFont(font(26, QFont.DemiBold))
    p.setPen(QColor(255, 255, 255, 90))
    p.drawText(QRectF(0, H - 74, W, 40), Qt.AlignCenter, "@duykhangdangzn1")

    draw_progress(p, (idx + min(1.0, t / dur)) / total)
    p.end()
    return pm


def draw_hook(p: QPainter, narr: "base.Narration", t: float):
    lines = [("BÀI TẬP DỰ ÁN", 86, QFont.Black, WHITE, 0),
             ("ĐẦU TIÊN Ở DUT", 110, QFont.Black, YELLOW, 1),
             ("kèm một trợ lý AI", 56, QFont.DemiBold, QColor("#C9D3F0"), 2)]
    # tự thu nhỏ nếu dòng quá rộng khung 1080
    for i, (text, size, weight, color, k) in enumerate(lines):
        while size > 40 and QFontMetrics(font(size, weight)).horizontalAdvance(text) > W - 110:
            size -= 2
        lines[i] = (text, size, weight, color, k)
    metrics = [QFontMetrics(font(sz, wt)) for _, sz, wt, _, _ in lines]
    gap = 26
    total = sum(m.height() for m in metrics) + gap * (len(lines) - 1)
    y = 880 - total / 2
    for (text, size, weight, color, k), m in zip(lines, metrics):
        start = 0.05 + 0.26 * k          # hiện ngay đầu video, không chờ hết câu thoại
        a = ease_out((t - start) / 0.42)
        if a > 0:
            f = font(size, weight)
            p.save()
            p.setOpacity(a)
            p.setFont(f)
            p.setPen(color)
            p.drawText(QRectF(-40, y + (1 - a) * 40, W + 80, m.height()),
                       Qt.AlignCenter, text)
            p.restore()
        y += m.height() + gap


def draw_end(p: QPainter, narr: "base.Narration", t: float):
    a1 = ease_out((t - 0.0) / 0.6)
    p.save()
    p.setOpacity(a1)
    p.setFont(font(54, QFont.Bold))
    p.setPen(WHITE)
    p.drawText(QRectF(0, 600, W, 120), Qt.AlignCenter, "Quản lý Học phần")
    p.setFont(font(54, QFont.Bold))
    p.setPen(YELLOW)
    p.drawText(QRectF(0, 668, W, 120), Qt.AlignCenter, "+ Trợ lý AI học tập")
    p.restore()

    a2 = ease_out((t - 1.0) / 0.6)
    if a2 > 0:
        p.save()
        p.setOpacity(a2)
        box = QPainterPath()
        box.addRoundedRect(QRectF(70, 920, W - 140, 176), 28, 28)
        p.fillPath(box, QColor(255, 255, 255, 20))
        p.setFont(font(34, QFont.DemiBold))
        p.setPen(QColor("#9FB0D8"))
        p.drawText(QRectF(70, 936, W - 140, 50), Qt.AlignCenter, "github.com/duykhangdangzn1")
        p.setFont(font(54, QFont.Bold))
        p.setPen(YELLOW)
        p.drawText(QRectF(70, 982, W - 140, 76), Qt.AlignCenter, "Study_Management")
        p.setFont(font(26, QFont.Medium))
        p.setPen(MUTED)
        p.drawText(QRectF(0, 1130, W, 60), Qt.AlignCenter,
                   "tin học xây dựng · đh bách khoa đà nẵng")
        p.restore()


# ------------------------------------------------------------------- encoder
class Encoder:
    def __init__(self, out: Path):
        self.out = out
        self.proc = subprocess.Popen(
            [base.FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo",
             "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)

    def write(self, pm: QPixmap):
        img = pm.toImage().convertToFormat(QImage.Format.Format_RGB32)
        bpl, row = img.bytesPerLine(), W * 4
        buf = bytes(img.constBits())
        if bpl != row:
            buf = b"".join(buf[y * bpl:y * bpl + row] for y in range(H))
        self.proc.stdin.write(buf)

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.wait()


# ------------------------------------------------------------------- dựng
def main(check: bool = False) -> int:
    for sc in SCENES:
        if sc["image"]:
            sc["pix"] = QPixmap(str(SHOT / sc["image"]))
            if sc["pix"].isNull():
                print(f"  [!] thiếu ảnh {sc['image']}")
                return 2

    print("[1/3] Giọng đọc…")
    total_dur = 0.0
    jobs = []
    for sc in SCENES:
        n = base.Narration(sc["name"], sc["text"])
        wav = n.build()
        dur = n.duration + TAIL
        jobs.append((sc, n, wav, dur))
        total_dur += dur
        print(f"  {sc['name']}: {dur:.1f}s")

    print(f"  tổng: {total_dur:.1f}s ({total_dur / 60:.1f} phút)")
    if check:
        return 0

    print("[2/3] Mã hoá hình…")
    silent = OUT / "tiktok_silent.mp4"
    enc = Encoder(silent)
    t0 = time.time()
    done = 0
    total_frames = sum(int(round(d * FPS)) for _, _, _, d in jobs)
    for idx, (sc, n, wav, dur) in enumerate(jobs):
        caps = captions(n)
        frames = int(round(dur * FPS))
        for f in range(frames):
            pm = frame(sc, n, caps, f / FPS, dur, idx, len(jobs))
            if idx == 0 and f < 9:                      # mở từ đen
                q = QPainter(pm)
                q.fillRect(pm.rect(), QColor(0, 0, 0, int(255 * (1 - f / 9))))
                q.end()
            enc.write(pm)
        done += frames
        print(f"  {sc['name']}: {frames} khung ({done}/{total_frames})")
    enc.close()

    print("[3/3] Ghép tiếng + nhạc nền…")
    parts = []
    for sc, n, wav, dur in jobs:
        parts.append(wav)
        parts.append(base._gap_wav(TAIL))
    voice = AUD / "tiktok_voice.wav"
    base.concat_wavs(parts, voice)
    music = AUD / "tiktok_music.wav"
    base.build_music(total_dur + 1.0, music)

    out = OUT / "TikTok_GioiThieu_QuanLyHocPhan.mp4"
    # ghi ra tệp tạm rồi thay thế: tránh lỗi khi video đang được mở xem
    tmp = out.with_name(out.stem + "_dang_dung.mp4")
    r = base.ff("-i", str(silent), "-i", str(voice), "-i", str(music),
                "-filter_complex",
                "[1:a]volume=1.0[a1];[2:a]volume=0.16[a2];"
                "[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(tmp))
    if r.returncode != 0:
        print("  ffmpeg lỗi:", r.stderr[-500:])
        return 3
    try:
        tmp.replace(out)
    except OSError:
        alt = out.with_name(out.stem + "_v2.mp4")
        tmp.replace(alt)
        print(f"  [!] tệp cũ đang mở nên không ghi đè được → {alt.name}")
        out = alt
    print(f"XONG: {out} ({out.stat().st_size / 1e6:.2f} MB, "
          f"{base.media_duration(out):.1f}s, dựng {time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
