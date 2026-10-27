#!/usr/bin/env python3
"""Build the cigblu hub (cigblu/**/index.html) from pages.json.

Edit pages.json (or redirects-old-site.json), then run:
    python3 _src/cigblu/build.py
Only index.html files are written; other files in page folders (images, drafts) are left alone.
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HUB, 'cigblu')
DATA = json.load(open(os.path.join(HERE, 'pages.json')))
OLD = json.load(open(os.path.join(HERE, 'redirects-old-site.json')))
PAGES = DATA['pages']
BY_ID = {p['id']: p for p in PAGES}
CHECKED = DATA['checked']
LIVE = DATA['live_host']

PRI = {'P0': ('P0', 'ต้องแก้ก่อนเปิดตัว', 'high'), 'P1': ('P1', 'แก้ก่อนโปรโมต', 'med'), 'P2': ('P2', 'ปรับปรุงทีหลังได้', 'low')}
ST = {'wip-it': 'IT กำลังทำ', 'it': 'รอ IT', 'mkt': 'รอ MKT', 'sales': 'รอ Sales', 'eng': 'รอ Eng/QA', 'test': 'รอทดสอบ', 'done': 'เสร็จบนเว็บจริง'}


def esc(s):
    return html.escape(s or '', quote=True)


def rich(s):
    """Escape, then turn `code` into <code>."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', esc(s)).replace('\n', '<br>')


def st_label(st):
    if st.startswith('decide:'):
        return 'รอตัดสินใจ: ' + st.split(':', 1)[1], 'hold'
    return ST.get(st, st), ('ok' if st in ('done', 'wip-it') else 'wait')


def depth(pid):
    return pid.count('/') + 1


def rel(from_id, to_id):
    """Relative link from page from_id (None = cigblu/index.html) to page to_id's index.html."""
    up = '../' * (depth(from_id) if from_id else 0)
    return up + (to_id + '/' if to_id else '') + 'index.html'


def root(from_id):
    return '../' * (depth(from_id) if from_id else 0)


# ---------- derived items ----------
def items_of(p):
    items = list(p.get('items', []))
    live, target = p.get('live'), p.get('target')
    if p.get('built') and live and target and live != target and '<' not in target:
        dupes = p.get('dupes', [])
        if dupes:
            items.insert(0, dict(p='P1', who='IT', st='it',
                t='หน้านี้มี 2 URL ที่เป็นสินค้าเดียวกัน (Google เห็นเป็นหน้าซ้ำ): %s และ %s' % (live, ', '.join(dupes)),
                do='รวมเป็นหน้าเดียวที่ `%s` · ย้ายเนื้อหาการตลาดที่ดีจากหน้า /products/… เข้ามา · redirect 308 จากทั้ง %s · ลบ URL เก่าออกจาก sitemap' % (target, ', '.join([live] + dupes)),
                done='เปิด URL เก่าทั้ง %d อันแล้วไปที่ %s' % (1 + len(dupes), target)))
        else:
            items.insert(0, dict(p='P1', who='IT', st='it',
                t='URL ยังไม่ตรงกับที่ตกลง (ดูหน้า "แผนที่ URL")',
                do='เปลี่ยน URL เป็น `%s` และตั้ง redirect 308 จาก `%s`' % (target, live),
                done='เปิด %s แล้วไปที่ %s' % (live, target)))
    order = {'P0': 0, 'P1': 1, 'P2': 2}
    return sorted(items, key=lambda i: order[i['p']])


def open_items(p, pris=('P0', 'P1')):
    return [i for i in items_of(p) if i['st'] != 'done' and i['p'] in pris]


def page_status(p):
    if not p.get('built'):
        return 'ยังไม่มีหน้า', 'st-todo'
    p0, p1 = len(open_items(p, ('P0',))), len(open_items(p, ('P1',)))
    if p0:
        return 'ต้องแก้ก่อนเปิดตัว', 'st-confirm'
    if p1:
        return 'รอแก้ %d จุด' % p1, 'st-wip'
    return 'ใช้ได้', 'st-live'


