#!/usr/bin/env python3
"""Generates ui.html by embedding all HTML files as JS strings."""
import os, json

BASE = '/Users/lilo.stitch/Downloads/jazz bridge'
OUT  = os.path.join(BASE, 'figma-plugin', 'ui.html')

PAGES = [
    ('01_home',            '홈'),
    ('02_event_detail',    '이벤트 상세'),
    ('03_calendar',        '캘린더'),
    ('04_splash',          '스플래시'),
    ('05_onboarding_1',    '온보딩 1'),
    ('06_onboarding_2',    '온보딩 2'),
    ('07_onboarding_3',    '온보딩 3'),
    ('08_permissions',     '권한'),
    ('09_search',          '검색'),
    ('10_follow',          '팔로우'),
    ('11_my',              '마이'),
    ('12_booking_qty',     '예매 수량'),
    ('13_booking_payment', '예매 결제'),
    ('14_booking_complete','예매 완료'),
    ('15_artist_profile',  '아티스트 프로필'),
    ('16_venue_profile',   '공연장 프로필'),
    ('17_notifications',   '알림'),
    ('18_archive',         '아카이브'),
]

def escape_template(s):
    s = s.replace('\\', '\\\\')
    s = s.replace('`', '\\`')
    s = s.replace('${', '\\${')
    return s

