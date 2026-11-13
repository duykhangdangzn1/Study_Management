import sys, pathlib, tempfile
sys.path.insert(0, "app")
import core
from core import COURSES, GradeBook
from ai_engine import LocalAnalytics

tmp = pathlib.Path(tempfile.mkdtemp())
gb = GradeBook(tmp/"g3.json")
an = LocalAnalytics(gb)
pc = {c["id"]: len(gb.dependents(c["id"])) for c in COURSES if "ALL" not in c["prereq"]}
multi = sorted([k for k,v in pc.items() if v>=2], key=lambda k: -pc[k])[:5]
print("top multi-unlock:", [(k, core.COURSE_BY_ID[k]["name"], pc[k], core.COURSE_BY_ID[k]["prereq"]) for k in multi])
target = multi[0]
c = core.COURSE_BY_ID[target]
print("target:", target, c["name"], "prereq:", c["prereq"], "sem:", c["semester"])
print("prereq_ids:", gb.prereq_ids(target))
for p in gb.prereq_ids(target):
    if p not in gb.grades:
        r = gb.save(p, 8,8,8)
        print("  save prereq", p, core.COURSE_BY_ID[p]["name"], r.ok, r.problems)
r = gb.save(target, 3,3,3)
print("save target:", r.ok, r.problems)
print("result:", gb.result(target))
rep = LocalAnalytics(gb).report()
print("failed:", [(f["id"],f["name"]) for f in rep.failed])
print("retake:", [(p.cid,p.name,p.suggest_when) for p in rep.retake_plan])