def children(pid):
    return [p for p in PAGES if p.get('parent') == pid]


def owner_badge(o):
    cls = {'IT': 'owner-it', 'MKT': 'owner-cpk'}.get(o, 'owner-itcpk')
    return '<span class="badge %s">%s</span>' % (cls, esc(o))


def url_html(path, link=True):
    if not path:
        return '<span class="muted">—</span>'
    if path.startswith('http'):
        return '<a class="url" href="%s" target="_blank" rel="noopener">%s ↗</a>' % (esc(path), esc(path))
    if link and '<' not in path:
        return '<a class="url" href="%s%s" target="_blank" rel="noopener">%s ↗</a>' % (esc(LIVE), esc(path), esc(path))
    return '<span class="url">%s</span>' % esc(path)


def file_btn(f, from_id, owner_id=None):
    href = f['href']
    if '{root}' in href:
        href = href.replace('{root}', root(from_id))
    elif owner_id and owner_id != from_id and not href.startswith('http'):
        href = root(from_id) + owner_id + '/' + href
    if f.get('kind') == 'private':
        return '<a class="dl private" href="%s" target="_blank" rel="noopener">🔒 %s</a>' % (esc(href), esc(f['label']))
    return '<a class="dl" href="%s" download>⬇ %s</a>' % (esc(href), esc(f['label'])) if not href.endswith('.html') else \
           '<a class="dl" href="%s">📄 %s</a>' % (esc(href), esc(f['label']))


def head(title, from_id):
    return ('<!doctype html>\n<html lang="th">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="noindex, nofollow">\n<title>%s · CIG Web Hub</title>\n'
            '<link rel="stylesheet" href="%s../assets/hub.css">\n</head>\n<body class="cb">\n') % (esc(title), root(from_id))


def topbar(from_id, crumbs):
    parts = ['<a class="home-link" href="%s">← Dashboard</a>' % rel(from_id, None)]
    for cid in crumbs:
        parts.append('<a class="crumb" href="%s">%s</a>' % (rel(from_id, cid), esc(BY_ID[cid]['title'])))
    return '<div class="topbar">%s</div>\n' % ' › '.join(parts)


LEGEND = ('<p class="legend"><b>P0</b> ต้องแก้ก่อนเปิดตัว/ก่อนรับ lead · <b>P1</b> แก้ก่อนโปรโมตวงกว้าง · '
          '<b>P2</b> ปรับปรุงทีหลังได้ — แต่ละข้อบอก <b>ใครทำ</b> · <b>ทำอะไร</b> · <b>ไฟล์</b> · <b>เสร็จเมื่อไร</b></p>')


def card(i, from_id, show_page=None):
    code, label, cls = PRI[i['p']]
    sl, scls = st_label(i['st'])
    out = ['<div class="ci %s">' % cls,
           '<div class="ci-top"><span class="sev %s">%s · %s</span><span class="who">ใครทำ: %s</span><span class="stt %s">%s</span></div>' % (cls, code, label, esc(i['who']), scls, esc(sl))]
    if show_page:
        out.append('<p class="ci-page"><a href="%s">%s</a></p>' % (rel(from_id, show_page), esc(BY_ID[show_page]['title'])))
    out.append('<div class="ci-title">%s</div>' % rich(i['t']))
    out.append('<p><b>ทำ:</b> %s</p>' % rich(i['do']))
    if i.get('where'):
        out.append('<p><b>ที่:</b> %s</p>' % rich(i['where']))
    if i.get('files'):
        out.append('<p class="files"><b>ไฟล์:</b> %s</p>' % ' '.join(file_btn(f, from_id, show_page or from_id) for f in i['files']))
    out.append('<p class="done-when"><b>เสร็จเมื่อ:</b> %s</p>' % rich(i['done']))
    if i.get('why'):
        out.append('<p class="why">ทำไม: %s</p>' % rich(i['why']))
    out.append('</div>')
    return '\n'.join(out)


