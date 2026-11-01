"""
ui_theme.py

"""
from __future__ import annotations

import html as _html

import streamlit as st

ACCENT = "#ffb703"
ACCENT_2 = "#00e5ff"

_THEME_CSS = """
<style>
:root{
  --ntl-accent:#ffb703;
  --ntl-accent-2:#00e5ff;
  --ntl-bg-soft:rgba(127,127,140,.07);
  --ntl-bg-card:rgba(127,127,140,.09);
  --ntl-border:rgba(127,127,140,.24);
  --ntl-radius:14px;
  --ntl-shadow:0 6px 24px rgba(0,0,0,.14);
}
html{scroll-behavior:smooth}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1500px}
header[data-testid="stHeader"]{background:transparent}

/* ---------- Hero ---------- */
.ntl-hero{position:relative;overflow:hidden;border:1px solid var(--ntl-border);border-radius:18px;
  padding:22px 26px;margin:2px 0 14px;
  background:
    radial-gradient(900px 220px at 100% -20%,rgba(255,183,3,.22),transparent 60%),
    radial-gradient(700px 200px at 0% 120%,rgba(0,229,255,.14),transparent 60%),
    linear-gradient(135deg,rgba(20,22,30,.92),rgba(30,34,46,.88));
  color:#f4f6fa;box-shadow:var(--ntl-shadow);animation:ntlUp .5s both}
.ntl-hero h1{margin:0;font-size:1.65rem;font-weight:800;letter-spacing:-.3px;line-height:1.25;color:#fff;padding:0}
.ntl-hero p{margin:6px 0 0;color:#b6bdcb;font-size:.95rem}
.ntl-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.ntl-chip{font-size:.74rem;font-weight:600;padding:4px 11px;border-radius:999px;
  border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.07);color:#e8ecf4}
.ntl-chip b{color:var(--ntl-accent)}

/* ---------- Empty state / steps ---------- */
.ntl-empty{border:1px dashed var(--ntl-border);border-radius:18px;padding:26px 24px;margin-top:8px;
  background:var(--ntl-bg-soft);animation:ntlUp .5s both}
.ntl-empty h3{margin:0 0 4px;font-size:1.2rem}
.ntl-empty .sub{opacity:.75;font-size:.92rem;margin-bottom:16px}
.ntl-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.ntl-step{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border-radius:12px;
  border:1px solid var(--ntl-border);background:var(--ntl-bg-card);
  transition:transform .18s ease,border-color .18s ease}
.ntl-step:hover{transform:translateY(-3px);border-color:rgba(255,183,3,.6)}
.ntl-step .n{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;
  background:var(--ntl-accent);color:#111;font-weight:800;font-size:.85rem}
.ntl-step b{display:block;font-size:.9rem}
.ntl-step span{font-size:.8rem;opacity:.75;line-height:1.4}

/* ---------- Banner kết quả ---------- */
.ntl-place{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}
.ntl-place h4{margin:0;font-size:1.25rem;font-weight:800;padding:0}
.ntl-place .meta{display:flex;flex-wrap:wrap;gap:6px}
.ntl-tag{font-size:.74rem;font-weight:600;padding:3px 10px;border-radius:999px;
  border:1px solid var(--ntl-border);background:var(--ntl-bg-soft)}
.ntl-tag.hot{border-color:rgba(255,183,3,.6);color:var(--ntl-accent)}

/* ---------- Section header ---------- */
.ntl-sec{display:flex;align-items:center;gap:10px;margin:18px 0 6px}
.ntl-sec i{width:4px;height:20px;border-radius:2px;background:linear-gradient(var(--ntl-accent),var(--ntl-accent-2))}
.ntl-sec span{font-size:1.05rem;font-weight:700}

/* ---------- Metric ---------- */
div[data-testid="stMetric"]{background:var(--ntl-bg-card);border:1px solid var(--ntl-border);
  border-radius:var(--ntl-radius);padding:12px 16px;
  transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
div[data-testid="stMetric"]:hover{transform:translateY(-3px);border-color:rgba(255,183,3,.6);box-shadow:var(--ntl-shadow)}
div[data-testid="stMetricValue"]{font-weight:800;letter-spacing:-.3px}
div[data-testid="stMetricLabel"] p{font-size:.78rem;text-transform:uppercase;letter-spacing:.5px;opacity:.75}

/* ---------- Tabs ---------- */
div[data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--ntl-border);padding-bottom:0}
button[data-baseweb="tab"]{border-radius:10px 10px 0 0;padding:10px 18px;font-weight:600;
  transition:background .15s ease}
button[data-baseweb="tab"]:hover{background:var(--ntl-bg-soft)}
button[data-baseweb="tab"][aria-selected="true"]{background:var(--ntl-bg-card)}
div[data-baseweb="tab-highlight"]{background:linear-gradient(90deg,var(--ntl-accent),var(--ntl-accent-2))!important;height:3px!important}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"]{border-right:1px solid var(--ntl-border)}
section[data-testid="stSidebar"] .block-container{padding-top:1rem}
section[data-testid="stSidebar"] h2{font-size:1rem;text-transform:uppercase;letter-spacing:.8px;
  display:flex;align-items:center;gap:8px;margin-bottom:.4rem}
section[data-testid="stSidebar"] h2:before{content:"";width:4px;height:16px;border-radius:2px;
  background:linear-gradient(var(--ntl-accent),var(--ntl-accent-2))}
section[data-testid="stSidebar"] hr{margin:.8rem 0}
.ntl-brand{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.ntl-brand .logo{width:36px;height:36px;border-radius:10px;display:grid;place-items:center;font-size:1.2rem;
  background:linear-gradient(135deg,#1c2030,#2b3350);border:1px solid var(--ntl-border)}
.ntl-brand b{display:block;font-size:.95rem;line-height:1.1}
.ntl-brand span{font-size:.72rem;opacity:.65}

/* ---------- Buttons ---------- */
div.stButton>button,div[data-testid="stDownloadButton"]>button,div[data-testid="stFormSubmitButton"]>button{
  border-radius:11px;font-weight:700;transition:transform .15s ease,box-shadow .15s ease,filter .15s ease}
div.stButton>button:hover:not(:disabled),div[data-testid="stDownloadButton"]>button:hover:not(:disabled),
div[data-testid="stFormSubmitButton"]>button:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.25)}
div.stButton>button:active:not(:disabled){transform:translateY(0)}
div.stButton>button[kind="primary"],div[data-testid="stDownloadButton"]>button[kind="primary"],
div[data-testid="stFormSubmitButton"]>button[kind="primary"]{
  background:linear-gradient(135deg,#ffb703,#ff8c00);border:none;color:#1a1100}
div.stButton>button[kind="primary"]:hover:not(:disabled){filter:brightness(1.07)}
div.stButton>button:disabled{opacity:.45}
div.stButton>button:focus-visible,button[data-baseweb="tab"]:focus-visible{outline:2px solid var(--ntl-accent-2);outline-offset:2px}

/* ---------- Containers / expanders / tables ---------- */
div[data-testid="stExpander"]{border:1px solid var(--ntl-border);border-radius:var(--ntl-radius);overflow:hidden;
  background:var(--ntl-bg-soft)}
div[data-testid="stExpander"] summary{font-weight:600}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:var(--ntl-radius)}
div[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden;border:1px solid var(--ntl-border)}
div[data-testid="stAlert"]{border-radius:12px}
div[data-testid="stStatus"],details[data-testid="stStatusWidget"]{border-radius:var(--ntl-radius)}
iframe{border-radius:14px}
h3,h4{letter-spacing:-.2px}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:rgba(127,127,140,.4);border-radius:8px}
::-webkit-scrollbar-thumb:hover{background:rgba(255,183,3,.6)}

/* ---------- Responsive ---------- */
@media (max-width:768px){
  .block-container{padding-left:.8rem;padding-right:.8rem}
  .ntl-hero{padding:16px}
  .ntl-hero h1{font-size:1.3rem}
  button[data-baseweb="tab"]{padding:8px 10px;font-size:.85rem}
}
@keyframes ntlUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""


_FX_CSS = """
<style>
/* ===== Vòng 2: hiệu ứng ===== */
@keyframes ntlFade{from{opacity:0}to{opacity:1}}
@keyframes ntlPop{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}
@keyframes ntlFloat{0%,100%{transform:translate(0,0)}50%{transform:translate(-22px,16px)}}
@keyframes ntlShine{to{background-position:200% 0}}
@keyframes ntlBar{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes ntlSweep{0%{transform:translateX(-120%)}60%,100%{transform:translateX(120%)}}
@keyframes ntlPulse{0%,100%{box-shadow:0 0 0 0 rgba(255,183,3,.45)}50%{box-shadow:0 0 0 9px rgba(255,183,3,0)}}
@keyframes ntlRipple{from{transform:scale(0);opacity:.45}to{transform:scale(2.6);opacity:0}}

/* Hero: aurora + chữ ánh kim */
.ntl-hero:before,.ntl-hero:after{content:"";position:absolute;border-radius:50%;filter:blur(42px);pointer-events:none}
.ntl-hero:before{width:260px;height:260px;right:-60px;top:-130px;background:#ffb703;opacity:.5;animation:ntlFloat 8s ease-in-out infinite}
.ntl-hero:after{width:230px;height:230px;left:32%;bottom:-150px;background:#00e5ff;opacity:.26;animation:ntlFloat 10s ease-in-out infinite reverse}
.ntl-hero>*{position:relative;z-index:1}
.ntl-hero h1{background:linear-gradient(90deg,#fff,#ffe29a,#9ff3ff,#ffe29a,#fff);background-size:200% 100%;
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:ntlShine 7s linear infinite}
.ntl-chip{animation:ntlPop .35s cubic-bezier(.2,.8,.2,1) backwards}
.ntl-chip:nth-child(2){animation-delay:.06s}.ntl-chip:nth-child(3){animation-delay:.12s}.ntl-chip:nth-child(4){animation-delay:.18s}
.ntl-step{animation:ntlUp .38s cubic-bezier(.2,.8,.2,1) backwards}
.ntl-step:nth-child(2){animation-delay:.07s}.ntl-step:nth-child(3){animation-delay:.14s}.ntl-step:nth-child(4){animation-delay:.21s}
.ntl-step .n{transition:transform .25s ease}.ntl-step:hover .n{transform:scale(1.15) rotate(-6deg)}
.ntl-tag{animation:ntlPop .3s ease backwards}
.ntl-place h4{background:linear-gradient(90deg,var(--ntl-accent),#ff8c00);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}

/* Vào cảnh theo thứ tự cho cột / thẻ / bảng / tab */
div[data-testid="stHorizontalBlock"]>div{animation:ntlUp .38s cubic-bezier(.2,.8,.2,1) backwards}
div[data-testid="stHorizontalBlock"]>div:nth-child(2){animation-delay:.05s}
div[data-testid="stHorizontalBlock"]>div:nth-child(3){animation-delay:.10s}
div[data-testid="stHorizontalBlock"]>div:nth-child(4){animation-delay:.15s}
div[data-testid="stHorizontalBlock"]>div:nth-child(5){animation-delay:.20s}
div[data-testid="stHorizontalBlock"]>div:nth-child(6){animation-delay:.25s}
div[data-baseweb="tab-panel"]{animation:ntlFade .3s ease both}
div[data-testid="stExpander"],div[data-testid="stDataFrame"],div[data-testid="stAlert"],
div[data-testid="stVerticalBlockBorderWrapper"]{animation:ntlUp .35s cubic-bezier(.2,.8,.2,1) backwards}
div[data-testid="stExpander"]{transition:border-color .18s ease}
div[data-testid="stExpander"]:hover{border-color:rgba(255,183,3,.5)}
div[data-testid="stPlotlyChart"],div[data-testid="stVegaLiteChart"]{animation:ntlPop .4s ease backwards}
iframe{animation:ntlFade .5s ease both}

/* Thẻ chỉ số: vạch nhấn chạy ra khi xuất hiện */
div[data-testid="stMetric"]{position:relative;overflow:hidden}
div[data-testid="stMetric"]:before{content:"";position:absolute;left:0;right:0;top:0;height:3px;transform-origin:left;
  background:linear-gradient(90deg,var(--ntl-accent),var(--ntl-accent-2));animation:ntlBar .6s cubic-bezier(.2,.8,.2,1) both}

/* Nút: ánh quét + gợn sóng khi bấm */
div.stButton>button,div[data-testid="stDownloadButton"]>button,div[data-testid="stFormSubmitButton"]>button{position:relative;overflow:hidden}
div.stButton>button[kind="primary"]:not(:disabled):after,div[data-testid="stDownloadButton"]>button[kind="primary"]:after,
div[data-testid="stFormSubmitButton"]>button[kind="primary"]:after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,.38) 50%,transparent 65%);animation:ntlSweep 3.6s ease-in-out infinite}
section[data-testid="stSidebar"] div.stButton>button[kind="primary"]:not(:disabled){animation:ntlPulse 2.4s ease-out infinite}
.ntl-ripple{position:absolute;border-radius:50%;background:rgba(255,255,255,.55);pointer-events:none;animation:ntlRipple .55s ease-out forwards}

/* Điều khiển nhập liệu theo màu nhấn */
div[data-baseweb="slider"] div[role="slider"]{background:var(--ntl-accent)!important;box-shadow:0 0 0 4px rgba(255,183,3,.22);transition:box-shadow .15s ease}
div[data-baseweb="slider"] div[role="slider"]:hover{box-shadow:0 0 0 7px rgba(255,183,3,.25)}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div{border-radius:10px;transition:border-color .15s ease,box-shadow .15s ease}
div[data-baseweb="select"]>div:hover,div[data-baseweb="input"]>div:hover{border-color:rgba(255,183,3,.7)}
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,rgba(127,127,140,.5),transparent)!important}
div[data-testid="stSidebar"] [data-testid="stRadio"] label{transition:color .15s ease}
div[data-testid="stTooltipContent"]{border-radius:10px}
div[data-testid="stToast"]{border-radius:12px;border:1px solid rgba(255,183,3,.5);animation:ntlPop .3s ease both}

/* Thanh tiến trình cuộn + nút lên đầu trang */
.ntl-progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:999999;pointer-events:none;
  background:linear-gradient(90deg,var(--ntl-accent),var(--ntl-accent-2));transition:width .1s linear}
