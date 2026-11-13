"""Dung video gioi thieu phan mem (1920x1080) co voice-over tieng Viet.

Nguyen ly: quay chinh ung dung dang chay o che do offscreen (moi khung hinh la
mot lan grab cua cua so that), ghep caption + spotlight + thanh tien trinh, roi
long tieng bang TTS (uu tien edge-tts giong vi-VN, du phong gTTS) va ma hoa
H.264 bang ffmpeg di kem imageio-ffmpeg (khong can cai ffmpeg he thong).

    python tools/make_intro_video.py --check    # render vai khung de xem truoc
    python tools/make_intro_video.py            # xuat video hoan chinh

Dau ra: video/GioiThieu_TinHocXayDung.mp4 (+ phu_de.srt, kich_ban.md)
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from PySide6.QtCore import QPoint, QRectF, Qt, QTime, QTimer
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

APP = QApplication.instance() or QApplication([])

import ai_engine
import ai_page
import automation
import core
import ui_kit
import main as main_mod
from ai_engine import LocalAnalytics
from core import GradeBook
from main import MainWindow

W, H, FPS = 1920, 1080, 15
PAD = 0.75          # giay nghi sau moi doan thuyet minh
APP_H = 952         # chieu cao khung ung dung; phan con lai duoi cung la DAI PHU DE rieng
APP_W = int(round(W * APP_H / 1080))
APP_X = (W - APP_W) // 2
BAND_H = H - APP_H
OUT = ROOT / "video"
AUD = OUT / "audio"
SENT = OUT / "sent"
VOICE_DIR = ROOT / "tools" / "piper_voices"
PIPER_MODEL = VOICE_DIR / "vi_VN-vais1000-medium.onnx"
VIENEU_VOICE = os.environ.get("VIENEU_VOICE", "")    # rong = giong mac dinh cua VieNeu

INK = QColor("#060C1E")
INK2 = QColor("#101B3E")
YELLOW = QColor("#FFD60A")
BLUE = QColor("#4C66FF")
WHITE = QColor("#FFFFFF")
MUTED = QColor("#A9B4D0")

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:                                             # pragma: no cover
    FFMPEG = shutil.which("ffmpeg")


# --------------------------------------------------------------------- helpers
def ff(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args],
                          capture_output=True, text=True)


def media_duration(path: Path) -> float:
    """Do dai tep am thanh/video (giay) bang cach doc stderr cua ffmpeg."""
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


# ------------------------------------------------------------------------- TTS
def chunk_text(text: str, limit: int = 150) -> list[str]:
    parts = re.split(r"(?<=[\.\!\?\;:])\s+", text.strip())
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= limit:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                out.append(cur)
            while len(p) > limit:
                out.append(p[:limit].strip())
                p = p[limit:].strip()
            cur = p
    if cur:
        out.append(cur)
    return [c for c in out if c]


def to_wav(src: Path, dst: Path):
    ff("-i", str(src), "-ar", "24000", "-ac", "1", str(dst))


def concat_wavs(files: list[Path], dst: Path):
    listing = dst.with_suffix(".txt")
    listing.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", str(listing), "-ar", "24000", "-ac", "1", str(dst))
    listing.unlink(missing_ok=True)


def silence_wav(seconds: float, dst: Path):
    ff("-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{seconds:.2f}", str(dst))


def synth_edge(text: str, dst: Path) -> bool:
    try:
        import edge_tts
    except Exception:
        return False
    voice = os.environ.get("TTS_VOICE", "vi-VN-HoaiMyNeural")

    async def go():
        com = edge_tts.Communicate(text, voice)
        await com.save(str(dst))

    for _ in range(3):
        try:
            asyncio.run(go())
            if dst.exists() and dst.stat().st_size > 2000:
                return True
        except Exception:
            time.sleep(1.5)
    return False


def synth_gtts(text: str, dst: Path, tmp: Path) -> bool:
    try:
        from gtts import gTTS
    except Exception:
        return False
    chunks = chunk_text(text)
    if not chunks:
        return False
    pieces: list[Path] = []
    silent = tmp / "comma.wav"
    silence_wav(0.12, silent)
    for i, c in enumerate(chunks):
        mp3 = tmp / f"chunk_{i}.mp3"
        wav = tmp / f"chunk_{i}.wav"
        try:
            gTTS(text=c, lang="vi").save(str(mp3))
        except Exception:
            return False
        to_wav(mp3, wav)
        pieces.append(wav)
        if i != len(chunks) - 1:
            pieces.append(silent)
    concat_wavs(pieces, dst)
    return dst.exists() and dst.stat().st_size > 2000


def _dur(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


ENGINE = os.environ.get("TTS_ENGINE", "auto").strip().lower()
_CACHE: dict = {}
# (length_scale, noise_w_scale): cham + rung nhieu hon = nhan nha hon
STYLE = {"normal": (1.0, 0.85), "emphasis": (1.12, 0.93), "calm": (0.95, 0.78)}


def _vieneu():
    """VieNeu-TTS v3 (ONNX, CPU) - giong tieng Viet tu nhien nhat dang dung duoc."""
    if "vieneu" not in _CACHE:
        try:
            from vieneu import Vieneu
            t0 = time.time()
            _CACHE["vieneu"] = Vieneu()
            print(f"  [TTS] vieneu san sang ({time.time() - t0:.0f}s)")
        except Exception as e:                                     # pragma: no cover
            print("  [TTS] vieneu khong dung duoc:", type(e).__name__, str(e)[:120])
            _CACHE["vieneu"] = None
    return _CACHE["vieneu"]


def _piper():
    if "piper" not in _CACHE:
        try:
            from piper import PiperVoice
            _CACHE["piper"] = PiperVoice.load(str(PIPER_MODEL))
            print("  [TTS] piper san sang")
        except Exception as e:                                     # pragma: no cover
            print("  [TTS] piper khong dung duoc:", str(e)[:120])
            _CACHE["piper"] = None
    return _CACHE["piper"]


def _sentence_vieneu(text: str, dst: Path) -> bool:
    tts = _vieneu()
    if tts is None:
        return False
    try:
        kw = {"voice": VIENEU_VOICE} if VIENEU_VOICE else {}
        tts.save(tts.infer(text, **kw), str(dst))
        return dst.exists() and dst.stat().st_size > 2000
    except Exception as e:
        print("  [TTS] vieneu loi:", type(e).__name__, str(e)[:120])
        _CACHE["vieneu"] = None
        return False


def _sentence_piper(text: str, dst: Path, style: str) -> bool:
    voice = _piper()
    if voice is None:
        return False
    try:
        from piper import SynthesisConfig
        speed, noise_w = STYLE.get(style, STYLE["normal"])
        cfg = SynthesisConfig(length_scale=speed, noise_scale=0.667,
                              noise_w_scale=noise_w, normalize_audio=True)
        with wave.open(str(dst), "wb") as w:
            voice.synthesize_wav(text, w, syn_config=cfg)
        return dst.exists() and dst.stat().st_size > 2000
    except Exception as e:
        print("  [TTS] piper loi:", str(e)[:120])
        return False


def synth_sentence(text: str, style: str = "normal") -> Path:
    """Tong hop MOT cau thanh WAV 24 kHz; cache theo noi dung + kieu doc."""
    SENT.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{ENGINE}|{style}|{text}".encode("utf-8")).hexdigest()[:16]
    wav = SENT / f"{key}.wav"
    if wav.exists() and wav.stat().st_size > 2000:
        return wav
    tdir = Path(tempfile.mkdtemp())
    src = tdir / "s.wav"
    ok = False
    if ENGINE in ("auto", "vieneu"):
        ok = _sentence_vieneu(text, src)
    if not ok and ENGINE in ("auto", "piper"):
        ok = _sentence_piper(text, src, style)
    if not ok and ENGINE in ("auto", "gtts"):
        ok = synth_gtts(text, src, tdir)
    if not ok:
        silence_wav(max(2.0, len(text) / 14.0), wav)
        print("  [TTS] FALLBACK im lang:", text[:40])
        return wav
    to_wav(src, wav)
    return wav


def _gap_wav(seconds: float) -> Path:
    p = SENT / f"gap_{int(round(seconds * 100)):03d}.wav"
    if not p.exists():
        silence_wav(seconds, p)
    return p


class Narration:
    """Loi thuyet minh mot canh: tong hop tung cau de canh hinh dung dung luc."""

    def __init__(self, name: str, text: str, styles: dict | None = None):
        self.name = name
        self.styles = styles or {}
        self.sents: list[str] = []
        self.gaps: list[float] = []
        paras = [p.strip() for p in str(text).split("\n") if p.strip()]
        for pi, para in enumerate(paras):
            parts = [p.strip() for p in re.split(r"(?<=[\.\!\?])\s+", para) if p.strip()]
            for i, p in enumerate(parts):
                self.sents.append(p)
                last = i == len(parts) - 1
                self.gaps.append(0.60 if (last and pi < len(paras) - 1) else 0.30)
        self.offsets: list[float] = []
        self.durs: list[float] = []
        self.duration = 0.0

    def build(self) -> Path:
        parts: list[Path] = []
        acc = 0.0
        t0 = time.time()
        for i, s in enumerate(self.sents):
            w = synth_sentence(s, self.styles.get(i, "normal"))
            d = _dur(w)
            self.offsets.append(acc)
            self.durs.append(d)
            parts.append(w)
            parts.append(_gap_wav(self.gaps[i]))
            acc += d + self.gaps[i]
        out = AUD / f"{self.name}.wav"
        concat_wavs(parts, out)
        self.duration = _dur(out)
        print(f"  [TTS] {self.name}: {len(self.sents)} cau · {self.duration:.1f}s "
              f"({time.time() - t0:.1f}s)")
        return out

    def at(self, phrase: str) -> float:
        """Thoi diem (giay trong canh) bat dau noi cum tu 'phrase'."""
        low = phrase.lower()
        for i, s in enumerate(self.sents):
            pos = s.lower().find(low)
            if pos >= 0:
                return self.offsets[i] + (pos / max(1, len(s))) * self.durs[i]
        for i, s in enumerate(self.sents):
            if low[:12] in s.lower():
                return self.offsets[i]
        print(f"  [canh bao] {self.name}: khong thay cum '{phrase}'")
        return self.duration * 0.55


def build_music(dur: float, out: Path):
    """Nhac nen khong loi, nhe, vong hop am Am - F - C - G, khong lan tie.nh thoai."""
    import numpy as np
    sr = 24000
    total = int((dur + 2.0) * sr)
    buf = np.zeros(total)
    chords = [[220.00, 261.63, 329.63, 440.00],        # Am
              [174.61, 220.00, 261.63, 349.23],        # F
              [261.63, 329.63, 392.00, 523.25],        # C
              [196.00, 246.94, 293.66, 392.00]]        # G
    bar = 4.0
    nbar = int(np.ceil(total / sr / bar))
    for b in range(nbar):
        chord = chords[b % len(chords)]
        start = int(b * bar * sr)
        seg = min(total - start, int(bar * sr))
        if seg <= 0:
            break
        t = np.arange(seg) / sr
        env = np.minimum(1.0, t / 1.1) * np.minimum(1.0, np.maximum(0.0, (seg / sr - t) / 1.4))
        trem = 1.0 + 0.06 * np.sin(2 * np.pi * 0.13 * (t + b * bar))
        pad = np.zeros(seg)
        for f in chord:
            pad += np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
        buf[start:start + seg] += pad * env * trem * (0.055 / len(chord))
        step = bar / 8
        for k in range(8):
            f = chord[k % len(chord)] * (2 if k >= 4 else 1)
            s0 = int((b * bar + k * step) * sr)
            if s0 >= total:
                break
            ln = min(int(1.8 * sr), total - s0)
            tt = np.arange(ln) / sr
            note = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)
            note *= np.exp(-tt * 2.6) * np.minimum(1.0, tt / 0.01) * 0.03
            buf[s0:s0 + ln] += note
        s0 = int(b * bar * sr)
        ln = min(int(3.6 * sr), total - s0)
        if ln > 0:
            tt = np.arange(ln) / sr
            buf[s0:s0 + ln] += np.sin(2 * np.pi * chord[0] / 2 * tt) * np.exp(-tt * 0.9) * 0.035
    k = np.hanning(9)
    buf = np.convolve(buf, k / k.sum(), mode="same")
    fin, fout = int(3.0 * sr), int(4.0 * sr)
    buf[:fin] *= np.linspace(0, 1, fin)
    buf[-fout:] *= np.linspace(1, 0, fout)
    buf = buf / (float(np.max(np.abs(buf))) or 1.0) * 0.55
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((buf * 32767).astype("<i2").tobytes())
    print(f"  [nhac] {out.name}: {dur:.1f}s")


# ----------------------------------------------------------------------- slides
def _grad(p: QPainter, a: str, b: str):
    g = QLinearGradient(0, 0, W, H)
    g.setColorAt(0, QColor(a))
    g.setColorAt(1, QColor(b))
    p.fillRect(0, 0, W, H, g)


def _glow(p: QPainter, cx: float, cy: float, r: float, color: QColor):
    g = QRadialGradient(cx, cy, r)
    c = QColor(color)
    c.setAlpha(80)
    g.setColorAt(0, c)
    c2 = QColor(color)
    c2.setAlpha(0)
    g.setColorAt(1, c2)
    p.fillRect(0, 0, W, H, g)


def _font(size: int, weight=QFont.Normal) -> QFont:
    f = QFont(ui_kit.FONT_FAMILY, 12)
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


def _text(p: QPainter, x, y, w, size, text, color=WHITE, weight=QFont.Normal, align=Qt.AlignLeft):
    f = _font(size, weight)
    p.setFont(f)
    p.setPen(color)
    p.drawText(QRectF(x, y, w, size * 2.2), align | Qt.AlignTop | Qt.TextWordWrap, text)
    return QFontMetrics(f)


def _chip(p: QPainter, x, y, text, fg=WHITE, bg=QColor(255, 255, 255, 26), size=20):
    f = _font(size, QFont.DemiBold)
    p.setFont(f)
    fm = QFontMetrics(f)
    w = fm.horizontalAdvance(text) + 42
    h = size + 26
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
    p.fillPath(path, bg)
    p.setPen(fg)
    p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, text)
    return w


def slide_title(thumb: QPixmap | None) -> QPixmap:
    pm = QPixmap(W, H)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _grad(p, "#05091A", "#12204F")
    _glow(p, W * 0.86, H * 0.16, 620, YELLOW)
    _glow(p, W * 0.12, H * 0.95, 700, BLUE)

    logo = QPixmap(str(ROOT / "app" / "assets" / "logo_badge.png"))
    if not logo.isNull():
        p.drawPixmap(120, 96, logo.scaledToHeight(104, Qt.SmoothTransformation))

    _text(p, 120, 236, 900, 22, "ĐỒ ÁN MÔN HỌC · ỨNG DỤNG TIN HỌC TRONG XÂY DỰNG",
          YELLOW, QFont.Bold)
    _text(p, 116, 276, 980, 82, "Quản lý Học phần", WHITE, QFont.ExtraBold)
    _text(p, 116, 372, 980, 62, "& Trợ lý AI học tập", QColor("#BFC9E8"), QFont.ExtraBold)
    _text(p, 120, 470, 860, 24,
          "Ngành Tin học Xây dựng · Khoa Xây dựng\n"
          "Trường Đại học Bách khoa – Đại học Đà Nẵng", MUTED)

    x = 120
    x += _chip(p, x, 580, "PySide6 · Windows") + 14
    x += _chip(p, x, 580, "9 học kỳ · 156 tín chỉ") + 14
    _chip(p, x, 580, "Trợ lý AI online · Tự động hoá")

    p.setPen(QPen(QColor(255, 255, 255, 40), 2))
    p.drawLine(QPoint(120, 700), QPoint(940, 700))
    _text(p, 120, 720, 980, 21, "Nhóm thực hiện: Đặng Duy Khang · Trần Bảo Khang",
          QColor("#D6DEF5"))
    _text(p, 120, 754, 980, 21, "Đỗ Chí Kiên · Đỗ Công Tuấn Anh", QColor("#D6DEF5"))
    _text(p, 120, 792, 980, 19, "GVHD: Nguyễn Thanh Hải  ·  Phiên bản 2.0.6", MUTED)

    if thumb is not None and not thumb.isNull():
        card = QRectF(1116, 226, 704, 528)
        glow = QColor(0, 0, 0, 120)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawRoundedRect(card.adjusted(-14, -10, 14, 26), 26, 26)
        scaled = thumb.scaled(int(card.width()), int(card.height()),
                              Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        path = QPainterPath()
        path.addRoundedRect(card, 22, 22)
        p.save()
        p.setClipPath(path)
        p.drawPixmap(int(card.x()), int(card.y()), scaled)
        p.restore()
        p.setPen(QPen(QColor(255, 255, 255, 60), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(card, 22, 22)
    p.end()
    return pm


def slide_problem() -> QPixmap:
    pm = QPixmap(W, H)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _grad(p, "#05091A", "#0E1738")
    _glow(p, W * 0.5, -120, 700, BLUE)
    _text(p, 120, 108, 1200, 26, "BÀI TOÁN", YELLOW, QFont.Bold)
    _text(p, 116, 148, 1600, 54, "Sinh viên đang tự làm mọi thứ bằng tay", WHITE, QFont.ExtraBold)

    cols = [
        ("Vấn đề hiện tại", BLUE, ["Cộng điểm 20/20/60 bằng máy tính tay, dễ sai",
                                  "Không biết môn nào bị khoá do chưa đạt môn trước",
                                  "Không theo dõi được nguy cơ cảnh báo học tập",
                                  "Không rõ còn bao nhiêu tín chỉ để tốt nghiệp"]),
        ("Phần mềm giải quyết", YELLOW, ["Nhập một lần: tổng kết, điểm chữ, GPA, CPA tự tính",
                                        "Tự động khoá môn theo học phần học trước",
                                        "Cảnh báo học tập + kế hoạch học lại từ dữ liệu thật",
                                        "Trợ lý AI tư vấn và tự động nhắc nhở hằng ngày"]),
    ]
    x = 120
    for title, accent, items in cols:
        box = QRectF(x, 268, 780, 560)
        path = QPainterPath()
        path.addRoundedRect(box, 26, 26)
        p.fillPath(path, QColor(255, 255, 255, 14))
        p.setPen(QPen(QColor(255, 255, 255, 36), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(box, 26, 26)
        p.fillRect(QRectF(x + 40, 316, 64, 6), accent)
        _text(p, x + 40, 344, 700, 34, title, WHITE, QFont.Bold)
        y = 424
        for it in items:
            p.setPen(accent)
            p.setBrush(accent)
            p.drawEllipse(QRectF(x + 42, y + 12, 9, 9))
            _text(p, x + 68, y, 650, 23, it, QColor("#D3DBF0"))
            y += 92
        x += 820
    p.end()
    return pm


def slide_end(rep) -> QPixmap:
    pm = QPixmap(W, H)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _grad(p, "#05091A", "#12204F")
    _glow(p, W * 0.2, H * 0.1, 640, YELLOW)
    _text(p, 120, 92, 1400, 24, "GIÁ TRỊ KỸ THUẬT", YELLOW, QFont.Bold)
    _text(p, 116, 130, 1500, 52, "Một sản phẩm hoàn chỉnh, không phải bản thử", WHITE, QFont.ExtraBold)

    cards = [
        ("sparkles", "Trợ lý AI online", "API chuẩn OpenAI · model auto:smart"),
        ("chart", "Lõi tính điểm chính xác", "20/20/60 · GPA, CPA, xếp loại, tín chỉ"),
        ("bell", "Tự động hoá chạy nền", "Nhắc giờ học · cảnh báo · AI coach"),
        ("check", "4 bộ kiểm thử tự động", "Lõi · AI · tự động hoá · giao diện"),
        ("save", "Đóng gói 1 tệp .exe", "Chạy trên Windows, không cần cài Python"),
        ("star", "Giao diện sáng / tối", "Thiết kế bo tròn, không lỗi hiển thị"),
    ]
    x, y = 120, 232
    for i, (ic, title, sub) in enumerate(cards):
        box = QRectF(x, y, 520, 148)
        path = QPainterPath()
        path.addRoundedRect(box, 22, 22)
        p.fillPath(path, QColor(255, 255, 255, 15))
        p.setPen(QPen(QColor(255, 255, 255, 34), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(box, 22, 22)
        pm_icon = ui_kit.icon_pixmap(ic, YELLOW.name(), 34)
        p.drawPixmap(int(box.x() + 34), int(box.y() + 34), pm_icon)
        _text(p, box.x() + 96, box.y() + 32, 400, 26, title, WHITE, QFont.Bold)
        _text(p, box.x() + 96, box.y() + 72, 400, 20, sub, MUTED)
        x += 560
        if i == 2:
            x, y = 120, 404
    if rep is not None:
        _text(p, 120, 588, 1400, 24,
              f"Dữ liệu minh hoạ: CPA {ai_page.fmt(rep.cpa4)}/4 · "
              f"{core.fmt_credits(rep.credits_passed)}/{core.PROGRAM['total_credits']} tín chỉ",
              QColor("#9FACCC"))

    _text(p, 120, 760, 1600, 76, "Cảm ơn thầy cô đã theo dõi", WHITE, QFont.ExtraBold)
    _text(p, 120, 862, 1600, 24,
          "Nhóm thực hiện: Đặng Duy Khang · Trần Bảo Khang · Đỗ Chí Kiên · Đỗ Công Tuấn Anh  ·  GVHD: Nguyễn Thanh Hải",
          QColor("#C8D1EA"))
    p.end()
    return pm


# ------------------------------------------------------------------- overlays
BAND_BG = QColor("#070D1F")


def compose(raw: QPixmap, cam: tuple = (1.0, 960, 470)) -> QPixmap:
    """Dat khung ung dung vao khung hinh, chua san dai rieng o duoi cho phu de.

    `cam` = (zoom, cx, cy): phong to vung dang noi de chu tren hinh to, de doc hon
    ca ban goc, trong khi phu de nam o dai rieng nen khong che noi dung.
    """
    zoom, cx, cy = cam
    zoom = max(1.0, float(zoom))
    rw, rh = W / zoom, APP_H / zoom
    x0 = min(max(0.0, cx - rw / 2), raw.width() - rw)
    y0 = min(max(0.0, cy - rh / 2), raw.height() - rh)
    pm = QPixmap(W, H)
    pm.fill(BAND_BG)
    p = QPainter(pm)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.drawPixmap(QRectF(0, 0, W, APP_H), raw, QRectF(x0, y0, rw, rh))
    grad = QLinearGradient(0, APP_H, 0, APP_H + 22)
    grad.setColorAt(0, QColor(255, 255, 255, 22))
    grad.setColorAt(1, QColor(255, 255, 255, 0))
    p.fillRect(QRectF(0, APP_H, W, 22), grad)
    p.end()
    return pm


def draw_caption(pm: QPixmap, title: str, sub: str):
    """Phu de nam trong dai rieng o duoi khung hinh — khong che noi dung ung dung."""
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    y = APP_H
    p.fillRect(QRectF(0, y, W, 3), QColor(255, 255, 255, 26))
    p.fillRect(QRectF(0, y, 240, 3), YELLOW)
    _text(p, 44, y + 20, W - 120, 25, title, WHITE, QFont.Bold)
    _text(p, 44, y + 60, W - 120, 20, sub, QColor("#B9C4DE"))
    p.end()


def draw_spot(pm: QPixmap, widget, color=YELLOW, dim=104):
    if widget is None or not widget.isVisible():
        return
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    tl = widget.mapTo(pm_ref[0], QPoint(0, 0))
    r = QRectF(tl.x() - 10, tl.y() - 10, widget.width() + 20, widget.height() + 20)
    outer = QPainterPath()
    outer.addRect(QRectF(-60, -60, pm.width() + 120, pm.height() + 120))
    inner = QPainterPath()
    inner.addRoundedRect(r, 18, 18)
    p.fillPath(outer.subtracted(inner), QColor(4, 9, 24, dim))
    p.setPen(QPen(color, 3.2))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(r, 18, 18)
    p.end()


def draw_progress(pm: QPixmap, frac: float):
    p = QPainter(pm)
    h = 5
    y = pm.height() - h
    p.fillRect(QRectF(0, y, pm.width(), h), QColor(255, 255, 255, 26))
    p.fillRect(QRectF(0, y, pm.width() * max(0.0, min(1.0, frac)), h), YELLOW)
    p.end()


def fade_black(pm: QPixmap, alpha: float):
    if alpha <= 0:
        return
    p = QPainter(pm)
    p.fillRect(pm.rect(), QColor(0, 0, 0, int(max(0, min(255, alpha * 255)))))
    p.end()


pm_ref: list[QWidget] = []


# ------------------------------------------------------------------ demo data
def build_demo(tmp: Path) -> GradeBook:
    book = GradeBook(tmp / "demo_grades.json")
    rng = random.Random(2026)
    for sem in range(1, 6):
        base = 7.35 + 0.16 * sem
        for c in book.courses_in(sem):
            if "ALL" in c["prereq"] or book.is_locked(c["id"]):
                continue
            if c["elective"] and sem not in (4, 5):
                continue
            vals = [round(min(10.0, max(5.0, base + rng.uniform(-1.3, 1.3))), 1) for _ in range(3)]
            book.save(c["id"], *vals)
    # mot mon khong dat o hoc ky moi nhat da nhap diem -> demo canh bao + hoc lai
    cand = [c for c in book.courses_in(5)
            if "ALL" not in c["prereq"] and book.result(c["id"]) is not None
            and not any(book.result(d) is not None for d in book.dependents(c["id"]))]
    if cand:
        book.save(cand[0]["id"], 3.5, 4.0, 3.0)
    return book


def chat_answer(book) -> str:
    rep = LocalAnalytics(book).report()
    cpa = ai_page.fmt(rep.cpa4)
    cred = core.fmt_credits(rep.credits_passed)
    total = core.PROGRAM["total_credits"]
    info = book.next_semester_info() or {}
    st = info.get("stats") or {}
    sem = info.get("semester") or 6
    nxt = st.get("n_plan") or 10
    elec = st.get("electives_needed") or 2
    if rep.retake_plan:
        p = rep.retake_plan[0]
        n_dep = len(book.dependents(p.cid))
        first = f"Học lại {p.name}"
        why = f"Mở khoá {n_dep} học phần phụ thuộc" if n_dep else "Hoàn tất học phần nền tảng"
    else:
        first, why = "Không cần học lại", "Đã đạt toàn bộ học phần đã học"
    return (f"Dựa trên bảng điểm hiện tại của bạn (CPA {cpa}/4 · {cred}/{total} tín chỉ), "
            f"đây là kế hoạch cho học kỳ {sem}:\n\n"
            "| Ưu tiên | Việc cần làm | Vì sao |\n| --- | --- | --- |\n"
            f"| 1 | {first} | {why} |\n"
            f"| 2 | Đăng ký đủ {nxt} học phần học kỳ {sem} | Giữ đúng tiến độ 9 học kỳ |\n"
            f"| 3 | Chọn {elec} môn tự chọn | Đủ {total} tín chỉ tốt nghiệp |\n\n"
            "Ba việc nên làm ngay trong hai tuần tới:\n"
            "1. Chốt danh sách học lại trước hạn đăng ký.\n"
            "2. Dành hai buổi mỗi tuần cho môn nền tảng.\n"
            "3. Cập nhật điểm đúng hạn để hệ thống tính lại CPA.")


# ------------------------------------------------------------------ encoder
class Encoder:
    def __init__(self, out: Path):
        out.parent.mkdir(parents=True, exist_ok=True)
        self.out = out
        self.proc = subprocess.Popen(
            [FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             str(out)], stdin=subprocess.PIPE)

    def write(self, pm: QPixmap):
        img = pm.toImage().convertToFormat(QImage.Format.Format_RGB32)
        bpl = img.bytesPerLine()
        buf = bytes(img.constBits())
        row = W * 4
        if bpl != row:
            buf = b"".join(buf[y * bpl:y * bpl + row] for y in range(H))
        self.proc.stdin.write(buf)

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.wait()


# ------------------------------------------------------------------- scenes
def build_scenes(win: MainWindow, book: GradeBook, thumbs: dict) -> list[dict]:
    rep = LocalAnalytics(book).report()
    ai = lambda: win.ai  # noqa: E731  (lay lai sau khi rebuild theme)

    scenes: list[dict] = []

    def add(name, narration, caption, prep=None, tick=None, focus=None, slide=None,
            extra=0.0, cam=(1.0, 960, 470)):
        scenes.append(dict(name=name, narration=narration, caption=caption, prep=prep,
                           tick=tick, focus=focus, slide=slide, extra=extra, cam=cam))

    # 1 ---------------------------------------------------------------- mo dau
    add("01_mo_dau",
        "Em xin kính chào thầy Nguyễn Thanh Hải và quý thầy cô.\n"
        "Đây là phần mềm Quản lý Học phần và Trợ lý AI học tập, do nhóm em xây dựng "
        "cho ngành Tin học Xây dựng, Khoa Xây dựng, Trường Đại học Bách khoa, Đại học Đà Nẵng.",
        ("Quản lý Học phần & Trợ lý AI học tập",
         "Kính chào thầy Nguyễn Thanh Hải · Đồ án môn học · Ngành Tin học Xây dựng · ĐH Bách khoa – ĐH Đà Nẵng"),
        slide="title")

    # 2 ---------------------------------------------------------------- bai toan
    add("02_bai_toan",
        "Mỗi học kỳ, sinh viên phải tự cộng điểm theo công thức hai mươi phần trăm thành phần, "
        "hai mươi phần trăm giữa kỳ và sáu mươi phần trăm cuối kỳ.\n"
        "Cách làm thủ công rất dễ sai, "
        "khó biết môn nào đang bị khoá, và gần như không ai theo dõi được nguy cơ cảnh báo học tập hay "
        "tiến độ tốt nghiệp.",
        ("Bài toán", "Ba việc sinh viên phải tự làm bằng tay: tính điểm · xét môn bị khoá · theo dõi tốt nghiệp"),
        slide="problem")

    # 3 --------------------------------------------------------------- tong quan
    def prep_dash():
        win.go(1)
        win.dash.refresh()

    add("03_tong_quan",
        "Phần mềm giải quyết trọn vẹn ba việc đó trong một ứng dụng duy nhất trên máy tính.\n"
        "Chỉ cần nhập điểm một lần, toàn bộ điểm tổng kết, điểm chữ, điểm trung bình học kỳ, "
        "điểm trung bình tích luỹ, tín chỉ tích luỹ và xếp loại được tính tự động "
        "và cập nhật tức thì trên trang Tổng quan.",
        ("Tổng quan học tập", "GPA/CPA, tín chỉ tích lũy, học kỳ tiếp theo và biểu đồ điểm — tất cả tự động"),
        prep=prep_dash, cam=(1.06, 960, 470))

    # 4 --------------------------------------------------------------- nhap diem
    st: dict = {}

    def prep_scores():
        st.clear()
        win.go(2)
        win.courses.set_semester(6)
        cand = [c for c in book.courses_in(6)
                if "ALL" not in c["prereq"] and not book.is_locked(c["id"]) and not book.result(c["id"])]
        if cand:
            win.courses.focus_course(cand[0]["id"])
            st["cid"] = cand[0]["id"]

    def tick_scores(t, s):
        d = win.courses.detail
        edits = [e for e in d.findChildren(QLineEdit) if e.objectName() == "ScoreInput"]
        if len(edits) < 3:
            return
        t0 = s.at("khi gõ ba đầu điểm")
        vals = ["8", "9", "8.5"]
        prog = ease_out((t - t0) / 1.1) * 3.0
        for i, (e, v) in enumerate(zip(edits, vals)):
            k = max(0.0, min(1.0, prog - i))
            txt = v[:int(round(k * len(v)))]
            if e.text() != txt:
                e.setText(txt)
        if t > s.at("xét điều kiện đạt") and not st.get("saved"):
            st["saved"] = True
            d.b_save.click()

    add("04_nhap_diem",
        "Đây là phần nghiệp vụ quan trọng nhất.\n"
        "Ở trang Học phần và Nhập điểm, khi gõ ba đầu điểm, "
        "hệ thống tính ngay điểm tổng kết theo đúng trọng số, quy ra điểm chữ, xét điều kiện đạt và "
        "cập nhật lại điểm trung bình của cả học kỳ.",
        ("Nhập điểm tức thì", "Gõ TP · GK · CK → tổng kết, điểm chữ, trạng thái và GPA đổi ngay"),
        prep=prep_scores, tick=tick_scores, focus=lambda t, s: win.courses.detail,
        cam=(1.22, 1150, 470))

    # 5 ----------------------------------------------------------- mon bi khoa
    def prep_locked():
        win.go(2)
        win.courses.set_semester(7)
        win.courses.search.clear()

    add("05_mon_bi_khoa",
        "Hệ thống còn kiểm tra học phần học trước.\n"
        "Môn nào chưa đạt sẽ tự động khoá các môn phụ thuộc, "
        "đúng theo quy chế đào tạo, nên sinh viên thấy ngay mình cần học lại môn nào trước.",
        ("Tự động khoá môn theo học phần học trước", "Môn chưa đạt → các môn phụ thuộc hiện trạng thái “Bị khóa”"),
        prep=prep_locked, focus=lambda t, s: win.courses.table, cam=(1.14, 1010, 430))

    # 6 ---------------------------------------------------------------- ket qua
    add("06_ket_qua",
        "Trang Kết quả học tập tổng hợp điểm trung bình từng học kỳ và điểm trung bình tích luỹ, "
        "xếp loại, tín chỉ tích luỹ.\n"
        "Bảng điểm còn xuất được ra tệp xê-ét-vê để nộp kèm báo cáo.",
        ("Kết quả & tích lũy", "Bảng GPA/CPA từng học kỳ, xếp loại, tín chỉ tích lũy và xuất CSV"),
        prep=lambda: (win.go(3), win.results.refresh()), cam=(1.08, 960, 430))

    # 7 ------------------------------------------------------------ AI tong quan
    def prep_ai_overview():
        win.go(4)
        win.ai.open_tab("overview")
        win.ai.analysis.refresh()

    add("07_ai_tong_quan",
        "Trợ lý AI là phần nhóm em đầu tư nhiều nhất.\n"
        "Trang Tổng quan AI tự động sinh cảnh báo học tập, "
        "tiến độ tốt nghiệp, kế hoạch học lại và danh sách việc cần làm cho tuần này, tất cả đều tính từ chính "
        "bảng điểm của sinh viên.",
        ("Trợ lý AI · Tổng quan", "Cảnh báo học tập, tiến độ tốt nghiệp, kế hoạch học lại, việc cần làm"),
        prep=prep_ai_overview,
        focus=lambda t, s: (win.ai.analysis.retake_box.parentWidget() if t > s.at("kế hoạch học lại")
                            else win.ai.analysis.alert_box.parentWidget()),
        cam=(1.08, 1050, 470))

    # 8 ---------------------------------------------------------------- AI chat
    cst: dict = {}
    question = "Học kỳ 6 em nên đăng ký những môn nào để không bị khoá?"
    answer = chat_answer(book)

    def prep_chat():
        cst.clear()
        win.go(4)
        win.ai.open_tab("chat")
        win.ai.chat_tab.input.clear()

    def tick_chat(t, s):
        ch = win.ai.chat_tab
        t0 = s.at("Phần hội thoại")
        t1 = s.at("Trợ lý đọc trực tiếp dữ liệu học tập")
        span = max(0.8, (t1 - t0) * 0.6)
        n = int(min(1.0, max(0.0, (t - t0 - 0.2) / span)) * len(question))
        want = question[:n]
        if not cst.get("sent") and ch.input.text() != want:
            ch.input.setText(want)
        if n >= len(question) and not cst.get("sent"):
            cst["sent"] = True
            ch.input.clear()
            win.session.append("user", question)
            win.session.busy_changed.emit(True)
        if cst.get("sent") and t > t1 + 0.2 and not cst.get("answered"):
            cst["answered"] = True
            win.session.busy_changed.emit(False)
            win.session.append("assistant", answer)
            QTimer.singleShot(0, ch._scroll_bottom)
        if t > s.at("bong bóng chat nổi") - 0.4 and not cst.get("popup"):
            cst["popup"] = True
            win.floating.show_popup()

    add("08_ai_chat",
        "Phần hội thoại dùng mô hình trí tuệ nhân tạo chạy online, tương thích chuẩn mở.\n"
        "Trợ lý đọc trực tiếp dữ liệu học tập, trả lời bằng bảng biểu dễ đọc, lưu lịch sử theo từng phiên.\n"
        "Và có thể mở nhanh từ bong bóng chat nổi ở bất kỳ trang nào.",
        ("Trò chuyện với trợ lý AI", "AI đọc bảng điểm của bạn · trả lời bằng bảng Markdown · lưu lịch sử"),
        prep=prep_chat, tick=tick_chat, extra=2.6,
        focus=lambda t, s: win.ai.chat_tab.composer if t < s.at("Trợ lý đọc trực tiếp") else win.ai.chat_tab,
        cam=(1.30, 1200, 300))

    # 9 ----------------------------------------------------------- ke hoach
    def prep_plan():
        win.floating.close_popup()       # bong bong chi xuat hien o canh tro chuyen
        win.go(4)
        win.ai.open_tab("plan")
        win.ai.plan.refresh()

    add("09_ke_hoach",
        "Tab Kế hoạch học tập cá nhân hoá thời khoá biểu theo tuần, đề xuất phương pháp học dựa trên "
        "điểm số thực tế, và xếp lịch học lại theo từng học kỳ.",
        ("Kế hoạch học tập", "Thời khoá biểu tuần · phương pháp học cá nhân hoá · lịch học lại"),
        prep=prep_plan, cam=(1.12, 1050, 520))

    # 10 --------------------------------------------------------- tu dong hoa
    ast: dict = {}

    def prep_auto():
        ast.clear()
        win.go(4)
        win.ai.open_tab("automation")

    def tick_auto(t, s):
        au = win.ai.automation
        if t > s.at("Nhắc giờ học") and not ast.get("time"):
            ast["time"] = True
            au.time_study.setTime(QTime(19, 30))
            au.time_coach.setTime(QTime(8, 0))
        if t > s.at("chạy nền") and not ast.get("quiet"):
            ast["quiet"] = True
            au.cb_quiet.setChecked(True)
        if t > s.at("thông báo") and not ast.get("run"):
            ast["run"] = True
            au._run_now()

    add("10_tu_dong_hoa",
        "Tab Tự động hoá biến phần mềm thành một trợ lý chủ động.\n"
        "Nhắc giờ học, cảnh báo học tập, lời khuyên hằng ngày, chạy nền và thông báo ngay cả khi đang ở trang khác.",
        ("Tự động hoá nhắc nhở", "Nhắc giờ học · cảnh báo · AI coach hằng ngày · chạy nền, báo qua khay hệ thống"),
        prep=prep_auto, tick=tick_auto, focus=lambda t, s: win.ai.automation, cam=(1.12, 1050, 480))

    # 11 ------------------------------------------------------ cai dat + theme
    tst: dict = {}

    def prep_settings():
        tst.clear()
        win.go(4)
        win.ai.open_tab("settings")

    def tick_settings(t, s):
        if t > s.at("hai chế độ sáng và tối") and not tst.get("dark"):
            tst["dark"] = True
            win.animate = False
            win.set_theme("dark")
            win.animate = False
            win.go(4)
            win.ai.open_tab("settings")
        if t > s.at("đổi đồng bộ") and not tst.get("overview"):
            tst["overview"] = True
            win.go(4)
            win.ai.open_tab("overview")
            win.ai.analysis.refresh()

    add("11_cai_dat_theme",
        "Toàn bộ giao diện có hai chế độ sáng và tối; màu sắc, biểu tượng và biểu đồ đổi đồng bộ.\n"
        "Cấu hình trợ lý AI nằm trong tab Cài đặt, khoá bảo mật luôn được che khi hiển thị.",
        ("Cài đặt AI · Sáng / Tối", "Endpoint, model, kiểm tra kết nối · toàn bộ giao diện đổi theme đồng bộ"),
        prep=prep_settings, tick=tick_settings, cam=(1.06, 1000, 470))

    # 12 --------------------------------------------------------------- ky thuat
    def prep_product():
        win.floating.close_popup()
        win.go(0)

    add("12_ky_thuat",
        "Về kỹ thuật, phần mềm viết bằng Python, giao diện dựng bằng PySide6, đóng gói thành một tệp "
        "thực thi duy nhất chạy trực tiếp trên máy tính.\n"
        "Kèm theo là bốn bộ kiểm thử tự động cho lõi tính điểm, trợ lý AI, tự động hoá và giao diện, "
        "tất cả đều đạt.",
        ("Sản phẩm hoàn chỉnh", "PySide6 · đóng gói 1 tệp .exe · 4 bộ kiểm thử tự động đều đạt"),
        prep=prep_product, cam=(1.06, 1000, 470))

    # 13 ------------------------------------------------------------------ ket
    add("13_cam_on",
        "Nhóm em tin sản phẩm giải quyết đúng nhu cầu thực tế của sinh viên và có thể mở rộng cho các "
        "ngành khác.\n"
        "Nhóm em xin cảm ơn thầy Nguyễn Thanh Hải và quý thầy cô đã theo dõi.",
        ("Cảm ơn thầy cô đã theo dõi", "Quản lý Học phần & Trợ lý AI học tập · v2.0.6"),
        slide="end", prep=lambda: win.floating.close_popup())
    return scenes


# -------------------------------------------------------------------- runner
def render(check: bool = False, audio_only: bool = False):
    OUT.mkdir(exist_ok=True)
    AUD.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="video_"))

    ui_kit.load_fonts()
    main_mod.save_settings = lambda data: None
    ui_kit.MessageDialog.exec = lambda self, *a, **k: 0        # khong bao gio treo vi dialog
    demo_cfg = {"base_url": "http://127.0.0.1:31415/v1", "model": "auto:smart",
                "api_key": "sk-demo-4f7a1c2b9e8d6350"}
    ai_page.load_api_config = lambda: dict(demo_cfg)
    if hasattr(main_mod, "load_api_config"):
        main_mod.load_api_config = ai_page.load_api_config
    ai_page.CHAT_PATH = tmp / "chat.json"
    automation.CONFIG_PATH = tmp / "automation.json"
    automation.STORE_PATH = tmp / "reminders.json"

    book = build_demo(tmp)
    rep = LocalAnalytics(book).report()
    print(f"[demo] CPA {ai_page.fmt(rep.cpa4)} · {core.fmt_credits(rep.credits_passed)} TC · "
          f"{len(rep.failed)} mon khong dat · {len(rep.retake_plan)} mon hoc lai")

    win = MainWindow(book)
    win.animate = False
    win.toast = lambda text, kind="info": None   # tranh toast che noi dung khi quay
    win.resize(W, H)
    win.show()
    for _ in range(10):
        APP.processEvents()
    try:
        win.engine.stop()
    except Exception:
        pass
    pm_ref[:] = [win]

    thumbs = {}
    win.go(1)
    for _ in range(6):
        APP.processEvents()
    thumbs["dash"] = win.grab().scaledToWidth(1000, Qt.SmoothTransformation)

    scenes = build_scenes(win, book, thumbs)
    for sc in scenes:
        sc["s"] = Narration(sc["name"], sc["narration"])
        sc["audio"] = sc["s"].build()
        sc["dur"] = sc["s"].duration + PAD + float(sc.get("extra", 0.0))

    total = sum(sc["dur"] for sc in scenes)
    print(f"[video] {len(scenes)} doan · {total:.1f}s · {FPS} fps · {W}x{H}")
    if audio_only:
        for sc in scenes:
            print(f"  {sc['name']}: {sc['dur']:.1f}s")
        print("AUDIO OK")
        try:
            win.engine.stop()
            win.close()
        except Exception:
            pass
        return

    final: list = []        # bao cao cuoi cung (sau khi da nhap diem o canh 4)
    if check:
        cdir = OUT / "_check"
        cdir.mkdir(exist_ok=True)
        for i, sc in enumerate(scenes):
            if sc["prep"]:
                sc["prep"]()
            for _ in range(6):
                APP.processEvents()
            if sc["slide"] == "title":
                pm = slide_title(thumbs.get("dash"))
            elif sc["slide"] == "problem":
                pm = slide_problem()
            elif sc["slide"] == "end":
                if not final:
                    final.append(LocalAnalytics(book).report())
                pm = slide_end(final[0])
            else:
                t_mid = sc["dur"] * 0.6
                if sc["tick"]:
                    sc["tick"](t_mid, sc["s"])
                for _ in range(3):
                    APP.processEvents()
                raw = win.grab()
                fw = sc["focus"](t_mid, sc["s"]) if callable(sc["focus"]) else sc["focus"]
                if fw is not None:
                    draw_spot(raw, fw)
                pm = compose(raw, sc.get("cam", (1.0, 960, 470)))
            title, sub = sc["caption"]
            draw_caption(pm, title, sub)
            draw_progress(pm, (i + 1) / len(scenes))
            path = cdir / f"{sc['name']}.png"
            pm.save(str(path))
            print("  check ->", path.name)
        print("CHECK OK")
        return

    silent = OUT / "_video_silent.mp4"
    enc = Encoder(silent)
    starts, acc = [], 0.0
    for sc in scenes:
        starts.append(acc)
        acc += sc["dur"]
    cum = [0]
    for sc in scenes:
        cum.append(cum[-1] + sc["dur"])

    for i, sc in enumerate(scenes):
        sc["prep"] and sc["prep"]()
        for _ in range(6):
            APP.processEvents()
        n = max(2, int(round(cum[i + 1] * FPS)) - int(round(cum[i] * FPS)))
        print(f"  [{i + 1}/{len(scenes)}] {sc['name']}: {n} khung ({sc['dur']:.1f}s)")
        for k in range(n):
            t = k / max(1, n - 1)
            if sc["slide"] == "title":
                pm = slide_title(thumbs.get("dash"))
            elif sc["slide"] == "problem":
                pm = slide_problem()
            elif sc["slide"] == "end":
                if not final:               # so lieu cuoi cung, sau khi da nhap diem
                    final.append(LocalAnalytics(book).report())
                pm = slide_end(final[0])
            else:
                t_sec = t * sc["dur"]
                if sc["tick"]:
                    sc["tick"](t_sec, sc["s"])
                for _ in range(2):
                    APP.processEvents()
                raw = win.grab()
                fw = sc["focus"](t_sec, sc["s"]) if callable(sc["focus"]) else sc["focus"]
                if fw is not None:
                    draw_spot(raw, fw)
                pm = compose(raw, sc.get("cam", (1.0, 960, 470)))
            title, sub = sc["caption"]
            draw_caption(pm, title, sub)
            draw_progress(pm, (cum[i] + (k + 1) / n * sc["dur"]) / total)
            if k < 4:
                fade_black(pm, 1 - k / 4)
            if total - (cum[i] + k / n * sc["dur"]) < 0.5 and i == len(scenes) - 1:
                fade_black(pm, max(0.0, (k - (n - 6)) / 6))
            enc.write(pm)
    enc.close()
    print("[video] xong hinh anh")

    # ---- ghep am thanh theo dung moc thoi gian
    parts: list[Path] = []
    for sc in scenes:
        parts.append(sc["audio"])
        # im lang phai bang dung PAD + phan giu them cua canh, neu khong cac canh sau bi lech tieng
        parts.append(_gap_wav(PAD + float(sc.get("extra", 0.0))))
    narration = OUT / "_narration.wav"
    concat_wavs(parts, narration)
    print(f"[audio] thuyet minh {media_duration(narration):.1f}s")

    music = OUT / "_music.wav"
    build_music(media_duration(narration), music)

    final = OUT / "GioiThieu_TinHocXayDung.mp4"
    tmp_out = OUT / "_final.mp4"          # ghi tam roi thay the (tranh file dang mo)
    tmp_out.unlink(missing_ok=True)
    r = ff("-i", str(silent), "-i", str(narration), "-i", str(music),
           "-filter_complex",
           "[2:a]volume=0.18[m];[1:a]volume=0.92[n];[n][m]amix=inputs=2:duration=first:normalize=0[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
           "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(tmp_out))
    if r.returncode != 0:
        print("MUX FAIL:", r.stderr[-800:])
    else:
        try:
            final.unlink(missing_ok=True)
            tmp_out.replace(final)
            print(f"[ok] {final} · {final.stat().st_size / 1e6:.1f} MB")
        except OSError as e:
            print(f"[canh bao] khong thay the duoc file dich ({e}); giu ban tam {tmp_out}")

    # ---- phu de
    srt = OUT / "phu_de.srt"
    lines = []
    for i, sc in enumerate(scenes):
        t0, t1 = cum[i] + 0.1, cum[i + 1] - 0.1
        title, sub = sc["caption"]
        lines.append(f"{i + 1}\n{_stamp(t0)} --> {_stamp(t1)}\n{title}\n{sub}\n")
    srt.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] {srt}")

    silent.unlink(missing_ok=True)
    narration.unlink(missing_ok=True)
    music.unlink(missing_ok=True)
    try:
        win.engine.stop()
        win.close()
    except Exception:
        pass


def _stamp(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="chi render vai khung de xem truoc")
    ap.add_argument("--audio-only", action="store_true", help="chi sinh thuyet minh va do do dai")
    args = ap.parse_args()
    t0 = time.time()
    render(check=args.check, audio_only=args.audio_only)
    print(f"[time] {time.time() - t0:.1f}s")