def page_html(p):
    pid = p['id']
    crumbs = []
    c = p.get('parent')
    while c:
        crumbs.insert(0, c)
        c = BY_ID[c].get('parent')
    sl, scls = page_status(p)
    o = [head(p['title'], pid), topbar(pid, crumbs), '<main class="wrap">\n<div class="hero">']
    o.append('<div class="hero-badges">%s<span class="pill %s">%s</span></div>' % (owner_badge(p.get('owner', '')), scls, esc(sl)))
    o.append('<h1>%s</h1>' % esc(p['title']))
    live, target = p.get('live'), p.get('target')
    if p.get('kind') != 'site':
        rows = []
        if p.get('external'):
            rows.append('ตอนนี้ลิงก์ออก: ' + url_html(p['external']))
        rows.append('URL ตอนนี้: ' + (url_html(live) if live else '<span class="muted">ยังไม่มีหน้าบนเว็บ</span>'))
        if target != live:
            rows.append('URL ที่ตกลง: ' + (url_html(target, link=False) if target else '<span class="muted">รอตั้งชื่อ</span>'))
        o.append('<p class="hero-urls">%s</p>' % '<br>'.join(rows))
    if p.get('desc'):
        o.append('<p class="hero-note">%s</p>' % esc(p['desc']))
    o.append('</div>')

    items = items_of(p)
    o.append('<section class="block"><h2><span class="num">1</span> ต้องทำอะไร <span class="hint">เช็คเว็บจริง %s</span></h2>' % CHECKED)
    if items:
        o.append(LEGEND)
        o.extend(card(i, pid) for i in items)
    else:
        o.append('<p class="empty">ไม่มีงานค้างในหน้านี้</p>')
    for n in p.get('note_items', []):
        o.append('<p class="see-also">↪ %s</p>' % rich(n))
    o.append('</section>')
    doc = os.path.join(HERE, 'docs', pid + '.html')
    if os.path.exists(doc):
        o.append(open(doc).read())

    files = [f for i in items for f in i.get('files', [])] + p.get('files', [])
    refs = p.get('refs', [])
    if files or refs:
        o.append('<section class="block"><h2><span class="num">2</span> ไฟล์และลิงก์</h2>')
        if files:
            o.append('<p>%s</p>' % ' '.join(file_btn(f, pid) for f in files))
        if refs:
            o.append('<ul class="refs">%s</ul>' % ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (esc(r['href']), esc(r['label'])) for r in refs))
        if any(f.get('kind') == 'private' for f in files) or any('github.com/tikittisak/cib-website' in r['href'] for r in refs):
            o.append('<p class="small muted">🔒 = อยู่ใน repo private (cib-website) เปิดได้เฉพาะคนที่มีสิทธิ์ — ขอสิทธิ์จาก Ti</p>')
        o.append('</section>')

    if p.get('fixed'):
        o.append('<section class="block"><h2><span class="num">✓</span> เสร็จแล้ว <span class="hint">ยืนยันบนเว็บจริง %s</span></h2><ul class="refs">%s</ul></section>'
                 % (CHECKED, ''.join('<li>%s</li>' % rich(f) for f in p['fixed'])))

    kids = children(pid)
    if kids:
        o.append('<section class="block"><h2><span class="num">↓</span> หน้าย่อย</h2><table class="kv">')
        for k in kids:
            ksl, kcls = page_status(k)
            o.append('<tr><td><a href="%s">%s</a></td><td><span class="pill %s">%s</span></td></tr>' % (rel(pid, k['id']), esc(k['title']), kcls, esc(ksl)))
        o.append('</table></section>')
    o.append('<footer class="scaffold-foot">เช็คเว็บจริงล่าสุด %s · ข้อมูลหน้านี้มาจาก <code>_src/cigblu/pages.json</code></footer>\n</main>\n</body></html>\n' % CHECKED)
    return '\n'.join(o)


