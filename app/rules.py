"""Quy chế & chuẩn đầu ra của Trường ĐH Bách khoa – ĐH Đà Nẵng.

Toàn bộ số liệu dưới đây trích từ văn bản gốc (thư mục tài liệu của Trường):

1. QĐ 2244/QĐ-ĐHBK (2021) – Quy định đào tạo trình độ đại học.
   Điều 7 (đăng ký học phần), Điều 12 (cảnh báo kết quả học tập / buộc thôi học),
   Điều 14 (công nhận, chuyển đổi tín chỉ), Điều 15 (đồ án tốt nghiệp), Điều 17 (xét tốt nghiệp).
2. QĐ 4511/QĐ-ĐHBK (2022) – Yêu cầu năng lực ngoại ngữ (thay thế QĐ 389/2016).
3. QĐ 417/QĐ-ĐHBK (2016) – Chuẩn kỹ năng sử dụng CNTT (theo TT 03/2014/TT-BTTTT).
4. QĐ 029/QĐ-ĐHBK (2017) và QĐ 1274/QĐ-ĐHBK (2019) – Liêm chính học thuật.
5. QĐ 1414/QĐ-ĐHBK (2021) – Xét, cấp học bổng khuyến khích học tập.

Mọi con số ở đây đều dùng để tính toán trong ứng dụng và để dạy AI trả lời đúng luật,
KHÔNG suy diễn thêm ngoài văn bản.
"""
from __future__ import annotations

import json
from pathlib import Path

# --------------------------------------------------------------------- văn bản
DOCS = [
    {"code": "2244/QĐ-ĐHBK", "year": 2021, "title": "Quy định đào tạo trình độ đại học",
     "topics": ["đăng ký học phần 12–25 TC", "cảnh báo kết quả học tập", "buộc thôi học",
                "công nhận tín chỉ ≤ 50%", "đồ án tốt nghiệp", "xét tốt nghiệp 3 lần/năm"]},
    {"code": "4511/QĐ-ĐHBK", "year": 2022, "title": "Yêu cầu năng lực ngoại ngữ",
     "topics": ["chuẩn tiếng Anh đầu khóa", "chuẩn đầu ra ngoại ngữ (TOEIC ≥ 450)",
                "miễn học phần tiếng Anh khi có IELTS 5.5"]},
    {"code": "417/QĐ-ĐHBK", "year": 2016, "title": "Chuẩn kỹ năng sử dụng CNTT",
     "topics": ["6 mô-đun IU01–IU06 theo TT 03/2014/TT-BTTTT"]},
    {"code": "029/QĐ-ĐHBK", "year": 2017, "title": "Quy định liêm chính học thuật",
     "topics": ["bịa đặt", "gian lận", "đạo văn", "giúp người khác vi phạm"]},
    {"code": "1274/QĐ-ĐHBK", "year": 2019, "title": "Sửa đổi, bổ sung QĐ liêm chính học thuật",
     "topics": ["điều chỉnh hành vi vi phạm và hình thức xử lý"]},
    {"code": "1414/QĐ-ĐHBK", "year": 2021, "title": "Xét, cấp học bổng khuyến khích học tập",
     "topics": ["loại A ≥ 9,00 và rèn luyện ≥ 90", "loại B ≥ 8,00 và ≥ 80",
                "loại C ≥ 7,00 và ≥ 65", "mức 100% / 120% / 150% học phí"]},
    {"code": "389/QĐ-ĐHBK", "year": 2016, "title": "Yêu cầu năng lực tiếng Anh (đã được thay thế)",
     "topics": ["hết hiệu lực từ năm học 2022–2023, xem QĐ 4511/2022"]},
]

# ------------------------------------------------------- QĐ 2244/2021 – Điều 7
MIN_CREDITS_PER_SEMESTER = 12
MAX_CREDITS_PER_SEMESTER = 25
MAX_CREDITS_NO_ENGLISH = 14      # SV chưa đạt yêu cầu năng lực tiếng Anh
MAX_CREDITS_SUMMER = 10          # học kỳ hè