entries = []
for name, title in PAGES:
    path = os.path.join(BASE, f'{name}.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()
    escaped = escape_template(html)
    entries.append(f'  {{name:{json.dumps(name)},title:{json.dumps(title)},html:`{escaped}`}}')

pages_js = ',\n'.join(entries)

UI = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#fff;padding:16px;color:#1a1a1a}}
h2{{font-size:15px;font-weight:700;margin-bottom:4px}}
p{{font-size:12px;color:#666;margin-bottom:12px}}
#btn{{width:100%;padding:11px;background:#534AB7;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity .2s}}
#btn:disabled{{opacity:.45;cursor:not-allowed}}
.bar-wrap{{margin-top:10px;background:#f0f0f0;border-radius:4px;height:6px;overflow:hidden}}
.bar{{height:6px;background:#534AB7;border-radius:4px;width:0;transition:width .4s}}
#log{{margin-top:10px;font-size:11.5px;color:#444;line-height:1.7;max-height:320px;overflow-y:auto}}
.ok{{color:#1D9E75}}.err{{color:#e53e3e}}
</style>
</head>
<body>
<h2>🎷 Jazz Bridge HTML → Figma</h2>
<p>HTML을 파싱해서 Figma 프레임으로 생성합니다 (18개 화면)</p>
<button id="btn">모든 화면 가져오기</button>
<div class="bar-wrap"><div class="bar" id="bar"></div></div>
<div id="log"></div>

<!-- hidden render iframe: sandbox allows scripts so computed styles work -->
<iframe id="frame"
  sandbox="allow-scripts allow-same-origin"
  style="position:fixed;left:-9999px;top:0;width:375px;height:812px;border:none;"></iframe>

<script>
const PAGES = [
{pages_js}
];

const btn  = document.getElementById('btn');
const logEl= document.getElementById('log');
const bar  = document.getElementById('bar');
const iframe = document.getElementById('frame');

function log(msg, cls) {{
  const d = document.createElement('div');
  d.textContent = msg;
  if (cls) d.className = cls;
  logEl.appendChild(d);
  logEl.scrollTop = logEl.scrollHeight;
}}

/* ── color helpers ── */
function parseRgb(str) {{
  if (!str) return null;
  const m = str.match(/rgba?\\((\\d+(?:\\.\\d+)?),\\s*(\\d+(?:\\.\\d+)?),\\s*(\\d+(?:\\.\\d+)?)/);
  if (!m) return null;
  return {{r: +m[1]/255, g: +m[2]/255, b: +m[3]/255}};
}}
function parseOpacity(str) {{
  const m = str && str.match(/rgba\\([\\d\\s.,]+,\\s*([\\d.]+)\\)/);
  return m ? parseFloat(m[1]) : 1;
}}
function isTransp(str) {{
  if (!str || str === 'transparent') return true;
  const m = str.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
  if (!m) return true;
  return m[4] !== undefined && parseFloat(m[4]) < 0.01;
}}

/* ── DOM traversal ── */
function collectElements(doc) {{
  const SKIP = new Set(['HTML','HEAD','STYLE','LINK','SCRIPT','META','TITLE','NOSCRIPT']);
  const els  = [];

  function walk(el, depth) {{
    if (depth > 25 || SKIP.has(el.tagName)) return;

    const cs   = doc.defaultView.getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;

    const rect = el.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    if (rect.top > 830 || rect.left > 390 || rect.bottom < -5) return;

    const bg      = cs.backgroundColor;
    const hasBg   = !isTransp(bg);
    const bw      = parseFloat(cs.borderTopWidth) || 0;
    const bc      = cs.borderTopColor;
    const hasBord = bw > 0.05 && !isTransp(bc);
    const bRadius = parseFloat(cs.borderRadius) || 0;

    let directText = '';
    el.childNodes.forEach(n => {{ if (n.nodeType === 3) directText += n.textContent; }});
    directText = directText.trim();

    const hasChildren = el.children.length > 0;

    if (hasBg || hasBord || bRadius > 0 || (directText && !hasChildren)) {{
      els.push({{
        x: Math.round(rect.left),
        y: Math.round(rect.top),
        w: Math.round(rect.width),
        h: Math.round(rect.height),
        bgColor   : hasBg    ? parseRgb(bg) : null,
        bgOpacity : hasBg    ? parseOpacity(bg) : 1,
        color     : parseRgb(cs.color),
        fontSize  : parseFloat(cs.fontSize) || 14,
        fontWeight: parseInt(cs.fontWeight) || 400,
        borderRadius: bRadius,
        borderWidth : bw,
        borderColor : hasBord ? parseRgb(bc) : null,
        hasBorder   : hasBord,
        text        : directText,
        hasChildren,
      }});
    }}
    Array.from(el.children).forEach(c => walk(c, depth + 1));
  }}

  walk(doc.body, 0);
  return els;
}}

/* ── render one page ── */
function renderPage(page, index) {{
  return new Promise(resolve => {{
    iframe.onload = () => {{
      setTimeout(() => {{
        try {{
          const els = collectElements(iframe.contentDocument);
          resolve({{name: page.name, title: page.title, width: 375, height: 812, elements: els, index}});
        }} catch(e) {{
          resolve({{name: page.name, title: page.title, width: 375, height: 812, elements: [], index, error: e.message}});
        }}
      }}, 900);   // wait for layout + icon font
    }};
    iframe.srcdoc = page.html;
  }});
}}

/* ── main flow ── */
btn.addEventListener('click', () => {{
  btn.disabled = true;
  logEl.innerHTML = '';
  log('Figma 연결 중 / 폰트 로드...');
  parent.postMessage({{pluginMessage: {{type: 'START'}}}}, '*');
}});

let frameDoneResolve = null;

window.onmessage = async (ev) => {{
  const msg = ev.data && ev.data.pluginMessage;
  if (!msg) return;

  if (msg.type === 'FONTS_READY') {{
    log('폰트 준비 완료. HTML 파싱 시작...');

    for (let i = 0; i < PAGES.length; i++) {{
      const page = PAGES[i];
      log(`⏳ (${{i+1}}/${{PAGES.length}}) ${{page.title}} 파싱 중...`);
      bar.style.width = `${{Math.round(i / PAGES.length * 100)}}%`;

      const data = await renderPage(page, i);
      if (data.error) log(`  ⚠ 파싱 오류: ${{data.error}}`, 'err');

      parent.postMessage({{pluginMessage: {{type: 'CREATE_FRAME', ...data}}}}, '*');

      await new Promise(r => {{ frameDoneResolve = r; }});
    }}

    bar.style.width = '100%';
    parent.postMessage({{pluginMessage: {{type: 'ALL_DONE'}}}}, '*');
    log('✅ 완료! Figma에서 18개 프레임을 확인하세요.', 'ok');
    btn.disabled = false;
  }}

  if (msg.type === 'FRAME_DONE') {{
    log(`  ✓ ${{msg.name}}`, 'ok');
    frameDoneResolve && frameDoneResolve();
  }}

  if (msg.type === 'FRAME_ERROR') {{
    log(`  ✗ ${{msg.name}}: ${{msg.error}}`, 'err');
    frameDoneResolve && frameDoneResolve();
  }}

  if (msg.type === 'ERROR') {{
    log('오류: ' + msg.error, 'err');
    btn.disabled = false;
  }}
}};
</script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(UI)

print(f'✅ ui.html 생성 완료 ({len(PAGES)}개 페이지 임베드)')
print(f'   → {OUT}')