# ---------- dashboard ----------
def dashboard():
    built = [p for p in PAGES if p['kind'] != 'site']
    counts = {}
    for p in built:
        counts[page_status(p)[1]] = counts.get(page_status(p)[1], 0) + 1
    all_open = [(p, i) for p in PAGES for i in items_of(p) if i['st'] != 'done']
    n0 = sum(1 for _, i in all_open if i['p'] == 'P0')
    n1 = sum(1 for _, i in all_open if i['p'] == 'P1')
    n2 = sum(1 for _, i in all_open if i['p'] == 'P2')
    o = [head('Dashboard', None), '<main class="wrap dash cb">', '<div class="hero big">',
         '<div class="hero-badges"><span class="badge tagline">web hub · cigblu.com</span></div>',
         '<h1>CIG BluSolutions — Web Hub</h1>',
         '<p class="hero-note">ที่เดียวสำหรับ IT · MKT · Eng/QA · Sales — แต่ละหน้าเว็บ <strong>ต้องทำอะไร · ใช้ไฟล์ไหน · ใครทำ · เสร็จเมื่อไร</strong></p>',
         '<p class="hero-sub">เช็คเว็บจริงล่าสุด %s ที่ web.cigblusolutions.com (เว็บทดสอบ) → จะย้ายไป www.cigblu.com · รวมผลจากรายงานทบทวนเว็บ 26 ต.ค. 2569</p>' % CHECKED,
         '</div>']
    o.append('<div class="launch"><h2>พร้อมเปิดตัวหรือยัง? <span class="pill st-confirm">ยังไม่พร้อม</span></h2>'
             '<p>ยังมี <b>P0 ค้าง %d ข้อ</b> — ต้องปิดทุกข้อ แล้วให้ 4 ฝ่ายอนุมัติร่วมกัน</p>' % n0 if n0 else
             '<div class="launch"><h2>พร้อมเปิดตัวหรือยัง? <span class="pill st-wip">รออนุมัติ</span></h2><p>P0 ปิดครบแล้ว — รอ 4 ฝ่ายอนุมัติ</p>')
    o.append('<p><a class="dl" href="todo/index.html">📋 งานที่ต้องทำทั้งหมด (แยกตามคนทำ)</a> <a class="dl" href="url-map/index.html">🔗 แผนที่ URL + redirect</a> <a class="dl" href="site-wide/index.html">🌐 งานทั้งเว็บ</a> <a class="dl" href="navigation/index.html">🧭 เมนูเว็บ (mapping + design)</a> <a class="dl" href="guide-it/index.html">🛠 คู่มือ IT: ทดสอบ + SEO/AI crawler</a></p>')
    o.append('<table class="kv signoff"><tr><td>MKT</td><td>ยังไม่อนุมัติ</td></tr><tr><td>IT</td><td>ยังไม่อนุมัติ</td></tr>'
             '<tr><td>Engineering / QA</td><td>ยังไม่อนุมัติ</td></tr><tr><td>Sales</td><td>ยังไม่อนุมัติ</td></tr></table></div>')
    o.append('<div class="stats">'
             '<div class="stat"><b>%d</b><span>หน้าทั้งหมด</span></div>' % len(built) +
             '<div class="stat"><b>%d</b><span>🔴 ต้องแก้ก่อนเปิดตัว</span></div>' % counts.get('st-confirm', 0) +
             '<div class="stat"><b>%d</b><span>🟡 รอแก้</span></div>' % counts.get('st-wip', 0) +
             '<div class="stat"><b>%d</b><span>🟢 ใช้ได้</span></div>' % counts.get('st-live', 0) +
             '<div class="stat"><b>%d</b><span>⚪ ยังไม่มีหน้า</span></div>' % counts.get('st-todo', 0) +
             '<div class="stat"><b>%d / %d / %d</b><span>งานค้าง P0 / P1 / P2</span></div>' % (n0, n1, n2) +
             '</div>')
    o.append('<p class="legend">สถานะหน้า: 🔴 มี P0 ค้าง · 🟡 มี P1 ค้าง · 🟢 ไม่มี P0/P1 ค้าง (อาจเหลือ P2) · ⚪ ยังไม่มีหน้าบนเว็บ — คอลัมน์ "ค้าง" นับเฉพาะ P0 + P1</p>')
    o.append('<table class="board"><thead><tr><th>#</th><th>หน้า</th><th>URL ตอนนี้ → ที่ตกลง</th><th>เจ้าของ</th><th>สถานะ</th><th>ค้าง</th></tr></thead><tbody>')
    order = [p['id'] for p in PAGES if p['kind'] == 'site'] + [p['id'] for p in PAGES if p['kind'] != 'site']
    for n, pid in enumerate(order, 1):
        p = BY_ID[pid]
        sl, scls = page_status(p) if p['kind'] != 'site' else (('ต้องแก้ก่อนเปิดตัว', 'st-confirm') if open_items(p, ('P0',)) else ('รอแก้', 'st-wip'))
        lvl = pid.count('/') - (1 if pid.startswith('products/') and pid != 'products/catalog' else 0)
        lvl = 0 if not p.get('parent') else (2 if BY_ID[p['parent']].get('parent') else 1)
        live, target = p.get('live'), p.get('target')
        if p.get('external') and not live:
            u = url_html(p['external'])
        else:
            u = url_html(live) if live else '<span class="muted">ยังไม่มี</span>'
        if p['kind'] != 'site' and target != live:
            u += '<br><span class="to">→ %s</span>' % (esc(target) if target else 'รอตั้งชื่อ')
        if p['kind'] == 'site':
            u = '<span class="muted">%s</span>' % esc(p.get('summary', 'โดเมน, server, URL, อีเมล, ทดสอบ'))
        cnt = len(open_items(p))
        o.append('<tr class="lvl%d%s" onclick="location.href=\'%s\'"><td class="num">%d</td><td class="tt">%s<a href="%s">%s</a></td><td>%s</td><td>%s</td><td><span class="pill %s">%s</span></td><td class="cnt">%s</td></tr>'
                 % (lvl, ' sitewide' if p['kind'] == 'site' else '', rel(None, pid), n, '· ' * lvl, rel(None, pid), esc(p['title']),
                    u.replace('<a ', '<a onclick="event.stopPropagation()" '), owner_badge(p.get('owner', '')), scls, esc(sl), cnt or ''))
    o.append('</tbody></table>')
    o.append('<footer class="scaffold-foot">%d หน้า · เช็คเว็บจริง %s · แก้ข้อมูลที่ <code>_src/cigblu/pages.json</code> แล้วรัน <code>python3 _src/cigblu/build.py</code></footer>\n</main>\n</body></html>\n' % (len(built), CHECKED))
    return '\n'.join(o)


