"""
generate_dashboard.py  —  Génère dashboard.html (standalone, offline-ready)
Usage : python generate_dashboard.py
"""
import csv, json, os, base64
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Charge Chart.js (offline si disponible, CDN sinon) ──────────────────────
_chartjs_path = os.path.join(BASE, "chart.min.js")
if os.path.exists(_chartjs_path):
    with open(_chartjs_path, encoding="utf-8") as _f:
        CHARTJS = "<script>" + _f.read() + "</script>"
else:
    CHARTJS = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'

GENERATED = datetime.now().strftime("%d/%m/%Y %H:%M")

_logo_path = os.path.join(BASE, "veolia.png")
LOGO_B64 = ("data:image/png;base64," + base64.b64encode(open(_logo_path,"rb").read()).decode()) if os.path.exists(_logo_path) else ""

# ── Lecture CSV ──────────────────────────────────────────────────────────────
def load_csv(filename):
    path = os.path.join(BASE, filename)
    with open(path, encoding="utf-8-sig") as f:
        rows = []
        for row in csv.DictReader(f):
            clean = {}
            for k, v in row.items():
                try:
                    clean[k] = float(v) if v != "" else None
                except (ValueError, TypeError):
                    clean[k] = v
            rows.append(clean)
    return rows

data      = load_csv("data_synthese.csv")
data_eur_t = load_csv("data_synthese_eur_t.csv")

DATA_JSON  = json.dumps(data,       ensure_ascii=True)
EUR_T_JSON = json.dumps(data_eur_t, ensure_ascii=True)

