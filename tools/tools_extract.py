import docx, json, re
d = docx.Document('/home/ubuntu/attachments/963ac5fd-6872-4662-8c6e-bb5da99314a6/TomTat_hocPhan_2.docx')
def clean(s): return re.sub(r'\s+', ' ', s.replace('\n', ' ')).strip()
descs = [clean(r.cells[2].text) for r in d.tables[3].rows[1:]]
t = d.tables[4]
sem = 0; courses = []; elective = False
for r in t.rows[2:]:
    c = [clean(x.text) for x in r.cells]
    name = c[1]
    m = re.match(r'HỌC KỲ (\d+)', name)
    if m: sem = int(m.group(1)); elective = False; continue
    if name.startswith('Tự chọn'): elective = True; continue
    courses.append(dict(semester=sem, name=name, credits=float(c[7]), lt=c[2], da=c[3], pbl=c[4], th=c[5], tt=c[6],
                        tienquyet=c[8], hoctruoc=c[9], songhanh=c[10], elective=elective))
assert len(courses) == len(descs), (len(courses), len(descs))
for co, de in zip(courses, descs): co['desc'] = de
json.dump(courses, open('/tmp/raw.json', 'w'), ensure_ascii=False, indent=1)
for i, co in enumerate(courses): print(i, co['semester'], co['name'], co['credits'], '|', co['tienquyet'], '|', co['hoctruoc'], '|', co['songhanh'], 'E' if co['elective'] else '')
print(sum(c['credits'] for c in courses if not c['elective']))
