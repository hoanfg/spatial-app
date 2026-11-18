"""Visual theme and reusable Streamlit components."""
from __future__ import annotations

import html as _html
import math
import re

import streamlit as st

SODIUM = "#F2A93B"
LED = "#9FD8FF"
NIGHT = "#0A1024"

_FONTS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600&display=swap');
</style>
"""

_THEME_CSS = """
<style>
:root{
  --ntl-sodium:#F2A93B;
  --ntl-led:#9FD8FF;
  --ntl-night:#0A1024;
  --ntl-line:rgba(130,142,185,.30);
  --ntl-soft:rgba(130,142,185,.07);
  --ntl-display:"Source Serif 4","Source Serif Pro",Georgia,"Times New Roman",serif;
  --ntl-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --ntl-rule:rgba(142,153,184,.28);
  --ntl-body:"Instrument Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --ntl-r-panel:6px;
  --ntl-r-ctl:4px;
}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stSidebar"],
button,input,textarea,select{font-family:var(--ntl-body)}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-family:var(--ntl-display);letter-spacing:-.015em}
html{scroll-behavior:smooth}
.block-container{padding-top:1.4rem;padding-bottom:3.5rem;max-width:1480px}
header[data-testid="stHeader"]{background:transparent}
hr{border:0!important;border-top:1px solid var(--ntl-line)!important;background:none!important;height:0!important}