# ---------- todo ----------
WHO_TAGS = ['IT', 'MKT', 'Sales', 'Eng/QA', 'Ti']


def todo():
    rows = [(p, i) for p in PAGES for i in items_of(p) if i['st'] != 'done']
    o = [head('งานที่ต้องทำ', 'todo'), topbar('todo', []), '<main class="wrap">', '<div class="hero">',
         '<h1>งานที่ต้องทำทั้งหมด</h1>',
         '<p class="hero-note">ทุกข้อที่ยังไม่เสร็จจากทุกหน้า เรียง P0 → P1 → P2 · กดปุ่มด้านล่างเพื่อดูเฉพาะงานของฝ่ายตัวเอง</p></div>',
         '<div class="filters" id="f"><button data-w="" class="on">ทั้งหมด (%d)</button>' % len(rows)]
    for w in WHO_TAGS:
        n = sum(1 for _, i in rows if w in i['who'] or (w == 'Ti' and 'decide:Ti' in i['st']) or (w != 'Ti' and i['who'] == 'ทุกฝ่าย'))
        o.append('<button data-w="%s">%s (%d)</button>' % (w, w, n))
    o.append('</div>')
    for pri in ('P0', 'P1', 'P2'):
        sel = [(p, i) for p, i in rows if i['p'] == pri]
        o.append('<section class="block"><h2><span class="num">%s</span> %s <span class="hint">%d ข้อ</span></h2>' % (pri, PRI[pri][1], len(sel)))
        for p, i in sel:
            tags = ' '.join(w for w in WHO_TAGS if w in i['who'] or (w == 'Ti' and 'decide:Ti' in i['st']) or i['who'] == 'ทุกฝ่าย')
            o.append('<div class="todo-row" data-who="%s">%s</div>' % (esc(tags), card(i, 'todo', show_page=p['id'])))
        o.append('</section>')
    o.append('''<script>
document.getElementById('f').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
document.querySelectorAll('#f button').forEach(function(x){x.classList.toggle('on',x===b)});var w=b.dataset.w;
document.querySelectorAll('.todo-row').forEach(function(r){r.style.display=!w||r.dataset.who.split(' ').indexOf(w)>=0?'':'none'})});
</script>''')
    o.append('<footer class="scaffold-foot">เช็คเว็บจริง %s</footer>\n</main>\n</body></html>\n' % CHECKED)
    return '\n'.join(o)