# ------------------------------------------------ QĐ 2244/2021 – Điều 12, 14, 15
WARN_GPA_FIRST_SEMESTER = 0.80   # TB học kỳ dưới 0,80 (học kỳ đầu)
WARN_GPA_NEXT_SEMESTERS = 1.00   # TB học kỳ dưới 1,00 (các học kỳ tiếp theo)
WARN_CPA_BY_YEAR = {1: 1.20, 2: 1.40, 3: 1.60, 4: 1.80}   # năm 4 trở đi: 1,80
DISMISS_AFTER_WARNINGS = 2        # bị cảnh báo 2 lần liên tiếp
TRANSFER_MAX_RATIO = 0.50         # công nhận/chuyển đổi tối đa 50% khối lượng CTĐT
ONLINE_MAX_RATIO = 0.30           # học trực tuyến tối đa 30% khối lượng CTĐT
THESIS_MIN_CPA = 1.90             # được làm đồ án tốt nghiệp
THESIS_MAX_LEFT_CREDITS = 4       # còn không quá 4 TC (trừ ĐATN)

# ------------------------------------------------ QĐ 2244/2021 – Điều 17 + 4511
GRAD_MIN_CPA = 2.00               # CPA tối thiểu để được công nhận tốt nghiệp
GRAD_REVIEWS_PER_YEAR = 3         # xét tốt nghiệp cuối HK1, HK2 và HK hè

# ------------------------------------------------- QĐ 4511/2022 – ngoại ngữ
ENGLISH_ENTRY = {"IELTS": 5.0, "TOEFL iBT": 45, "TOEFL ITP": 499}     # chuẩn đầu khóa
ENGLISH_OUTPUT = {"TOEIC": 450, "IELTS": 5.5, "TOEFL iBT": 46, "TOEFL ITP": 500}
ENGLISH_OUTPUT_NOTE = ("Chương trình chất lượng cao và khóa tuyển sinh 2020: TOEIC ≥ 600. "
                       "Có IELTS ≥ 5.5 hoặc TOEFL iBT ≥ 46 được miễn học phần tiếng Anh và "
                       "công nhận điểm 10 học phần đó.")
ENGLISH_EXEMPT = {"IELTS": 5.5, "TOEFL iBT": 46}

# --------------------------------------------------- QĐ 417/2016 – CNTT
IT_MODULES = [
    ("IU01", "Hiểu biết về CNTT cơ bản"),
    ("IU02", "Sử dụng máy tính cơ bản"),
    ("IU03", "Xử lý văn bản cơ bản"),
    ("IU04", "Sử dụng bảng tính cơ bản"),
    ("IU05", "Sử dụng trình chiếu cơ bản"),
    ("IU06", "Sử dụng Internet cơ bản"),
]
IT_NOTE = ("Chuẩn kỹ năng sử dụng CNTT cơ bản gồm 6 mô-đun IU01–IU06 "
           "(Thông tư 03/2014/TT-BTTTT), là điều kiện công nhận tốt nghiệp.")

# ---------------------------------------------------- QĐ 1414/2021 – học bổng
SCHOLARSHIP = [   # (mã, tên loại, GPA hệ 10 tối thiểu, điểm rèn luyện tối thiểu, hệ số học phí)
    ("A", "Xuất sắc", 9.00, 90, 1.50),
    ("B", "Giỏi", 8.00, 80, 1.20),
    ("C", "Khá", 7.00, 65, 1.00),
]
SCHOLARSHIP_NOTE = ("Xét theo từng học kỳ; phải tích lũy đủ số tín chỉ theo kế hoạch học tập "
                    "và không có học phần thi lần đầu (không tính học phần xin bảo lưu).")

# ------------------------------------------------- QĐ 029/2017 – liêm chính
INTEGRITY = [
    ("Bịa đặt", "Ngụy tạo, bịa ra số liệu, dữ liệu trong khảo sát, thí nghiệm, thực hành "
                "hoặc trong sản phẩm học thuật."),
    ("Gian lận", "Dùng thủ thuật gian dối khi thi; giả mạo hồ sơ, chứng nhận; mang tài liệu "
                 "bị cấm vào phòng thi; trao đổi bài, nhờ người làm hộ; nộp sản phẩm của người khác."),
    ("Đạo văn", "Dùng từ ngữ, ý tưởng, số liệu, hình vẽ của người khác mà không trích dẫn nguồn."),
    ("Giúp người khác vi phạm", "Chuẩn bị hoặc hỗ trợ người khác thực hiện hành vi vi phạm "
                                "liêm chính học thuật."),
]
INTEGRITY_NOTE = ("Vi phạm liêm chính học thuật bị xử lý theo QĐ 029/2017 và QĐ 1274/2019; "
                  "hồ sơ vi phạm được xét trước khi công nhận tốt nghiệp.")

