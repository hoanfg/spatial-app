"""
ui_theme.py — Lớp giao diện (UI/UX) cho NTL Spatial Econometrics.

Chỉ chứa CSS + các hàm hiển thị. KHÔNG có tính toán, công thức hay tham số phân tích.
Tương thích cả giao diện sáng và tối của Streamlit.
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


def inject_theme() -> None:
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


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