# ---------- url map ----------
def url_map():
    o = [head('แผนที่ URL', 'url-map'), topbar('url-map', []), '<main class="wrap">', '<div class="hero">',
         '<h1>แผนที่ URL + redirect</h1>',
         '<p class="hero-note">URL ที่ตกลงแล้ว (Ti อนุมัติ 2026-10-27) เน้น SEO และ AI crawler — เปลี่ยนก่อนย้ายไป www.cigblu.com จะถูกที่สุด เพราะยังไม่มีใครลิงก์มาที่เว็บทดสอบ</p></div>',
         '<section class="block"><h2><span class="num">1</span> กติกา URL</h2><ol class="refs">'
         '<li>ตัวพิมพ์เล็กทั้งหมด คั่นคำด้วย <code>-</code> ไม่มี .html ไม่มี / ท้าย</li>'
         '<li>โครงสร้าง <code>/products/&lt;family&gt;/&lt;รุ่น&gt;</code> ลึกไม่เกิน 3 ชั้น — URL บอกได้ว่าสินค้าอยู่กลุ่มไหน</li>'
         '<li>ใช้คำที่ลูกค้า/วิศวกรค้นหาจริง ขึ้นต้นด้วยประเภทสินค้า เช่น <code>air-cooled-condenser-ec-fan</code></li>'
         '<li>ไม่ใช้รหัสภายใน (ACC, CU-SH) ปี หรือคำแคมเปญ</li>'
         '<li>1 หน้า = 1 URL: canonical ชี้ตัวเอง, อยู่ใน sitemap ครั้งเดียว, BreadcrumbList ตรงกับ path, llms.txt ใช้ URL เดียวกัน</li>'
         '<li>URL เก่าทุกอัน redirect แบบ 308/301 ไปหน้าที่ใกล้ที่สุด — ไม่โยนไปหน้าแรกทั้งหมด</li></ol></section>',
         '<section class="block"><h2><span class="num">2</span> URL เว็บทดสอบ → URL ที่ตกลง <span class="hint">IT ทำก่อน cutover</span></h2>',
         '<table class="mini"><tr><td>หน้า</td><td>URL ตอนนี้</td><td>URL ที่ตกลง</td></tr>']
    for p in PAGES:
        if p['kind'] == 'site' or not (p.get('live') or p.get('target')):
            continue
        live, target = p.get('live') or '—', p.get('target') or 'รอ MKT ตั้งชื่อ'
        lives = [live] + p.get('dupes', [])
        changed = live != (p.get('target') or '')
        o.append('<tr><td><a href="../%s/index.html">%s</a></td><td><code>%s</code></td><td>%s</td></tr>'
                 % (p['id'], esc(p['title']), '</code><br><code>'.join(esc(x) for x in lives),
                    ('<b><code>%s</code></b>' % esc(target)) if changed else '<span class="muted">ไม่เปลี่ยน</span>'))
    o.append('</table><p class="small muted">URL ที่มีตัวพิมพ์ใหญ่ทุกอัน → redirect ไปตัวพิมพ์เล็ก (กฎเดียว)</p></section>')
    o.append('<section class="block" id="old-site"><h2><span class="num">3</span> URL เว็บเก่า (cigblusolutions.com) → เว็บใหม่ <span class="hint">IT ตั้งวัน cutover</span></h2>'
             '<p>URL เหล่านี้มี backlink และอันดับ Google อยู่แล้ว ถ้าไม่ redirect จะเสียทั้งหมด</p><table class="mini"><tr><td>URL เก่า</td><td>→ URL ใหม่</td></tr>')
    for a, b in OLD['rows']:
        o.append('<tr><td><code>%s</code></td><td>%s</td></tr>' % (esc(a), esc(b)))
    o.append('</table></section>')
    o.append('<section class="block"><h2><span class="num">4</span> โดเมน</h2><ul class="refs">'
             '<li>ตอนนี้: web.cigblusolutions.com ต้องตอบ <code>X-Robots-Tag: noindex</code> ทุกหน้า</li>'
             '<li>วัน cutover: <code>web.cigblusolutions.com/*</code> → <code>https://www.cigblu.com/*</code> (path เดิม)</li>'
             '<li><code>cigblu.com</code> และ <code>http://</code> → <code>https://www.cigblu.com</code></li></ul></section>')
    o.append('<footer class="scaffold-foot">ข้อมูลจาก <code>_src/cigblu/pages.json</code> + <code>redirects-old-site.json</code> · เช็ค %s</footer>\n</main>\n</body></html>\n' % CHECKED)
    return '\n'.join(o)