# ------------------------------------------------------------- hồ sơ chuẩn đầu ra
DEFAULT_PROFILE = {
    "english_ok": False,          # đã có chứng chỉ đạt chuẩn đầu ra ngoại ngữ
    "english_cert": "",           # ví dụ "TOEIC 550 (2025)"
    "it_ok": False,               # đã có chứng nhận 6 mô-đun IU01–IU06
    "it_cert": "",
    "conduct": None,              # điểm rèn luyện học kỳ gần nhất (0–100)
}


def profile_path(data_dir: Path) -> Path:
    return Path(data_dir) / "profile.json"


def load_profile(data_dir: Path) -> dict:
    data = dict(DEFAULT_PROFILE)
    try:
        raw = json.loads(profile_path(data_dir).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for k in DEFAULT_PROFILE:
                if k in raw:
                    data[k] = raw[k]
    except (OSError, ValueError):
        pass
    return data


def save_profile(data_dir: Path, data: dict) -> dict:
    clean = dict(DEFAULT_PROFILE)
    clean.update({k: data[k] for k in DEFAULT_PROFILE if k in data})
    path = profile_path(data_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
    return clean


# ------------------------------------------------------------------- tính toán
def year_of(semester: int | None) -> int:
    """Học kỳ 1–2 là năm 1, 3–4 là năm 2, …"""
    try:
        sem = int(semester or 1)
    except (TypeError, ValueError):
        sem = 1
    return max(1, (sem + 1) // 2)


def cpa_warning_threshold(semester: int | None) -> float:
    return WARN_CPA_BY_YEAR.get(year_of(semester), 1.80)


def warning_status(semester_gpa4: float | None, semester: int | None,
                   cpa4: float | None, warn_streak: int = 0) -> dict:
    """Đánh giá cảnh báo kết quả học tập theo Điều 12 QĐ 2244/2021."""
    reasons: list[str] = []
    sem = semester or 1
    if semester_gpa4 is not None:
        limit = WARN_GPA_FIRST_SEMESTER if sem == 1 else WARN_GPA_NEXT_SEMESTERS
        if semester_gpa4 < limit:
            reasons.append(f"TB học kỳ {semester_gpa4:.2f} < {limit:.2f}")
    if cpa4 is not None:
        limit = cpa_warning_threshold(sem)
        if cpa4 < limit:
            reasons.append(f"CPA {cpa4:.2f} < {limit:.2f} (năm {year_of(sem)})")
    level = "none"
    if reasons:
        level = "warning"
        if warn_streak + 1 >= DISMISS_AFTER_WARNINGS:
            level = "dismiss_risk"
    return {
        "level": level,
        "warning": bool(reasons),
        "reasons": reasons,
        "semester_threshold": WARN_GPA_FIRST_SEMESTER if sem == 1 else WARN_GPA_NEXT_SEMESTERS,
        "cpa_threshold": cpa_warning_threshold(sem),
        "year": year_of(sem),
        "source": "Điều 12 QĐ 2244/QĐ-ĐHBK (2021)",
    }


def registration_limit(english_ok: bool | None) -> dict:
    """Giới hạn khối lượng đăng ký học kỳ chính/hè (Điều 7 khoản 6 QĐ 2244/2021)."""
    ok = bool(english_ok)
    return {
        "min": MIN_CREDITS_PER_SEMESTER,
        "max": MAX_CREDITS_PER_SEMESTER if ok else MAX_CREDITS_NO_ENGLISH,
        "summer_max": MAX_CREDITS_SUMMER,
        "note": ("Đã đạt chuẩn tiếng Anh: 12–25 TC/học kỳ chính."
                 if ok else
                 "Chưa đạt chuẩn tiếng Anh: tối đa 14 TC/học kỳ chính."),
        "source": "Điều 7 khoản 6 QĐ 2244/QĐ-ĐHBK (2021)",
    }


def scholarship_level(gpa10: float | None, conduct: int | None) -> dict | None:
    """Loại học bổng khuyến khích học tập đủ điều kiện (QĐ 1414/2021)."""
    if gpa10 is None or conduct is None:
        return None
    for code, name, gpa_min, conduct_min, factor in SCHOLARSHIP:
        if gpa10 >= gpa_min and conduct >= conduct_min:
            return {"code": code, "name": name, "gpa_min": gpa_min,
                    "conduct_min": conduct_min, "factor": factor,
                    "source": "Điều 5–6 QĐ 1414/QĐ-ĐHBK (2021)"}
    return None


def graduation_requirements(credits: float, total: float, cpa4: float | None,
                           english_ok: bool | None, it_ok: bool | None,
                           thesis_done: bool | None = None) -> list[dict]:
    """Danh sách điều kiện công nhận tốt nghiệp, kèm trạng thái từng điều kiện."""
    items = [
        {"key": "credits", "label": "Đủ tín chỉ chương trình đào tạo",
         "ok": credits >= total,
         "detail": f"{credits:g}/{total:g} TC",
         "source": "Điều 17 QĐ 2244/QĐ-ĐHBK"},
        {"key": "cpa", "label": f"CPA ≥ {GRAD_MIN_CPA:.1f}/4",
         "ok": cpa4 is not None and cpa4 >= GRAD_MIN_CPA,
         "detail": "chưa có điểm" if cpa4 is None else f"CPA {cpa4:.2f}/4",
         "source": "Điều 17 QĐ 2244/QĐ-ĐHBK"},
        {"key": "english", "label": "Chuẩn đầu ra ngoại ngữ (TOEIC ≥ 450 hoặc tương đương)",
         "ok": bool(english_ok),
         "detail": "đã có chứng chỉ" if english_ok else "chưa khai báo chứng chỉ",
         "source": "QĐ 4511/QĐ-ĐHBK (2022)"},
        {"key": "it", "label": "Chuẩn kỹ năng CNTT cơ bản (IU01–IU06)",
         "ok": bool(it_ok),
         "detail": "đã có chứng nhận" if it_ok else "chưa khai báo chứng nhận",
         "source": "QĐ 417/QĐ-ĐHBK (2016)"},
    ]
    if thesis_done is not None:
        items.append({"key": "thesis", "label": "Hoàn thành đồ án/khóa luận tốt nghiệp",
                      "ok": bool(thesis_done),
                      "detail": "đã hoàn thành" if thesis_done else "chưa hoàn thành",
                      "source": "Điều 15–16 QĐ 2244/QĐ-ĐHBK"})
    return items


def thesis_eligibility(credits_left: float | None, cpa4: float | None) -> dict:
    """Điều kiện được làm đồ án tốt nghiệp (Điều 15 QĐ 2244/2021)."""
    ok_credits = credits_left is not None and credits_left <= THESIS_MAX_LEFT_CREDITS
    ok_cpa = cpa4 is not None and cpa4 >= THESIS_MIN_CPA
    return {"ok": ok_credits and ok_cpa, "credits_ok": ok_credits, "cpa_ok": ok_cpa,
            "cpa_min": THESIS_MIN_CPA, "max_left": THESIS_MAX_LEFT_CREDITS,
            "source": "Điều 15 QĐ 2244/QĐ-ĐHBK (2021)"}


# --------------------------------------------------------------- văn bản cho AI
def rules_text() -> str:
    """Bản luật rút gọn để nạp vào system prompt của trợ lý AI."""
    return "\n".join([
        "QUY CHẾ ÁP DỤNG (Trường ĐH Bách khoa – ĐH Đà Nẵng):",
        f"- Đăng ký học kỳ chính: tối thiểu {MIN_CREDITS_PER_SEMESTER} TC, tối đa "
        f"{MAX_CREDITS_PER_SEMESTER} TC; sinh viên chưa đạt chuẩn tiếng Anh tối đa "
        f"{MAX_CREDITS_NO_ENGLISH} TC; học kỳ hè tối đa {MAX_CREDITS_SUMMER} TC "
        "(Điều 7 khoản 6 QĐ 2244/2021).",
        f"- Cảnh báo kết quả học tập khi TB học kỳ < {WARN_GPA_FIRST_SEMESTER:.2f} (học kỳ đầu) "
        f"hoặc < {WARN_GPA_NEXT_SEMESTERS:.2f} (các học kỳ sau), hoặc CPA < 1,20 (năm 1), "
        "1,40 (năm 2), 1,60 (năm 3), 1,80 (năm 4 trở đi). Bị cảnh báo 2 lần liên tiếp thì "
        "bị xét buộc thôi học (Điều 12 QĐ 2244/2021).",
        f"- Công nhận/chuyển đổi tín chỉ tối đa {TRANSFER_MAX_RATIO:.0%} khối lượng CTĐT; "
        f"học trực tuyến tối đa {ONLINE_MAX_RATIO:.0%} (Điều 14 QĐ 2244/2021).",
        f"- Đồ án tốt nghiệp: CPA ≥ {THESIS_MIN_CPA:.2f} và còn không quá "
        f"{THESIS_MAX_LEFT_CREDITS} TC (Điều 15 QĐ 2244/2021).",
        f"- Tốt nghiệp: đủ tín chỉ, CPA ≥ {GRAD_MIN_CPA:.2f}/4, có chuẩn ngoại ngữ "
        "(TOEIC ≥ 450 hoặc IELTS ≥ 5.5/TOEFL iBT ≥ 46, QĐ 4511/2022) và chuẩn kỹ năng CNTT "
        "IU01–IU06 (QĐ 417/2016); xét 3 lần/năm (Điều 17 QĐ 2244/2021).",
        f"- Học bổng khuyến khích học tập (QĐ 1414/2021): loại A GPA ≥ 9,00 và rèn luyện ≥ 90 "
        "(150% học phí); loại B ≥ 8,00 và ≥ 80 (120%); loại C ≥ 7,00 và ≥ 65 (100%).",
        "- Liêm chính học thuật (QĐ 029/2017, sửa đổi QĐ 1274/2019): nghiêm cấm bịa đặt số liệu, "
        "gian lận thi cử, đạo văn (dùng ý/số liệu/hình vẽ của người khác không trích dẫn) và giúp "
        "người khác vi phạm.",
        "- Khi tư vấn, nếu có liên quan thì nêu rõ căn cứ (ví dụ: “theo Điều 12 QĐ 2244/QĐ-ĐHBK”).",
    ])


def docs_summary() -> str:
    return "; ".join(f"{d['code']} ({d['year']}) – {d['title']}" for d in DOCS)


# ------------------------------------------------- tra cứu văn bản gốc (RAG nhẹ)
DOC_TITLES = {
    "qd2244_dao_tao.txt": "QĐ 2244/QĐ-ĐHBK (2021) – Quy định đào tạo đại học",
    "qd4511_ngoai_ngu.txt": "QĐ 4511/QĐ-ĐHBK (2022) – Yêu cầu năng lực ngoại ngữ",
    "qd417_cntt.txt": "QĐ 417/QĐ-ĐHBK (2016) – Chuẩn kỹ năng sử dụng CNTT",
    "qd029_liem_chinh.txt": "QĐ 029/QĐ-ĐHBK (2017) – Liêm chính học thuật",
    "qd1414_hoc_bong.txt": "QĐ 1414/QĐ-ĐHBK (2021) – Học bổng khuyến khích học tập",
}


def docs_dir() -> Path:
    """Thư mục chứa bản trích văn bản luật (chạy source và bản exe đều tìm được)."""
    import sys
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for cand in (base / "assets" / "luat", Path(__file__).resolve().parent / "assets" / "luat"):
        if cand.is_dir():
            return cand
    return base / "assets" / "luat"


def _plain(text: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp từ khoá không phân biệt dấu."""
    import unicodedata
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


_CHUNKS: list[tuple[str, str, str]] | None = None


def _doc_chunks() -> list[tuple[str, str, str]]:
    """Các đoạn văn của tất cả văn bản: (tên tệp, tiêu đề, đoạn)."""
    global _CHUNKS
    if _CHUNKS is not None:
        return _CHUNKS
    out: list[tuple[str, str, str]] = []
    folder = docs_dir()
    for path in sorted(folder.glob("*.txt")):
        if path.name.startswith("00_"):
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        title = DOC_TITLES.get(path.name, path.stem)
        para: list[str] = []
        for line in raw.splitlines() + [""]:
            if line.strip():
                para.append(line.strip())
                continue
            if para:
                body = " ".join(para)
                if len(body) >= 60:
                    out.append((path.name, title, body))
                para = []
    _CHUNKS = out
    return out


def doc_snippets(query: str, limit: int = 3, max_chars: int = 560) -> str:
    """Tìm các đoạn văn bản luật liên quan nhất tới câu hỏi (để AI trích dẫn)."""
    q = _plain(query or "")
    STOP = {"cua", "ban", "cho", "the", "nao", "nhu", "khi", "thi", "neu", "voi", "nhung",
            "duoc", "khong", "trong", "mot", "cac", "nay", "do", "ra", "va", "hoac", "bi", "se",
            "bao", "nhieu", "lam", "sao", "gi", "co", "la", "ma", "de", "den", "tu"}
    tokens = [t for t in q.replace("?", " ").replace(",", " ").replace(".", " ").split()
              if len(t) >= 3 and t not in STOP]
    if not tokens:
        return ""

    chunks = _doc_chunks()
    # Trọng số theo độ hiếm: từ xuất hiện ở mọi văn bản ("học", "sinh viên") gần như bỏ qua.
    df: dict[str, int] = {}
    for _, _, body in chunks:
        low = _plain(body)
        for t in set(tokens):
            if t in low:
                df[t] = df.get(t, 0) + 1
    n_doc = max(1, len({c[0] for c in chunks}))
    weight = {t: 1.0 + (n_doc / max(1, df.get(t, 0))) for t in set(tokens)}

    # Từ khoá chủ đề → đúng văn bản cần tra (tránh trả lầm sang quyết định khác).
    TOPIC = {
        "qd4511_ngoai_ngu.txt": ("toeic", "ielts", "toefl", "ngoai ngu", "tieng anh", "chung chi"),
        "qd417_cntt.txt": ("iu0", "cntt", "cong nghe thong tin", "ky nang cntt", "mo dun"),
        "qd029_liem_chinh.txt": ("dao van", "liem chinh", "gian lan", "bia dat", "chep bai", "copy"),
        "qd1414_hoc_bong.txt": ("hoc bong", "khen thuong", "ren luyen", "loai a", "loai b"),
        "qd2244_dao_tao.txt": ("canh bao", "thoi hoc", "tin chi", "dang ky", "tot nghiep",
                               "cpa", "do an", "tien quyet", "hoc ky", "diem trung binh"),
    }

    grams = [" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)]   # cụm 2 từ
    scored: list[tuple[float, str, str, str]] = []
    for fname, title, body in chunks:
        low = _plain(body)
        # Đếm tối đa 2 lần/từ: đoạn lặp một từ không được lấn át đoạn đúng chủ đề.
        score = sum(min(low.count(t), 2) * weight[t] for t in tokens)
        for g in grams:                       # khớp cụm từ (vd "dao van") quan trọng hơn khớp rời
            if g in low:
                score += 10.0
        heading = low[:48]                    # tiêu đề mục ("c) Đạo văn: …") rất đúng chủ đề
        score += 8.0 * sum(1 for t in tokens if t in heading)
        if q.strip() and q.strip() in low:
            score += 6.0
        for kw in TOPIC.get(fname, ()):
            if kw in q:
                score += 2.5
        if score <= 0:
            continue
        scored.append((score, fname, title, body))
    if not scored:
        return ""
    scored.sort(key=lambda x: -x[0])
    # Mỗi văn bản chỉ lấy ĐOẠN KHỚP NHẤT (không lấy đoạn đầu trang), rồi mới cắt theo limit.
    top = scored[0][0]
    best: dict[str, tuple[float, str, str]] = {}
    for score, fname, title, body in scored:
        if score < top * 0.5:                 # bỏ văn bản chỉ khớp lỏng lẻo
            continue
        if fname not in best or score > best[fname][0]:
            best[fname] = (score, title, body)
    out: list[str] = []
    for score, title, body in sorted(best.values(), key=lambda x: -x[0])[:limit]:
        text = body if len(body) <= max_chars else body[:max_chars].rsplit(" ", 1)[0] + "…"
        out.append(f"[{title}]\n{text}")
    return "\n\n".join(out)
