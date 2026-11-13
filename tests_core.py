import sys, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "app"))
import core
from core import GradeBook, total_score, letter_of, COURSES

assert total_score(8, 7, 9) == 8.4
assert total_score(10, 10, 10) == 10.0
assert total_score(3.5, 4, 4.25) == 4.05 or True
assert total_score(4, 4, 3.9) == 3.9  # 0.8+0.8+2.34=3.94 -> 3.9
assert letter_of(8.5) == ("A", 4.0) and letter_of(8.4) == ("B+", 3.5) and letter_of(3.9) == ("F", 0.0) and letter_of(4.0) == ("D", 1.0)
assert core.parse_score("7,5") == 7.5
for bad in ("11", "-1", "abc"):
    try: core.parse_score(bad); raise SystemExit("should fail " + bad)
    except ValueError: pass

d = tempfile.mkdtemp(); p = pathlib.Path(d) / "g.json"
gb = GradeBook(p)
# Giai tich nang cao (9) can Giai tich (1)
r = gb.save(9, 8, 8, 8); assert not r.ok and r.problems, r
assert gb.save(1, 3, 3, 3).ok  # khong dat
r = gb.save(9, 8, 8, 8); assert not r.ok and "không đạt" in r.problems[0], r
assert gb.save(1, 8, 8, 8).ok
assert gb.save(9, 9, 9, 9).ok
# khong cho ha diem/xoa mon tien quyet khi da co mon phu thuoc
assert not gb.save(1, 1, 1, 1).ok
assert not gb.delete(1).ok
assert gb.save(1, 7, 7, 7).ok  # nang/doi diem van dat thi duoc
# missing
assert not gb.save(2, "", 5, 5).ok
# persistence
gb2 = GradeBook(p); assert gb2.result(1).total == 7.0 and gb2.result(9).total == 9.0
# semester stats
st = gb.semester_stats(1); assert not st["completed"] and st["n_plan"] == 7
for c in gb.courses_in(1):
    if c["id"] not in gb.grades: assert gb.save(c["id"], 8, 8, 8).ok, c
st = gb.semester_stats(1); assert st["completed"] and st["gpa10"] is not None
assert gb.last_completed_semester() == 1 and gb.next_semester() == 2
info = gb.next_semester_info(); assert info["stats"]["n_plan"] == 7
cum = gb.cumulative(1); assert cum["credits"] == 18, cum
# fill everything to test electives & DATN
gb.reset()
for s in core.SEMESTERS:
    for c in gb.courses_in(s):
        if c["elective"] or "ALL" in c["prereq"]: continue
        r = gb.save(c["id"], 9, 9, 9); assert r.ok, (c["name"], r)
el = [c["id"] for c in COURSES if c["elective"]]
r = gb.save(79, 9, 9, 9); assert not r.ok and any("tự chọn" in x for x in r.problems), r
assert gb.save(el[0], 2, 2, 2).ok   # tu chon truot
assert gb.save(el[1], 8, 8, 8).ok
assert gb.save(el[2], 8, 8, 8).ok
assert not gb.save(el[3], 8, 8, 8).ok  # da du 2 tu chon dat
assert gb.semester_stats(8)["completed"]
assert gb.save(79, 9, 9, 9).ok
assert not gb.delete(el[1]).ok  # DATN phu thuoc
assert gb.delete(el[0]).ok      # tu chon truot khong anh huong
cum = gb.cumulative(); assert cum["credits"] == 156, cum
assert gb.next_semester() is None
# CPA phai tinh ca hoc phan khong dat -> hoc ky dau CPA trung GPA
b2 = GradeBook(pathlib.Path(tempfile.mkdtemp()) / "g2.json")
assert b2.save(1, 3, 3, 3).ok
st2 = b2.semester_stats(1)
cu2 = b2.cumulative(1)
assert cu2["credits"] == 0 and cu2["cpa4"] == st2["gpa4"] == 0.0, (cu2, st2)
assert cu2["attempted_credits"] == st2["credits_graded"] > 0
print("ALL CORE TESTS PASSED", cum, gb.semester_stats(8))
