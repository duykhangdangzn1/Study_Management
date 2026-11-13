import json, re, unicodedata, pprint
raw = json.load(open('/tmp/raw.json'))
def norm(s):
    s = unicodedata.normalize('NFC', s).lower().replace('thuỷ', 'thủy')
    return re.sub(r'\s+', ' ', s).strip()
ALIAS = {
    'kc btct - phần cơ bản': 'kết cấu bê tông cốt thép - phần cơ bản',
    'kết cấu nhà btct': 'kết cấu nhà bê tông cốt thép',
    'ứng dụng xs và tk trong xây dựng': 'ứng dụng xác suất và thống kê trong xây dựng',
    'thủy lực': 'thủy lực',
}
names = {norm(c['name']): i + 1 for i, c in enumerate(raw)}
def resolve(text):
    if not text: return []
    if text.startswith('Tất cả'): return ['ALL']
    out = []
    for part in re.split(r'[;,]', text):
        k = ALIAS.get(norm(part), norm(part))
        if k not in names: raise SystemExit('UNRESOLVED: %r in %r' % (part, text))
        out.append(names[k])
    return out
courses = []
for i, c in enumerate(raw):
    courses.append(dict(id=i + 1, semester=c['semester'], name=c['name'].replace('Cơ lý thuyết ', 'Cơ lý thuyết').strip(),
        credits=c['credits'], elective=c['elective'],
        prereq=resolve(c['tienquyet']) + resolve(c['hoctruoc']), coreq=resolve(c['songhanh']),
        prereq_text=c['hoctruoc'] or c['tienquyet'], coreq_text=c['songhanh'],
        hours=dict(lt=c['lt'], da=c['da'], pbl=c['pbl'], th=c['th'], tt=c['tt']), desc=c['desc']))
with open('app/courses_data.py', 'w') as f:
    f.write('"""Du lieu hoc phan nganh Tin hoc Xay dung (trich tu TomTat_hocPhan.docx)."""\n\n')
    f.write('PROGRAM = ' + pprint.pformat(dict(name='TIN HỌC XÂY DỰNG', name_en='CONSTRUCTION INFORMATICS', major='KỸ THUẬT XÂY DỰNG', code='7580201', faculty='KHOA XÂY DỰNG', total_credits=156, semesters=9, elective_required=2), width=120) + '\n\n')
    f.write('COURSES = ' + pprint.pformat(courses, width=120, sort_dicts=False) + '\n')
for c in courses: print(c['id'], c['name'], c['prereq'], c['coreq'])