# ── Template HTML ────────────────────────────────────────────────────────────
HTML = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>P&L Centres de Tri</title>
%%CHARTJS%%
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#f0f2f5;color:#1a1a2e}
/* header */
header{background:linear-gradient(135deg,#003a63 0%,#00a3e0 100%);color:#fff;padding:16px 28px;display:flex;align-items:center;justify-content:space-between}
header h1{font-size:1.3rem;font-weight:700}
.header-right{text-align:right;font-size:.78rem;opacity:.85;line-height:1.6}
/* tabs */
.tabs{display:flex;background:#fff;border-bottom:2px solid #e8eaed;padding:0 28px;gap:4px}
.tab{padding:13px 22px;cursor:pointer;font-size:.88rem;font-weight:500;color:#666;border-bottom:3px solid transparent;margin-bottom:-2px;transition:all .2s}
.tab:hover{color:#00a3e0}
.tab.active{color:#00a3e0;border-bottom-color:#00a3e0;font-weight:600}
/* toolbar */
.toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:18px 28px 14px;border-bottom:1px solid #eef0f2}
.toolbar label{font-size:.82rem;color:#555;margin-right:2px;font-weight:600}
.btn-pill{padding:6px 18px;border:2px solid #00a3e0;border-radius:20px;background:transparent;color:#00a3e0;cursor:pointer;font-size:.82rem;font-weight:500;transition:all .15s}
.btn-pill:hover{background:#e0f6ff}
.btn-pill.active{background:#00a3e0;color:#fff}
.btn-pill.budget{border-color:#f59e0b;color:#d97706}.btn-pill.budget.active{background:#f59e0b;color:#fff;border-color:#f59e0b}
select.sel{padding:5px 12px;border:2px solid #e0e0e0;border-radius:8px;font-size:.85rem;background:#fff;color:#333;cursor:pointer;outline:none}
select.sel:focus{border-color:#00a3e0}
.spacer{flex:1}
.btn-print{padding:7px 20px;background:#00a3e0;border:none;border-radius:8px;font-size:.82rem;cursor:pointer;color:#fff;font-weight:600;transition:all .15s;letter-spacing:.2px}
.btn-print:hover{background:#0092c9}
/* page */
.page{display:none;padding:20px 28px 32px}
.page.active{display:block}
/* kpis */
.kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:18px 0 16px}
.kpi-card{background:#fff;border-radius:12px;padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,.08);border-left:4px solid #0f3460}
.kpi-card.g{border-left-color:#10b981}.kpi-card.o{border-left-color:#f59e0b}
.kpi-card.r{border-left-color:#ef4444}.kpi-card.p{border-left-color:#8b5cf6}
.kpi-label{font-size:.7rem;text-transform:uppercase;letter-spacing:.8px;color:#888;margin-bottom:6px}
.kpi-value{font-size:1.5rem;font-weight:700}
.kpi-sub{font-size:.7rem;color:#aaa;margin-top:3px}
/* alertes */
.alert-bar{background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:11px 18px;margin-bottom:16px;font-size:.82rem;color:#dc2626;display:flex;align-items:center;gap:10px}
.alert-bar.hidden{display:none}
.alert-ok{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:11px 18px;margin-bottom:16px;font-size:.82rem;color:#16a34a;display:flex;align-items:center;gap:10px}
.alert-trend{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:11px 18px;margin-bottom:16px;font-size:.82rem;color:#d97706;display:flex;align-items:center;gap:10px}
.alert-trend.hidden{display:none}
.site-link{cursor:pointer;color:#003a63;text-decoration:underline dotted;text-underline-offset:2px}
.site-link:hover{color:#00a3e0}
/* ranking */
.rank-table{width:100%;border-collapse:collapse;font-size:.82rem}
.rank-table th{background:#003a63;color:#fff;padding:8px 12px;text-align:right;font-weight:600}
.rank-table th:first-child{text-align:left}
.rank-table td{padding:7px 12px;border-bottom:1px solid #f0f0f0;text-align:right}
.rank-table td:first-child{text-align:left}
.rank-table tr.best-row td{background:#f0fdf4}
.rank-table tr.worst-row td{background:#fef2f2}
.rank-num{display:inline-block;width:22px;height:22px;border-radius:50%;text-align:center;line-height:22px;font-size:.7rem;font-weight:700;margin-right:6px;color:#fff}
.rn-g{background:#10b981}.rn-r{background:#ef4444}.rn-d{background:#94a3b8}
/* categories quadrant */
.cat-legend{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 6px;font-size:.8rem}
.cat-badge{display:flex;align-items:center;gap:6px;padding:5px 13px;border-radius:20px;font-weight:600}
.cat-badge.champ{background:#dcfce7;color:#15803d}
.cat-badge.effic{background:#dbeafe;color:#1d4ed8}
.cat-badge.devel{background:#fff7ed;color:#c2410c}
.cat-badge.diff{background:#fef2f2;color:#dc2626}
.cat-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
/* chart cards */
.row2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}
.card{background:#fff;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.card.full{grid-column:1/-1}
.card-title{font-size:.78rem;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:.5px;margin-bottom:14px}
.ch{position:relative;height:300px}
.ch.tall{height:380px}
.ch.med{height:260px}
/* tables */
.pl-table{width:100%;border-collapse:collapse;font-size:.82rem}
.pl-table th{background:#003a63;color:#fff;padding:9px 12px;text-align:right;font-weight:600}
.pl-table th:first-child{text-align:left}
.pl-table td{padding:7px 12px;border-bottom:1px solid #f0f0f0;text-align:right}
.pl-table td:first-child{text-align:left;color:#555}
.pl-table tr:hover td{background:#f8f9ff}
.pl-table tr.sub td{font-weight:600;background:#eef2ff;color:#1a1a2e}
.pl-table tr.tot td{font-weight:700;background:#003a63;color:#fff;font-size:.86rem}
.indent{padding-left:26px!important;color:#777;font-size:.79rem}
.pos{color:#10b981;font-weight:600}.neg{color:#ef4444;font-weight:600}
/* heatmap */
.hm-wrap{overflow-x:auto}
.hm-table{width:100%;border-collapse:collapse;font-size:.8rem}
.hm-table th{background:#003a63;color:#fff;padding:7px 10px;text-align:center;white-space:nowrap}
.hm-table th:first-child{text-align:left}
.hm-table td{padding:6px 10px;text-align:center;border-bottom:1px solid #eee}
.hm-table td:first-child{text-align:left;font-weight:500;color:#333}
/* executive summary */
.exec-summary{background:linear-gradient(135deg,#003a63 0%,#005a94 100%);color:#fff;border-radius:12px;padding:18px 24px;margin-bottom:20px;display:none}
.es-title{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;opacity:.65;margin-bottom:12px}
.es-grid{display:flex;flex-wrap:wrap;gap:6px}
.es-cell{background:rgba(255,255,255,.1);border-radius:8px;padding:8px 14px;min-width:110px}
.es-cell.es-period{background:rgba(255,255,255,.18)}
.es-label{font-size:.65rem;text-transform:uppercase;letter-spacing:.7px;opacity:.65;margin-bottom:2px}
.es-val{font-size:.95rem;font-weight:700;line-height:1.2}
/* mini-synthèse site */
.dt-exec{background:#f0f8ff;border-left:4px solid #00a3e0;border-radius:0 10px 10px 0;padding:14px 20px;margin:18px 0 4px;font-size:.85rem;line-height:1.9;color:#1a1a2e}
.dt-exec-title{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.9px;color:#00a3e0;margin-bottom:5px}
.dt-exec .neg{color:#ef4444;font-weight:700}.dt-exec .pos{color:#10b981;font-weight:700}
/* print */
@media print{
  .tabs,.toolbar,.btn-print{display:none!important}
  .page{display:none!important}
  .page.active{display:block!important;padding:6px 10px}
  header{background:#003a63!important;-webkit-print-color-adjust:exact;print-color-adjust:exact;padding:8px 18px!important;color:#fff!important}
  header h1,header .header-right{color:#fff!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .exec-summary{background:#003a63!important;color:#fff!important;-webkit-print-color-adjust:exact;print-color-adjust:exact;display:block!important;page-break-inside:avoid}
  .home-cover{min-height:auto;background:#fff!important}
  body{background:#fff!important}
  .card{break-inside:avoid;page-break-inside:avoid;box-shadow:none!important;border:1px solid #e0e0e0;margin-bottom:8px}
  .kpi-grid,.kpi-card{-webkit-print-color-adjust:exact;print-color-adjust:exact;break-inside:avoid}
  .kpi-card.g,.kpi-card.p,.kpi-card.r,.kpi-card.o{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .row2{grid-template-columns:1fr 1fr;gap:8px}
  .alert-bar,.alert-ok{page-break-inside:avoid;-webkit-print-color-adjust:exact;print-color-adjust:exact;display:block!important}
  .card-title,.kpi-label,.kpi-value,.kpi-sub{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .pos{color:#10b981!important}.neg{color:#ef4444!important}
  .ch{height:200px!important}.ch.tall{height:220px!important}
  .podium-grid{grid-template-columns:1fr 1fr}
  canvas{max-width:100%!important}
  @page{size:A4 landscape;margin:8mm 10mm}
}
/* ── Présentation mode ────────────────────────────────── */
.card{transition:box-shadow .2s,transform .12s ease}
.btn-pill{transition:all .15s ease}
.kpi-card{transition:box-shadow .2s,transform .12s ease}
.exec-summary{transition:background .3s}
.cmp-metric-row:last-child{border-bottom:none}
/* ── Page de garde ────────────────────────────────── */
.home-cover{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:72vh;text-align:center;padding:40px 20px;background:linear-gradient(160deg,#f0f6ff 0%,#fff 60%)}
.home-logo{height:72px;margin-bottom:30px}
.home-title{font-size:2rem;font-weight:800;color:#003a63;margin-bottom:6px;letter-spacing:-.5px}
.home-sub{font-size:1rem;color:#5a6a7a;margin-bottom:10px}
.home-period{font-size:.82rem;color:#aaa;margin-bottom:36px}
.home-kpis{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;margin-bottom:28px}
.home-kpi{background:#fff;border-radius:14px;padding:20px 28px;box-shadow:0 2px 16px rgba(0,58,99,.1);min-width:140px;border-top:4px solid #00a3e0}
.home-kpi.g{border-top-color:#10b981}
.home-kpi.o{border-top-color:#f59e0b}
.home-kpi-val{font-size:1.7rem;font-weight:800;color:#1a1a2e;line-height:1.1}
.home-kpi-lbl{font-size:.68rem;text-transform:uppercase;letter-spacing:.7px;color:#888;margin-top:5px}
.home-kpi-trend{font-size:.75rem;font-weight:600;margin-top:5px}
.home-date{font-size:.75rem;color:#bbb;margin-top:10px}
/* ── KPI trends ── */
.kpi-trend{font-size:.72rem;font-weight:600;margin-top:2px;min-height:14px}
/* ── Top 3 / Flop 3 ── */
.podium-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px}
.podium-card{background:#fff;border-radius:10px;padding:14px 18px;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.podium-title{font-size:.7rem;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#555;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.podium-row{display:flex;justify-content:space-between;align-items:center;padding:5px 2px;border-bottom:1px solid #f3f4f6;font-size:.82rem}
.podium-row:last-child{border-bottom:none}
/* ── Comparaison 2 sites ── */
#dt-compare{margin:0 0 14px;display:none}
.cmp-wrap{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.cmp-side{background:#fff;border-radius:10px;padding:14px 18px;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.cmp-site-title{font-size:.95rem;font-weight:700;color:#003a63;border-left:4px solid #00a3e0;padding-left:10px;margin-bottom:10px}
.cmp-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f3f4f6;font-size:.82rem}
.cmp-row:last-child{border-bottom:none}
.cmp-delta{font-size:.72rem;font-weight:600;margin-left:8px}
</style>
</head>
<body>
<header>
  <div style="display:flex;align-items:center;gap:14px">
    <img src="%%LOGO%%" alt="Veolia" style="height:32px;filter:brightness(0) invert(1);opacity:.92">
    <h1>Dashboard P&amp;L &#8212; Centres de Tri</h1>
  </div>
  <div class="header-right">
    <div>R2023 &middot; R2024 &middot; R2025 &middot; <span style="background:rgba(245,158,11,.35);border:1px solid rgba(245,158,11,.6);padding:1px 7px;border-radius:4px;font-size:.75rem;font-weight:700">B2026</span></div>
    <div>Mis &agrave; jour le %%DATE%%</div>
  </div>
</header>

<div class="tabs">
  <div class="tab active"  onclick="showTab('home',this)">&#127968; Accueil</div>
  <div class="tab"         onclick="showTab('ov',this)">Vue d&#8217;ensemble</div>
  <div class="tab"         onclick="showTab('dt',this)">D&eacute;tail par site</div>
  <div class="tab"         onclick="showTab('et',this)">Vue &euro;/t</div>
  <div class="tab"         onclick="showTab('rg',this)">R&eacute;gion</div>
</div>

<!-- ═══ ONGLET 0 — PAGE DE GARDE ════════════════════════════════════════════ -->
<div class="page active" id="tab-home">
  <div class="home-cover">
    <img src="%%LOGO%%" alt="Veolia" class="home-logo">
    <div class="home-title">Dashboard P&amp;L &mdash; Centres de Tri</div>
    <div class="home-sub">Analyse de performance du parc de centres de tri</div>
    <div class="home-period">R2023 &middot; R2024 &middot; R2025 &middot; B2026</div>
    <div class="home-kpis">
      <div class="home-kpi"><div class="home-kpi-val" id="hm-ca">—</div><div class="home-kpi-lbl">CA Total (R2025)</div><div class="home-kpi-trend" id="hm-ca-tr"></div></div>
      <div class="home-kpi g"><div class="home-kpi-val" id="hm-eb">—</div><div class="home-kpi-lbl">EBITDA Total (R2025)</div><div class="home-kpi-trend" id="hm-eb-tr"></div></div>
      <div class="home-kpi o"><div class="home-kpi-val" id="hm-tn">—</div><div class="home-kpi-lbl">Tonnes Entrantes (R2025)</div><div class="home-kpi-trend" id="hm-tn-tr"></div></div>
      <div class="home-kpi"><div class="home-kpi-val" id="hm-tx">—</div><div class="home-kpi-lbl">Taux EBITDA (R2025)</div><div class="home-kpi-trend" id="hm-tx-tr"></div></div>
      <div class="home-kpi"><div class="home-kpi-val" id="hm-ns">—</div><div class="home-kpi-lbl">Sites suivis</div><div class="home-kpi-trend" id="hm-ns-tr"></div></div>
    </div>
    <div class="home-date">Mis &agrave; jour le %%DATE%%</div>
  </div>
</div>

<!-- ═══ ONGLET 1 — VUE D'ENSEMBLE ═══════════════════════════════════════════ -->
<div class="page" id="tab-ov">
  <div class="toolbar">
    <label>Ann&eacute;e :</label>
    <button class="btn-pill ov-yr active" onclick="toggleOvYear('all',this)">Tous</button>
    <button class="btn-pill ov-yr" onclick="toggleOvYear('2023',this)">R2023</button>
    <button class="btn-pill ov-yr" onclick="toggleOvYear('2024',this)">R2024</button>
    <button class="btn-pill ov-yr" onclick="toggleOvYear('2025',this)">R2025</button>
    <button class="btn-pill ov-yr budget" onclick="toggleOvYear('2026',this)">B2026</button>
    <label style="margin-left:14px">Sites :</label>
    <div id="ov-site-pills" style="display:flex;gap:4px;flex-wrap:wrap">
      <button class="btn-pill active" onclick="toggleOvSite('all',this)">Tous</button>
    </div>
    <div class="spacer"></div>
    <button class="btn-print" onclick="window.print()" title="Imprime l'onglet actif en PDF A4 paysage">&#128438; Exporter PDF</button>
  </div>
  <div id="exec-summary" class="exec-summary"></div>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-label">Chiffre d&#8217;Affaires</div><div class="kpi-value" id="kpi-ca">&#8212;</div><div class="kpi-sub" id="kpi-ca-s"></div><div class="kpi-trend" id="kpi-ca-tr"></div></div>
    <div class="kpi-card g"><div class="kpi-label">EBITDA</div><div class="kpi-value" id="kpi-eb">&#8212;</div><div class="kpi-sub" id="kpi-eb-s"></div><div class="kpi-trend" id="kpi-eb-tr"></div></div>
    <div class="kpi-card o"><div class="kpi-label">Tonnes Entrantes</div><div class="kpi-value" id="kpi-tn">&#8212;</div><div class="kpi-sub" id="kpi-tn-s"></div><div class="kpi-trend" id="kpi-tn-tr"></div></div>
    <div class="kpi-card p" id="kpi-card-best"><div class="kpi-label">&#127942; Meilleur site EBITDA</div><div class="kpi-value" id="kpi-best">&#8212;</div><div class="kpi-sub" id="kpi-best-s"></div></div>
    <div class="kpi-card r" id="kpi-card-worst"><div class="kpi-label">&#9888;&#65039; Site en alerte</div><div class="kpi-value" id="kpi-worst">&#8212;</div><div class="kpi-sub" id="kpi-worst-s"></div></div>
  </div>
  <div class="alert-bar hidden" id="alert-bar">&#128680; <span id="alert-msg"></span></div>
  <div class="alert-trend hidden" id="alert-trend">&#128201; <span id="alert-trend-msg"></span></div>
  <div class="alert-ok hidden" id="alert-ok">&#10004;&#65039; <span id="alert-ok-msg"></span></div>
  <div class="card full" id="rank-card" style="margin-bottom:18px">
    <div class="card-title">Classement EBITDA par site (derni&egrave;re p&eacute;riode s&eacute;lectionn&eacute;e)</div>
    <div id="rank-wrap"></div>
  </div>
  <div class="row2">
    <div class="card full"><div class="card-title">Chiffre d&#8217;Affaires par site</div><div class="ch tall"><canvas id="c-ca"></canvas></div></div>
  </div>
  <div class="row2">
    <div class="card full"><div class="card-title" id="eb-chart-title">EBITDA par site</div><div class="ch" id="eb-chart-wrap"><canvas id="c-eb"></canvas></div></div>
  </div>
  <div class="row2">
    <div class="card full"><div class="card-title">&Eacute;volution de la marge EBITDA % par site &#8212; R&eacute;el uniquement (R2023 &rarr; R2025)</div><div class="ch tall"><canvas id="c-marg"></canvas></div></div>
  </div>
</div>

<!-- ═══ ONGLET 2 — DETAIL PAR SITE ══════════════════════════════════════════ -->
<div class="page" id="tab-dt">
  <div class="toolbar">
    <label>Site :</label>
    <select class="sel" id="dt-site" onchange="renderDt()"></select>
    <label style="margin-left:14px">Comparer avec :</label>
    <select class="sel" id="dt-site2" onchange="renderDt()">
      <option value="">— aucun —</option>
    </select>
    <div class="spacer"></div>
    <button class="btn-print" onclick="window.print()" title="Imprime l'onglet actif en PDF A4 paysage">&#128438; Exporter PDF</button>
  </div>
  <div id="dt-compare" class="dt-exec"></div>
  <div id="dt-exec" class="dt-exec" style="display:none;margin:0 28px 0"></div>
  <div class="row2" id="dt-row-evol" style="margin-top:16px">
    <div class="card"><div class="card-title">&Eacute;volution CA / Marge / EBITDA / EBIT</div><div class="ch"><canvas id="c-evol"></canvas></div></div>
    <div class="card" id="dt-card-donut"><div class="card-title">R&eacute;partition des charges internes
      <select class="sel" id="donut-year" onchange="renderDonut()" style="margin-left:10px;font-size:.8rem">
        <option value="2025">R2025</option><option value="2024">R2024</option><option value="2023">R2023</option>
      </select>
    </div><div class="ch"><canvas id="c-donut"></canvas></div></div>
  </div>
  <div class="row2" id="dt-row-bench" style="margin-top:0">
    <div class="card"><div class="card-title">Positionnement vs parc &#8212; EBITDA &euro;/t
      <select class="sel" id="bench-year" onchange="renderBench()" style="margin-left:10px;font-size:.8rem">
        <option value="2025">R2025</option><option value="2024">R2024</option><option value="2023">R2023</option><option value="2026">B2026</option>
      </select>
    </div><div class="ch"><canvas id="c-bench"></canvas></div></div>
    <div class="card"><div class="card-title">R&eacute;sum&eacute; d&#8217;&eacute;volution vs parc</div><div id="bench-evol-wrap" style="overflow-y:auto;max-height:290px"></div></div>
  </div>
  <div class="row2" id="dt-row-wf">
    <div class="card full">
      <div class="card-title">Cascade P&amp;L (Waterfall)
        <select class="sel" id="wf-year" onchange="renderWaterfall()" style="margin-left:10px;font-size:.8rem">
          <option value="2025">R2025</option><option value="2024">R2024</option><option value="2023">R2023</option><option value="2026">B2026</option>
        </select>
      </div>
      <div class="ch tall"><canvas id="c-wf"></canvas></div>
    </div>
  </div>
  <div class="card" id="dt-card-pl" style="margin-bottom:0">
    <div class="card-title" id="dt-pl-title">Tableau P&amp;L d&eacute;taill&eacute;</div>
    <div id="pl-wrap"></div>
  </div>
</div>

<!-- ═══ ONGLET 3 — EUR/T ══════════════════════════════════════════════════════ -->
<div class="page" id="tab-et">
  <div class="toolbar">
    <label>Ann&eacute;e :</label>
    <button class="btn-pill et-yr active" onclick="toggleEtYear('all',this)">Tous</button>
    <button class="btn-pill et-yr" onclick="toggleEtYear('R2023',this)">R2023</button>
    <button class="btn-pill et-yr" onclick="toggleEtYear('R2024',this)">R2024</button>
    <button class="btn-pill et-yr" onclick="toggleEtYear('R2025',this)">R2025</button>
    <label style="margin-left:14px">Sites :</label>
    <div id="et-site-pills" style="display:flex;gap:4px;flex-wrap:wrap">
      <button class="btn-pill active" onclick="toggleEtSite('all',this)">Tous</button>
    </div>
    <div class="spacer"></div>
    <button class="btn-print" onclick="window.print()" title="Imprime l'onglet actif en PDF A4 paysage">&#128438; Exporter PDF</button>
  </div>
  <div class="row2" style="margin-top:18px">
    <div class="card"><div class="card-title">CA &euro;/t par site</div><div class="ch tall"><canvas id="c-et-ca"></canvas></div></div>
    <div class="card"><div class="card-title">EBITDA &euro;/t par site</div><div class="ch tall"><canvas id="c-et-eb"></canvas></div></div>
  </div>
  <div class="row2">
    <div class="card full"><div class="card-title">Charges internes &euro;/t par site &#8212; tri&eacute;es par EBITDA &euro;/t</div><div class="ch tall"><canvas id="c-charges-et"></canvas></div></div>
  </div>
  <div class="row2">
    <div class="card full">
      <div class="card-title">Matrice de positionnement : Tonnes vs EBITDA &euro;/t</div>
      <div class="ch" style="height:340px"><canvas id="c-scatter"></canvas></div>
      <div id="cat-table-wrap" style="margin-top:16px"></div>
    </div>
  </div>
  <div class="card" style="margin-bottom:0">
    <div class="card-title">Tableau &euro;/t &#8212; m&eacute;triques cl&eacute;s</div>
    <div class="hm-wrap" id="hm-wrap"></div>
  </div>
</div>

<!-- ═══ ONGLET 4 — REGION ════════════════════════════════════════════════════ -->
<div class="page" id="tab-rg">
  <div class="toolbar">
    <label>Ann&eacute;e :</label>
    <button class="btn-pill rg-yr active" onclick="toggleRgYear('all',this)">Tous</button>
    <button class="btn-pill rg-yr" onclick="toggleRgYear('2023',this)">R2023</button>
    <button class="btn-pill rg-yr" onclick="toggleRgYear('2024',this)">R2024</button>
    <button class="btn-pill rg-yr" onclick="toggleRgYear('2025',this)">R2025</button>
    <span style="margin-left:18px;color:#ddd">|</span>
    <label style="margin-left:14px">Vue CA :</label>
    <button class="btn-pill rg-ca-type active" onclick="setRgCAType('bar',this)">Barres</button>
    <button class="btn-pill rg-ca-type" onclick="setRgCAType('line',this)">Ligne</button>
    <div class="spacer"></div>
    <button class="btn-print" onclick="window.print()" title="Imprime l'onglet actif en PDF A4 paysage">&#128438; Exporter PDF</button>
  </div>
  <div class="kpi-grid" style="margin-top:18px">
    <div class="kpi-card"><div class="kpi-label">CA Total</div><div class="kpi-value" id="rg-ca">&#8212;</div><div class="kpi-sub" id="rg-ca-s"></div></div>
    <div class="kpi-card g"><div class="kpi-label">EBITDA Total</div><div class="kpi-value" id="rg-eb">&#8212;</div><div class="kpi-sub" id="rg-eb-s"></div></div>
    <div class="kpi-card o"><div class="kpi-label">Tonnes Totales</div><div class="kpi-value" id="rg-tn">&#8212;</div><div class="kpi-sub" id="rg-tn-s"></div></div>
  </div>
  <div class="row2">
    <div class="card"><div class="card-title">CA par r&eacute;gion <span id="rg-ca-period" style="font-size:10px;font-weight:400;color:#999;margin-left:6px"></span></div><div class="ch"><canvas id="c-rg-ca"></canvas></div></div>
    <div class="card"><div class="card-title">EBITDA par r&eacute;gion (M&euro;) <span id="rg-eb-period" style="font-size:10px;font-weight:400;color:#999;margin-left:6px"></span></div><div class="ch"><canvas id="c-rg-eb"></canvas></div></div>
  </div>
  <div class="row2">
    <div class="card"><div class="card-title">EBITDA &euro;/t par r&eacute;gion <span id="rg-ebt-period" style="font-size:10px;font-weight:400;color:#999;margin-left:6px"></span></div><div class="ch"><canvas id="c-rg-ebt"></canvas></div></div>
    <div class="card">
      <div class="card-title" style="display:flex;justify-content:space-between;align-items:center">
        <span>Carte &mdash; performance r&eacute;gionale</span>
        <select class="sel" id="rg-metric" onchange="setRgMetric(this.value)" style="font-size:.78rem">
          <option value="CA">CA</option>
          <option value="PNE">PNE</option>
          <option value="Marge_Brute_Cash">Marge Brute</option>
          <option value="EBITDA" selected>EBITDA</option>
          <option value="EBIT_Courant">EBIT</option>
        </select>
      </div>
      <div id="rg-map" style="display:flex;justify-content:center;align-items:center;padding:8px 0"></div>
    </div>
  </div>
  <div class="podium-grid" id="rg-podium" style="margin-top:4px"></div>
  <div class="card" style="margin-bottom:0">
    <div class="card-title">Synth&egrave;se par r&eacute;gion &nbsp;<span style="font-size:11px;font-weight:normal;color:#999">&#9654; Cliquer sur une r&eacute;gion pour voir les sites</span> &nbsp;<span id="rg-table-period" style="font-size:10px;font-weight:400;color:#999"></span></div>
    <div id="rg-table-wrap"></div>
  </div>
</div>

<script>
// ══════════════════════════════════════════════════════
// DATA
// ══════════════════════════════════════════════════════
const DATA = %%DATA%%;
const EURT = %%EURT%%;

// ══════════════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════════════
const fmt  = n => n==null?'—':new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0}).format(n);
const fmtM = n => n==null?'—':(n/1e6).toFixed(2).replace('.',',')+' M\u20ac';
const fmtK = n => n==null?'—':(n/1e3).toFixed(1).replace('.',',')+' kt';
const fmtE = n => n==null?'—':fmt(n)+' \u20ac';
const fmtT = n => (n==null||n==='')?'—':Number(n).toFixed(1)+' \u20ac/t';
const COLORS=['#0f3460','#533483','#e94560','#16c79a','#f4a261','#2196f3','#ff9f1c','#118ab2','#e63946','#2a9d8f','#e9c46a'];
const C3 = (i)=>[COLORS[0],COLORS[2],COLORS[3],'#f59e0b'][i%4];
const SITES = [...new Set(DATA.map(d=>d.Site))];
const YEARS = ['2023','2024','2025','2026'];
const REAL_YEARS = ['2023','2024','2025'];
const yr2lbl = yr => (yr==='2026'||yr==='B2026')?'B2026':yr.startsWith('R')?yr:'R'+yr;

// ══════════════════════════════════════════════════════
// TABS
// ══════════════════════════════════════════════════════

// ── Heatmap standalone (sites=lignes, métriques=colonnes) ──
// Helper : crée un chart en détruisant proprement tout chart existant sur le canvas
function mkChart(id, config){
  const canvas=document.getElementById(id);
  if(!canvas) return null;
  const existing=Chart.getChart(canvas);
  if(existing) existing.destroy();
  return new Chart(canvas, config);
}

function showTab(id,el){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  el.classList.add('active');
  // Double rAF: attendre que le navigateur ait recalculé le layout (display:none→block)
  // avant de créer les charts, sinon les canvas restent à 0×0
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    if(id==='home') renderHome();
    if(id==='ov') renderOv();
    if(id==='dt') renderDt();
    if(id==='et') renderEt();
    if(id==='rg') renderRg();
  }));
}

// Navigation croisée : ouvre la fiche d'un site depuis n'importe quelle vue
function goToSite(site){
  const sel=document.getElementById('dt-site');
  if(!sel) return;
  sel.value=site;
  const tabBtn=[...document.querySelectorAll('.tab')].find(function(t){return (t.getAttribute('onclick')||'').includes("'dt'");});
  if(tabBtn) showTab('dt',tabBtn);
  requestAnimationFrame(function(){window.scrollTo({top:0,behavior:'smooth'});});
}

// ══════════════════════════════════════════════════════
// ONGLET 1 — VUE D'ENSEMBLE
// ══════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════
// EXECUTIVE SUMMARY
// ══════════════════════════════════════════════════════
function renderHome(){
  const yr='2025', yrPrev='2024';
  const rows=DATA.filter(d=>String(d.Annee)===yr);
  const rowsPrev=DATA.filter(d=>String(d.Annee)===yrPrev);
  const sum=(arr,k)=>arr.reduce((s,d)=>s+(d[k]||0),0);
  const ca=sum(rows,'CA'), caPrev=sum(rowsPrev,'CA');
  const eb=sum(rows,'EBITDA'), ebPrev=sum(rowsPrev,'EBITDA');
  const tn=sum(rows,'Tonnes_entrantes'), tnPrev=sum(rowsPrev,'Tonnes_entrantes');
  const tx=ca?(eb/ca*100):0, txPrev=caPrev?(ebPrev/caPrev*100):0;
  const trend=(v,p,isAmt)=>{
    if(!p||p===0) return '';
    const d=v-p, pct=((d/Math.abs(p))*100).toFixed(1);
    const up=d>=0;
    return '<span style="color:'+(up?'#10b981':'#ef4444')+'">'+(up?'&#8679;':'&#8681;')+' '+(up?'+':'')+pct+'% vs R2024</span>';
  };
  document.getElementById('hm-ca').textContent=fmtM(ca);
  document.getElementById('hm-ca-tr').innerHTML=trend(ca,caPrev,true);
  document.getElementById('hm-eb').textContent=fmtM(eb);
  document.getElementById('hm-eb').style.color=eb>=0?'#10b981':'#ef4444';
  document.getElementById('hm-eb-tr').innerHTML=trend(eb,ebPrev,true);
  document.getElementById('hm-tn').textContent=fmtK(tn);
  document.getElementById('hm-tn-tr').innerHTML=trend(tn,tnPrev,true);
  document.getElementById('hm-tx').textContent=tx.toFixed(1)+'%';
  document.getElementById('hm-tx').style.color=eb>=0?'#10b981':'#ef4444';
  const txD=tx-txPrev; document.getElementById('hm-tx-tr').innerHTML='<span style="color:'+(txD>=0?'#10b981':'#ef4444')+'">'+(txD>=0?'&#8679;':'&#8681;')+' '+(txD>=0?'+':'')+txD.toFixed(1)+' pts vs R2024</span>';
  document.getElementById('hm-ns').textContent=SITES.length;
  document.getElementById('hm-ns-tr').innerHTML='<span style="color:#888">'+[...new Set(DATA.filter(d=>d.Region).map(d=>d.Region))].length+' r\u00e9gions</span>';
}

function renderExecSummary(){
  const el=document.getElementById('exec-summary');
  if(!el) return;
  const siteArr=ovSites.has('all')?SITES:[...ovSites];
  const activeExYrs=(ovYears.has('all')?REAL_YEARS:[...ovYears]).slice().sort();
  const isBudget=activeExYrs.length===1&&activeExYrs[0]==='2026';
  const isMultiYr=activeExYrs.length>1;
  const firstYr=activeExYrs[0];
  const lastYr=activeExYrs[activeExYrs.length-1];
  const lastRows=DATA.filter(d=>String(d.Annee)===lastYr&&siteArr.includes(d.Site));
  const firstRows=DATA.filter(d=>String(d.Annee)===firstYr&&siteArr.includes(d.Site));
  const refCA=lastRows.reduce((s,d)=>s+(d.CA||0),0);
  const refEB=lastRows.reduce((s,d)=>s+(d.EBITDA||0),0);
  const refTN=lastRows.reduce((s,d)=>s+(d.Tonnes_entrantes||0),0);
  const firstCA=firstRows.reduce((s,d)=>s+(d.CA||0),0);
  const firstEB=firstRows.reduce((s,d)=>s+(d.EBITDA||0),0);
  const bysite=siteArr.map(s=>{
    const r=lastRows.filter(d=>d.Site===s);
    return {site:s,ca:r.reduce((a,d)=>a+(d.CA||0),0),eb:r.reduce((a,d)=>a+(d.EBITDA||0),0)};
  }).sort((a,b)=>b.eb-a.eb);
  const negatifs=bysite.filter(d=>d.eb<0);
  const best=bysite.filter(d=>d.eb>=0)[0];
  const worst=bysite[bysite.length-1];
  let caCell;
  if(isMultiYr&&firstCA!==0){
    const caD=refCA-firstCA;
    const caPct=((caD/Math.abs(firstCA))*100).toFixed(0);
    const caCol=caD>=0?'#6ee7b7':'#fca5a5';
    const caArr=caD>=0?'\u2B06':'\u2B07';
    caCell='<div class="es-cell"><div class="es-label">CA '+yr2lbl(firstYr)+' \u2192 '+yr2lbl(lastYr)+'</div><div class="es-val">'+fmtM(firstCA)+' \u2192 '+fmtM(refCA)+'<span style="color:'+caCol+';font-size:.78rem;margin-left:6px">'+caArr+' '+(caD>=0?'+':'')+caPct+'%</span></div></div>';
  } else {
    caCell='<div class="es-cell"><div class="es-label">CA ('+yr2lbl(lastYr)+')</div><div class="es-val">'+fmtM(refCA)+'</div></div>';
  }
  let ebCell;
  if(isMultiYr&&firstEB!==0){
    const ebD=refEB-firstEB;
    const ebPct=((ebD/Math.abs(firstEB))*100).toFixed(0);
    const ebCol=ebD>=0?'#6ee7b7':'#fca5a5';
    const ebArr=ebD>=0?'\u2B06':'\u2B07';
    ebCell='<div class="es-cell"><div class="es-label">EBITDA '+yr2lbl(firstYr)+' \u2192 '+yr2lbl(lastYr)+'</div><div class="es-val" style="color:'+(refEB>=0?'#6ee7b7':'#fca5a5')+'">'+fmtM(firstEB)+' \u2192 '+fmtM(refEB)+'<span style="color:'+ebCol+';font-size:.78rem;margin-left:6px">'+ebArr+' '+(ebD>=0?'+':'')+ebPct+'%</span></div></div>';
  } else if(!isBudget){
    const prevYr=lastYr==='2025'?'2024':lastYr==='2024'?'2023':null;
    let evoSpan='';
    if(prevYr){
      const prevEB=DATA.filter(d=>String(d.Annee)===prevYr&&siteArr.includes(d.Site)).reduce((s,d)=>s+(d.EBITDA||0),0);
      if(prevEB!==0){
        const d2=refEB-prevEB;
        const p2=((d2/Math.abs(prevEB))*100).toFixed(0);
        const c2=d2>=0?'#6ee7b7':'#fca5a5';
        const a2=d2>=0?'\u2B06':'\u2B07';
        evoSpan='<span style="color:'+c2+';font-size:.78rem;margin-left:6px">'+a2+' '+(d2>=0?'+':'')+p2+'% vs '+yr2lbl(prevYr)+'</span>';
      }
    }
    ebCell='<div class="es-cell"><div class="es-label">EBITDA ('+yr2lbl(lastYr)+')</div><div class="es-val" style="color:'+(refEB>=0?'#6ee7b7':'#fca5a5')+'">'+fmtM(refEB)+evoSpan+'</div></div>';
  } else {
    const p25EB=DATA.filter(d=>String(d.Annee)==='2025'&&siteArr.includes(d.Site)).reduce((s,d)=>s+(d.EBITDA||0),0);
    let evoSpan='';
    if(p25EB!==0){
      const d2=refEB-p25EB;
      const p2=((d2/Math.abs(p25EB))*100).toFixed(0);
      const c2=d2>=0?'#6ee7b7':'#fca5a5';
      const a2=d2>=0?'\u2B06':'\u2B07';
      evoSpan='<span style="color:'+c2+';font-size:.78rem;margin-left:6px">'+a2+' '+(d2>=0?'+':'')+p2+'% vs R2025</span>';
    }
    ebCell='<div class="es-cell"><div class="es-label">EBITDA (B2026)</div><div class="es-val" style="color:'+(refEB>=0?'#6ee7b7':'#fca5a5')+'">'+fmtM(refEB)+evoSpan+'</div></div>';
  }
  const periodLabel=isBudget?'Budget 2026':isMultiYr?(yr2lbl(firstYr)+' \u2192 '+yr2lbl(lastYr)):yr2lbl(lastYr);
  const refLabel=yr2lbl(lastYr);
  let msg='<div class="es-title">&#128202; Synth\u00e8se Executive \u2014 Parc Centres de Tri Veolia</div>';
  msg+='<div class="es-grid">';
  msg+='<div class="es-cell es-period"><div class="es-label">P\u00e9riode</div><div class="es-val">'+periodLabel+'</div></div>';
  msg+=caCell;
  msg+=ebCell;
  msg+='<div class="es-cell"><div class="es-label">Volume ('+refLabel+')</div><div class="es-val">'+fmtK(refTN)+'</div></div>';
  msg+='<div class="es-cell"><div class="es-label">Sites en perte</div><div class="es-val" style="color:'+(negatifs.length>0?'#fca5a5':'#6ee7b7')+'">'+negatifs.length+'/'+siteArr.length+'</div></div>';
  if(siteArr.length>1&&best) msg+='<div class="es-cell"><div class="es-label">&#127942; Meilleur EBITDA</div><div class="es-val">'+best.site+'<span style="font-size:.75rem;opacity:.75;margin-left:5px">'+fmtM(best.eb)+'</span></div></div>';
  if(siteArr.length>1&&worst&&worst.eb<0) msg+='<div class="es-cell"><div class="es-label">&#9888; Plus d\u00e9ficitaire</div><div class="es-val" style="color:#fca5a5">'+worst.site+'<span style="font-size:.75rem;opacity:.75;margin-left:5px">'+fmtM(worst.eb)+'</span></div></div>';
  msg+='</div>';
  el.innerHTML=msg;
  el.style.display='block';
}

let ovYears=new Set(['all']), cCA=null, cEB=null, cMarg=null;
let ovSites=new Set(['all']);
function toggleOvSite(s,btn){
  const allBtn=document.querySelector('#ov-site-pills .btn-pill');
  if(s==='all'){ovSites=new Set(['all']);document.querySelectorAll('#ov-site-pills .btn-pill').forEach(b=>b.classList.remove('active'));allBtn.classList.add('active');}
  else{
    ovSites.delete('all');allBtn.classList.remove('active');
    if(ovSites.has(s)){ovSites.delete(s);btn.classList.remove('active');}
    else{ovSites.add(s);btn.classList.add('active');}
    if(ovSites.size===0){ovSites=new Set(['all']);allBtn.classList.add('active');}
  }
  renderOv();
}

function toggleEtSite(s,btn){
  const allBtn=document.querySelector('#et-site-pills .btn-pill');
  if(s==='all'){etSites=new Set(['all']);document.querySelectorAll('#et-site-pills .btn-pill').forEach(b=>b.classList.remove('active'));allBtn.classList.add('active');}
  else{
    etSites.delete('all');allBtn.classList.remove('active');
    if(etSites.has(s)){etSites.delete(s);btn.classList.remove('active');}
    else{etSites.add(s);btn.classList.add('active');}
    if(etSites.size===0){etSites=new Set(['all']);allBtn.classList.add('active');}
  }
  renderEt();
}

function toggleOvYear(y,btn){
  const allBtn=document.querySelector('.ov-yr');
  if(y==='all'){ovYears=new Set(['all']);document.querySelectorAll('.ov-yr').forEach(b=>b.classList.remove('active'));allBtn.classList.add('active');}
  else{
    ovYears.delete('all');allBtn.classList.remove('active');
    if(ovYears.has(y)){ovYears.delete(y);btn.classList.remove('active');}
    else{ovYears.add(y);btn.classList.add('active');}
    if(ovYears.size===0){ovYears=new Set(['all']);allBtn.classList.add('active');}
  }
  renderOv();
}

function renderOv(){
  renderExecSummary();
  const isAll=ovSites.has('all');
  const siteArr=isAll?SITES:[...ovSites];
  const activeYrs=ovYears.has('all')?REAL_YEARS:[...ovYears];
  const hasBgt=activeYrs.includes('2026');
  let rows=DATA.filter(d=>activeYrs.includes(String(d.Annee)));
  rows=rows.filter(d=>siteArr.includes(d.Site));

  const ca=rows.reduce((s,d)=>s+(d.CA||0),0);
  const eb=rows.reduce((s,d)=>s+(d.EBITDA||0),0);
  const tn=rows.reduce((s,d)=>s+(d.Tonnes_entrantes||0),0);
  const ns=siteArr.length;

  document.getElementById('kpi-ca').textContent=fmtM(ca);
  document.getElementById('kpi-ca-s').textContent=ns+' site'+(ns>1?'s':'');
  document.getElementById('kpi-eb').textContent=fmtM(eb);
  document.getElementById('kpi-eb').style.color=eb>=0?'#10b981':'#ef4444';
  document.getElementById('kpi-eb-s').textContent='Taux: '+(ca?((eb/ca)*100).toFixed(1):0)+'%';
  document.getElementById('kpi-tn').textContent=fmtK(tn);
  document.getElementById('kpi-tn-s').textContent='tonnes entrantes';
  // ── Tendances KPI vs année précédente (seulement si 1 seule année réelle sélectionnée) ──
  const realYrsSelected=activeYrs.filter(y=>y!=='2026');
  const lastRealYr=realYrsSelected.length===1?realYrsSelected[0]:null;
  const prevYr=lastRealYr?String(parseInt(lastRealYr)-1):null;
  const trendBadge=(v,vPrev,id)=>{
    const el=document.getElementById(id);
    if(!el) return;
    if(!prevYr||!vPrev||Math.abs(vPrev)<0.01){el.innerHTML='';return;}
    const d=v-vPrev, pct=((d/Math.abs(vPrev))*100).toFixed(1);
    const up=d>=0;
    el.innerHTML='<span style="color:'+(up?'#10b981':'#ef4444')+'">'+(up?'\u2B06':'\u2B07')+' '+(up?'+':'')+pct+'% vs '+yr2lbl(prevYr)+'</span>';
  };
  const prevRows=DATA.filter(d=>siteArr.includes(d.Site)&&String(d.Annee)===prevYr);
  trendBadge(ca,prevRows.reduce((s,d)=>s+(d.CA||0),0),'kpi-ca-tr');
  trendBadge(eb,prevRows.reduce((s,d)=>s+(d.EBITDA||0),0),'kpi-eb-tr');
  trendBadge(tn,prevRows.reduce((s,d)=>s+(d.Tonnes_entrantes||0),0),'kpi-tn-tr');

  // Best/worst/ranking : seulement si tous les sites
  document.getElementById('kpi-card-best').style.display=isAll?'':'none';
  document.getElementById('kpi-card-worst').style.display=isAll?'':'none';
  document.getElementById('rank-card').style.display=isAll?'':'none';
  document.querySelector('.kpi-grid').style.gridTemplateColumns=isAll?'repeat(5,1fr)':'repeat(3,1fr)';

  if(isAll){
    const bysite=SITES.map(s=>{
      const r=rows.filter(d=>d.Site===s);
      const sum=k=>r.reduce((a,d)=>a+(d[k]||0),0);
      return {site:s,ca:sum('CA'),pne:sum('PNE'),mb:sum('Marge_Brute_Cash'),eb:sum('EBITDA'),ebit:sum('EBIT_Courant'),tn:sum('Tonnes_entrantes')};
    }).sort((a,b)=>b.eb-a.eb);

    const best=bysite[0], worst=bysite[bysite.length-1];
    if(best){document.getElementById('kpi-best').textContent=best.site;document.getElementById('kpi-best-s').textContent=fmtM(best.eb)+' EBITDA';}
    if(worst){document.getElementById('kpi-worst').textContent=worst.site;document.getElementById('kpi-worst-s').textContent=fmtM(worst.eb)+' EBITDA';document.getElementById('kpi-worst').style.color=worst.eb<0?'#ef4444':'#1a1a2e';}

    const sitesNegatifs=bysite.filter(d=>d.eb<0).map(d=>d.site);
    const sitesPositifs=bysite.filter(d=>d.eb>=0);
    const alertBar=document.getElementById('alert-bar');
    const alertOk=document.getElementById('alert-ok');
    if(sitesNegatifs.length>0){alertBar.classList.remove('hidden');document.getElementById('alert-msg').textContent=sitesNegatifs.length+' site'+(sitesNegatifs.length>1?'s en alerte (EBITDA n\u00e9gatif)':' en alerte (EBITDA n\u00e9gatif)')+' : '+sitesNegatifs.join(', ');}else{alertBar.classList.add('hidden');}
    // Alerte tendance : EBITDA en baisse 2 années consécutives (2023→2024 ET 2024→2025)
    const trendAlertEl=document.getElementById('alert-trend');
    if(trendAlertEl){
      const declining=SITES.filter(function(s){
        const e23=DATA.find(function(d){return d.Site===s&&String(d.Annee)==='2023';});
        const e24=DATA.find(function(d){return d.Site===s&&String(d.Annee)==='2024';});
        const e25=DATA.find(function(d){return d.Site===s&&String(d.Annee)==='2025';});
        if(!e23||!e24||!e25) return false;
        return Number(e24.EBITDA)<Number(e23.EBITDA)&&Number(e25.EBITDA)<Number(e24.EBITDA);
      });
      if(declining.length>0){
        trendAlertEl.classList.remove('hidden');
        document.getElementById('alert-trend-msg').innerHTML='<strong>'+declining.length+' site'+(declining.length>1?'s':'')+'</strong> en baisse EBITDA 2 ann\u00e9es cons\u00e9cutives (R2023\u2192R2025) : '+declining.map(function(s){return '<span class="site-link" data-site="'+s+'" onclick="goToSite(this.dataset.site)">'+s+'</span>';}).join(', ');
      } else {
        trendAlertEl.classList.add('hidden');
      }
    }
    if(sitesPositifs.length>0){alertOk.classList.remove('hidden');document.getElementById('alert-ok-msg').innerHTML='<strong>'+sitesPositifs.length+' site'+(sitesPositifs.length>1?'s en EBITDA positif':'  en EBITDA positif')+'</strong> \u2014 '+sitesPositifs.map(d=>d.site+' <span style="color:#10b981;font-weight:700">'+fmtM(d.eb)+'</span>').join(' &middot; ');}else{alertOk.classList.add('hidden');}

    let h='<table class="rank-table"><thead><tr><th>#&nbsp;Site</th><th>CA</th><th>PNE</th><th>Marge Brute</th><th>EBITDA</th><th>EBIT</th><th>Taux EBITDA</th><th>Tonnes</th></tr></thead><tbody>';
    bysite.forEach((d,i)=>{
      const tauxPct=d.ca?((d.eb/d.ca)*100).toFixed(1)+'%':'—';
      const cls=i===0?'best-row':d.eb<0?'worst-row':'';
      const rnCls=i===0?'rn-g':d.eb<0?'rn-r':'rn-d';
      h+='<tr class="'+cls+'"><td><span class="rank-num '+rnCls+'">'+(i+1)+'</span><span class="site-link" data-site="'+d.site+'" onclick="goToSite(this.dataset.site)">'+d.site+'</span></td>';
      h+='<td>'+fmtM(d.ca)+'</td>';
      h+='<td class="neg">'+fmtM(d.pne)+'</td>';
      h+='<td class="'+(d.mb>=0?'pos':'neg')+'">'+fmtM(d.mb)+'</td>';
      h+='<td class="'+(d.eb>=0?'pos':'neg')+'">'+fmtM(d.eb)+'</td>';
      h+='<td class="'+(d.ebit>=0?'pos':'neg')+'">'+fmtM(d.ebit)+'</td>';
      h+='<td>'+tauxPct+'</td><td>'+fmtK(d.tn)+'</td></tr>';
    });
    h+='</tbody></table>';
    document.getElementById('rank-wrap').innerHTML=h;
  } else {
    document.getElementById('alert-bar').classList.add('hidden');
    const _at=document.getElementById('alert-trend');if(_at)_at.classList.add('hidden');
    document.getElementById('alert-ok').classList.add('hidden');
  }

  const sitesVisible=siteArr;

  const activeYears=ovYears.has('all')?YEARS:activeYrs;
  const ds=activeYears.map((yr,i)=>({
    label:yr2lbl(yr),
    data:sitesVisible.map(s=>{const r=DATA.find(d=>d.Site===s&&String(d.Annee)===yr);return r?(r.CA/1e6):0;}),
    backgroundColor:C3(i),borderRadius:4
  }));
  cCA=mkChart('c-ca',{type:'bar',data:{labels:sitesVisible,datasets:ds},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+' M\u20ac'}}},scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},x:{grid:{display:false}}}}});

  // ── EBITDA chart ──
  const ebNote = ovYears.has('all') ? REAL_YEARS.map(yr2lbl).join(' + ') : activeYrs.map(yr2lbl).join(' + ');
  document.getElementById('eb-chart-title').textContent = 'EBITDA par site \u2014 ' + ebNote;
  const ebData=sitesVisible.map(s=>rows.filter(d=>d.Site===s).reduce((a,d)=>a+(d.EBITDA||0),0));
  const sorted=sitesVisible.map((s,i)=>({s,v:ebData[i]})).sort((a,b)=>a.v-b.v);
  const isBgt26=hasBgt&&activeYrs.length===1;
  cEB=mkChart('c-eb',{type:'bar',data:{labels:sorted.map(d=>d.s),datasets:[{label:'EBITDA',data:sorted.map(d=>d.v/1e6),backgroundColor:sorted.map(d=>d.v>=0?(isBgt26?'rgba(245,158,11,.55)':'rgba(16,185,129,.5)'):'rgba(239,68,68,.5)'),borderColor:sorted.map(d=>d.v>=0?(isBgt26?'#f59e0b':'#10b981'):'#ef4444'),borderWidth:2,borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' EBITDA: '+c.parsed.x.toFixed(2)+' M\u20ac'}}},scales:{x:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}}});

  // Evolution marge EBITDA % par site
  const margSites=siteArr;
  const margDs=margSites.map((s,i)=>({
    label:s,
    data:REAL_YEARS.map(yr=>{
      const r=DATA.find(d=>d.Site===s&&String(d.Annee)===yr);
      return (r&&r.CA&&r.CA!==0)?Math.round((r.EBITDA/r.CA)*1000)/10:null;
    }),
    borderColor:COLORS[i%COLORS.length],
    backgroundColor:COLORS[i%COLORS.length]+'33',
    tension:.35,fill:false,pointRadius:6,pointHoverRadius:9,spanGaps:true,borderWidth:2.5
  }));
  cMarg=mkChart('c-marg',{
    type:'line',
    data:{labels:REAL_YEARS.map(yr2lbl),datasets:margDs},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'right',labels:{font:{size:10},usePointStyle:true,pointStyleWidth:8}},
        tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+(c.parsed.y!=null?c.parsed.y.toFixed(1)+'%':'\u2014')}}
      },
      scales:{
        y:{title:{display:true,text:'Marge EBITDA %'},grid:{color:'#f0f0f0'},ticks:{callback:v=>v+'%'}},
        x:{grid:{color:'#f0f0f0'}}
      }
    }
  });
}

// ══════════════════════════════════════════════════════
// ONGLET 2 — DETAIL
// ══════════════════════════════════════════════════════
let cEvol=null, cDonut=null, cWF=null, cBench=null;
let cmpYear='2025';

function setCmpYear(yr){
  cmpYear=yr;
  const site=document.getElementById('dt-site').value;
  const site2=(document.getElementById('dt-site2')||{}).value||'';
  document.querySelectorAll('.cmp-yr-btn').forEach(b=>{b.classList.toggle('active',b.dataset.yr===yr);});
  if(site&&site2&&site2!==site) renderCompare(site,site2);
}

function renderDt(){
  const site=document.getElementById('dt-site').value;
  const site2=(document.getElementById('dt-site2')||{}).value||'';
  if(!site) return;
  const rows=DATA.filter(d=>d.Site===site).sort((a,b)=>a.Annee-b.Annee);
  const isCmp=!!(site2&&site2!==site);
  const cmpDiv=document.getElementById('dt-compare');
  // Show/hide sections based on compare mode
  if(cmpDiv) cmpDiv.style.display=isCmp?'block':'none';
  document.getElementById('dt-exec').style.display=isCmp?'none':'none'; // handled by renderSiteExec
  // En mode comparaison : uniquement le bloc compare + graphique évolution
  ['dt-card-donut','dt-row-wf','dt-row-bench','dt-card-pl'].forEach(id=>{
    const el=document.getElementById(id);
    if(el) el.style.display=isCmp?'none':'';
  });
  if(isCmp){
    renderCompare(site,site2);
  } else {
    renderSiteExec(site,rows);
    renderEvol(rows);
    renderDonut();
    renderBench();
    renderWaterfall();
    renderPL(rows);
  }
}

function renderCompare(s1,s2){
  const yr=cmpYear;
  const METRICS=[
    {k:'CA',            l:"Chiffre d'affaires", fmt:fmtM,   pos:'high'},
    {k:'PNE',           l:'PNE',                fmt:fmtM,   pos:'low'},
    {k:'Marge_Brute_Cash',l:'Marge Brute',      fmt:fmtM,   pos:'high'},
    {k:'EBITDA',        l:'EBITDA',             fmt:fmtM,   pos:'high'},
    {k:'EBIT_Courant',  l:'EBIT',               fmt:fmtM,   pos:'high'},
    {k:'Couts_personnel',l:'Personnel',         fmt:fmtM,   pos:'low'},
    {k:'Energie',       l:'\u00c9nergie',        fmt:fmtM,   pos:'low'},
    {k:'_Maintenance',  l:'Maintenance',         fmt:fmtM,   pos:'low'},
    {k:'Tonnes_entrantes',l:'Tonnes',           fmt:fmtK,   pos:'high'},
  ];
  const get=(row,k)=>{
    if(k==='_Maintenance') return (row.Maintenance_courante||0)+(row.Maintenance_obligatoire||0);
    return row[k]||0;
  };
  const r1=DATA.find(d=>d.Site===s1&&String(d.Annee)===yr)||{};
  const r2=DATA.find(d=>d.Site===s2&&String(d.Annee)===yr)||{};
  const side=(site,r,other)=>{
    const eb=r.EBITDA||0, ca=r.CA||0;
    const tx=ca?(eb/ca*100).toFixed(1)+'%':'—';
    const tn=r.Tonnes_entrantes||0;
    const ebt=tn>0?(eb/tn).toFixed(1)+' \u20ac/t':'—';
    let h='<div class="cmp-side"><div class="cmp-site-title">'+site+'</div>';
    METRICS.forEach(({k,l,fmt,pos})=>{
      const v=get(r,k), vo=get(other,k);
      const better=(pos==='high')?(v>=vo):(v<=vo);
      const star=(better&&v!==vo)?'<span style="color:#f59e0b;margin-left:4px">\u2605</span>':'';
      const col=k==='EBITDA'?(eb>=0?'#10b981':'#ef4444'):'#1a1a2e';
      h+='<div class="cmp-row"><span style="color:#666">'+l+'</span><span style="font-weight:700;color:'+col+'">'+fmt(v)+star+'</span></div>';
    });
    h+='<div class="cmp-row"><span style="color:#666">Taux EBITDA</span><span style="font-weight:700">'+tx+'</span></div>';
    h+='<div class="cmp-row"><span style="color:#666">EBITDA \u20ac/t</span><span style="font-weight:700">'+ebt+'</span></div>';
    h+='</div>';
    return h;
  };
  const cmpDiv=document.getElementById('dt-compare');
  if(!cmpDiv) return;
  // Year selector buttons
  const yrBtns=YEARS.map(y=>'<button class="btn-pill cmp-yr-btn'+(y===yr?' active':'')+(y==='2026'?' budget':'')+'" data-yr="'+y+'" onclick="setCmpYear(this.dataset.yr)">'+yr2lbl(y)+'</button>').join('');
  cmpDiv.innerHTML='<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;padding:10px 14px;background:#f8fafc;border-radius:8px"><span style="font-size:.8rem;color:#555;font-weight:600">Ann\u00e9e :</span>'+yrBtns+'<span style="margin-left:12px;font-size:.78rem;color:#aaa">\u2605 = meilleur des deux</span></div>'
    +'<div class="cmp-wrap">'+side(s1,r1,r2)+side(s2,r2,r1)+'</div>';
  // Combined evolution chart (EBITDA + CA) — reuse c-evol canvas
  const labs=[...REAL_YEARS,'2026'].map(yr2lbl);
  const allYrs=[...REAL_YEARS,'2026'];
  const mkDs=(site,color,key,label,dash)=>({
    label:site+' '+label,
    data:allYrs.map(y=>{const r=DATA.find(d=>d.Site===site&&String(d.Annee)===y);return r?(r[key]/1e6):null;}),
    borderColor:color,backgroundColor:color+'22',tension:.3,pointRadius:4,fill:false,
    borderWidth:dash?1.5:2.5,borderDash:dash?[5,4]:[],spanGaps:true
  });
  cEvol=mkChart('c-evol',{type:'line',
    data:{labels:labs,datasets:[mkDs(s1,COLORS[0],'EBITDA','EBITDA',false),mkDs(s2,COLORS[2],'EBITDA','EBITDA',false),mkDs(s1,COLORS[0],'CA','CA',true),mkDs(s2,COLORS[2],'CA','CA',true)]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{usePointStyle:true,font:{size:10}}},tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+' M\u20ac'}}},scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}}}}
  });
}

function renderSiteExec(site,rows){
  const el=document.getElementById('dt-exec');
  if(!el) return;
  const realRows=rows.filter(d=>String(d.Annee)!=='2026').sort((a,b)=>Number(a.Annee)-Number(b.Annee));
  if(!realRows.length){el.style.display='none';return;}
  const last=realRows[realRows.length-1];
  const first=realRows[0];
  const lastYr=String(last.Annee);
  const firstYr=String(first.Annee);
  const isMulti=realRows.length>1;
  const eb=last.EBITDA||0, ca=last.CA||0, tn=last.Tonnes_entrantes||0;
  const marge=ca?(eb/ca*100).toFixed(1):null;
  const ebFirst=first.EBITDA||0, caFirst=first.CA||0;
  const parkData=SITES.map(s=>{const r=DATA.find(d=>d.Site===s&&String(d.Annee)===lastYr);return{s,eb:(r?r.EBITDA:0)||0};}).sort((a,b)=>b.eb-a.eb);
  const rank=parkData.findIndex(d=>d.s===site)+1;
  const b26=rows.find(d=>String(d.Annee)==='2026');
  const evoSpan=(delta,base,col)=>{
    if(base===0) return '';
    const pct=((delta/Math.abs(base))*100).toFixed(0);
    const arr=delta>=0?'\u2B06':'\u2B07';
    return '<span style="color:'+col+';font-size:.78rem;margin-left:5px">'+arr+' '+(delta>=0?'+':'')+pct+'%</span>';
  };
  const cell=(label,valHtml)=>'<div style="background:rgba(0,163,224,.07);border-radius:8px;padding:8px 14px;min-width:110px"><div style="font-size:.62rem;text-transform:uppercase;letter-spacing:.7px;color:#888;margin-bottom:2px">'+label+'</div><div style="font-size:.9rem;font-weight:700;color:#1a1a2e;line-height:1.3">'+valHtml+'</div></div>';
  const periodLabel=isMulti?yr2lbl(firstYr)+' \u2192 '+yr2lbl(lastYr):yr2lbl(lastYr);
  let caVal;
  if(isMulti&&caFirst!==0){
    const d=ca-caFirst;
    caVal=fmtM(caFirst)+' \u2192 '+fmtM(ca)+evoSpan(d,caFirst,d>=0?'#10b981':'#ef4444');
  } else {caVal=fmtM(ca);}
  let ebVal;
  if(isMulti&&ebFirst!==0){
    const d=eb-ebFirst;
    const ebColor=eb>=0?'#10b981':'#ef4444';
    ebVal='<span style="color:'+ebColor+'">'+fmtM(ebFirst)+'</span> \u2192 <span style="color:'+ebColor+'">'+fmtM(eb)+'</span>'+evoSpan(d,ebFirst,d>=0?'#10b981':'#ef4444');
  } else {
    ebVal='<span style="color:'+(eb>=0?'#10b981':'#ef4444')+'">'+fmtM(eb)+'</span>'+(marge?' <span style="font-size:.75rem;color:#888">('+marge+'%)</span>':'');
  }
  let margeVal='';
  if(isMulti){
    const mF=caFirst?(ebFirst/caFirst*100).toFixed(1):null;
    const mL=ca?(eb/ca*100).toFixed(1):null;
    if(mF&&mL) margeVal=mF+'% \u2192 '+mL+'%';
  } else if(marge){margeVal=marge+'%';}
  let h='<div class="dt-exec-title">&#128205; '+site+' \u2014 \u00c9volution</div>';
  h+='<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px">';
  h+=cell('P\u00e9riode',periodLabel);
  h+=cell('CA',caVal);
  h+=cell('EBITDA',ebVal);
  if(margeVal) h+=cell('Taux EBITDA',margeVal);
  h+=cell('Volume ('+yr2lbl(lastYr)+')',fmtK(tn));
  h+=cell('Rang parc EBITDA ('+yr2lbl(lastYr)+')','#'+rank+' / '+SITES.length);
  if(b26){
    const b26eb=b26.EBITDA||0, b26ca=b26.CA||0;
    const b26m=b26ca?(b26eb/b26ca*100).toFixed(1):null;
    const b26d=b26eb-eb;
    const b26v='<span style="color:'+(b26eb>=0?'#10b981':'#ef4444')+'">'+fmtM(b26eb)+'</span>'+evoSpan(b26d,eb!==0?eb:null,b26d>=0?'#10b981':'#ef4444')+(b26m?' <span style="font-size:.75rem;color:#888">('+b26m+'%)</span>':'');
    h+=cell('B2026 EBITDA',b26v);
  }
  h+='</div>';
  el.innerHTML=h;
  el.style.display='block';
}

function renderBench(){
  const site=document.getElementById('dt-site').value;
  const yr=document.getElementById('bench-year').value;
  if(!site) return;

  // EBITDA eur/t pour tous les sites pour l'annee selectionnee
  const getEurt=(s)=>{
    const row=DATA.find(d=>d.Site===s&&String(d.Annee)===String(yr));
    if(!row||!row.Tonnes_entrantes||Number(row.Tonnes_entrantes)===0) return null;
    return Number(row.EBITDA)/Number(row.Tonnes_entrantes);
  };
  const pts=SITES.map(s=>({s,v:getEurt(s)})).filter(d=>d.v!==null).sort((a,b)=>b.v-a.v);

  const labels=pts.map(d=>d.s);
  const values=pts.map(d=>d.v);
  const colors=pts.map(d=>d.s===site?'#0f3460':'rgba(148,163,184,.6)');
  const borders=pts.map(d=>d.s===site?'#0f3460':'#94a3b8');

  cBench=mkChart('c-bench',{
    type:'bar',
    data:{labels,datasets:[{data:values,backgroundColor:colors,borderColor:borders,borderWidth:2,borderRadius:4}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>' '+(c.parsed.x||0).toFixed(1)+' \u20ac/t'}}},
      scales:{x:{title:{display:true,text:'EBITDA \u20ac/t'},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}
    }
  });

  // Tableau evolution vs parc
  const rank=pts.findIndex(d=>d.s===site)+1;
  let h='<table class="rank-table" style="font-size:.78rem"><thead><tr><th style="text-align:left">Ann\u00e9e</th><th>EBITDA \u20ac/t</th><th>Moy. parc</th><th>\u00c9cart</th><th>Rang</th></tr></thead><tbody>';
  YEARS.forEach((y,yi)=>{
    const siteVal=getEurt_yr(site,y);
    const allVals=SITES.map(s=>getEurt_yr(s,y)).filter(v=>v!==null);
    const avg=allVals.length?allVals.reduce((a,b)=>a+b,0)/allVals.length:null;
    const ecart=siteVal!==null&&avg!==null?siteVal-avg:null;
    const rnk=allVals.length?[...allVals].sort((a,b)=>b-a).indexOf(siteVal)+1:null;
    const isBgt=y==='2026';
    const rowStyle=isBgt?'background:rgba(245,158,11,.08);font-style:italic;color:#92400e':'';
    const yearLabel=isBgt?'<b style="color:#d97706">B2026</b> <span style="background:#fde68a;color:#92400e;font-size:.62rem;font-weight:700;padding:1px 5px;border-radius:3px;vertical-align:middle;margin-left:3px">BUDGET</span>':'<b>'+y+'</b>';
    let trend='';
    if(yi>0&&!isBgt){const prev=getEurt_yr(site,YEARS[yi-1]);if(prev!==null&&siteVal!==null)trend=siteVal>prev?'\u2191':siteVal<prev?'\u2193':'\u2192';}
    h+='<tr style="'+rowStyle+'"><td>'+yearLabel+' '+trend+'</td>';
    h+='<td class="'+(siteVal>=0?'pos':'neg')+'">'+(siteVal!==null?siteVal.toFixed(1)+' \u20ac/t':'\u2014')+'</td>';
    h+='<td>'+(avg!==null&&!isBgt?avg.toFixed(1)+' \u20ac/t':'\u2014')+'</td>';
    h+='<td>'+(ecart!==null&&!isBgt?(ecart>=0?'<span class="pos">+':' <span class="neg">')+ecart.toFixed(1)+' \u20ac/t</span>':'\u2014')+'</td>';
    h+='<td>'+(rnk&&!isBgt?rnk+'/'+allVals.length:'\u2014')+'</td></tr>';
  });
  h+='</tbody></table>';
  h+='<div style="margin-top:10px;font-size:.78rem;color:#555;padding:0 4px">Rang '+yr+' : <b>'+rank+'/'+pts.length+'</b> sites</div>';
  document.getElementById('bench-evol-wrap').innerHTML=h;
}

function getEurt_yr(site,yr){
  // Calculé depuis les données principales pour cohérence
  const row=DATA.find(d=>d.Site===site&&String(d.Annee)===String(yr));
  if(!row||!row.Tonnes_entrantes||Number(row.Tonnes_entrantes)===0) return null;
  return Number(row.EBITDA)/Number(row.Tonnes_entrantes);
}

function renderEvol(rows){
  const realRows=rows.filter(d=>String(d.Annee)!=='2026');
  const labs=realRows.map(d=>yr2lbl(String(d.Annee)));
  const mk=(label,key,color)=>({label,data:realRows.map(d=>(d[key]||0)/1e6),borderColor:color,backgroundColor:color+'22',tension:.3,fill:false,pointRadius:5});
  cEvol=mkChart('c-evol',{type:'line',data:{labels:labs,datasets:[mk('CA','CA',COLORS[0]),mk('Marge Brute','Marge_Brute_Cash',COLORS[3]),mk('EBITDA','EBITDA',COLORS[2]),mk('EBIT','EBIT_Courant',COLORS[4])]},options:{responsive:true,maintainAspectRatio:false,plugins:{tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+' M\u20ac'}}},scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}}}}});
}

function renderDonut(){
  const site=document.getElementById('dt-site').value;
  const yr=document.getElementById('donut-year').value;
  if(!site) return;
  const row=DATA.find(d=>d.Site===site&&String(d.Annee)===yr);
  if(!row){const _cd=Chart.getChart(document.getElementById('c-donut'));if(_cd)_cd.destroy();cDonut=null;return;}
  const vals=[Math.abs(row.Couts_personnel||0),Math.abs(row.Energie||0),Math.abs((row.Maintenance_courante||0)+(row.Maintenance_obligatoire||0)),Math.abs(row.Traitement_sous_produits||0),Math.abs(row.Autres_couts_exploitation||0)];
  const labs=['Personnel','\u00c9nergie','Maintenance','Traitement s.-p.','Autres co\u00fbts'];
  cDonut=mkChart('c-donut',{type:'doughnut',data:{labels:labs,datasets:[{data:vals,backgroundColor:COLORS.slice(0,5),borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{font:{size:11}}},tooltip:{callbacks:{label:c=>' '+c.label+': '+fmt(c.parsed)+' \u20ac'}}}}});
}

function renderWaterfall(){
  const site=document.getElementById('dt-site').value;
  const yr=document.getElementById('wf-year').value;
  if(!site) return;
  const row=DATA.find(d=>d.Site===site&&String(d.Annee)===yr);
  if(!row){const _cw=Chart.getChart(document.getElementById('c-wf'));if(_cw)_cw.destroy();cWF=null;return;}

  // Build waterfall steps
  const steps=[
    {l:'CA',             v: row.CA||0,                                             type:'total'},
    {l:'Co\u00fbts ventes',    v: row.Couts_ventes_cash||0,                              type:'delta'},
    {l:'PNE',            v: row.PNE||0,                                            type:'subtotal'},
    {l:'Personnel',      v: row.Couts_personnel||0,                                type:'delta'},
    {l:'\u00c9nergie',        v: row.Energie||0,                                        type:'delta'},
    {l:'Maintenance',    v:(row.Maintenance_courante||0)+(row.Maintenance_obligatoire||0), type:'delta'},
    {l:'Traitement',     v: row.Traitement_sous_produits||0,                       type:'delta'},
    {l:'Autres',         v: row.Autres_couts_exploitation||0,                      type:'delta'},
    {l:'Marge Brute',    v: row.Marge_Brute_Cash||0,                               type:'subtotal'},
    {l:'Com.+G&A',       v:(row.Couts_commerciaux||0)+(row.Couts_GA||0),           type:'delta'},
    {l:'EBITDA',         v: row.EBITDA||0,                                         type:'subtotal'},
    {l:'Amort.',         v:(row.CDV_personnel_non_cash||0)+(row.Amortissements||0)+(row.Amortissement_IFRIC12||0), type:'delta'},
    {l:'EBIT',           v: row.EBIT_Courant||0,                                   type:'total'},
  ];

  // Compute floating bar positions
  let running=0;
  const barData=[], colors=[], stepOrig=[];
  steps.forEach(s=>{
    const vm=s.v/1e6;
    stepOrig.push(vm);
    if(s.type==='total'||s.type==='subtotal'){
      barData.push([0,vm]);
      colors.push('rgba(15,52,96,.82)');   // bleu pour CA, PNE, MB, EBITDA, EBIT
      running=vm;
    } else {
      const start=running, end=running+vm;
      barData.push([Math.min(start,end),Math.max(start,end)]);
      colors.push('rgba(239,68,68,.72)');  // rouge pour tous les postes de coût
      running=end;
    }
  });

  cWF=mkChart('c-wf',{
    type:'bar',
    data:{labels:steps.map(s=>s.l),datasets:[{data:barData,backgroundColor:colors,borderColor:colors.map(c=>c.replace('.82','1').replace('.72','1')),borderWidth:1,borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},
        tooltip:{callbacks:{
          title:c=>steps[c[0].dataIndex].l,
          label:c=>{const v=stepOrig[c.dataIndex];const s=steps[c.dataIndex];const sign=s.type==='delta'?(v>=0?'+':''):( v>=0?'':'-');return ' '+sign+Math.abs(v).toFixed(2)+' M\u20ac'+(s.type==='delta'?' (\u0394)':' (total)');}
        }}
      },
      scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}}}
    }
  });
}

function renderPL(rows){
  const defs=[
    {l:"Tonnes entrantes",      k:"Tonnes_entrantes",    fmt:v=>fmt(v)+' t',     t:''},
    {l:"Chiffre d'affaires",    k:"CA",                  fmt:v=>fmtE(v),         t:'sub'},
    {l:"  Prestations service", k:"Prestations_service", fmt:v=>fmtE(v),         t:'ind'},
    {l:"  Ventes mati\u00e8res",      k:"Ventes_matieres",    fmt:v=>fmtE(v),         t:'ind'},
    {l:"  Revenus travaux",     k:"Revenus_travaux",     fmt:v=>fmtE(v),         t:'ind'},
    {l:"Co\u00fbts ventes cash",      k:"Couts_ventes_cash",  fmt:v=>fmtE(v),         t:''},
    {l:"PNE",                   k:"PNE",                 fmt:v=>fmtE(v),         t:'sub'},
    {l:"  Personnel",           k:"Couts_personnel",     fmt:v=>fmtE(v),         t:'ind'},
    {l:"  \u00c9nergie",              k:"Energie",             fmt:v=>fmtE(v),         t:'ind'},
    {l:"  Maintenance courante",k:"Maintenance_courante",fmt:v=>fmtE(v),         t:'ind'},
    {l:"  Maintenance oblig.",  k:"Maintenance_obligatoire",fmt:v=>fmtE(v),      t:'ind'},
    {l:"  Traitement s.-p.",    k:"Traitement_sous_produits",fmt:v=>fmtE(v),     t:'ind'},
    {l:"  Autres co\u00fbts",        k:"Autres_couts_exploitation",fmt:v=>fmtE(v),   t:'ind'},
    {l:"MARGE BRUTE CASH",                k:"Marge_Brute_Cash",        fmt:v=>fmtE(v), t:'tot'},
    {l:"  Co\u00fbts commerciaux (COM)", k:"Couts_commerciaux",       fmt:v=>fmtE(v), t:'ind'},
    {l:"  Co\u00fbts G\u00e9n. & Admin. (G&A)", k:"Couts_GA",         fmt:v=>fmtE(v), t:'ind'},
    {l:"  Management Fees & redevances", k:"Management_Fees",         fmt:v=>fmtE(v), t:'ind'},
    {l:"EBITDA",                         k:"EBITDA",                  fmt:v=>fmtE(v), t:'tot'},
    {l:"  CDV Personnel (non cash)",     k:"CDV_personnel_non_cash",  fmt:v=>fmtE(v), t:'ind'},
    {l:"  Amortissements & d\u00e9pr\u00e9ciation", k:"Amortissements", fmt:v=>fmtE(v), t:'ind'},
    {l:"  Amortissement IFRIC12",        k:"Amortissement_IFRIC12",   fmt:v=>fmtE(v), t:'ind'},
    {l:"EBIT COURANT",                   k:"EBIT_Courant",            fmt:v=>fmtE(v), t:'tot'},
  ];
  const hasVar=rows.length>=2;
  let h='<table class="pl-table"><thead><tr><th>Poste</th>';
  rows.forEach(r=>h+='<th>'+yr2lbl(String(r.Annee))+'</th>');
  if(hasVar) h+='<th>Var R24/R23</th><th>Var R25/R24</th>';
  h+='</tr></thead><tbody>';
  defs.forEach(d=>{
    const cls=d.t==='tot'?'tot':d.t==='sub'?'sub':'';
    h+='<tr'+(cls?' class="'+cls+'"':'')+'>';
    h+='<td'+(d.t==='ind'?' class="indent"':'')+'>'+d.l+'</td>';
    rows.forEach(r=>{const v=r[d.k];h+='<td>'+d.fmt(v)+'</td>';});
    if(hasVar){
      const r23=rows.find(r=>String(r.Annee)==='2023'),r24=rows.find(r=>String(r.Annee)==='2024'),r25=rows.find(r=>String(r.Annee)==='2025');
      const pct=(a,b)=>a!=null&&b!=null&&a!==0?((b-a)/Math.abs(a)*100).toFixed(1)+'%':'—';
      const vA=pct(r23&&r23[d.k],r24&&r24[d.k]),vB=pct(r24&&r24[d.k],r25&&r25[d.k]);
      const cl=v=>v!=='—'?(parseFloat(v)>=0?'pos':'neg'):'';
      h+='<td class="'+cl(vA)+'">'+vA+'</td><td class="'+cl(vB)+'">'+vB+'</td>';
    }
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('pl-wrap').innerHTML=h;
}

// ══════════════════════════════════════════════════════
// ONGLET 3 — EUR/T
// ══════════════════════════════════════════════════════
let etYears=new Set(['all']), etSites=new Set(['all']), cEtEB=null, cEtCA=null, cScatter=null, cChargesEt=null;

function toggleEtYear(y,btn){
  const allBtn=document.querySelector('.et-yr');
  if(y==='all'){etYears=new Set(['all']);document.querySelectorAll('.et-yr').forEach(b=>b.classList.remove('active'));allBtn.classList.add('active');}
  else{
    etYears.delete('all');allBtn.classList.remove('active');
    if(etYears.has(y)){etYears.delete(y);btn.classList.remove('active');}
    else{etYears.add(y);btn.classList.add('active');}
    if(etYears.size===0){etYears=new Set(['all']);allBtn.classList.add('active');}
  }
  renderEt();
}

const getVal=(s,yr,metric)=>{
  // EBITDA €/t : toujours calculé depuis les données principales (évite les incohérences source)
  if(metric.trim()==='EBITDA'){
    const yrNum=yr.replace(/^R/,'');
    const row=DATA.find(d=>d.Site===s&&String(d.Annee)===yrNum);
    if(!row||!row.Tonnes_entrantes||Number(row.Tonnes_entrantes)===0) return null;
    return Number(row.EBITDA)/Number(row.Tonnes_entrantes);
  }
  const r=EURT.find(d=>d.Site===s&&d.Annee===yr&&d.Metrique&&d.Metrique.trim()===metric.trim());
  return r&&r.Valeur_EUR_t!==''?Number(r.Valeur_EUR_t):null;
};

function renderEt(){
  const yrs=etYears.has('all')?['R2023','R2024','R2025']:[...etYears];
  const sites=etSites.has('all')?SITES:[...etSites];


  const makeBar=(metric)=>yrs.map((yr,i)=>({label:yr2lbl(yr),data:sites.map(s=>getVal(s,yr,metric)),backgroundColor:C3(i)+'bb',borderColor:C3(i),borderWidth:2,borderRadius:4}));

  cEtEB=mkChart('c-et-eb',{type:'bar',data:{labels:sites,datasets:makeBar('EBITDA')},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+(c.parsed.x||0).toFixed(1)+' \u20ac/t'}}},scales:{x:{title:{display:true,text:'\u20ac/t'},grid:{color:'#f0f0f0'}}}}});

  cEtCA=mkChart('c-et-ca',{type:'bar',data:{labels:sites,datasets:makeBar("VE000001 - Chiffre d'affaires")},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+(c.parsed.x||0).toFixed(1)+' \u20ac/t'}}},scales:{x:{title:{display:true,text:'\u20ac/t'},grid:{color:'#f0f0f0'}}}}});

  // Charges internes empilées — triées par EBITDA €/t
  const etActiveYrs=etYears.has('all')?['R2023','R2024','R2025']:[...etYears];
  const chargeYear=etActiveYrs[etActiveYrs.length-1];
  const chargeMetrics=[
    {m:"  VE000051 - Co\u00fbts de personnel",                                          l:'Personnel',       color:'#0f3460'},
    {m:"  VE000077 - Co\u00fbt des \u00e9nergies pour production & distribution",       l:'\u00c9nergie',          color:'#e94560'},
    {m:"  VE000067 - Entretien & maintenance courante (hors personnel)",               l:'Maint. courante', color:'#533483'},
    {m:"  VE000071 - Maint. Obligatoire Programm\u00e9e & renouvel. (hors pers.)",     l:'Maint. oblig.',   color:'#16c79a'},
    {m:"  VE000089 - Traitement et \u00e9vacuation des sous-produits",                 l:'Traitement s.-p.',color:'#f4a261'},
    {m:"  VE000097 - Autres co\u00fbts d'exploitation",                                l:'Autres co\u00fbts',    color:'#2196f3'},
  ];
  // Trier les sites par EBITDA €/t décroissant
  const chargeSites=[...sites].sort((a,b)=>{
    const va=getVal(a,chargeYear,'EBITDA')||0, vb=getVal(b,chargeYear,'EBITDA')||0;
    return vb-va;
  });
  const chargeDs=chargeMetrics.map(cm=>({
    label:cm.l,
    data:chargeSites.map(s=>{ const v=getVal(s,chargeYear,cm.m); return v!==null?Math.abs(v):0; }),
    backgroundColor:cm.color+'cc',
    borderColor:cm.color,
    borderWidth:1,
    borderRadius:2,
  }));
  cChargesEt=mkChart('c-charges-et',{
    type:'bar',
    data:{labels:chargeSites,datasets:chargeDs},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'top',labels:{font:{size:10},usePointStyle:true}},
        tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+(c.parsed.y||0).toFixed(1)+' \u20ac/t'}}},
      scales:{
        x:{stacked:true,grid:{display:false}},
        y:{stacked:true,title:{display:true,text:'\u20ac/t'},grid:{color:'#f0f0f0'}}
      }
    }
  });

  // Scatter quadrant — 4 categories
  const scatterYear=chargeYear.replace('R','');
  const allPts=SITES.map(s=>{
    const row=DATA.find(d=>d.Site===s&&String(d.Annee)===scatterYear);
    const eurt=getVal(s,'R'+scatterYear,'EBITDA');
    if(!row||eurt===null) return null;
    return {x:row.Tonnes_entrantes,y:eurt,label:s};
  }).filter(Boolean);

  const THRESH_TN=35000, THRESH_EB=0;

  const CATS=[
    {key:'champ',label:'Grands & Rentables',    desc:'>35kt & EBITDA/t>0', color:'#10b981',filt:p=>p.y>THRESH_EB&&p.x>=THRESH_TN},
    {key:'effic',label:'Petits & Rentables',    desc:'<35kt & EBITDA/t>0', color:'#2196f3',filt:p=>p.y>THRESH_EB&&p.x<THRESH_TN},
    {key:'devel',label:'Grands \u00e0 optimiser',  desc:'>35kt & EBITDA/t\u22640',color:'#f59e0b',filt:p=>p.y<=THRESH_EB&&p.x>=THRESH_TN},
    {key:'diff', label:'Petits \u00e0 relancer',   desc:'<35kt & EBITDA/t\u22640',color:'#ef4444',filt:p=>p.y<=THRESH_EB&&p.x<THRESH_TN},
  ];

  // Régression linéaire
  const trendDs=(function(){
    const n=allPts.length; if(n<2) return null;
    const sx=allPts.reduce(function(a,p){return a+p.x;},0);
    const sy=allPts.reduce(function(a,p){return a+p.y;},0);
    const sxy=allPts.reduce(function(a,p){return a+p.x*p.y;},0);
    const sx2=allPts.reduce(function(a,p){return a+p.x*p.x;},0);
    const slope=(n*sxy-sx*sy)/(n*sx2-sx*sx);
    const intercept=(sy-slope*sx)/n;
    const minX=Math.min.apply(null,allPts.map(function(p){return p.x;}));
    const maxX=Math.max.apply(null,allPts.map(function(p){return p.x;}));
    const r2=(function(){
      const meanY=sy/n;
      const ss_tot=allPts.reduce(function(a,p){return a+Math.pow(p.y-meanY,2);},0);
      const ss_res=allPts.reduce(function(a,p){return a+Math.pow(p.y-(slope*p.x+intercept),2);},0);
      return ss_tot>0?1-ss_res/ss_tot:0;
    })();
    return {type:'line',label:'Tendance (R²='+r2.toFixed(2)+')',
      data:[{x:minX,y:slope*minX+intercept},{x:maxX,y:slope*maxX+intercept}],
      borderColor:'#94a3b8',borderWidth:2,borderDash:[7,4],
      pointRadius:0,fill:false,tension:0,order:99};
  })();
  cScatter=mkChart('c-scatter',{
    type:'scatter',
    data:{datasets:[...CATS.map(c=>({
      label:c.label+' \u2014 '+c.desc,
      data:allPts.filter(c.filt),
      backgroundColor:c.color+'bb',borderColor:c.color,borderWidth:2,
      pointRadius:11,pointHoverRadius:14,
    })),...(trendDs?[trendDs]:[])]}  ,
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'top',labels:{usePointStyle:true,font:{size:11},filter:function(item){return item.text!==''&&!item.text.startsWith('Tendance')||item.text.startsWith('Tendance');}}},
        tooltip:{callbacks:{label:function(c){if(c.dataset.type==='line'||!c.raw.label) return null; return ' '+c.raw.label+' \u2014 '+fmt(c.raw.x)+' t / '+c.raw.y.toFixed(1)+' \u20ac/t';}}}
      },
      scales:{
        x:{title:{display:true,text:'Tonnes entrantes'},grid:{color:'#f0f0f0'}},
        y:{title:{display:true,text:'EBITDA \u20ac/t'},grid:{color:'#f0f0f0'}}
      }
    }
  });

  // Category table
  let hc='<div class="cat-legend">';
  CATS.forEach(c=>{const n=allPts.filter(c.filt).length;if(n) hc+='<div class="cat-badge '+c.key+'"><div class="cat-dot" style="background:'+c.color+'"></div>'+c.label+' ('+n+')</div>';});
  hc+='</div><table class="rank-table" style="margin-top:8px"><thead><tr><th>Cat\u00e9gorie</th><th>Site</th><th>Tonnes</th><th>EBITDA \u20ac/t</th></tr></thead><tbody>';
  CATS.forEach(c=>{
    allPts.filter(c.filt).sort((a,b)=>b.y-a.y).forEach((p,i)=>{
      hc+='<tr><td style="color:'+c.color+';font-weight:700">'+(i===0?c.label:'')+'</td><td><span class="site-link" data-site="'+p.label+'" onclick="goToSite(this.dataset.site)">'+p.label+'</span></td><td>'+fmt(p.x)+' t</td><td class="'+(p.y>=0?'pos':'neg')+'">'+p.y.toFixed(1)+' \u20ac/t</td></tr>';
    });
  });
  hc+='</tbody></table>';
  document.getElementById('cat-table-wrap').innerHTML=hc;

  // Heatmap — sites en lignes, métriques en colonnes, une année à la fois
  // getValSum : somme plusieurs métriques €/t (ex: maintenance courante + obligatoire)
  const getValSum=(s,yr,mArr)=>{
    const vals=mArr.map(m=>getVal(s,yr,m));
    if(vals.every(v=>v===null)) return null;
    return vals.reduce((sum,v)=>sum+(v||0),0);
  };
  const HM_COLS=[
    {l:"CA \u20ac/t",          get:(s,y)=>getVal(s,y,"VE000001 - Chiffre d'affaires"),                                                   type:'revenue'},
    {l:'PNE \u20ac/t',         get:(s,y)=>getVal(s,y,'PNE'),                                                                              type:'result'},
    {l:'Personnel \u20ac/t',   get:(s,y)=>getVal(s,y,'VE000051 - Co\u00fbts de personnel'),                                               type:'cost'},
    {l:'\u00c9nergie \u20ac/t',get:(s,y)=>getVal(s,y,'VE000077 - Co\u00fbt des \u00e9nergies pour production & distribution'),            type:'cost'},
    {l:'Maintenance \u20ac/t', get:(s,y)=>getValSum(s,y,['VE000067 - Entretien & maintenance courante (hors personnel)','VE000071 - Maint. Obligatoire Programm\u00e9e & renouvel. (hors pers.)']), type:'cost'},
    {l:'Autres co\u00fbts \u20ac/t',get:(s,y)=>getVal(s,y,"VE000097 - Autres co\u00fbts d'exploitation"),                               type:'cost'},
    {l:'Marge Brute \u20ac/t', get:(s,y)=>getVal(s,y,'Marge Brute Cash'),                                                                type:'result'},
    {l:'EBITDA \u20ac/t',      get:(s,y)=>getVal(s,y,'EBITDA'),                                                                           type:'result'},
    {l:'EBIT \u20ac/t',        get:(s,y)=>getVal(s,y,'EBIT Courant'),                                                                     type:'result'},
  ];
  // Pick the reference year for the heatmap: last selected real year
  const hmYr=yrs.filter(y=>y!=='B2026').pop()||yrs[yrs.length-1];
  const hmPrevYr=hmYr==='R2023'?null:('R'+(parseInt(hmYr.replace('R',''))-1));
  let h='<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:12px;font-size:.8rem;color:#555">'
    +'<span style="font-weight:700;color:#003a63;font-size:.85rem">Tableau \u20ac/t \u2014 '+yr2lbl(hmYr)+'</span>'
    +(hmPrevYr?'<span style="color:#aaa">(\u2191\u2193 vs '+yr2lbl(hmPrevYr)+')</span>':'')
    +'<span style="margin-left:auto;display:flex;gap:10px;align-items:center">'
    +'<span><span style="display:inline-block;width:10px;height:10px;background:rgba(16,185,129,.35);border-radius:2px;vertical-align:middle;margin-right:4px"></span>Positif</span>'
    +'<span><span style="display:inline-block;width:10px;height:10px;background:rgba(239,68,68,.3);border-radius:2px;vertical-align:middle;margin-right:4px"></span>N\u00e9gatif</span>'
    +'</span></div>';
  h+='<table class="hm-table"><thead><tr><th>Site</th>';
  HM_COLS.forEach(c=>h+='<th>'+c.l+'</th>');
  h+='</tr></thead><tbody>';
  // Sort sites by EBITDA €/t descending
  const sitesSorted=[...sites].sort((a,b)=>{
    const va=getVal(a,hmYr,'EBITDA')||0, vb=getVal(b,hmYr,'EBITDA')||0;
    return vb-va;
  });
  sitesSorted.forEach((s,si)=>{
    const rowBg=si%2===0?'':'background:#fafbfc';
    h+='<tr style="'+rowBg+'"><td style="font-weight:700;color:#003a63">'+s+'</td>';
    HM_COLS.forEach(col=>{
      const v=col.get(s,hmYr);
      const vprev=hmPrevYr?col.get(s,hmPrevYr):null;
      let bg='';
      if(v!==null&&col.type==='result') bg=v>=0?'background:rgba(16,185,129,.22)':'background:rgba(239,68,68,.22)';
      let arrow='';
      if(v!==null&&vprev!==null&&Math.abs(v-vprev)>0.05){
        const isUp=(v-vprev)>0;
        const upGood=(col.type==='result'||col.l.startsWith('CA'));
        const arrowCol=(isUp===upGood)?'#10b981':'#ef4444';
        arrow='<span style="color:'+arrowCol+';font-size:.7rem;margin-left:2px">'+(isUp?'\u2191':'\u2193')+'</span>';
      }
      h+='<td style="'+bg+'">'+(v!==null?v.toFixed(1):'\u2014')+arrow+'</td>';
    });
    h+='</tr>';
  });
  // Ligne moyenne parc
  h+='<tr style="background:#eef2ff;font-weight:700;border-top:2px solid #c7d2fe"><td style="color:#003a63">\u2300 Moyenne parc</td>';
  HM_COLS.forEach(col=>{
    const vals=sites.map(s=>col.get(s,hmYr)).filter(v=>v!==null);
    const avg=vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:null;
    const bg=avg!==null&&col.type==='result'?(avg>=0?'background:rgba(16,185,129,.15)':'background:rgba(239,68,68,.15)'):'';
    h+='<td style="'+bg+'">'+(avg!==null?avg.toFixed(1):'\u2014')+'</td>';
  });
  h+='</tr>';
  h+='</tbody></table>';
  document.getElementById('hm-wrap').innerHTML=h;
}

// ══════════════════════════════════════════════════════
// ONGLET 4 — REGION
// ══════════════════════════════════════════════════════
const REG_MAP={'Nantes':'COU','Saran':'COU','Amiens':'NNO','Paris 15':'IDF','Le Havre':'NNO','Sevran':'IDF','Ch\u00e9zy':'IDF','Portes les Valences':'BARA','Montpellier':'BARA','Millau':'BARA','B\u00e8gles':'SO'};
let rgYears=new Set(['all']), cRgCA=null, cRgEB=null, cRgEBT=null, rgCAType='bar', rgMetric='EBITDA';

function toggleRgYear(y,btn){
  const allBtn=document.querySelector('.rg-yr');
  if(y==='all'){rgYears=new Set(['all']);document.querySelectorAll('.rg-yr').forEach(function(b){b.classList.remove('active');});allBtn.classList.add('active');}
  else{
    rgYears.delete('all');allBtn.classList.remove('active');
    if(rgYears.has(y)){rgYears.delete(y);btn.classList.remove('active');}
    else{rgYears.add(y);btn.classList.add('active');}
    if(rgYears.size===0){rgYears=new Set(['all']);allBtn.classList.add('active');}
  }
  renderRg();
}

function setRgCAType(type,btn){
  rgCAType=type;
  document.querySelectorAll('#tab-rg .rg-ca-type').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  renderRg();
}

function setRgMetric(m){
  rgMetric=m;
  renderRg();
}

function toggleRgDrill(el){
  const rg=el.getAttribute('data-rg');
  const drills=document.querySelectorAll('[data-drill="'+rg+'"]');
  const visible=drills.length>0&&drills[0].style.display!=='none';
  drills.forEach(function(r){r.style.display=visible?'none':'table-row';});
  const arrow=document.getElementById('rg-arrow-'+rg);
  if(arrow) arrow.textContent=visible?'\u25b6':'\u25bc';
}

function renderRg(){
  const allRows=DATA.map(function(d){return Object.assign({},d,{Reg:d.Region||REG_MAP[d.Site]||'Autre'});});
  const activeRgYrs=rgYears.has('all')?REAL_YEARS:[...rgYears].filter(function(y){return y!=='2026';});
  const rgIsAll=rgYears.has('all');
  const rgIsSingle=!rgIsAll&&activeRgYrs.length===1;
  const rows=allRows.filter(function(d){return activeRgYrs.includes(String(d.Annee));});
  // Étiquette période affichée sous chaque graphique/tableau
  const rgPeriodLabel='Données : '+activeRgYrs.map(yr2lbl).join(' + ');
  ['rg-ca-period','rg-eb-period','rg-ebt-period','rg-table-period'].forEach(function(id){const el=document.getElementById(id);if(el)el.textContent='('+activeRgYrs.map(yr2lbl).join(' + ')+')'});
  const regions=[...new Set(allRows.map(function(d){return d.Reg;}))].sort();

  // ── KPIs ───────────────────────────────────────────────────────
  const totalCA=rows.reduce(function(s,d){return s+(d.CA||0);},0);
  const totalEB=rows.reduce(function(s,d){return s+(d.EBITDA||0);},0);
  const totalTN=rows.reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);
  document.getElementById('rg-ca').textContent=fmtM(totalCA);
  document.getElementById('rg-ca-s').textContent=regions.length+' r\u00e9gions';
  document.getElementById('rg-eb').textContent=fmtM(totalEB);
  document.getElementById('rg-eb-s').textContent='Taux: '+(totalCA?((totalEB/totalCA)*100).toFixed(1):0)+'%';
  document.getElementById('rg-tn').textContent=fmtK(totalTN);
  document.getElementById('rg-tn-s').textContent='tonnes entrantes';

  // ── CA chart : barres group\u00e9es ou ligne tendance ───────────────
  if(rgCAType==='line'&&rgIsAll){
    const caLine=regions.map(function(rg,i){
      return {label:rg,data:REAL_YEARS.map(function(yr){return allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;}).reduce(function(s,d){return s+(d.CA||0);},0)/1e6;}),borderColor:COLORS[i],backgroundColor:COLORS[i]+'33',tension:0.3,pointRadius:5,pointHoverRadius:8,fill:false,borderWidth:2};
    });
    cRgCA=mkChart('c-rg-ca',{type:'line',data:{labels:REAL_YEARS.map(yr2lbl),datasets:caLine},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:function(c){return ' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+' M\u20ac';}}}},scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},x:{grid:{display:false}}}}});
  } else {
    const yList0=rgIsAll?REAL_YEARS:activeRgYrs;
    const caDs=yList0.map(function(yr,i){return {label:yr2lbl(yr),data:regions.map(function(rg){return allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;}).reduce(function(s,d){return s+(d.CA||0);},0)/1e6;}),backgroundColor:C3(i),borderRadius:4};});
    cRgCA=mkChart('c-rg-ca',{type:'bar',data:{labels:regions,datasets:caDs},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:function(c){return ' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+' M\u20ac';}}}},scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},x:{grid:{display:false}}}}});
  }

  // ── EBITDA chart (horizontal, tri\u00e9) ───────────────────────────
  const sortedRg=regions.map(function(rg){return {rg:rg,v:rows.filter(function(d){return d.Reg===rg;}).reduce(function(s,d){return s+(d.EBITDA||0);},0)};}).sort(function(a,b){return a.v-b.v;});
  cRgEB=mkChart('c-rg-eb',{type:'bar',data:{labels:sortedRg.map(function(d){return d.rg;}),datasets:[{label:'EBITDA',data:sortedRg.map(function(d){return d.v/1e6;}),backgroundColor:sortedRg.map(function(d){return d.v>=0?'rgba(16,185,129,.5)':'rgba(239,68,68,.5)';}),borderColor:sortedRg.map(function(d){return d.v>=0?'#10b981':'#ef4444';}),borderWidth:2,borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return ' EBITDA: '+c.parsed.x.toFixed(2)+' M\u20ac';}}}},scales:{x:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}}});

  // ── EBITDA \u20ac/t chart ───────────────────────────────────────────
  const ebtArr=regions.map(function(rg){
    const sub=rows.filter(function(d){return d.Reg===rg;});
    const eb=sub.reduce(function(s,d){return s+(d.EBITDA||0);},0);
    const tn=sub.reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);
    return {rg:rg,v:tn>0?Math.round(eb/tn*10)/10:null};
  }).filter(function(d){return d.v!==null;}).sort(function(a,b){return a.v-b.v;});
  cRgEBT=mkChart('c-rg-ebt',{type:'bar',data:{labels:ebtArr.map(function(d){return d.rg;}),datasets:[{label:'EBITDA \u20ac/t',data:ebtArr.map(function(d){return d.v;}),backgroundColor:ebtArr.map(function(d){return d.v>=0?'rgba(16,185,129,.5)':'rgba(239,68,68,.5)';}),borderColor:ebtArr.map(function(d){return d.v>=0?'#10b981':'#ef4444';}),borderWidth:2,borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return ' '+c.parsed.x.toFixed(1)+' \u20ac/t';}}}},scales:{x:{title:{display:true,text:'\u20ac/t'},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}}});

  // ── Cartes visuelles par r\u00e9gion ──────────────────────────────
  const rgMvMap={};
  regions.forEach(function(rg){rgMvMap[rg]=rows.filter(function(d){return d.Reg===rg;}).reduce(function(s,d){return s+(d[rgMetric]||0);},0);});
  const rgTnMap2={};
  regions.forEach(function(rg){rgTnMap2[rg]=rows.filter(function(d){return d.Reg===rg;}).reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);});
  const rgCAMap={};
  regions.forEach(function(rg){rgCAMap[rg]=rows.filter(function(d){return d.Reg===rg;}).reduce(function(s,d){return s+(d.CA||0);},0);});
  const sortedCards=regions.map(function(rg){return {rg:rg,v:rgMvMap[rg],tn:rgTnMap2[rg]||0,ca:rgCAMap[rg]||0};}).sort(function(a,b){return b.v-a.v;});
  const maxAbsV=Math.max.apply(null,sortedCards.map(function(d){return Math.abs(d.v)||0;}));
  const RG_SITES={};
  regions.forEach(function(rg){RG_SITES[rg]=[...new Set(allRows.filter(function(d){return d.Reg===rg;}).map(function(d){return d.Site;}))];});
  const ML={'CA':'CA','PNE':'PNE','Marge_Brute_Cash':'Marge Brute','EBITDA':'EBITDA','EBIT_Courant':'EBIT'};
  let cards='<div style="display:flex;flex-direction:column;gap:8px;width:100%">';
  sortedCards.forEach(function(d,i){
    const isPos=d.v>=0;
    const col=isPos?'#10b981':'#ef4444';
    const bgcol=isPos?'rgba(16,185,129,.08)':'rgba(239,68,68,.08)';
    const pct=maxAbsV>0?(Math.abs(d.v)/maxAbsV*100):0;
    const tauxStr=d.ca?(d.v/d.ca*100).toFixed(1)+'%':'—';
    const sites=RG_SITES[d.rg]||[];
    const vLabel=fmtM(d.v);
    cards+='<div style="display:flex;align-items:center;gap:12px;background:'+bgcol+';border-left:3px solid '+col+';border-radius:8px;padding:10px 14px">';
    // Rank + nom
    cards+='<div style="min-width:80px">';
    cards+='<div style="font-size:.65rem;color:#aaa;font-weight:600;letter-spacing:.5px">#'+(i+1)+'</div>';
    cards+='<div style="font-size:1rem;font-weight:700;color:#1a1a2e">'+d.rg+'</div>';
    cards+='<div style="font-size:.65rem;color:#aaa;margin-top:1px">'+sites.join(' \u00b7 ')+'</div>';
    cards+='</div>';
    // Barre + valeur
    cards+='<div style="flex:1">';
    cards+='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">';
    cards+='<span style="font-size:.68rem;color:#888">'+ML[rgMetric]+'</span>';
    cards+='<span style="font-size:1rem;font-weight:700;color:'+col+'">'+vLabel+'</span>';
    cards+='</div>';
    cards+='<div style="background:#e5e7eb;border-radius:4px;height:8px">';
    cards+='<div style="width:'+pct.toFixed(1)+'%;height:8px;background:'+col+';border-radius:4px;transition:width .3s"></div>';
    cards+='</div>';
    cards+='</div>';
    // Stats droite
    cards+='<div style="min-width:90px;text-align:right">';
    cards+='<div style="font-size:.72rem;color:#555">'+fmtK(d.tn)+'</div>';
    cards+='<div style="font-size:.65rem;color:#aaa">tonnes entr.</div>';
    if(rgMetric==='EBITDA'&&d.ca){cards+='<div style="font-size:.68rem;color:'+col+';font-weight:600;margin-top:3px">'+tauxStr+'</div><div style="font-size:.62rem;color:#aaa">taux EBITDA</div>';}
    cards+='</div>';
    cards+='</div>';
  });
  cards+='</div>';
  document.getElementById('rg-map').innerHTML=cards;

  // ── Tableau drill-down + taux% + \u0394 N-1 ────────────────────────
  const tableYrs=activeRgYrs;
  let h='<table class="pl-table"><thead><tr><th>R\u00e9gion / Site</th>';
  if(!rgIsSingle){
    tableYrs.forEach(function(yr){h+='<th>CA '+yr2lbl(yr)+'</th><th>EBITDA '+yr2lbl(yr)+'</th><th>Taux%</th><th>Δ vs N-1</th>';});
  } else {
    h+='<th>CA</th><th>EBITDA</th><th>Taux%</th><th>EBITDA \u20ac/t</th><th>\u0394 vs N-1</th><th>Tonnes</th>';
  }
  h+='</tr></thead><tbody>';

  regions.forEach(function(rg){
    const sitesInRg=[...new Set(allRows.filter(function(d){return d.Reg===rg;}).map(function(d){return d.Site;}))];
    if(!rgIsSingle){
      h+='<tr class="rg-row" data-rg="'+rg+'" onclick="toggleRgDrill(this)" style="cursor:pointer"><td><b id="rg-arrow-'+rg+'">\u25b6</b> <b>'+rg+'</b> <span style="font-size:10px;color:#888">('+sitesInRg.length+' sites)</span></td>';
      tableYrs.forEach(function(yr,yi){
        const sub=allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;});
        const ca=sub.reduce(function(s,d){return s+(d.CA||0);},0);
        const eb=sub.reduce(function(s,d){return s+(d.EBITDA||0);},0);
        const tx=ca?((eb/ca)*100).toFixed(1)+'%':'—';
        let delta='—',dcolor='#888';
        if(yi>0){
          const ps=allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===tableYrs[yi-1];});
          const peb=ps.reduce(function(s,d){return s+(d.EBITDA||0);},0);
          const diff=eb-peb; delta=(diff>=0?'+':'')+fmtM(diff); dcolor=diff>=0?'#10b981':'#ef4444';
        }
        h+='<td>'+fmtM(ca)+'</td><td class="'+(eb>=0?'pos':'neg')+'">'+fmtM(eb)+'</td><td>'+tx+'</td><td style="font-size:11px;color:'+dcolor+'">'+delta+'</td>';
      });
      h+='</tr>';
      sitesInRg.forEach(function(site){
        h+='<tr data-drill="'+rg+'" style="display:none;background:#f8fafc"><td style="padding-left:28px;font-size:12px">\u21b3 <span class="site-link" onclick="goToSite(this.dataset.site)" data-site="'+site+'">'+site+'</span></td>';
        tableYrs.forEach(function(yr,yi){
          const sub=allRows.filter(function(d){return d.Site===site&&String(d.Annee)===yr;});
          const ca=sub.reduce(function(s,d){return s+(d.CA||0);},0);
          const eb=sub.reduce(function(s,d){return s+(d.EBITDA||0);},0);
          const tx=ca?((eb/ca)*100).toFixed(1)+'%':'—';
          let delta='—',dcolor='#888';
          if(yi>0){
            const ps=allRows.filter(function(d){return d.Site===site&&String(d.Annee)===tableYrs[yi-1];});
            const peb=ps.reduce(function(s,d){return s+(d.EBITDA||0);},0);
            const diff=eb-peb; delta=(diff>=0?'+':'')+fmtM(diff); dcolor=diff>=0?'#10b981':'#ef4444';
          }
          h+='<td style="font-size:12px">'+fmtM(ca)+'</td><td class="'+(eb>=0?'pos':'neg')+'" style="font-size:12px">'+fmtM(eb)+'</td><td style="font-size:12px">'+tx+'</td><td style="font-size:11px;color:'+dcolor+'">'+delta+'</td>';
        });
        h+='</tr>';
      });
    } else {
      const sub=rows.filter(function(d){return d.Reg===rg;});
      const ca=sub.reduce(function(s,d){return s+(d.CA||0);},0);
      const eb=sub.reduce(function(s,d){return s+(d.EBITDA||0);},0);
      const tn=sub.reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);
      const tx=ca?((eb/ca)*100).toFixed(1)+'%':'—';
      const ebt=tn>0?(eb/tn).toFixed(1)+' \u20ac/t':'—';
      const prevYr=String(parseInt(activeRgYrs[0])-1);
      const ps=allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===prevYr;});
      const peb=ps.reduce(function(s,d){return s+(d.EBITDA||0);},0);
      const diff=ps.length>0?eb-peb:null;
      const delta=diff!==null?(diff>=0?'+':'')+fmtM(diff):'—';
      const dcolor=diff!==null&&diff>=0?'#10b981':diff===null?'#888':'#ef4444';
      h+='<tr class="rg-row" data-rg="'+rg+'" onclick="toggleRgDrill(this)" style="cursor:pointer"><td><b id="rg-arrow-'+rg+'">\u25b6</b> <b>'+rg+'</b> <span style="font-size:10px;color:#888">('+sitesInRg.length+' sites)</span></td>';
      h+='<td>'+fmtM(ca)+'</td><td class="'+(eb>=0?'pos':'neg')+'">'+fmtM(eb)+'</td><td>'+tx+'</td><td>'+ebt+'</td><td style="font-size:11px;color:'+dcolor+'">'+delta+'</td><td>'+fmtK(tn)+'</td></tr>';
      sitesInRg.forEach(function(site){
        const ss=rows.filter(function(d){return d.Site===site;});
        const sca=ss.reduce(function(s,d){return s+(d.CA||0);},0);
        const seb=ss.reduce(function(s,d){return s+(d.EBITDA||0);},0);
        const stn=ss.reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);
        const stx=sca?((seb/sca)*100).toFixed(1)+'%':'—';
        const sebt=stn>0?(seb/stn).toFixed(1)+' \u20ac/t':'—';
        const sps=allRows.filter(function(d){return d.Site===site&&String(d.Annee)===prevYr;});
        const speb=sps.reduce(function(s,d){return s+(d.EBITDA||0);},0);
        const sdiff=sps.length>0?seb-speb:null;
        const sdelta=sdiff!==null?(sdiff>=0?'+':'')+fmtM(sdiff):'—';
        const sdcolor=sdiff!==null&&sdiff>=0?'#10b981':sdiff===null?'#888':'#ef4444';
        h+='<tr data-drill="'+rg+'" style="display:none;background:#f8fafc"><td style="padding-left:28px;font-size:12px">\u21b3 <span class="site-link" onclick="goToSite(this.dataset.site)" data-site="'+site+'">'+site+'</span></td>';
        h+='<td style="font-size:12px">'+fmtM(sca)+'</td><td class="'+(seb>=0?'pos':'neg')+'" style="font-size:12px">'+fmtM(seb)+'</td><td style="font-size:12px">'+stx+'</td><td style="font-size:12px">'+sebt+'</td><td style="font-size:11px;color:'+sdcolor+'">'+sdelta+'</td><td style="font-size:12px">'+fmtK(stn)+'</td>';
        h+='</tr>';
      });
    }
  });
  h+='</tbody></table>';
  document.getElementById('rg-table-wrap').innerHTML=h;

  // ── Top 3 / Flop 3 sites ──────────────────────────────────────
  const podiumEl=document.getElementById('rg-podium');
  if(podiumEl){
    const siteEb=SITES.map(s=>{
      const sub=rows.filter(d=>d.Site===s);
      const eb=sub.reduce((a,d)=>a+(d.EBITDA||0),0);
      const ca=sub.reduce((a,d)=>a+(d.CA||0),0);
      return {s,eb,tx:ca?(eb/ca*100).toFixed(1):null};
    }).sort((a,b)=>b.eb-a.eb);
    const top3=siteEb.slice(0,3);
    const flop3=siteEb.slice(-3).reverse();
    const makeCard=(title,icon,sites,isTop)=>{
      let c='<div class="podium-card"><div class="podium-title">'+icon+' '+title+'</div>';
      sites.forEach((d,i)=>{
        const col=isTop?'#10b981':'#ef4444';
        const rank=isTop?(i+1):(SITES.length-i);
        c+='<div class="podium-row"><span><b style="color:#aaa;font-size:.7rem;margin-right:6px">#'+rank+'</b><span class="site-link" data-site="'+d.s+'" onclick="goToSite(this.dataset.site)">'+d.s+'</span></span>';
        c+='<span><b style="color:'+col+'">'+fmtM(d.eb)+'</b>'+(d.tx?'<span style="color:#aaa;font-size:.7rem;margin-left:5px">'+d.tx+'%</span>':'')+'</span></div>';
      });
      c+='</div>';
      return c;
    };
    podiumEl.innerHTML=makeCard('Top 3 EBITDA','\U0001F3C6',top3,true)+makeCard('Flop 3 EBITDA','\u26A0\uFE0F',flop3,false);
  }
}

// ══════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════
(function init(){
  SITES.forEach(s=>{
    // Pills Vue d'ensemble
    const b1=document.createElement('button');
    b1.className='btn-pill'; b1.textContent=s;
    b1.onclick=function(){toggleOvSite(s,this);};
    document.getElementById('ov-site-pills').appendChild(b1);
    // Pills Vue €/t
    const b2=document.createElement('button');
    b2.className='btn-pill'; b2.textContent=s;
    b2.onclick=function(){toggleEtSite(s,this);};
    document.getElementById('et-site-pills').appendChild(b2);
    // Dropdown Détail par site
    const o=document.createElement('option');
    o.value=s; o.textContent=s;
    document.getElementById('dt-site').appendChild(o);
    // Dropdown Comparaison
    const o2=document.createElement('option');
    o2.value=s; o2.textContent=s;
    document.getElementById('dt-site2').appendChild(o2);
  });
  // Animations & interactions Chart.js globales
  if(typeof Chart!=='undefined'){
    Chart.defaults.animation.duration=480;
    Chart.defaults.animation.easing='easeInOutQuart';
    Chart.defaults.interaction.mode='index';
    Chart.defaults.interaction.intersect=false;
  }
  requestAnimationFrame(()=>requestAnimationFrame(()=>{renderHome();}));

  // ── Redimensionnement charts avant/après impression ─────────────────────
  window.addEventListener('beforeprint', function(){
    document.querySelectorAll('.ch').forEach(function(el){
      el.dataset.origH = el.style.height || '';
      el.style.height = el.classList.contains('tall') ? '220px' : '200px';
      var c = el.querySelector('canvas');
      if(c){ var chart = Chart.getChart(c); if(chart) chart.resize(); }
    });
  });
  window.addEventListener('afterprint', function(){
    document.querySelectorAll('.ch').forEach(function(el){
      el.style.height = el.dataset.origH || '';
      delete el.dataset.origH;
    });
    var p = document.querySelector('.page.active');
    if(!p) return;
    var id = p.id.replace('tab-','');
    requestAnimationFrame(function(){ requestAnimationFrame(function(){
      if(id==='home') renderHome();
      else if(id==='ov') renderOv();
      else if(id==='dt') renderDt();
      else if(id==='et') renderEt();
      else if(id==='rg') renderRg();
    }); });
  });
})();
</script>
</body>
</html>
"""

# ── Injection ────────────────────────────────────────────────────────────────
html_out = (HTML
    .replace("%%CHARTJS%%", CHARTJS)
    .replace("%%DATE%%",    GENERATED)
    .replace("%%LOGO%%",    LOGO_B64)
    .replace("%%DATA%%",    DATA_JSON)
    .replace("%%EURT%%",    EUR_T_JSON)
)

out_path = os.path.join(BASE, "dashboard.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"[OK] dashboard.html ({os.path.getsize(out_path)//1024} Ko) - {GENERATED}")