.ntl-top{position:fixed;right:22px;bottom:22px;width:44px;height:44px;border-radius:50%;border:1px solid var(--ntl-border);
  background:rgba(20,22,30,.88);color:#ffb703;font-size:1.15rem;cursor:pointer;z-index:999998;display:grid;place-items:center;
  opacity:0;transform:translateY(14px);pointer-events:none;transition:opacity .2s ease,transform .2s ease,border-color .2s ease;
  backdrop-filter:blur(6px)}
.ntl-top.show{opacity:1;transform:none;pointer-events:auto}
.ntl-top:hover{border-color:var(--ntl-accent);transform:translateY(-3px)}

/* Ẩn khung iframe 0px dùng cho script */
div[data-testid="stElementContainer"]:has(iframe[height="0"]),div.element-container:has(iframe[height="0"]){display:none}
</style>
"""

_FX_JS = """
<script>
(function () {
  var P = window.parent, D;
  try { D = P.document; } catch (e) { return; }
  if (P.__ntlFx) { return; }
  P.__ntlFx = true;
  var reduce = P.matchMedia && P.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 1) Đếm số cho thẻ chỉ số (~0.7s) */
  function textNode(el) {
    var w = D.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n;
    while ((n = w.nextNode())) { if (/\\d/.test(n.nodeValue)) { return n; } }
    return null;
  }
  function animate(el) {
    if (el.__ntlBusy) { return; }
    var tn = textNode(el);
    if (!tn) { return; }
    var full = tn.nodeValue;
    if (el.__ntlLast === full) { return; }
    el.__ntlLast = full;
    var m = full.match(/^([^\\d\\-+]*)([\\-+]?[\\d,]*\\.?\\d+)(.*)$/);
    if (!m || reduce) { return; }
    var raw = m[2], target = parseFloat(raw.replace(/,/g, ''));
    if (!isFinite(target) || target === 0) { return; }
    var dec = raw.indexOf('.') >= 0 ? raw.split('.')[1].length : 0;
    var commas = raw.indexOf(',') >= 0;
    function fmt(v) {
      var s = v.toFixed(dec);
      if (commas) { var a = s.split('.'); a[0] = a[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ','); s = a.join('.'); }
      return m[1] + s + m[3];
    }
    var t0 = null, dur = 700, last = null;
    el.__ntlBusy = true;
    function step(ts) {
      if (t0 === null) { t0 = ts; }
      var t = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - t, 3);
      if (tn.nodeValue !== full && tn.nodeValue !== last) { el.__ntlBusy = false; return; }
      last = t < 1 ? fmt(target * e) : full;
      tn.nodeValue = last;
      if (t < 1) { P.requestAnimationFrame(step); } else { el.__ntlBusy = false; }
    }
    P.requestAnimationFrame(step);
  }
  var pending = false;
  function scan() {
    pending = false;
    D.querySelectorAll('[data-testid="stMetricValue"]').forEach(animate);
  }
  new P.MutationObserver(function () {
    if (!pending) { pending = true; P.requestAnimationFrame(scan); }
  }).observe(D.body, {childList: true, subtree: true});
  scan();

  /* 2) Gợn sóng khi bấm nút */
  D.addEventListener('click', function (e) {
    if (reduce || !e.target.closest) { return; }
    var b = e.target.closest('.stButton button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button');
    if (!b) { return; }
    var r = b.getBoundingClientRect(), d = Math.max(r.width, r.height), s = D.createElement('span');
    s.className = 'ntl-ripple';
    s.style.cssText = 'width:' + d + 'px;height:' + d + 'px;left:' + (e.clientX - r.left - d / 2) + 'px;top:' + (e.clientY - r.top - d / 2) + 'px';
    b.appendChild(s);
    setTimeout(function () { if (s.parentNode) { s.parentNode.removeChild(s); } }, 600);
  }, true);

  /* 3) Thanh tiến trình cuộn + nút lên đầu trang */
  var bar = D.createElement('div'); bar.className = 'ntl-progress';
  var top = D.createElement('button'); top.className = 'ntl-top'; top.type = 'button';
  top.setAttribute('aria-label', 'Back to top'); top.textContent = '\\u2191';
  D.body.appendChild(bar); D.body.appendChild(top);
  var tries = 0;
  function bind() {
    var sc = D.querySelector('[data-testid="stMain"]') || D.querySelector('section.main');
    if (!sc) { if (tries++ < 20) { setTimeout(bind, 400); } return; }
    function upd() {
      var max = sc.scrollHeight - sc.clientHeight;
      bar.style.width = (max > 0 ? Math.min(100, sc.scrollTop / max * 100) : 0) + '%';
      top.classList.toggle('show', sc.scrollTop > 500);
    }
    sc.addEventListener('scroll', upd, {passive: true});
    top.addEventListener('click', function () { sc.scrollTo({top: 0, behavior: reduce ? 'auto' : 'smooth'}); });
    upd();
  }
  bind();
})();
</script>
"""


def inject_theme() -> None:
    st.markdown(_THEME_CSS, unsafe_allow_html=True)
    st.markdown(_FX_CSS, unsafe_allow_html=True)


def enable_fx() -> None:
    try:
        import streamlit.components.v1 as components
        components.html(_FX_JS, height=0)
    except Exception:  # noqa: BLE001
        pass


def sidebar_brand(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="ntl-brand"><div class="logo">🌙</div>'
        f'<div><b>{_html.escape(title)}</b><span>{_html.escape(subtitle)}</span></div></div>',
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, chips: list[tuple[str, str]] | None = None) -> None:
    """chips: danh sách (nhãn, giá trị)."""
    chip_html = ""
    if chips:
        chip_html = '<div class="ntl-chips">' + "".join(
            f'<span class="ntl-chip">{_html.escape(k)} <b>{_html.escape(v)}</b></span>' for k, v in chips
        ) + "</div>"
    st.markdown(
        f'<div class="ntl-hero"><h1>{_html.escape(title)}</h1><p>{_html.escape(subtitle)}</p>{chip_html}</div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, hint: str, steps: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="ntl-step"><div class="n">{i}</div><div><b>{_html.escape(t)}</b>'
        f'<span>{_html.escape(d)}</span></div></div>'
        for i, (t, d) in enumerate(steps, 1)
    )
    st.markdown(
        f'<div class="ntl-empty"><h3>{_html.escape(title)}</h3><div class="sub">{_html.escape(hint)}</div>'
        f'<div class="ntl-steps">{cards}</div></div>',
        unsafe_allow_html=True,
    )


def place_banner(place: str, tags: list[str]) -> None:
    t = "".join(f'<span class="ntl-tag">{_html.escape(x)}</span>' for x in tags)
    st.markdown(
        f'<div class="ntl-place"><h4>📍 {_html.escape(place)}</h4><div class="meta">{t}</div></div>',
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="ntl-sec"><i></i><span>{_html.escape(title)}</span></div>', unsafe_allow_html=True)