/* ================= HERO ================= */
.ntl-hero{position:relative;overflow:hidden;min-height:176px;display:flex;align-items:center;container-type:inline-size;
  background:var(--ntl-night);border:1px solid #1E2A55;border-radius:20px;color:#EEF2FB}
.ntl-field{position:absolute;top:0;right:0;bottom:0;width:min(52%,640px);padding:16px 18px;display:grid;
  grid-template-columns:repeat(26,1fr);align-content:center;gap:5px;pointer-events:none;
  -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 62%);mask-image:linear-gradient(90deg,transparent 0,#000 62%)}
.ntl-field i{display:block;aspect-ratio:1/1;border-radius:3px;background:#8E99B8;opacity:0;animation:ntlLit .5s cubic-bezier(.2,.7,.2,1) var(--d) forwards}
.ntl-field i.s{background:var(--ntl-sodium)}
.ntl-field i.g{box-shadow:0 0 9px rgba(242,169,59,.55)}
.ntl-field i.l{background:var(--ntl-led);box-shadow:0 0 14px rgba(159,216,255,.75)}
@keyframes ntlLit{from{opacity:0;transform:scale(.6)}to{opacity:var(--o);transform:none}}

.ntl-field i.t{animation:ntlLit .5s cubic-bezier(.2,.7,.2,1) var(--d) forwards,
  ntlTwinkle var(--t) ease-in-out calc(var(--d) + 1s + var(--p)) infinite}
@keyframes ntlTwinkle{0%,100%{opacity:var(--o)}50%{opacity:calc(var(--o) * .35)}}
.ntl-field i.r{animation:ntlLit .5s cubic-bezier(.2,.7,.2,1) var(--d) forwards,
  ntlRipple 6s ease-out calc(var(--d) + 1.6s + var(--r)) infinite}
@keyframes ntlRipple{0%,38%,100%{opacity:var(--o)}10%{opacity:1}}

html.ntl-offscreen .ntl-field i.t,html.ntl-offscreen .ntl-field i.r{animation-play-state:paused}
html.ntl-calm .ntl-field i.t,html.ntl-calm .ntl-field i.r{animation:ntlLit .5s cubic-bezier(.2,.7,.2,1) var(--d) forwards}
.ntl-hero-body{position:relative;z-index:1;padding:30px 34px;max-width:60%}
.ntl-title{font-family:var(--ntl-display);font-size:1.95rem;font-weight:700;line-height:1.1;letter-spacing:-.025em;color:#F3F6FD}
.ntl-sub{margin-top:8px;color:#A5B1D1;font-size:1.02rem;max-width:40ch;line-height:1.45}
.ntl-facts{display:flex;flex-wrap:wrap;margin:20px 0 0;padding:0}
.ntl-facts div{padding:0 15px;border-left:1px solid #2A376A}
.ntl-facts div:first-child{padding-left:0;border-left:0}
.ntl-facts dt{font-size:.74rem;color:#7F8BB0;margin:0 0 2px}
.ntl-facts dd{font-size:.88rem;font-weight:600;margin:0;color:#DDE4F6}


.ntl-empty{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:40px;margin:22px 0 8px;align-items:start}
.ntl-empty-h{font-family:var(--ntl-display);font-size:1.7rem;font-weight:700;line-height:1.15;letter-spacing:-.02em}
.ntl-empty-p{margin-top:10px;opacity:.72;line-height:1.55;max-width:44ch}
.ntl-steps{list-style:none;margin:0;padding:0;position:relative}
.ntl-steps:before{content:"";position:absolute;left:15px;top:18px;bottom:18px;width:1px;background:var(--ntl-line)}
.ntl-steps li{position:relative;display:flex;gap:16px;padding:10px 0}
.ntl-steps .n{flex:none;width:31px;height:31px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:.85rem;
  background:var(--stApp-bg,transparent);border:1px solid var(--ntl-line);position:relative;z-index:1;backdrop-filter:blur(2px)}
.ntl-steps li:first-child .n{background:var(--ntl-sodium);border-color:var(--ntl-sodium);color:#1A1206}
.ntl-steps b{display:block;font-size:1rem}
.ntl-steps span{display:block;font-size:.9rem;opacity:.7;line-height:1.45;margin-top:1px}


.ntl-plate{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:14px 28px;margin:2px 0 14px}
.ntl-where .up{font-size:.88rem;opacity:.65;margin-bottom:2px}
.ntl-where .name{font-family:var(--ntl-display);font-size:1.9rem;font-weight:700;line-height:1.08;letter-spacing:-.025em}
.ntl-where .name:before{content:"";display:inline-block;width:.42em;height:.42em;margin-right:.42em;border-radius:2px;
  background:var(--ntl-sodium);box-shadow:0 0 12px rgba(242,169,59,.6);vertical-align:.12em}
.ntl-meta{display:flex;flex-wrap:wrap;margin:0;padding:0}
.ntl-meta div{padding:0 16px;border-left:1px solid var(--ntl-line)}
.ntl-meta div:first-child{padding-left:0;border-left:0}
.ntl-meta dt{font-size:.74rem;opacity:.6;margin:0}
.ntl-meta dd{font-size:.95rem;font-weight:600;margin:0}

.ntl-sec{margin:22px 0 6px;font-family:var(--ntl-display);font-size:1.15rem;font-weight:700}


div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]){gap:0!important;
  border-top:1px solid var(--ntl-line);border-bottom:1px solid var(--ntl-line)}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"])>div{padding:16px 20px}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"])>div:first-child{padding-left:2px}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"])>div:not(:first-child){border-left:1px solid var(--ntl-line)}
div[data-testid="stMetric"]{background:none!important;border:0!important;padding:0!important;border-radius:0}
div[data-testid="stMetricValue"]{font-family:var(--ntl-display);font-weight:600;font-size:1.9rem;letter-spacing:-.02em;
  line-height:1.15;font-variant-numeric:tabular-nums}
div[data-testid="stMetricLabel"] p{font-size:.84rem;opacity:.68;text-transform:none;letter-spacing:0}

/* ================= TAB ================= */
div[data-baseweb="tab-list"]{gap:30px;border-bottom:1px solid var(--ntl-line)}
button[data-baseweb="tab"]{background:none!important;padding:12px 2px;font-family:var(--ntl-display);font-size:1.02rem;font-weight:600;
  opacity:.6;border-radius:0;transition:opacity .15s ease}
button[data-baseweb="tab"]:hover,button[data-baseweb="tab"][aria-selected="true"]{opacity:1}
div[data-baseweb="tab-highlight"]{background:var(--ntl-sodium)!important;height:3px!important;border-radius:3px 3px 0 0}
div[data-baseweb="tab-border"]{background:transparent!important}
div[data-baseweb="tab-panel"]{animation:ntlTab .2s ease both;padding-top:1rem}
@keyframes ntlTab{from{opacity:0}to{opacity:1}}

/* ================= SIDEBAR ================= */
[data-testid="stSidebar"]{border-right:1px solid var(--ntl-line)}
[data-testid="stSidebar"] h2{font-size:1.02rem;font-weight:700;display:flex;align-items:center;gap:10px;margin:.2rem 0 .6rem;
  text-transform:none;letter-spacing:-.01em}
[data-testid="stSidebar"] h2:before{content:"";flex:none;width:9px;height:9px;border-radius:2px;background:var(--ntl-sodium)}
[data-testid="stSidebar"] hr{margin:1.1rem 0}
.ntl-brand{display:flex;align-items:center;gap:12px;margin:2px 0 14px}
.ntl-mark{flex:none;width:34px;height:34px;display:grid;grid-template-columns:repeat(3,1fr);gap:3px;padding:5px;
  background:var(--ntl-night);border-radius:9px}
.ntl-mark i{border-radius:1.5px;background:#4A5784;opacity:.5}
.ntl-mark i.s{background:var(--ntl-sodium);opacity:1}
.ntl-mark i.l{background:var(--ntl-led);opacity:1}
.ntl-brand b{display:block;font-family:var(--ntl-display);font-size:1.02rem;line-height:1.1;letter-spacing:-.01em}
.ntl-brand span{font-size:.78rem;opacity:.62}


button[data-testid^="stBaseButton"],div[data-testid="stDownloadButton"] button,div[data-testid="stFormSubmitButton"] button{
  border-radius:var(--ntl-r-ctl);font-weight:600;transition:border-color .15s ease,background .15s ease,transform .1s ease}
button[data-testid="stBaseButton-secondary"]:hover:not(:disabled){border-color:var(--ntl-sodium)!important;color:inherit}
button[data-testid="stBaseButton-primary"],button[kind="primary"],button[kind="primaryFormSubmit"]{
  background:var(--ntl-sodium)!important;border:1px solid var(--ntl-sodium)!important;color:#1A1206!important;
  min-height:2.9rem;font-weight:700;font-size:1rem;letter-spacing:-.005em}
button[data-testid="stBaseButton-primary"] p,button[kind="primary"] p{color:#1A1206!important;font-weight:700}
button[data-testid="stBaseButton-primary"]:hover:not(:disabled),button[kind="primary"]:hover:not(:disabled){
  background:#FFBE5C!important;border-color:#FFBE5C!important;box-shadow:0 0 0 4px rgba(242,169,59,.25)}
button[data-testid="stBaseButton-primary"]:active:not(:disabled){transform:scale(.985)}
button[data-testid="stBaseButton-primary"]:disabled,button[kind="primary"]:disabled{opacity:.4}
button:focus-visible,[role="tab"]:focus-visible{outline:2px solid var(--ntl-led)!important;outline-offset:2px}


div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,div[data-baseweb="base-input"]{border-radius:var(--ntl-r-ctl)!important;
  border-color:var(--ntl-line)!important;transition:border-color .15s ease}
div[data-baseweb="select"]:hover>div,div[data-baseweb="input"]:hover>div{border-color:rgba(242,169,59,.7)!important}
div[data-baseweb="select"]:focus-within>div,div[data-baseweb="input"]:focus-within>div{border-color:var(--ntl-sodium)!important}
[data-testid="stSliderThumbValue"]{font-weight:700;font-variant-numeric:tabular-nums}
label[data-testid="stWidgetLabel"] p{font-size:.88rem;font-weight:500}


div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] .ntl-plate){
  border:0!important;padding:0!important;background:none!important}
div[data-testid="stExpander"]{border:0!important;border-bottom:1px solid var(--ntl-line)!important;border-radius:0!important;background:none!important}
div[data-testid="stExpander"] details{border:0!important;border-radius:0!important;background:none!important}
div[data-testid="stExpander"] summary{font-weight:600;padding-left:0;padding-right:0}
div[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden;border:1px solid var(--ntl-line)}
div[data-testid="stAlert"],div[data-testid="stAlertContainer"]{border-radius:10px}
div[data-testid="stStatus"],div[data-testid="stStatusWidget"]{border-radius:14px;border:1px solid var(--ntl-line)!important;background:none!important}
div[data-testid="stToast"]{border-radius:12px;border:1px solid rgba(242,169,59,.55)}
iframe{border-radius:var(--ntl-r-panel)}
iframe[title="streamlit_folium.st_folium"]{box-shadow:0 0 0 1px var(--ntl-line)}
[data-testid="stCaptionContainer"]{opacity:.72}


::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:rgba(130,142,185,.4);border-radius:8px}
::-webkit-scrollbar-thumb:hover{background:rgba(242,169,59,.7)}
.ntl-top{position:fixed;right:22px;bottom:22px;width:42px;height:42px;border-radius:10px;border:1px solid #2A376A;
  background:var(--ntl-night);color:var(--ntl-sodium);font-size:1.1rem;cursor:pointer;z-index:999998;display:grid;place-items:center;
  opacity:0;transform:translateY(10px);pointer-events:none;transition:opacity .18s ease,transform .18s ease}
.ntl-top.show{opacity:1;transform:none;pointer-events:auto}
div[data-testid="stElementContainer"]:has(iframe[height="0"]),div.element-container:has(iframe[height="0"]){display:none}

/* ================= RESPONSIVE ================= */
@media (max-width:900px){
  .ntl-hero-body{max-width:100%;padding:24px 22px}
  .ntl-field{display: none !important;}
  .ntl-title{font-size:1.6rem}
  .ntl-facts{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px}
  .ntl-facts div,.ntl-facts div:first-child{padding:0;border-left:0}
  .ntl-empty{grid-template-columns:1fr;gap:18px}
}
@media (max-width:640px){
  .block-container{padding-left:.9rem;padding-right:.9rem}
  div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"])>div:not(:first-child){border-left:0;border-top:1px solid var(--ntl-line)}
  .ntl-where .name{font-size:1.5rem}
  div[data-testid="stMetricValue"]{font-size:1.6rem}
  div[data-baseweb="tab-list"]{gap:18px}
}
@container (max-width:760px){
  .ntl-field{width:100%;opacity:.24;-webkit-mask-image:none;mask-image:none}
  .ntl-field i.t,.ntl-field i.r{animation:ntlLit .5s cubic-bezier(.2,.7,.2,1) var(--d) forwards}
  .ntl-hero-body{max-width:100%;padding:24px 24px}
  .ntl-title{font-size:1.6rem}
  .ntl-facts{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px}
  .ntl-facts div,.ntl-facts div:first-child{padding:0;border-left:0}
}
@media (prefers-reduced-motion:reduce){
  .ntl-field i,.ntl-field i.t,.ntl-field i.r{animation:none;opacity:var(--o)}
  div[data-baseweb="tab-panel"]{animation:none}
  *{transition:none!important}
}
</style>
"""

_UX_CSS = """
<style>
:root{--ntl-glass:rgba(17,25,54,.88)}
@media (prefers-color-scheme: light){:root{--ntl-glass:rgba(255,255,255,.9)}}

/* ===== Sidebar ===== */
[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.ntl-brand),
[data-testid="stSidebar"] div.element-container:has(.ntl-brand){order:-2}
[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(button[data-testid="stBaseButton-primary"]){
  position:sticky;bottom:0;z-index:6;margin-top:.4rem;padding:14px 0 10px;
  background:linear-gradient(to top,var(--ntl-glass) 78%,transparent);
  -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}


[data-testid="stRadio"] [role="radiogroup"]{gap:6px;flex-wrap:wrap}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"]{flex-direction:row}
[data-testid="stRadio"] label[data-baseweb="radio"]{margin:0;padding:5px 13px;border:1px solid var(--ntl-line);
  border-radius:999px;cursor:pointer;transition:border-color .15s ease,background .15s ease}
[data-testid="stRadio"] label[data-baseweb="radio"]>div:first-of-type{display:none}
[data-testid="stRadio"] label[data-baseweb="radio"]:hover{border-color:rgba(242,169,59,.65)}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){border-color:var(--ntl-sodium);background:rgba(242,169,59,.15)}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p{font-weight:700}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:focus-visible){outline:2px solid var(--ntl-led);outline-offset:2px}


div[data-baseweb="tab-list"]{position:sticky;top:3.4rem;z-index:20;background:var(--ntl-glass);
  -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}


[data-testid="stMain"] h3{font-size:1.28rem;font-weight:700;display:flex;align-items:center;gap:10px;margin-top:1.2rem}
[data-testid="stMain"] h3:before{content:"";flex:none;width:9px;height:9px;border-radius:2px;background:var(--ntl-sodium)}


.ntl-redfix [data-testid="stSlider"],.ntl-redfix [data-testid="stCheckbox"],.ntl-redfix [data-testid="stToggle"]{filter:hue-rotate(38deg)}
</style>
"""


_LAYOUT_CSS = """
<style>

[data-testid="stMain"]{
  background:
    radial-gradient(900px 420px at 85% -8%,rgba(159,216,255,.075),transparent 62%),
    radial-gradient(700px 380px at 0% 105%,rgba(242,169,59,.055),transparent 60%),
    radial-gradient(rgba(142,153,184,.13) 1px,transparent 1.3px) 0 0/26px 26px,
    var(--ntl-night,#0A1024)}
@media (min-width:1000px){
  [data-testid="stSidebar"]{border-right:0;background:transparent}
  [data-testid="stSidebar"] [data-testid="stSidebarContent"]{
    margin:12px 0 12px 12px;height:calc(100% - 24px);border-radius:20px;
    background:linear-gradient(180deg,#131C3E 0%,#0F1733 46%,#0D1430 100%);
    border:1px solid #243063;
    box-shadow:0 18px 44px rgba(2,5,18,.55),inset 0 1px 0 rgba(159,216,255,.09)}
  [data-testid="stSidebar"] [data-testid="stSidebarContent"]:before{
    content:"";position:absolute;left:22px;right:22px;top:0;height:2px;border-radius:0 0 3px 3px;
    background:linear-gradient(90deg,transparent,var(--ntl-sodium,#F2A93B),var(--ntl-led,#9FD8FF),transparent);opacity:.8}
}

.ntl-empty{container-type:inline-size;display:block;margin:34px 0 8px;text-align:center}
.ntl-empty-h{font-size:2rem}
.ntl-empty-p{margin:12px auto 0;max-width:56ch;opacity:.75}
.ntl-steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:30px;text-align:left}
.ntl-steps:before{display:none}
.ntl-steps li{flex-direction:column;gap:12px;padding:18px 18px 20px;border:1px solid var(--ntl-line);border-radius:16px;
  background:linear-gradient(180deg,rgba(26,36,76,.55),rgba(14,21,48,.55));
  opacity:0;animation:ntlRise .5s cubic-bezier(.2,.7,.2,1) forwards;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.ntl-steps li:nth-child(1){animation-delay:.05s}.ntl-steps li:nth-child(2){animation-delay:.13s}
.ntl-steps li:nth-child(3){animation-delay:.21s}.ntl-steps li:nth-child(4){animation-delay:.29s}
.ntl-steps li:hover{transform:translateY(-3px);border-color:#3B4C8F;box-shadow:0 12px 28px rgba(2,5,18,.45)}
.ntl-steps li:first-child{border-color:rgba(242,169,59,.55)}
@keyframes ntlRise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@container (max-width:880px){.ntl-steps{grid-template-columns:repeat(2,minmax(0,1fr))}}
@container (max-width:460px){.ntl-steps{grid-template-columns:1fr}.ntl-empty-h{font-size:1.6rem}}
@media (prefers-reduced-motion:reduce){.ntl-steps li{animation:none;opacity:1}}


[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"]{display:none!important}
.block-container{max-width:1320px}

div[data-testid="stHorizontalBlock"]:has(.ntl-brand){align-items:center;margin:0 0 .6rem}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) .ntl-brand{margin:0}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand)>div[data-testid="stColumn"]:last-child{
  display:flex;flex-direction:column;align-items:flex-end}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"] [role="radiogroup"]{
  flex-wrap:nowrap;gap:0;padding:3px;border:1px solid var(--ntl-line);border-radius:999px;background:rgba(14,21,48,.6)}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"] label[data-baseweb="radio"]{
  border-color:transparent;padding:4px 14px}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl){position:relative;border:1px solid #243063;border-radius:20px;
  background:linear-gradient(180deg,rgba(24,34,72,.82),rgba(13,20,46,.82));padding:.6rem .9rem .5rem;margin:.4rem 0 1.2rem;
  box-shadow:0 18px 44px rgba(2,5,18,.45),inset 0 1px 0 rgba(159,216,255,.09)}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl):before{content:"";position:absolute;left:26px;right:26px;top:0;height:2px;
  border-radius:0 0 3px 3px;background:linear-gradient(90deg,transparent,var(--ntl-sodium,#F2A93B),var(--ntl-led,#9FD8FF),transparent);opacity:.85}
.ntl-dl{display:flex;align-items:center;gap:10px;margin:0 0 .5rem;font-family:var(--ntl-display);font-weight:700;font-size:.98rem;letter-spacing:-.01em}
.ntl-dl span{flex:none;display:grid;place-items:center;width:24px;height:24px;border-radius:50%;font-size:.78rem;
  border:1px solid var(--ntl-sodium,#F2A93B);color:var(--ntl-sodium,#F2A93B);background:rgba(242,169,59,.1)}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl) button[data-testid="stBaseButton-primary"]{
  min-height:3.6rem;font-size:1.05rem;border-radius:14px;box-shadow:0 8px 24px rgba(242,169,59,.28)}

.block-container{padding-top:4.4rem}
header[data-testid="stHeader"]{pointer-events:none}
header[data-testid="stHeader"] [data-testid="stToolbar"],header[data-testid="stHeader"] [data-testid="stToolbar"] *{pointer-events:auto}

div[data-testid="stElementContainer"]:has(style),div.element-container:has(style){display:none!important}

[data-testid="stRadio"] label[data-baseweb="radio"]>*:not(:last-child){position:absolute;width:1px;height:1px;opacity:0;overflow:hidden;pointer-events:none}
[data-testid="stRadio"] label[data-baseweb="radio"]>*:last-child{display:block!important}

div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"]{width:100%}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"] [role="radiogroup"]{
  width:100%;max-width:300px;margin-left:auto;flex-wrap:nowrap;gap:0}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"] label[data-baseweb="radio"]{
  flex:1 1 0;justify-content:center;text-align:center;padding:7px 14px;position:relative}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"] label[data-baseweb="radio"] p{white-space:nowrap}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl) [data-testid="stTextInput"] input{padding:.55rem .8rem}
[class*="st-key-srch_hit"]{margin-bottom:-.55rem}
[class*="st-key-srch_hit"] button{justify-content:flex-start;text-align:left;min-height:2.3rem;padding:.3rem .85rem;font-weight:500;
  font-size:.92rem;border:1px solid var(--ntl-line);background:rgba(26,36,76,.5)}
[class*="st-key-srch_hit"] button p{text-align:left;font-weight:500}
[class*="st-key-srch_hit"] button{display:flex;justify-content:flex-start}
[class*="st-key-srch_hit"] button>div,[class*="st-key-srch_hit"] button [data-testid="stMarkdownContainer"]{flex:1;text-align:left;justify-content:flex-start}
[class*="st-key-srch_nav"] button{min-height:2rem;padding:0;font-size:1.2rem;line-height:1}
[class*="st-key-srch_hit"] button:before{content:none}
[class*="st-key-srch_hit"] button:hover:not(:disabled){border-color:var(--ntl-sodium);background:rgba(242,169,59,.12)}
@media (max-width:760px){.block-container{max-width:100%}}
</style>
"""


# "Night chart sheet": the app is laid out like a survey sheet -- graticule paper, hairline rules,
# serif titles, monospace instrument readouts, square pixels. Override layer, injected last.
_SHEET_CSS = """
<style>
/* ----- giấy: lưới kinh vĩ rất mờ thay cho chấm ----- */
[data-testid="stMain"]{background:
  linear-gradient(rgba(142,153,184,.05) 1px,transparent 1px) 0 0/96px 96px,
  linear-gradient(90deg,rgba(142,153,184,.05) 1px,transparent 1px) 0 0/96px 96px,
  radial-gradient(900px 420px at 88% -10%,rgba(159,216,255,.045),transparent 62%),
  var(--ntl-night,#0A1024)}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-weight:600;letter-spacing:-.01em}

/* ----- banner = khung tờ bản đồ: viền kép + thước chia độ ----- */
.ntl-hero{border-radius:6px;border-color:#26335F;background:#080D1F}
.ntl-hero:before{content:"";position:absolute;inset:7px;border:1px solid rgba(142,153,184,.17);border-radius:2px;pointer-events:none;z-index:2}
.ntl-hero:after{content:"";position:absolute;left:7px;right:7px;bottom:7px;height:6px;pointer-events:none;z-index:2;opacity:.65;
  background:repeating-linear-gradient(90deg,rgba(142,153,184,.55) 0 1px,transparent 1px 12px)}
.ntl-hero-body{padding:34px 40px 40px}
.ntl-title{font-weight:600;font-size:2.15rem;line-height:1.1;letter-spacing:-.012em}
.ntl-sub{color:#9AA6C6}
.ntl-facts dt,.ntl-meta dt{font-family:var(--ntl-mono);font-size:.64rem;letter-spacing:.09em;text-transform:uppercase;color:#7F8BB0;opacity:1}
.ntl-facts dd{font-family:var(--ntl-mono);font-size:.8rem;font-weight:500}
.ntl-field{gap:4px}
.ntl-field i{border-radius:1px}
.ntl-field i.g{box-shadow:none}
.ntl-field i.l{box-shadow:0 0 9px rgba(159,216,255,.45)}

/* ----- thanh trên cùng + chuyển ngôn ngữ ----- */
.ntl-mark{border-radius:4px}
.ntl-mark i{border-radius:1px}
.ntl-brand b{font-family:var(--ntl-display);font-size:1.06rem;font-weight:600}
.ntl-brand span{font-family:var(--ntl-mono);font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;opacity:.6}
[data-testid="stRadio"] label[data-baseweb="radio"]{border-radius:4px}
div[data-testid="stHorizontalBlock"]:has(.ntl-brand) [data-testid="stRadio"] [role="radiogroup"]{border-radius:6px}

/* ----- bảng điều khiển = phiếu nhập liệu ----- */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl){border-radius:6px;border-color:#26335F;background:rgba(12,19,44,.72);
  box-shadow:none;padding:.9rem 1.1rem .6rem}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl):before{left:18px;right:auto;width:58px;height:3px;border-radius:0;
  background:var(--ntl-sodium,#F2A93B);opacity:1}
.ntl-dl{font-family:var(--ntl-display);font-size:1.05rem;font-weight:600;gap:10px;letter-spacing:-.005em}
.ntl-dl span{width:auto;height:auto;padding:2px 6px;border-radius:2px;font-family:var(--ntl-mono);font-size:.7rem;font-weight:500;
  letter-spacing:.06em;border:1px solid rgba(242,169,59,.55);background:none;color:var(--ntl-sodium,#F2A93B)}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ntl-dl) button[data-testid="stBaseButton-primary"]{
  min-height:3.4rem;border-radius:4px;box-shadow:none;font-size:1.02rem;letter-spacing:.01em}
button[data-testid="stBaseButton-primary"]:hover:not(:disabled){box-shadow:none;outline:2px solid rgba(242,169,59,.5);outline-offset:2px}
[class*="st-key-srch_hit"] button{border-radius:4px}
[class*="st-key-srch_hit"] button:before{content:"▸";color:var(--ntl-sodium,#F2A93B);font-family:var(--ntl-mono)}

/* ----- trạng thái chờ = quy trình thao tác (không thẻ, không vòng tròn) ----- */
.ntl-empty{text-align:left;margin:44px 0 8px}
.ntl-empty-h{font-size:2.3rem;font-weight:600;line-height:1.08;letter-spacing:-.015em}
.ntl-empty-p{margin:12px 0 0;max-width:64ch;text-align:left;opacity:.72}
.ntl-steps{gap:0 28px;margin-top:30px}
.ntl-steps li{padding:16px 0 6px;border:0;border-top:1px solid var(--ntl-rule);border-radius:0;background:none;
  transition:border-color .18s ease}
.ntl-steps li:first-child{border-top:2px solid var(--ntl-sodium)}
.ntl-steps li:hover{transform:none;box-shadow:none;border-top-color:var(--ntl-sodium)}
.ntl-steps .n{display:block;place-items:unset;text-align:left;width:auto;height:auto;border:0;border-radius:0;background:none!important;backdrop-filter:none;
  font-family:var(--ntl-mono);font-size:.78rem;font-weight:500;letter-spacing:.08em;color:#7F8BB0}
.ntl-steps li:first-child .n{color:var(--ntl-sodium)}
.ntl-steps b{font-family:var(--ntl-display);font-size:1.12rem;font-weight:600}
.ntl-steps span{font-size:.9rem}

/* ----- tiêu đề kết quả = bảng ghi địa điểm ----- */
.ntl-plate{align-items:stretch;flex-wrap:wrap;gap:16px 34px;margin:0 0 18px;padding:2px 0 0}
.ntl-where{flex:1 1 280px;align-self:center}
.ntl-where .up{font-family:var(--ntl-mono);font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;opacity:.62;margin-bottom:6px}
.ntl-where .name{font-size:2.5rem;font-weight:600;line-height:1.04;letter-spacing:-.018em}
.ntl-where .name:before{display:none}
.ntl-where .co{margin-top:10px;font-family:var(--ntl-mono);font-size:.78rem;letter-spacing:.04em;color:var(--ntl-sodium)}
.ntl-meta{align-self:center}
.ntl-sig{flex:0 0 auto;align-self:center;display:grid;grid-template-columns:repeat(var(--c),1fr);gap:2px;
  width:clamp(150px,20vw,250px);padding:8px;border:1px solid var(--ntl-rule);border-radius:2px;background:#080D1F}
.ntl-sig i{display:block;aspect-ratio:1/1;opacity:0;animation:ntlSig .45s cubic-bezier(.2,.7,.2,1) var(--d,0s) forwards}
.ntl-sig i.e{background:none;animation:none;opacity:1}
@keyframes ntlSig{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.ntl-sig i{animation:none;opacity:1}}
@media (max-width:640px){.ntl-sig{width:100%;max-width:260px}}

/* ----- số đo = đồng hồ đọc số ----- */
div[data-testid="stMetricLabel"] p{font-family:var(--ntl-mono);font-size:.68rem;letter-spacing:.07em;text-transform:uppercase;opacity:.66}
div[data-testid="stMetricValue"]{font-family:var(--ntl-display);font-weight:600;font-variant-numeric:lining-nums tabular-nums}

/* ----- đề mục trong tab: đánh số kiểu tờ bản đồ ----- */
div[data-baseweb="tab-panel"]{counter-reset:ntlsec}
[data-testid="stMain"] h3{counter-increment:ntlsec;font-size:1.4rem;font-weight:600;gap:12px}
[data-testid="stMain"] h3:before{content:counter(ntlsec,decimal-leading-zero);width:auto;height:auto;padding:2px 6px;border-radius:2px;
  border:1px solid rgba(242,169,59,.5);background:none;font-family:var(--ntl-mono);font-size:.7rem;font-weight:500;
  letter-spacing:.06em;color:var(--ntl-sodium)}

/* ----- bo góc vuông hơn ở mọi nơi còn lại ----- */
div[data-testid="stDataFrame"],div[data-testid="stAlert"],div[data-testid="stAlertContainer"],
div[data-testid="stStatus"],div[data-testid="stStatusWidget"],div[data-testid="stToast"],.ntl-top{border-radius:4px}
iframe{border-radius:var(--ntl-r-panel)}
</style>
"""


_FX_JS = r"""
<script>
(function () {
  var P = window.parent, D;
  try { D = P.document; } catch (e) { return; }
  if (P.__ntlFx3) { return; }
  P.__ntlFx3 = true;
  var reduce = P.matchMedia && P.matchMedia('(prefers-reduced-motion: reduce)').matches;


  var root = D.documentElement;
  var nav = P.navigator || {};
  var weak = reduce || (nav.hardwareConcurrency && nav.hardwareConcurrency <= 2) ||
             (nav.deviceMemory && nav.deviceMemory <= 2) || (nav.connection && nav.connection.saveData);
  if (weak) { root.classList.add('ntl-calm'); }
  else if (P.requestAnimationFrame) {

    var n = 0, t0 = 0;
    (function probe(ts) {
      if (!t0) { t0 = ts; }
      if (++n < 40) { P.requestAnimationFrame(probe); return; }
      if ((ts - t0) / (n - 1) > 34) { root.classList.add('ntl-calm'); }
    })(0);
  }

  setInterval(function () {
    var h = D.querySelector('.ntl-hero');
    var out = D.hidden || !h || h.getBoundingClientRect().bottom < 0;
    root.classList.toggle('ntl-offscreen', !!out);
  }, 800);


  function textNode(el) {
    var w = D.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n;
    while ((n = w.nextNode())) { if (/\d/.test(n.nodeValue)) { return n; } }
    return null;
  }
  function animate(el) {
    if (el.__ntlBusy) { return; }
    var tn = textNode(el);
    if (!tn) { return; }
    var full = tn.nodeValue;
    if (el.__ntlLast === full) { return; }
    el.__ntlLast = full;
    var m = full.match(/^([^\d\-+]*)([\-+]?[\d,]*\.?\d+)(.*)$/);
    if (!m || reduce) { return; }
    var raw = m[2], target = parseFloat(raw.replace(/,/g, ''));
    if (!isFinite(target) || target === 0) { return; }
    var dec = raw.indexOf('.') >= 0 ? raw.split('.')[1].length : 0;
    var commas = raw.indexOf(',') >= 0;
    function fmt(v) {
      var s = v.toFixed(dec);
      if (commas) { var a = s.split('.'); a[0] = a[0].replace(/\B(?=(\d{3})+(?!\d))/g, ','); s = a.join('.'); }
      return m[1] + s + m[3];
    }
    var t0 = null, dur = 600, last = null;
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
  function checkPrimary() {
    var th = D.querySelector('[data-testid="stSlider"] [role="slider"]');
    if (!th) { return; }
    var m = P.getComputedStyle(th).backgroundColor.match(/\d+/g);
    if (!m) { return; }
    D.documentElement.classList.toggle('ntl-redfix', +m[0] > 200 && +m[1] < 130 && +m[2] < 130);
  }
  function scan() {
    pending = false;
    D.querySelectorAll('[data-testid="stMetricValue"]').forEach(animate);
    checkPrimary();
  }
  new P.MutationObserver(function () {
    if (!pending) { pending = true; P.requestAnimationFrame(scan); }
  }).observe(D.body, {childList: true, subtree: true});
  scan();


  var top = D.createElement('button'); top.className = 'ntl-top'; top.type = 'button';
  top.setAttribute('aria-label', 'Back to top'); top.textContent = '↑';
  D.body.appendChild(top);
  var tries = 0;
  function bind() {
    var sc = D.querySelector('[data-testid="stMain"]') || D.querySelector('section.main');
    if (!sc) { if (tries++ < 20) { setTimeout(bind, 400); } return; }
    function upd() { top.classList.toggle('show', sc.scrollTop > 500); }
    sc.addEventListener('scroll', upd, {passive: true});
    top.addEventListener('click', function () { sc.scrollTo({top: 0, behavior: reduce ? 'auto' : 'smooth'}); });
    upd();
  }
  bind();
})();
</script>
"""


def inject_theme() -> None:
    st.markdown(_FONTS, unsafe_allow_html=True)
    st.markdown(_THEME_CSS, unsafe_allow_html=True)
    st.markdown(_UX_CSS, unsafe_allow_html=True)
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
    st.markdown(_SHEET_CSS, unsafe_allow_html=True)


def enable_fx() -> None:
    """Enable optional JavaScript effects."""
    try:
        import streamlit.components.v1 as components
        components.html(_FX_JS, height=0)
    except Exception:  # noqa: BLE001
        pass


def _esc(x) -> str:
    return _html.escape(str(x))


def _field_html(cols: int = 26, rows: int = 7) -> str:
    """Build the decorative grid field used by the hero banner."""
    seed = 11

    def rnd() -> float:
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return seed / 0x7FFFFFFF

    cx0, cy0 = 18.0, 3.0
    blobs = [(cx0, cy0, 1.0, 3.4), (9.5, 4.4, .62, 2.5), (23.0, 5.0, .5, 2.0), (13.0, 1.0, .4, 2.2), (4.5, 2.2, .3, 1.7)]
    out = []
    for r in range(rows):
        for c in range(cols):
            v = sum(a * math.exp(-((c - bx) ** 2 + (r - by) ** 2) / (2 * s * s)) for bx, by, a, s in blobs)
            v += (rnd() - .5) * .3
            if v < .16:
                cls, o = "", .12
            elif v < .36:
                cls, o = "s", .4
            elif v < .6:
                cls, o = "s", .72
            elif v < .86:
                cls, o = "s g", 1
            else:
                cls, o = "l", 1
            d = math.hypot(c - cx0, r - cy0) * .034
            idx = r * cols + c
            tw = ""
            if o >= .4 and (idx * 37 + 5) % 11 < 4:
                cls = (cls + " t").strip()
                tw = f";--t:{2.8 + (idx % 5) * .7:.1f}s;--p:{(idx % 7) * .35:.2f}s"
            elif o >= .4:
                cls = (cls + " r").strip()
                tw = f";--r:{math.hypot(c - cx0, r - cy0) * .16:.2f}s"
            out.append(f'<i class="{cls}" style="--d:{d:.2f}s;--o:{o}{tw}"></i>')
    return "".join(out)


_FIELD = None


def hero(title: str, subtitle: str, facts=None, chips=None) -> None:
    """Render the hero banner with optional label-value facts."""
    global _FIELD
    if _FIELD is None:
        _FIELD = _field_html()
    items = facts if facts is not None else chips
    fh = ""
    if items:
        fh = '<dl class="ntl-facts">' + "".join(
            f"<div><dt>{_esc(k)}</dt><dd>{_esc(v)}</dd></div>" for k, v in items
        ) + "</dl>"
    clean = re.sub(r"^[^\w]+", "", title)
    st.markdown(
        f'<div class="ntl-hero"><div class="ntl-field" aria-hidden="true">{_FIELD}</div>'
        f'<div class="ntl-hero-body"><div class="ntl-title">{_esc(clean)}</div>'
        f'<div class="ntl-sub">{_esc(subtitle)}</div>{fh}</div></div>',
        unsafe_allow_html=True,
    )


def sidebar_brand(title: str, subtitle: str) -> None:
    mark = "".join(f'<i class="{c}"></i>' for c in ("", "s", "", "s", "l", "s", "", "s", ""))
    st.markdown(
        f'<div class="ntl-brand"><div class="ntl-mark" aria-hidden="true">{mark}</div>'
        f'<div><b>{_esc(title)}</b><span>{_esc(subtitle)}</span></div></div>',
        unsafe_allow_html=True,
    )


def deck_label(n, text: str) -> None:
    """Render a numbered label for a control-panel group."""
    import re
    t = re.sub(r"^\s*\d+\.\s*", "", str(text))
    tag = f"{n:02d}" if isinstance(n, int) else str(n)
    st.markdown(f'<div class="ntl-dl"><span>{_esc(tag)}</span>{_esc(t)}</div>', unsafe_allow_html=True)


def empty_state(title: str, hint: str, steps) -> None:
    lis = "".join(
        f'<li><div class="n">{i:02d}</div><div><b>{_esc(t)}</b><span>{_esc(d)}</span></div></li>'
        for i, (t, d) in enumerate(steps, 1)
    )
    st.markdown(
        f'<div class="ntl-empty"><div><div class="ntl-empty-h">{_esc(title)}</div>'
        f'<div class="ntl-empty-p">{_esc(hint)}</div></div><ol class="ntl-steps">{lis}</ol></div>',
        unsafe_allow_html=True,
    )


def _dms(lat: float, lon: float) -> str:
    """Format a coordinate pair as degrees and minutes, e.g. 47°50′N · 16°32′E."""
    def one(v: float, pos: str, neg: str) -> str:
        t = int(round(abs(v) * 60))
        return f"{t // 60}°{t % 60:02d}′{pos if v >= 0 else neg}"
    return f"{one(lat, 'N', 'S')} · {one(lon, 'E', 'W')}"


# Colour ramp of the light signature: unlit -> dim amber -> sodium -> LED white-blue.
_SIG_RAMP = ((0.0, (27, 35, 72)), (0.45, (150, 104, 30)), (0.78, (242, 169, 59)), (1.0, (159, 216, 255)))


def _sig_color(t: float) -> str:
    for (t0, c0), (t1, c1) in zip(_SIG_RAMP, _SIG_RAMP[1:]):
        if t <= t1:
            k = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return "#%02X%02X%02X" % tuple(int(round(a + (b - a) * k)) for a, b in zip(c0, c1))
    return "#%02X%02X%02X" % _SIG_RAMP[-1][1]


def light_signature(x, y, v, cols: int = 30, max_rows: int = 14) -> str:
    """Pixel portrait of a locality: grid-cell centroids (x, y) with NTL values v, binned to a small
    square-pixel raster. Display only; it never feeds back into any computation."""
    import numpy as np
    x, y, v = (np.asarray(a, dtype=float) for a in (x, y, v))
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(v)
    if ok.sum() < 2:
        return ""
    x, y, v = x[ok], y[ok], np.maximum(v[ok], 0.0)
    dx, dy = float(np.ptp(x)), float(np.ptp(y))
    step = max(dx / cols, dy / max_rows, 1e-9)
    ix = np.minimum(((x - x.min()) / step).astype(int), int(dx / step))
    iy = np.minimum(((y.max() - y) / step).astype(int), int(dy / step))      # north at the top
    nc, nr = int(ix.max()) + 1, int(iy.max()) + 1
    tot = np.zeros((nr, nc)); cnt = np.zeros((nr, nc))
    np.add.at(tot, (iy, ix), v); np.add.at(cnt, (iy, ix), 1.0)
    mean = np.divide(tot, cnt, out=np.zeros_like(tot), where=cnt > 0)
    pos = mean[mean > 0]
    hi = float(np.quantile(pos, 0.99)) if pos.size else 0.0
    norm = np.clip(np.log1p(mean) / np.log1p(hi), 0, 1) if hi > 0 else np.zeros_like(mean)
    pk = np.unravel_index(int(np.argmax(norm)), norm.shape)
    out = []
    for r in range(nr):
        for c in range(nc):
            if cnt[r, c] == 0:
                out.append("<i class=\"e\"></i>")
                continue
            d = min(math.hypot(r - pk[0], c - pk[1]) * 0.035, 1.2)
            out.append(f'<i style="--d:{d:.2f}s;background:{_sig_color(float(norm[r, c]))}"></i>')
    return f'<div class="ntl-sig" style="--c:{nc}" aria-hidden="true">{"".join(out)}</div>'


def place_banner(place: str, facts, signature=None, coord=None) -> None:
    """Render a locality path, optional metadata facts, a coordinate readout and a light signature.

    signature: optional (x, y, values) arrays, drawn as a pixel portrait of the locality.
    coord: optional (lat, lon) in degrees.
    """
    parts = [p.strip() for p in str(place).split(" / ") if p.strip()]
    name = parts[-1] if parts else str(place)
    up = " / ".join(parts[:-1])
    meta = ""
    if facts:
        cells = []
        for f in facts:
            if isinstance(f, (tuple, list)) and len(f) == 2:
                cells.append(f"<div><dt>{_esc(f[0])}</dt><dd>{_esc(f[1])}</dd></div>")
            else:
                cells.append(f"<div><dd>{_esc(f)}</dd></div>")
        meta = '<dl class="ntl-meta">' + "".join(cells) + "</dl>"
    up_html = f'<div class="up">{_esc(up)}</div>' if up else ""
    co_html = ""
    if coord is not None:
        try:
            co_html = f'<div class="co">{_esc(_dms(float(coord[0]), float(coord[1])))}</div>'
        except (TypeError, ValueError, IndexError):
            co_html = ""
    sig_html = ""
    if signature is not None:
        try:
            sig_html = light_signature(*signature)
        except Exception:  # noqa: BLE001  (decoration must never break the page)
            sig_html = ""
    st.markdown(
        f'<div class="ntl-plate"><div class="ntl-where">{up_html}<div class="name">{_esc(name)}</div>{co_html}</div>'
        f'{meta}{sig_html}</div>',
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="ntl-sec">{_esc(title)}</div>', unsafe_allow_html=True)