def doc_page(name):
    src = open(os.path.join(HERE, 'docs', name + '.html')).read()
    title = re.search(r'<!-- title: (.*?) -->', src).group(1)
    note = re.search(r'<!-- note: (.*?) -->', src).group(1)
    return (head(title, name) + topbar(name, []) + '<main class="wrap">\n<div class="hero"><h1>%s</h1><p class="hero-note">%s</p></div>\n' % (esc(title), esc(note))
            + src + '<footer class="scaffold-foot">เนื้อหาจาก <code>_src/cigblu/docs/%s.html</code> · เช็คเว็บจริง %s</footer>\n</main>\n</body></html>\n' % (name, CHECKED))


def stub(target_rel, label):
    return ('<!doctype html>\n<html lang="th"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow">'
            '<meta http-equiv="refresh" content="0; url=%s"><title>ย้ายแล้ว</title></head>'
            '<body><p>หน้านี้ย้ายไปที่ <a href="%s">%s</a></p></body></html>\n') % (target_rel, target_rel, esc(label))


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(s)


def main():
    ids = set(BY_ID)
    for p in PAGES:
        write(os.path.join(OUT, p['id'], 'index.html'), page_html(p))
        for old in p.get('old_hub', []):
            if old in ids:
                continue
            up = '../' * depth(old)
            write(os.path.join(OUT, old, 'index.html'), stub(up + p['id'] + '/index.html', p['title']))
    write(os.path.join(OUT, 'index.html'), dashboard())
    write(os.path.join(OUT, 'todo', 'index.html'), todo())
    write(os.path.join(OUT, 'url-map', 'index.html'), url_map())
    for name in ('guide-it',):
        write(os.path.join(OUT, name, 'index.html'), doc_page(name))
    write(os.path.join(OUT, 'it-build-issues-by-page-th.html'), stub('todo/index.html', 'งานที่ต้องทำทั้งหมด'))
    print('built %d pages' % len(PAGES))


if __name__ == '__main__':
    main()
