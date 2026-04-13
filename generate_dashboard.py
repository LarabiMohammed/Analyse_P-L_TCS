"""
generate_dashboard.py  —  Génère dashboard.html (standalone, offline-ready)
Usage : python generate_dashboard.py

────────────────────────────────────────────────────────────────────────────
ARCHITECTURE GÉNÉRALE
────────────────────────────────────────────────────────────────────────────
Ce script Python remplit une unique fonction : assembler un fichier HTML
autonome (dashboard.html) qui contient TOUT — données, styles, graphiques —
sans dépendance externe (sauf Chart.js si chart.min.js est absent).

Fonctionnement :
  1. Lecture des fichiers CSV source (données P&L, €/t, KPIs techniques)
  2. Sérialisation en JSON, encodée en ASCII pour éviter les problèmes d'encodage
  3. Injection dans un template HTML via des balises %%PLACEHOLDER%%
  4. Écriture du fichier dashboard.html final

Fichiers source nécessaires (dans le même dossier) :
  - data_synthese.csv         : données P&L brutes par site et année
  - data_synthese_eur_t.csv   : charges détaillées en €/t (format long)
  - data_kpi_techniques.csv   : KPIs techniques (dispo, débit, heures, etc.)
  - chart.min.js              : Chart.js 4.4.0 en local (optionnel, CDN sinon)
  - veolia.png                : logo affiché dans l'en-tête (optionnel)

Onglets du dashboard :
  - Accueil (home)    : KPIs agrégés parc, évolution CA/EBITDA, top/flop sites
  - Vue d'ensemble    : comparaison multi-sites, drill-down P&L
  - Détail site       : P&L complet, waterfall, benchmark, évolution
  - Vue €/t           : charges internes €/t empilées, scatter positionnement
  - Vue région        : agrégats par région/groupe de sites
  - Perfs & Charges   : corrélations KPIs techniques ↔ charges (Pearson r)
────────────────────────────────────────────────────────────────────────────
"""
import csv, json, os, base64
from datetime import datetime

# Dossier du script — sert de base pour trouver les fichiers CSV et assets
BASE = os.path.dirname(os.path.abspath(__file__))

# ── Chart.js : embarqué si chart.min.js est présent, CDN sinon ──────────────
# L'embarquer permet d'utiliser le dashboard sans connexion internet.
_chartjs_path = os.path.join(BASE, "chart.min.js")
if os.path.exists(_chartjs_path):
    with open(_chartjs_path, encoding="utf-8") as _f:
        CHARTJS = "<script>" + _f.read() + "</script>"
else:
    CHARTJS = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'

# Date de génération — affichée dans le pied de page du dashboard
GENERATED = datetime.now().strftime("%d/%m/%Y %H:%M")

# ── Logo Veolia : encodé en base64 pour être embarqué dans le HTML ───────────
# Si le fichier n'existe pas, la variable est vide (pas d'erreur).
_logo_path = os.path.join(BASE, "veolia.png")
LOGO_B64 = ("data:image/png;base64," + base64.b64encode(open(_logo_path,"rb").read()).decode()) if os.path.exists(_logo_path) else ""

# ── Lecture CSV ──────────────────────────────────────────────────────────────
def load_csv(filename):
    """
    Charge un fichier CSV et convertit automatiquement les valeurs numériques
    en float. Les cellules vides deviennent None. Les valeurs non-numériques
    restent des strings.
    Encodage UTF-8 avec BOM (utf-8-sig) pour compatibilité Excel Windows.
    """
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

# Chargement des trois sources de données
data       = load_csv("data_synthese.csv")       # P&L brut par site et année
data_eur_t = load_csv("data_synthese_eur_t.csv") # Charges détaillées en €/t (format long : une ligne par métrique)
data_kpi   = load_csv("data_kpi_techniques.csv") # KPIs techniques : dispo, débit, heures, nb trieurs, etc.
data_q1    = load_csv("data_q1_2026.csv")         # Comptes réels Q1 2026 : jan→mars, par site et métrique

# Sérialisation JSON avec ensure_ascii=True : évite les problèmes d'encodage
# des caractères accentués lors de l'injection dans le template HTML.
DATA_JSON  = json.dumps(data,       ensure_ascii=True)
EUR_T_JSON = json.dumps(data_eur_t, ensure_ascii=True)
KPI_JSON   = json.dumps(data_kpi,   ensure_ascii=True)
Q1_JSON    = json.dumps(data_q1,    ensure_ascii=True)

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
/* ── Perfs & Charges DG ──────────────────────────────── */
.section-sep{display:flex;align-items:center;gap:10px;margin:26px 0 12px;font-size:.92rem;font-weight:700;color:#003a63}
.section-sep::before{content:'';display:block;width:4px;height:22px;border-radius:2px;flex-shrink:0;background:#003a63}
.section-sep.orange::before{background:#f59e0b}
.section-sep.red::before{background:#ef4444}
.verdict-badge{font-size:.72rem;font-weight:600;padding:2px 10px;border-radius:12px;margin-left:8px;vertical-align:middle}
.tk-note{font-size:.78rem;color:#666;margin:0 0 14px;font-style:italic;line-height:1.5}
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
/* ── Q1 2026 ────────────────────────────────────────────── */
.q1-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.q1-period{font-size:.78rem;font-weight:600;color:#6b7280;background:#f3f4f6;padding:4px 12px;border-radius:20px}
.q1-sc-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:24px}
.q1-sc{background:#fff;border-radius:14px;padding:18px 20px 14px;box-shadow:0 2px 12px rgba(0,0,0,.07);border-top:5px solid #e5e7eb;position:relative;overflow:hidden}
.q1-sc::after{content:'';position:absolute;top:0;right:0;width:60px;height:60px;border-radius:0 14px 0 60px;opacity:.07}
.q1-sc.green{border-top-color:#10b981}.q1-sc.green::after{background:#10b981}
.q1-sc.red{border-top-color:#ef4444}.q1-sc.red::after{background:#ef4444}
.q1-sc.neutral{border-top-color:#94a3b8}
.q1-sc-label{font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#9ca3af;margin-bottom:10px}
.q1-sc-val{font-size:1.45rem;font-weight:800;color:#111827;line-height:1;margin-bottom:3px;white-space:nowrap}
.q1-sc-bud{font-size:.72rem;color:#b0b8c4;margin-bottom:10px}
.q1-sc-ecart{font-size:.82rem;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.q1-sc-ecart .e-amt{font-size:.88rem}
.q1-sc-ecart .e-pct{font-size:.72rem;background:rgba(0,0,0,.06);padding:1px 6px;border-radius:10px}
.q1-sc-ecart.pos{color:#10b981}.q1-sc-ecart.neg{color:#ef4444}
.q1-prog{height:5px;background:#f1f5f9;border-radius:3px;overflow:hidden}
.q1-prog-fill{height:100%;border-radius:3px;transition:width .6s cubic-bezier(.4,0,.2,1)}
.q1-prog-fill.green{background:linear-gradient(90deg,#34d399,#10b981)}
.q1-prog-fill.red{background:linear-gradient(90deg,#f87171,#ef4444)}
.q1-chart-card{background:#fff;border-radius:14px;padding:20px 24px;box-shadow:0 2px 12px rgba(0,0,0,.07);margin-bottom:22px}
.q1-chart-title{font-size:.85rem;font-weight:700;color:#003a63;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.q1-legend-dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.q1-site-bar{display:flex;align-items:center;gap:10px;margin-bottom:10px;font-size:.8rem}
.q1-site-bar-lbl{width:140px;font-weight:600;color:#374151;text-align:right;flex-shrink:0}
.q1-site-bar-track{flex:1;height:22px;background:#f1f5f9;border-radius:4px;position:relative;overflow:visible}
.q1-site-bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding:0 8px;font-size:.72rem;font-weight:700;color:#fff;min-width:30px;white-space:nowrap;transition:width .5s ease}
.q1-site-bar-val{margin-left:8px;font-size:.75rem;font-weight:700;white-space:nowrap}
.q1-sel-row{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.q1-sel-lbl{font-size:.82rem;font-weight:700;color:#003a63}
/* ── Accordion P&L ── */
.q1-acc-item{border-bottom:1px solid #f1f5f9}
.q1-acc-item:last-child{border-bottom:none}
.q1-acc-hdr{display:flex;align-items:center;gap:16px;padding:13px 10px;cursor:pointer;user-select:none;border-radius:8px;transition:background .15s}
.q1-acc-hdr:hover{background:#f8fafc}
.q1-acc-met{font-size:.85rem;font-weight:800;color:#003a63;width:110px;flex-shrink:0}
.q1-acc-r26{font-size:.92rem;font-weight:700;color:#111827;width:90px}
.q1-acc-bud{font-size:.73rem;color:#9ca3af;width:110px}
.q1-acc-bar{flex:1;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden}
.q1-acc-bar-fill{height:100%;border-radius:4px;transition:width .5s ease}
.q1-acc-ecart{font-size:.82rem;font-weight:700;width:140px;text-align:right;flex-shrink:0}
.q1-acc-ecart.pos{color:#10b981}.q1-acc-ecart.neg{color:#ef4444}
.q1-acc-chev{font-size:.65rem;color:#9ca3af;transition:transform .22s;flex-shrink:0;width:14px;text-align:center}
.q1-acc-chev.open{transform:rotate(180deg)}
.q1-acc-body{display:none;padding:10px 0 18px 120px}
.q1-acc-body.open{display:block}
/* ── Bullet chart (vue par site) ── */
.q1-section-lbl{font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin:20px 0 10px;padding-left:4px}
.q1-bl-row{display:flex;align-items:center;gap:12px;margin-bottom:9px}
.q1-bl-lbl{font-size:.79rem;font-weight:700;color:#374151;width:130px;text-align:right;flex-shrink:0}
.q1-bl-wrap{flex:1;position:relative;height:28px}
.q1-bl-bud{position:absolute;top:2px;left:0;height:24px;background:#e9eef5;border-radius:5px}
.q1-bl-real{position:absolute;top:6px;left:0;height:16px;border-radius:4px;display:flex;align-items:center;padding:0 7px;font-size:.68rem;font-weight:700;color:#fff;white-space:nowrap;min-width:4px;transition:width .5s ease;z-index:1}
.q1-bl-mark{position:absolute;top:0;width:2px;height:28px;background:#94a3b8;border-radius:1px;z-index:2}
.q1-bl-valcol{font-size:.74rem;font-weight:700;width:82px;flex-shrink:0;white-space:nowrap;color:#111827}
.q1-bl-ecart{font-size:.71rem;font-weight:700;width:88px;flex-shrink:0;text-align:right;white-space:nowrap}
.q1-bl-ecart.pos{color:#10b981}.q1-bl-ecart.neg{color:#ef4444}
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
  <div class="tab"         onclick="showTab('tk',this)">Perfs &rarr; Charges</div>
  <div class="tab"         onclick="showTab('q1',this)">Suivi Q1 2026</div>
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
    <div class="card full">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px">
        <div class="card-title" id="charges-et-title" style="margin:0">Charges internes &euro;/t par site</div>
        <div style="display:flex;gap:5px;flex-wrap:wrap" id="charge-filter-pills">
          <button class="btn-pill charge-fil active" onclick="toggleChargeFil(&#39;all&#39;,this)" style="font-size:.75rem;padding:3px 12px">Toutes</button>
          <button class="btn-pill charge-fil" onclick="toggleChargeFil(&#39;Personnel&#39;,this)" style="font-size:.75rem;padding:3px 12px">Personnel</button>
          <button class="btn-pill charge-fil" onclick="toggleChargeFil(&#39;\u00c9nergie&#39;,this)" style="font-size:.75rem;padding:3px 12px">&Eacute;nergie</button>
          <button class="btn-pill charge-fil" onclick="toggleChargeFil(&#39;Maint. courante&#39;,this)" style="font-size:.75rem;padding:3px 12px">Maint. courante</button>
          <button class="btn-pill charge-fil" onclick="toggleChargeFil(&#39;Maint. oblig.&#39;,this)" style="font-size:.75rem;padding:3px 12px">Maint. oblig.</button>
          <button class="btn-pill charge-fil" onclick="toggleChargeFil(&#39;Traitement s.-p.&#39;,this)" style="font-size:.75rem;padding:3px 12px">Traitement s.-p.</button>
          <button class="btn-pill charge-fil" onclick="toggleChargeFil(&#39;Autres co\u00fbts&#39;,this)" style="font-size:.75rem;padding:3px 12px">Autres co&ucirc;ts</button>
        </div>
      </div>
      <div class="ch tall"><canvas id="c-charges-et"></canvas></div>
    </div>
  </div>
  <div class="row2">
    <div class="card full">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:4px">
        <div class="card-title" id="scatter-card-title" style="margin:0">Matrice de positionnement : Tonnes vs EBITDA &euro;/t</div>
        <div style="display:flex;gap:6px">
          <button class="btn-pill scatter-metric-btn active" onclick="setScatterMetric(\'ebitda\',this)">EBITDA &euro;/t</button>
          <button class="btn-pill scatter-metric-btn" onclick="setScatterMetric(\'ca\',this)">CA &euro;/t</button>
          <button class="btn-pill scatter-metric-btn" onclick="setScatterMetric(\'charges\',this)">Charges &euro;/t</button>
        </div>
      </div>
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
    <label style="margin-left:14px">Vue :</label>
    <button class="btn-pill rg-ca-type active" onclick="setRgCAType('bar',this)">Barres</button>
    <button class="btn-pill rg-ca-type" id="rg-btn-line" onclick="setRgCAType('line',this)">Ligne</button>
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

<!-- ═══ ONGLET — PERFS → CHARGES ════════════════════════════════ -->
<div class="page" id="tab-tk">
  <div class="toolbar">
    <label>Ann&eacute;e :</label>
    <button class="btn-pill tk-sc-yr active" onclick="tkScSetYr('all',this)">Toutes (moy.)</button>
    <button class="btn-pill tk-sc-yr" id="tk-btn-2023" onclick="tkScSetYr(2023,this)">R2023</button>
    <button class="btn-pill tk-sc-yr" onclick="tkScSetYr(2024,this)">R2024</button>
    <button class="btn-pill tk-sc-yr" onclick="tkScSetYr(2025,this)">R2025</button>
    <div class="spacer"></div>
    <button class="btn-print" onclick="window.print()" style="margin-left:12px">&#128438; Exporter PDF</button>
  </div>

  <!-- SECTION A — Corrélations parc -->
  <div class="section-sep orange" style="margin-top:18px">Corr&eacute;lations parc &mdash; influence des perfs techniques sur les charges &euro;/t</div>
  <p class="tk-note">Chaque point = un site. Choisissez l&rsquo;indicateur et l&rsquo;ann&eacute;e pour explorer les corr&eacute;lations.</p>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap">
    <span style="font-size:.78rem;font-weight:700;color:#555">KPI :</span>
    <button class="btn-pill tk-kpi active" onclick="tkSetKpi('debit',this)">D&eacute;bit (t/h)</button>
    <button class="btn-pill tk-kpi" onclick="tkSetKpi('dispo',this)">Disponibilit&eacute; globale (%)</button>
    <button class="btn-pill tk-kpi" onclick="tkSetKpi('dispo_process',this)">Disponibilit&eacute; process (%)</button>
    <button class="btn-pill tk-kpi" onclick="tkSetKpi('heures',this)">Heures fonct.</button>
    <button class="btn-pill tk-kpi" onclick="tkSetKpi('productivite',this)">Productivit&eacute; (t/h/op.)</button>
  </div>
  <div id="tk-dispo-proc-note" style="display:none;font-size:.75rem;color:#f59e0b;font-weight:600;margin-bottom:10px;padding:5px 12px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;width:fit-content">
    &#9888; Dispo process : donn&eacute;es 2023 indisponibles &mdash; R2023 exclu du scatter
  </div>
  <div class="row2" style="margin-bottom:28px">
    <div class="card" style="border-top:3px solid #f59e0b">
      <div class="card-title">Personnel &euro;/t &larr; <span id="tk-kpi-lbl-pers">D&eacute;bit (t/h)</span> <span id="tk-verdict-pers" class="verdict-badge"></span></div>
      <div style="position:relative;height:400px"><canvas id="tk-sc-pers"></canvas></div>
    </div>
    <div class="card" style="border-top:3px solid #ef4444">
      <div class="card-title">Maintenance &euro;/t &larr; <span id="tk-kpi-lbl-maint">D&eacute;bit (t/h)</span> <span id="tk-verdict-maint" class="verdict-badge"></span></div>
      <div style="position:relative;height:400px"><canvas id="tk-sc-maint"></canvas></div>
    </div>
  </div>

  <!-- SECTION B — Vue par site -->
  <div class="section-sep">Analyse par site &mdash; &eacute;volution 2023&nbsp;&rarr;&nbsp;2025</div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap">
    <label style="font-size:.82rem;color:#555;font-weight:600">Site :</label>
    <select class="sel" id="tk-site-sel" onchange="tkSetSite(this.value)" style="font-size:.8rem;padding:4px 10px"></select>
  </div>

  <!-- 5 KPI cards site avec tendances -->
  <div class="kpi-grid" style="margin-bottom:22px;grid-template-columns:repeat(6,1fr);gap:10px">
    <div class="kpi-card" style="border-left-color:#00a3e0">
      <div class="kpi-label">Dispo globale</div>
      <div class="kpi-value" id="tk-sk-dispo">—</div>
      <div class="kpi-sub" id="tk-sk-dispo-s">R2025</div>
      <div class="kpi-trend" id="tk-sk-dispo-t"></div>
    </div>
    <div class="kpi-card" style="border-left-color:#0ea5e9">
      <div class="kpi-label">Dispo process</div>
      <div class="kpi-value" id="tk-sk-dispo-proc">—</div>
      <div class="kpi-sub" id="tk-sk-dispo-proc-s">R2025</div>
      <div class="kpi-trend" id="tk-sk-dispo-proc-t"></div>
    </div>
    <div class="kpi-card g">
      <div class="kpi-label">D&eacute;bit</div>
      <div class="kpi-value" id="tk-sk-debit">—</div>
      <div class="kpi-sub" id="tk-sk-debit-s">t/h · R2025</div>
      <div class="kpi-trend" id="tk-sk-debit-t"></div>
    </div>
    <div class="kpi-card" style="border-left-color:#8b5cf6">
      <div class="kpi-label">Taux de refus</div>
      <div class="kpi-value" id="tk-sk-refus">—</div>
      <div class="kpi-sub" id="tk-sk-refus-s">% · R2025</div>
      <div class="kpi-trend" id="tk-sk-refus-t"></div>
    </div>
    <div class="kpi-card o">
      <div class="kpi-label">Personnel &euro;/t</div>
      <div class="kpi-value" id="tk-sk-pers">—</div>
      <div class="kpi-sub" id="tk-sk-pers-s">&euro;/t · R2025</div>
      <div class="kpi-trend" id="tk-sk-pers-t"></div>
    </div>
    <div class="kpi-card r">
      <div class="kpi-label">Maintenance &euro;/t</div>
      <div class="kpi-value" id="tk-sk-maint">—</div>
      <div class="kpi-sub" id="tk-sk-maint-s">&euro;/t · R2025</div>
      <div class="kpi-trend" id="tk-sk-maint-t"></div>
    </div>
  </div>

  <!-- CA + contexte -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap">
    <span style="font-size:.82rem;font-weight:700;color:#003a63">CA &amp; contexte :</span>
    <button class="btn-pill tk-cax active" onclick="tkSetCaX('tonnage',this)" style="font-size:.78rem;padding:4px 14px">Tonnage entrant</button>
    <button class="btn-pill tk-cax" onclick="tkSetCaX('refus',this)" style="font-size:.78rem;padding:4px 14px">Taux de refus</button>
  </div>
  <div class="card full" style="margin-bottom:4px">
    <div style="position:relative;height:280px"><canvas id="tk-ca-chart"></canvas></div>
  </div>

  <!-- Charges + KPI overlay -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap">
    <span style="font-size:.78rem;font-weight:700;color:#555">Afficher en courbe :</span>
    <button class="btn-pill tk-kline" data-col="#0082b3" onclick="tkToggleKpiLine('debit',this)" style="border-color:#0082b3;color:#0082b3">D&eacute;bit</button>
    <button class="btn-pill tk-kline" data-col="#059669" onclick="tkToggleKpiLine('dispo',this)" style="border-color:#059669;color:#059669">Dispo globale</button>
    <button class="btn-pill tk-kline" data-col="#0ea5e9" onclick="tkToggleKpiLine('dispo_process',this)" style="border-color:#0ea5e9;color:#0ea5e9">Dispo process</button>
    <button class="btn-pill tk-kline" data-col="#ef4444" onclick="tkToggleKpiLine('refus',this)" style="border-color:#ef4444;color:#ef4444">Taux de refus</button>
    <button class="btn-pill tk-kline" data-col="#8b5cf6" onclick="tkToggleKpiLine('heures',this)" style="border-color:#8b5cf6;color:#8b5cf6">Heures fonct.</button>
    <button class="btn-pill tk-kline" data-col="#6366f1" onclick="tkToggleKpiLine('tonnage',this)" style="border-color:#6366f1;color:#6366f1">Tonnage entrant</button>
  </div>
  <div class="row2" style="margin-bottom:26px">
    <div class="card" style="border-top:3px solid #f59e0b">
      <div class="card-title">Co&ucirc;ts de Personnel &euro;/t</div>
      <div style="position:relative;height:320px"><canvas id="tk-pers-chart"></canvas></div>
    </div>
    <div class="card" style="border-top:3px solid #ef4444">
      <div class="card-title">Co&ucirc;ts de Maintenance &euro;/t</div>
      <div style="position:relative;height:320px"><canvas id="tk-maint-chart"></canvas></div>
    </div>
  </div>

  <!-- SECTION B.5 — Synthèse corrélations -->
  <div class="section-sep" style="margin-top:18px">Synth&egrave;se des corr&eacute;lations &mdash; KPI le plus influent par site</div>
  <p class="tk-note">Coefficient de Pearson calcul&eacute; sur 3 ans (2023&ndash;2025). Indique la force et le sens du lien entre chaque KPI et la charge &euro;/t &mdash; &agrave; lire comme une tendance, non une causalit&eacute;.
    &nbsp;<strong>|r|&nbsp;&ge;&nbsp;0,7</strong> = lien fort &nbsp;&middot;&nbsp; <strong>0,4&nbsp;&ndash;&nbsp;0,7</strong> = mod&eacute;r&eacute; &nbsp;&middot;&nbsp; <strong>&lt;&nbsp;0,4</strong> = faible.</p>
  <details style="margin-bottom:14px;font-size:.78rem;color:#555;cursor:pointer">
    <summary style="font-weight:600;color:#003a63;list-style:none;display:flex;align-items:center;gap:6px">
      <span style="font-size:.7rem;border:1px solid #003a63;border-radius:50%;width:16px;height:16px;display:inline-flex;align-items:center;justify-content:center">?</span>
      Comment est calcul&eacute; le r ?
    </summary>
    <div style="margin-top:8px;padding:12px 14px;background:#f8fafc;border-radius:8px;line-height:1.8">
      <strong>Formule :</strong> r = &Sigma;(x<sub>i</sub>&minus;x&#773;)(y<sub>i</sub>&minus;y&#773;) &nbsp;/&nbsp; &radic;[&Sigma;(x<sub>i</sub>&minus;x&#773;)&sup2; &times; &Sigma;(y<sub>i</sub>&minus;y&#773;)&sup2;]<br>
      <strong>Exemple &mdash; Dispo (x) vs Personnel &euro;/t (y) sur un site :</strong><br>
      &nbsp;&nbsp;2023 : x&nbsp;=&nbsp;89,2&nbsp;% &nbsp; y&nbsp;=&nbsp;87,8&nbsp;&euro;/t<br>
      &nbsp;&nbsp;2024 : x&nbsp;=&nbsp;88,1&nbsp;% &nbsp; y&nbsp;=&nbsp;99,3&nbsp;&euro;/t<br>
      &nbsp;&nbsp;2025 : x&nbsp;=&nbsp;86,9&nbsp;% &nbsp; y&nbsp;=&nbsp;100,8&nbsp;&euro;/t<br>
      &nbsp;&nbsp;x&#773;&nbsp;=&nbsp;88,1 &nbsp;&middot;&nbsp; y&#773;&nbsp;=&nbsp;96,0 &nbsp;&middot;&nbsp; &Sigma;(x<sub>i</sub>&minus;x&#773;)(y<sub>i</sub>&minus;y&#773;)&nbsp;=&nbsp;&minus;14,8<br>
      &nbsp;&nbsp;r&nbsp;=&nbsp;&minus;14,8&nbsp;/&nbsp;&radic;(2,65&nbsp;&times;&nbsp;101,3)&nbsp;=&nbsp;<strong>&minus;0,90</strong> &nbsp;&rarr;&nbsp; quand la dispo baisse, le co&ucirc;t de personnel monte.
    </div>
  </details>
  <div id="tk-corr-summary" style="margin-bottom:28px"></div>

  <!-- SECTION C — Tableau récap -->
  <div class="section-sep">Synth&egrave;se &mdash; tous les sites</div>
  <div class="card full" style="margin-bottom:18px">
    <div id="tk-table-wrap"></div>
  </div>
</div>

<!-- ═══ ONGLET Q1 2026 ══════════════════════════════════════════════════════ -->
<div class="page" id="tab-q1">

  <!-- ── En-tête ── -->
  <div class="q1-header" style="margin-top:4px">
    <div>
      <div style="font-size:1.05rem;font-weight:800;color:#003a63;margin-bottom:2px">Suivi T1 2026 &mdash; R&eacute;el vs Budget</div>
      <div class="q1-period">Cumul jan &rarr; mars 2026</div>
    </div>
    <button class="btn-print" onclick="window.print()">&#128438; Exporter PDF</button>
  </div>

  <!-- ── A — Vue globale parc ── -->
  <div class="section-sep" style="margin-top:22px">Vue globale parc &mdash; 11 sites</div>

  <!-- Scorecards 5 métriques -->
  <div class="q1-sc-grid" id="q1-global-cards"></div>

  <!-- Accordion P&L par composante -->
  <div class="q1-chart-card">
    <div class="q1-chart-title">
      Composantes P&amp;L &mdash; cliquer pour voir le d&eacute;tail par site
      <span style="font-size:.7rem;font-weight:400;color:#9ca3af;margin-left:6px">&#9660; vert = au-dessus du budget</span>
    </div>
    <div id="q1-accordion"></div>
  </div>

  <!-- ── B — Vue par site ── -->
  <div class="section-sep">D&eacute;tail par site</div>
  <div class="q1-sel-row">
    <span class="q1-sel-lbl">Site :</span>
    <select class="sel" id="q1-site-sel" onchange="q1SetSite(this.value)"></select>
  </div>

  <!-- Scorecards site -->
  <div class="q1-sc-grid" id="q1-site-cards"></div>

  <!-- Barres site — synthèse financière -->
  <div class="q1-chart-card">
    <div class="q1-chart-title" id="q1-site-fin-title">&mdash;</div>
    <div id="q1-site-fin-rows"></div>
  </div>
  <!-- Barres site — charges -->
  <div class="q1-chart-card" style="margin-bottom:32px">
    <div class="q1-chart-title" id="q1-site-chg-title">&mdash;</div>
    <div id="q1-site-chg-rows"></div>
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
// ── Fonctions de formatage des nombres ──────────────────────────────────────
// Toutes renvoient '—' si la valeur est null/undefined.
const fmt  = n => n==null?'—':new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0}).format(n); // entier séparateur milliers
const fmtM = n => n==null?'—':(n/1e6).toFixed(2).replace('.',',')+' M\u20ac';                    // millions €
const fmtK = n => n==null?'—':(n/1e3).toFixed(1).replace('.',',')+' kt';                          // kilo-tonnes
const fmtE = n => n==null?'—':fmt(n)+' \u20ac';                                                   // valeur en €
const fmtT = n => (n==null||n==='')?'—':Number(n).toFixed(1)+' \u20ac/t';                         // coût unitaire €/t

// ── Palettes de couleurs ─────────────────────────────────────────────────────
const COLORS=['#0f3460','#533483','#e94560','#16c79a','#f4a261','#2196f3','#ff9f1c','#118ab2','#e63946','#2a9d8f','#e9c46a'];
const C3 = (i)=>[COLORS[0],COLORS[2],COLORS[3],'#f59e0b'][i%4]; // rotation 4 couleurs pour barres multi-années

// ── Constantes globales issues des données ───────────────────────────────────
const SITES = [...new Set(DATA.map(d=>d.Site))];           // liste des sites dédupliqués
const YEARS = ['2023','2024','2025','2026'];                // toutes années (2026 = budget)
const REAL_YEARS = ['2023','2024','2025'];                  // réalisés uniquement
const yr2lbl = yr => (yr==='2026'||yr==='B2026')?'B2026':yr.startsWith('R')?yr:'R'+yr; // normalise le label : '2024' → 'R2024'


// ══════════════════════════════════════════════════════
// TABS
// ══════════════════════════════════════════════════════

// ── Heatmap standalone (sites=lignes, métriques=colonnes) ──
// ── mkChart(id, config) ──────────────────────────────────────────────────────
// Helper central pour créer un graphique Chart.js.
// Détruit toujours le graphique précédent sur le même canvas avant d'en créer
// un nouveau — évite l'erreur "Canvas is already in use".
// Utilisé par TOUS les onglets du dashboard.
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
    if(id==='tk') renderTk();
    if(id==='q1') renderQ1();
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
// ONGLET ACCUEIL — renderHome()
// Affiche les KPIs agrégés parc (CA, EBITDA, tonnes) pour R2025 vs R2024,
// le graphique d'évolution CA/EBITDA, et le classement top/flop sites.
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

// ══════════════════════════════════════════════════════
// ONGLET VUE D'ENSEMBLE — renderOv()
// Graphiques comparatifs multi-sites : CA, EBITDA, taux EBITDA, tonnes.
// Filtres : années (multi-sélection) + sites (multi-sélection).
// Appelle aussi renderExecSummary() pour le résumé KPIs en haut de page.
// ══════════════════════════════════════════════════════
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

// ══════════════════════════════════════════════════════
// ONGLET DÉTAIL SITE — renderDt()
// Affiche le P&L complet d'un site sélectionné : évolution CA/EBITDA,
// waterfall des charges, benchmark vs parc, comparaison avec un 2e site.
// Sous-fonctions : renderCompare, renderSiteExec, renderBench,
//                 renderEvol, renderDonut, renderWaterfall, renderPL
// ══════════════════════════════════════════════════════
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
// ONGLET VUE €/T — renderEt()
// Visualise les charges internes en €/t par site.
// Graphiques : CA €/t, EBITDA €/t, charges empilées par poste,
//              scatter positionnement (tonnes vs EBITDA/CA/charges),
//              tableau heatmap €/t toutes métriques.
//
// Filtres disponibles :
//   - Année (multi-sélection) : R2023, R2024, R2025
//   - Sites (multi-sélection)
//   - Charges (multi-sélection sur le graphe empilé) :
//       · "Toutes" → empilées triées par EBITDA
//       · 1 charge sélectionnée → barres simples (benchmark direct)
//       · 2+ charges → empilées (sous-ensemble)
//
// Source données : data_synthese_eur_t.csv (format long, une ligne par métrique)
// Accès via getVal(site, année, métrique) qui cherche dans EURT[]
// ══════════════════════════════════════════════════════
let etYears=new Set(['all']), etSites=new Set(['all']), cEtEB=null, cEtCA=null, cScatter=null, cChargesEt=null;
let etScatterMetric='ebitda'; // métrique axe Y du scatter : 'ebitda' | 'ca' | 'charges'
let etChargeFilter=new Set(['all']); // charges sélectionnées dans le filtre du graphe empilé

function toggleChargeFil(label, btn){
  var allBtn=document.querySelector('.charge-fil');
  if(label==='all'){
    etChargeFilter=new Set(['all']);
    document.querySelectorAll('.charge-fil').forEach(function(b){b.classList.remove('active');});
    allBtn.classList.add('active');
  } else {
    etChargeFilter.delete('all'); allBtn.classList.remove('active');
    if(etChargeFilter.has(label)){ etChargeFilter.delete(label); btn.classList.remove('active'); }
    else { etChargeFilter.add(label); btn.classList.add('active'); }
    if(etChargeFilter.size===0){ etChargeFilter=new Set(['all']); allBtn.classList.add('active'); }
  }
  renderEt();
}
function setScatterMetric(m,btn){
  etScatterMetric=m;
  document.querySelectorAll('.scatter-metric-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderEt();
}

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
  const chTitle=document.getElementById('charges-et-title');
  if(chTitle) chTitle.innerHTML='Charges internes \u20ac/t par site \u2014 tri\u00e9es par EBITDA \u20ac/t<span style="font-size:11px;font-weight:400;color:#999;margin-left:8px">'+chargeYear+'</span>';
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
  // Filtre charges sélectionnées
  var isAllCharges=etChargeFilter.has('all');
  var filteredChargeMetrics=isAllCharges?chargeMetrics:chargeMetrics.filter(function(cm){return etChargeFilter.has(cm.l);});
  var isStacked=isAllCharges||filteredChargeMetrics.length>1; // empilé si tout ou multi-sélection, groupé si 1 seule charge
  var chargeDs=filteredChargeMetrics.map(function(cm){
    return {
      label:cm.l,
      data:chargeSites.map(function(s){ var v=getVal(s,chargeYear,cm.m); return v!==null?Math.abs(v):0; }),
      backgroundColor:cm.color+'cc',
      borderColor:cm.color,
      borderWidth:isStacked?1:2,
      borderRadius:isStacked?2:4,
    };
  });
  var chTitleEl=document.getElementById('charges-et-title');
  if(chTitleEl){
    var chMode=isAllCharges?'tri\u00e9es par EBITDA \u20ac/t':'benchmark';
    chTitleEl.innerHTML='Charges internes \u20ac/t par site \u2014 '+chMode+'<span style="font-size:11px;font-weight:400;color:#999;margin-left:8px">'+chargeYear+'</span>';
  }
  cChargesEt=mkChart('c-charges-et',{
    type:'bar',
    data:{labels:chargeSites,datasets:chargeDs},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'top',labels:{font:{size:10},usePointStyle:true}},
        tooltip:{callbacks:{label:function(c){return ' '+c.dataset.label+': '+(c.parsed.y||0).toFixed(1)+' \u20ac/t';}}}},
      scales:{
        x:{stacked:isStacked,grid:{display:false}},
        y:{stacked:isStacked,title:{display:true,text:'\u20ac/t'},grid:{color:'#f0f0f0'}}
      }
    }
  });

  // Scatter quadrant — métrique sélectionnable
  const scatterYear=chargeYear.replace('R','');

  // Calcul de la valeur Y selon la métrique sélectionnée
  const getScatterY=(s)=>{
    const row=DATA.find(d=>d.Site===s&&String(d.Annee)===scatterYear);
    if(!row) return null;
    if(etScatterMetric==='ebitda'){
      return getVal(s,'R'+scatterYear,'EBITDA');
    } else if(etScatterMetric==='ca'){
      const tn=row.Tonnes_entrantes;
      return tn>0?row.CA/tn:null;
    } else { // charges
      const tn=row.Tonnes_entrantes;
      return tn>0?(row.PNE-row.Marge_Brute_Cash)/tn:null;
    }
  };

  const allPts=SITES.map(s=>{
    const row=DATA.find(d=>d.Site===s&&String(d.Annee)===scatterYear);
    const yv=getScatterY(s);
    if(!row||yv===null) return null;
    return {x:row.Tonnes_entrantes,y:yv,label:s};
  }).filter(Boolean);

  // Seuils : moyenne pondérée du parc pour X et Y
  const totalTn=allPts.reduce((s,p)=>s+p.x,0);
  const THRESH_TN=totalTn/allPts.length; // moyenne tonnes par site
  let THRESH_Y;
  if(etScatterMetric==='ebitda'){
    THRESH_Y=0; // seuil naturel rentabilité
  } else {
    // moyenne pondérée (total valeur / total tonnes)
    const totalCA_=allPts.reduce((s,p)=>{const r=DATA.find(d=>d.Site===p.label&&String(d.Annee)===scatterYear);return s+(r?r.CA:0);},0);
    const totalPNE_=allPts.reduce((s,p)=>{const r=DATA.find(d=>d.Site===p.label&&String(d.Annee)===scatterYear);return s+(r?r.PNE:0);},0);
    const totalMBC_=allPts.reduce((s,p)=>{const r=DATA.find(d=>d.Site===p.label&&String(d.Annee)===scatterYear);return s+(r?r.Marge_Brute_Cash:0);},0);
    if(etScatterMetric==='ca'){
      THRESH_Y=totalCA_/totalTn;
    } else {
      THRESH_Y=(totalPNE_-totalMBC_)/totalTn;
    }
  }

  // Config quadrants selon métrique
  const SCATTER_CFG={
    ebitda:{
      title:'Matrice de positionnement : Tonnes vs EBITDA \u20ac/t',
      yLabel:'EBITDA \u20ac/t',
      highGood:true,
      cats:[
        {key:'champ',label:'Grands & Rentables',    color:'#10b981'},
        {key:'effic',label:'Petits & Rentables',     color:'#2196f3'},
        {key:'devel',label:'Grands \u00e0 optimiser',color:'#f59e0b'},
        {key:'diff', label:'Petits \u00e0 relancer', color:'#ef4444'},
      ]
    },
    ca:{
      title:'Matrice de positionnement : Tonnes vs CA \u20ac/t',
      yLabel:'CA \u20ac/t',
      highGood:true,
      cats:[
        {key:'champ',label:'Gros volume, bonne r\u00e9mun\u00e9ration', color:'#10b981'},
        {key:'effic',label:'Petit volume, bonne r\u00e9mun\u00e9ration', color:'#2196f3'},
        {key:'devel',label:'Gros volume, faible r\u00e9mun\u00e9ration', color:'#f59e0b'},
        {key:'diff', label:'Petit volume, faible r\u00e9mun\u00e9ration', color:'#ef4444'},
      ]
    },
    charges:{
      title:'Matrice de positionnement : Tonnes vs Charges internes \u20ac/t',
      yLabel:'Charges internes \u20ac/t',
      highGood:false, // charges élevées = mauvais
      cats:[
        {key:'champ',label:'Gros volume, charges ma\u00eetris\u00e9es', color:'#10b981'},
        {key:'effic',label:'Petit volume, charges ma\u00eetris\u00e9es', color:'#2196f3'},
        {key:'devel',label:'Gros volume, charges \u00e9lev\u00e9es',    color:'#f59e0b'},
        {key:'diff', label:'Petit volume, charges \u00e9lev\u00e9es',   color:'#ef4444'},
      ]
    }
  };
  const cfg=SCATTER_CFG[etScatterMetric];
  const highGood=cfg.highGood;

  // filtres quadrants : haut/bas selon highGood
  const isGoodY=(y)=>highGood?y>THRESH_Y:y<=THRESH_Y;
  const isBadY =(y)=>highGood?y<=THRESH_Y:y>THRESH_Y;

  const CATS=cfg.cats.map((c,i)=>{
    const bigX=(i===0||i===2); // 0=GrandBon, 1=PetitBon, 2=GrandMauvais, 3=PetitMauvais
    const goodY=(i===0||i===1);
    return {...c,
      filt:goodY
        ?(p=>(isGoodY(p.y))&&(bigX?p.x>=THRESH_TN:p.x<THRESH_TN))
        :(p=>(isBadY(p.y))&&(bigX?p.x>=THRESH_TN:p.x<THRESH_TN))
    };
  });

  // Mise à jour titre carte avec année
  const scTitle=document.getElementById('scatter-card-title');
  if(scTitle) scTitle.innerHTML=cfg.title+'<span style="font-size:11px;font-weight:400;color:#999;margin-left:8px">'+chargeYear+'</span>';

  // Seuil affiché dans le titre Y
  const threshLabel=etScatterMetric==='ebitda'?'0 \u20ac/t (seuil rentabilit\u00e9)':
    'moy. parc : '+THRESH_Y.toFixed(0)+' \u20ac/t';

  // Plugin quadrants
  const quadrantPlugin={
    id:'quadrants',
    beforeDraw:function(chart){
      const {ctx,chartArea:{left,right,top,bottom},scales:{x,y}}=chart;
      const xM=x.getPixelForValue(THRESH_TN);
      const yM=y.getPixelForValue(THRESH_Y);
      ctx.save();
      // Quadrant colors: [haut-droit, haut-gauche, bas-droit, bas-gauche]
      // Si highGood : haut=bon → vert/bleu ; bas=mauvais → orange/rouge
      // Si !highGood (charges) : bas=bon → vert/bleu ; haut=mauvais → orange/rouge
      const topR=highGood?'rgba(16,185,129,.07)':'rgba(245,158,11,.07)';
      const topL=highGood?'rgba(33,150,243,.07)':'rgba(239,68,68,.07)';
      const botR=highGood?'rgba(245,158,11,.07)':'rgba(16,185,129,.07)';
      const botL=highGood?'rgba(239,68,68,.07)':'rgba(33,150,243,.07)';
      const quads=[
        {x1:xM,  y1:top, x2:right, y2:yM,     color:topR},
        {x1:left,y1:top, x2:xM,   y2:yM,      color:topL},
        {x1:xM,  y1:yM,  x2:right, y2:bottom,  color:botR},
        {x1:left,y1:yM,  x2:xM,   y2:bottom,   color:botL},
      ];
      quads.forEach(function(q){ctx.fillStyle=q.color;ctx.fillRect(q.x1,q.y1,q.x2-q.x1,q.y2-q.y1);});
      ctx.strokeStyle='rgba(100,116,139,.35)';ctx.lineWidth=1.5;ctx.setLineDash([6,4]);
      ctx.beginPath();ctx.moveTo(xM,top);ctx.lineTo(xM,bottom);ctx.stroke();
      ctx.beginPath();ctx.moveTo(left,yM);ctx.lineTo(right,yM);ctx.stroke();
      ctx.setLineDash([]);ctx.font='700 11px system-ui,sans-serif';
      // Labels dans les coins — ordre selon highGood
      // highGood : top=bon  → [0=gros-bon, 1=petit-bon, 2=gros-bad, 3=petit-bad]
      // !highGood : top=bad → coins [top-right=gros-bad=2, top-left=petit-bad=3, bot-right=gros-bon=0, bot-left=petit-bon=1]
      const co=highGood?[0,1,2,3]:[2,3,0,1];
      const corners=co.map(i=>({text:CATS[i].label,color:CATS[i].color}));
      ctx.textBaseline='top';
      ctx.fillStyle=corners[0].color+'cc';ctx.textAlign='right';ctx.fillText(corners[0].text,right-8,top+8);
      ctx.fillStyle=corners[1].color+'cc';ctx.textAlign='left'; ctx.fillText(corners[1].text,left+8,top+8);
      ctx.textBaseline='bottom';
      ctx.fillStyle=corners[2].color+'cc';ctx.textAlign='right';ctx.fillText(corners[2].text,right-8,bottom-8);
      ctx.fillStyle=corners[3].color+'cc';ctx.textAlign='left'; ctx.fillText(corners[3].text,left+8,bottom-8);
      // Seuil X annotation
      ctx.textBaseline='top';ctx.textAlign='center';ctx.font='500 10px system-ui,sans-serif';
      ctx.fillStyle='rgba(100,116,139,.6)';
      ctx.fillText('moy. '+Math.round(THRESH_TN/1000)+'kt',xM,top+2);
      ctx.restore();
    }
  };

  cScatter=mkChart('c-scatter',{
    type:'scatter',
    data:{datasets:CATS.map(c=>({
      label:c.label,
      data:allPts.filter(c.filt),
      backgroundColor:c.color+'bb',borderColor:c.color,borderWidth:2,
      pointRadius:11,pointHoverRadius:14,
    }))},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'top',labels:{usePointStyle:true,font:{size:11}}},
        tooltip:{callbacks:{label:function(c){
          if(!c.raw.label) return null;
          return ' '+c.raw.label+' \u2014 '+fmt(c.raw.x)+' t / '+c.raw.y.toFixed(1)+' \u20ac/t';
        }}}
      },
      scales:{
        x:{title:{display:true,text:'Tonnes entrantes'},grid:{color:'#f0f0f0'}},
        y:{title:{display:true,text:cfg.yLabel+' ('+threshLabel+')'},grid:{color:'#f0f0f0'}}
      }
    },
    plugins:[quadrantPlugin]
  });

  // Category table
  const metricColLabel=cfg.yLabel;
  let hc='<div class="cat-legend">';
  CATS.forEach(c=>{const n=allPts.filter(c.filt).length;if(n) hc+='<div class="cat-badge '+c.key+'"><div class="cat-dot" style="background:'+c.color+'"></div>'+c.label+' ('+n+')</div>';});
  hc+='</div><table class="rank-table" style="margin-top:8px"><thead><tr><th>Cat\u00e9gorie</th><th>Site</th><th>Tonnes</th><th>'+metricColLabel+'</th></tr></thead><tbody>';
  CATS.forEach(c=>{
    allPts.filter(c.filt).sort((a,b)=>highGood?(b.y-a.y):(a.y-b.y)).forEach((p,i)=>{
      const good=isGoodY(p.y);
      hc+='<tr><td style="color:'+c.color+';font-weight:700">'+(i===0?c.label:'')+'</td><td><span class="site-link" data-site="'+p.label+'" onclick="goToSite(this.dataset.site)">'+p.label+'</span></td><td>'+fmt(p.x)+' t</td><td class="'+(good?'pos':'neg')+'">'+p.y.toFixed(1)+' \u20ac/t</td></tr>';
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
// ONGLET RÉGION — renderRg()
// Agrège les données par région géographique et affiche CA/EBITDA
// sous forme de barres ou lignes d'évolution.
// REG_MAP : correspondance site → code région (COU, NNO, IDF, BARA, SO)
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

  // Désactiver le bouton Ligne si une seule année sélectionnée
  const lineBtn=document.getElementById('rg-btn-line');
  if(lineBtn){
    if(rgIsSingle){
      lineBtn.disabled=true; lineBtn.style.opacity='.35'; lineBtn.style.cursor='not-allowed';
      if(rgCAType==='line'){rgCAType='bar'; lineBtn.classList.remove('active'); document.querySelector('.rg-ca-type.active')||document.querySelector('.rg-ca-type').classList.add('active');}
    } else {
      lineBtn.disabled=false; lineBtn.style.opacity=''; lineBtn.style.cursor='';
    }
  }
  const isLine=rgCAType==='line'&&!rgIsSingle;
  const lineOpts=function(yLabel,fmtFn){return {responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:function(c){return ' '+c.dataset.label+': '+fmtFn(c.parsed.y);}}}},scales:{y:{title:{display:true,text:yLabel},grid:{color:'#f0f0f0'}},x:{grid:{display:false}}}};};

  // ── CA chart ───────────────────────────────────────────────────
  if(isLine){
    const caLine=regions.map(function(rg,i){
      return {label:rg,data:activeRgYrs.map(function(yr){return allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;}).reduce(function(s,d){return s+(d.CA||0);},0)/1e6;}),borderColor:COLORS[i],backgroundColor:COLORS[i]+'33',tension:0.3,pointRadius:5,pointHoverRadius:8,fill:false,borderWidth:2};
    });
    cRgCA=mkChart('c-rg-ca',{type:'line',data:{labels:activeRgYrs.map(yr2lbl),datasets:caLine},options:lineOpts('M\u20ac',function(v){return v.toFixed(2)+' M\u20ac';})});
  } else {
    const yList0=rgIsAll?REAL_YEARS:activeRgYrs;
    const caDs=yList0.map(function(yr,i){return {label:yr2lbl(yr),data:regions.map(function(rg){return allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;}).reduce(function(s,d){return s+(d.CA||0);},0)/1e6;}),backgroundColor:C3(i),borderRadius:4};});
    cRgCA=mkChart('c-rg-ca',{type:'bar',data:{labels:regions,datasets:caDs},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'},tooltip:{callbacks:{label:function(c){return ' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+' M\u20ac';}}}},scales:{y:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},x:{grid:{display:false}}}}});
  }

  // ── EBITDA chart ───────────────────────────────────────────────
  if(isLine){
    const ebLine=regions.map(function(rg,i){
      return {label:rg,data:activeRgYrs.map(function(yr){return allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;}).reduce(function(s,d){return s+(d.EBITDA||0);},0)/1e6;}),borderColor:COLORS[i],backgroundColor:COLORS[i]+'33',tension:0.3,pointRadius:5,pointHoverRadius:8,fill:false,borderWidth:2};
    });
    cRgEB=mkChart('c-rg-eb',{type:'line',data:{labels:activeRgYrs.map(yr2lbl),datasets:ebLine},options:lineOpts('M\u20ac',function(v){return v.toFixed(2)+' M\u20ac';})});
  } else {
    const sortedRg=regions.map(function(rg){return {rg:rg,v:rows.filter(function(d){return d.Reg===rg;}).reduce(function(s,d){return s+(d.EBITDA||0);},0)};}).sort(function(a,b){return a.v-b.v;});
    cRgEB=mkChart('c-rg-eb',{type:'bar',data:{labels:sortedRg.map(function(d){return d.rg;}),datasets:[{label:'EBITDA',data:sortedRg.map(function(d){return d.v/1e6;}),backgroundColor:sortedRg.map(function(d){return d.v>=0?'rgba(16,185,129,.5)':'rgba(239,68,68,.5)';}),borderColor:sortedRg.map(function(d){return d.v>=0?'#10b981':'#ef4444';}),borderWidth:2,borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return ' EBITDA: '+c.parsed.x.toFixed(2)+' M\u20ac';}}}},scales:{x:{title:{display:true,text:'M\u20ac'},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}}});
  }

  // ── EBITDA \u20ac/t chart ───────────────────────────────────────────
  if(isLine){
    const ebtLine=regions.map(function(rg,i){
      return {label:rg,data:activeRgYrs.map(function(yr){
        const sub=allRows.filter(function(d){return d.Reg===rg&&String(d.Annee)===yr;});
        const eb=sub.reduce(function(s,d){return s+(d.EBITDA||0);},0);
        const tn=sub.reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);
        return tn>0?Math.round(eb/tn*10)/10:null;
      }),borderColor:COLORS[i],backgroundColor:COLORS[i]+'33',tension:0.3,pointRadius:5,pointHoverRadius:8,fill:false,borderWidth:2,spanGaps:false};
    });
    cRgEBT=mkChart('c-rg-ebt',{type:'line',data:{labels:activeRgYrs.map(yr2lbl),datasets:ebtLine},options:lineOpts('\u20ac/t',function(v){return v.toFixed(1)+' \u20ac/t';})});
  } else {
    const ebtArr=regions.map(function(rg){
      const sub=rows.filter(function(d){return d.Reg===rg;});
      const eb=sub.reduce(function(s,d){return s+(d.EBITDA||0);},0);
      const tn=sub.reduce(function(s,d){return s+(d.Tonnes_entrantes||0);},0);
      return {rg:rg,v:tn>0?Math.round(eb/tn*10)/10:null};
    }).filter(function(d){return d.v!==null;}).sort(function(a,b){return a.v-b.v;});
    cRgEBT=mkChart('c-rg-ebt',{type:'bar',data:{labels:ebtArr.map(function(d){return d.rg;}),datasets:[{label:'EBITDA \u20ac/t',data:ebtArr.map(function(d){return d.v;}),backgroundColor:ebtArr.map(function(d){return d.v>=0?'rgba(16,185,129,.5)':'rgba(239,68,68,.5)';}),borderColor:ebtArr.map(function(d){return d.v>=0?'#10b981':'#ef4444';}),borderWidth:2,borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return ' '+c.parsed.x.toFixed(1)+' \u20ac/t';}}}},scales:{x:{title:{display:true,text:'\u20ac/t'},grid:{color:'#f0f0f0'}},y:{grid:{display:false}}}}});
  }

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
// ONGLET PERFS & CHARGES — renderTk()
//
// Objectif : croiser les KPIs techniques (dispo, débit, heures, productivité)
// avec les charges P&L (personnel €/t, maintenance €/t) pour identifier
// quels indicateurs techniques influencent le plus les coûts.
//
// Structure de l'onglet :
//   1. KPI cards  : dispo, débit, tonnage, personnel €/t, maintenance €/t
//   2. Scatter plots : corrélations KPI ↔ charges (un point par site)
//      → verdict qualitatif (Pearson r) via mkScatterTk()
//   3. Vue par site  : évolution CA + overlay KPI, charges Personnel/Maintenance
//   4. Synthèse corrélations : tableau KPI dominant par site (Pearson r pré-calculé)
//   5. Tableau récap : tous les sites, année sélectionnable, flèches N-1
//
// Données croisées dans getTkMerged() :
//   - KPI_RAW (data_kpi_techniques.csv) × DATA (data_synthese.csv)
//   - Résultat : un objet par (site, année) avec champs KPI + charges €/t
//
// TK_CORR : coefficients de Pearson pré-calculés hors-ligne (Python/Excel)
//   car avec 3 points par site, un calcul JS serait identique mais moins
//   transparent. Mis à jour manuellement si les données changent.
//
// TK_ANCIENS : sites historiques (contrats plus anciens), distinction
//   visuelle dans les scatter plots.
// ══════════════════════════════════════════════════════
const KPI_RAW = %%KPI%%;
const Q1_DATA = %%Q1_DATA%%;
const TK_ANCIENS = new Set(['Le Havre','Amiens','Sevran','Paris 15','Ch\u00e9zy']); // sites à contrats anciens
const TK_YRS = [2023,2024,2025];
const TK_YR_COL   = {2023:'rgba(99,102,241,.8)', 2024:'rgba(0,163,224,.8)',  2025:'rgba(16,185,129,.8)'};
const TK_YR_BDR   = {2023:'#4338ca',             2024:'#0082b3',             2025:'#059669'};
const TK_GEN_COL  = {ancien:'rgba(245,158,11,.82)',recent:'rgba(0,163,224,.82)'};
const TK_GEN_BDR  = {ancien:'#d97706',            recent:'#0082b3'};
let _tkMerged=null, tkYr='all', tkSite=null, tkC={}, tkScYr='all', tkScGen='all', tkKpi='debit', tkCaX='tonnage';

// ── getTkMerged() ─────────────────────────────────────────────────────────────
// Fusionne KPI techniques + données P&L en un tableau plat.
// Calcule à la volée les charges en €/t (personnel, maintenance).
// Calcule aussi la productivité = débit / nb_trieurs_poste.
// Résultat mis en cache dans _tkMerged pour ne pas recalculer à chaque render.
function getTkMerged(){
  if(_tkMerged) return _tkMerged;
  _tkMerged=[];
  KPI_RAW.forEach(function(k){
    var yr=+k.Annee;
    var pl=DATA.find(function(d){return d.Site===k.Site&&+d.Annee===yr;});
    if(!pl) return;
    var tn=Math.abs(+(pl.Tonnes_entrantes||0)); if(!tn) return;
    var cp=pl.Couts_personnel!=null?Math.abs(+pl.Couts_personnel)/tn:null;
    var mo=Math.abs(+(pl.Maintenance_obligatoire||0));
    var mc=Math.abs(+(pl.Maintenance_courante||0));
    var maint=(mo+mc)>0?(mo+mc)/tn:null;
    var dispo=k.Dispo_globale!=null?+k.Dispo_globale*100:null;
    var dispo_process=k.Dispo_process!=null&&k.Dispo_process!==''?+k.Dispo_process*100:null;
    var debit=k.Debit!=null?+k.Debit:null;
    var nbOp=k.Nb_trieurs_poste!=null&&k.Nb_trieurs_poste!==''?+k.Nb_trieurs_poste:null;
    var productivite=(debit!=null&&nbOp!=null&&nbOp>0)?debit/nbOp:null;
    _tkMerged.push({site:k.Site,annee:yr,
      gen:TK_ANCIENS.has(k.Site)?'ancien':'recent',
      dispo:dispo,
      dispo_process:dispo_process,
      heures:k.Heures_fonctionnement!=null?+k.Heures_fonctionnement:null,
      tonnage:k.Tonnage!=null?+k.Tonnage:null,
      debit:debit,
      productivite:productivite,
      personnel:cp,
      maintenance:maint,
      refus:k.Taux_refus!=null&&k.Taux_refus!==''?+k.Taux_refus:null});
  });
  return _tkMerged;
}

function tkFiltered(){ return tkYr==='all'?getTkMerged():getTkMerged().filter(function(d){return d.annee===+tkYr;}); }

function tkScFiltered(){
  var m=getTkMerged().filter(function(d){
    return tkScGen==='all' || d.gen===tkScGen;
  });
  if(tkScYr!=='all'){
    return m.filter(function(d){ return d.annee===+tkScYr; });
  }
  // Mode "Toutes (moy.)" : moyenne par site sur toutes les années
  // Exception : dispo_process n'a pas de données 2023, donc sa moyenne se calcule
  // uniquement sur les lignes où la valeur est non-null (2024+2025), sans forcer l'exclusion
  // des autres métriques — chaque métrique est moyennée sur ses valeurs non-null disponibles.
  var bySite={};
  m.forEach(function(d){
    if(!bySite[d.site]) bySite[d.site]={site:d.site,gen:d.gen,dispo:0,dispo_process:0,debit:0,heures:0,tonnage:0,productivite:0,personnel:0,maintenance:0,refus:0,_cnt:{}};
    var r=bySite[d.site];
    ['dispo','dispo_process','debit','heures','tonnage','productivite','personnel','maintenance','refus'].forEach(function(k){
      if(d[k]!=null){ r[k]+=d[k]; r._cnt[k]=(r._cnt[k]||0)+1; }
    });
  });
  return Object.values(bySite).map(function(r){
    var out={site:r.site,gen:r.gen,annee:'moy.'};
    ['dispo','dispo_process','debit','heures','tonnage','productivite','personnel','maintenance','refus'].forEach(function(k){
      out[k]=r._cnt[k]?r[k]/r._cnt[k]:null;
    });
    return out;
  });
}

function tkScSetYr(yr,el){
  tkScYr=yr;
  tkYr=yr;
  document.querySelectorAll('.tk-sc-yr').forEach(function(b){b.classList.remove('active');});
  el.classList.add('active');
  renderTkScatter();
  renderTkTable();
}

function tkScSetGen(gen,el){
  tkScGen=gen;
  document.querySelectorAll('.tk-sc-gen').forEach(function(b){b.classList.remove('active');});
  el.classList.add('active');
  renderTkScatter();
}

var TK_KPI_LABELS={debit:'D\u00e9bit (t/h)',dispo:'Disponibilit\u00e9 globale (%)',dispo_process:'Disponibilit\u00e9 process (%)',heures:'Heures de fonctionnement (h)',productivite:'Productivit\u00e9 (t/h/op.)'};

function tkSetKpi(kpi,el){
  tkKpi=kpi;
  document.querySelectorAll('.tk-kpi').forEach(function(b){b.classList.remove('active');});
  el.classList.add('active');
  // Dispo process : griser R2023 et basculer sur "all" si 2023 était sélectionné
  var btn2023=document.getElementById('tk-btn-2023');
  var note=document.getElementById('tk-dispo-proc-note');
  if(kpi==='dispo_process'){
    if(btn2023){btn2023.style.opacity='.35';btn2023.style.pointerEvents='none';}
    if(note) note.style.display='block';
    if(tkScYr===2023){
      tkScYr='all'; tkYr='all';
      document.querySelectorAll('.tk-sc-yr').forEach(function(b){b.classList.remove('active');});
      var allBtn=document.querySelector('.tk-sc-yr');
      if(allBtn) allBtn.classList.add('active');
    }
  } else {
    if(btn2023){btn2023.style.opacity='';btn2023.style.pointerEvents='';}
    if(note) note.style.display='none';
  }
  renderTkScatter();
}

function tkSetCaX(key,el){
  tkCaX=key;
  document.querySelectorAll('.tk-cax').forEach(function(b){b.classList.remove('active');});
  el.classList.add('active');
  renderTkCaChart();
}

// ── TK_CORR : coefficients de Pearson pré-calculés ──────────────────────────
// Structure : { site: { pers: { kpi: r }, maint: { kpi: r } } }
// 'pers'  = corrélation entre le KPI et Personnel €/t
// 'maint' = corrélation entre le KPI et Maintenance €/t
// null = pas assez de données pour calculer (ex. Millau sans taux de refus)
//
// ⚠️  Si les données CSV changent (nouveau site, nouvelle année),
//     recalculer ces valeurs avec le script extract_data.py ou via Excel.
// ── Interprétation du signe ──────────────────────────────────────────────────
// r négatif : quand le KPI monte, la charge baisse (ex. dispo↑ → personnel€/t↓)
// r positif : quand le KPI monte, la charge monte
// |r| ≥ 0.7 = lien fort · 0.4–0.7 = modéré · < 0.4 = faible
const TK_CORR={
  'Amiens':         {pers:{dispo:-0.904,debit:0.706,heures:0.525,refus:0.072,tonnage:0.904},  maint:{dispo:0.51,debit:-0.189,heures:-0.911,refus:-0.617,tonnage:-0.511}},
  'B\u00e8gles':    {pers:{dispo:-0.267,debit:-0.895,heures:-0.622,refus:-0.769,tonnage:-0.998},maint:{dispo:0.436,debit:-0.967,heures:0.051,refus:-0.155,tonnage:-0.789}},
  'Ch\u00e9zy':     {pers:{dispo:0.088,debit:-0.135,heures:0.564,refus:0.785,tonnage:0.215},  maint:{dispo:1.0,debit:0.979,heures:-0.784,refus:0.674,tonnage:0.989}},
  'Le Havre':       {pers:{dispo:0.607,debit:-0.96,heures:0.988,refus:0.968,tonnage:-0.917},  maint:{dispo:0.994,debit:-0.863,heures:0.79,refus:0.482,tonnage:-0.92}},
  'Millau':         {pers:{dispo:-0.999,debit:-0.855,heures:-0.986,refus:null,tonnage:-0.995}, maint:{dispo:0.971,debit:0.964,heures:0.903,refus:null,tonnage:0.93}},
  'Montpellier':    {pers:{dispo:-0.798,debit:-0.559,heures:-0.878,refus:-0.037,tonnage:-0.998},maint:{dispo:0.456,debit:0.721,heures:0.322,refus:0.978,tonnage:-0.24}},
  'Nantes':         {pers:{dispo:0.264,debit:-0.739,heures:-0.997,refus:-0.905,tonnage:-0.894},maint:{dispo:-0.692,debit:0.971,heures:0.915,refus:0.998,tonnage:0.999}},
  'Paris 15':       {pers:{dispo:-0.873,debit:0.331,heures:-0.529,refus:0.928,tonnage:0.351}, maint:{dispo:-1.0,debit:0.743,heures:-0.872,refus:0.636,tonnage:-0.141}},
  'Portes les Valences':{pers:{dispo:0.785,debit:0.787,heures:0.66,refus:0.836,tonnage:0.385},maint:{dispo:-0.953,debit:-0.951,heures:-0.992,refus:-0.922,tonnage:-0.981}},
  'Saran':          {pers:{dispo:0.628,debit:0.942,heures:0.628,refus:0.947,tonnage:0.976},   maint:{dispo:0.202,debit:-0.857,heures:0.203,refus:-0.353,tonnage:-0.451}},
  'Sevran':         {pers:{dispo:1.0,debit:-1.0,heures:1.0,refus:1.0,tonnage:1.0},            maint:{dispo:1.0,debit:-1.0,heures:1.0,refus:1.0,tonnage:1.0}}
};
const TK_CORR_SITES=['Amiens','B\u00e8gles','Ch\u00e9zy','Le Havre','Millau','Montpellier','Nantes','Paris 15','Portes les Valences','Saran','Sevran'];
const TK_CORR_KPIS=['dispo','debit','heures','refus','tonnage'];
const TK_CORR_KPI_LBL={dispo:'Dispo',debit:'D\u00e9bit',heures:'Heures',refus:'Taux de refus',tonnage:'Tonnage'};

function corrColor(r){
  if(r===null)return{bg:'#f1f5f9',fg:'#94a3b8'};
  var a=Math.abs(r);
  if(r<0){
    // bleu : charge baisse quand KPI monte
    var i=Math.round(a*180);
    return{bg:'rgb('+(255-i)+','+(255-i)+',255)',fg:a>0.6?'#1e3a8a':'#334155'};
  } else {
    // orange : charge monte quand KPI monte
    var i=Math.round(a*180);
    return{bg:'rgb(255,'+(255-Math.round(a*130))+','+(255-Math.round(a*200))+')',fg:a>0.6?'#7c2d12':'#334155'};
  }
}

function bestKpi(corrObj){
  var best=null,bestR=0;
  Object.keys(corrObj).forEach(function(k){
    var r=corrObj[k];
    if(r!==null&&Math.abs(r)>Math.abs(bestR)){bestR=r;best=k;}
  });
  return {k:best,r:bestR};
}

function renderTkCorr(){
  var sites=TK_CORR_SITES;
  var kpis=TK_CORR_KPIS;

  // Tendance réelle 2023→2025 par site et KPI (pour afficher le sens observé)
  var tkTrend={};
  getTkMerged().forEach(function(d){
    if(!tkTrend[d.site]) tkTrend[d.site]={};
    ['dispo','dispo_process','debit','heures','refus','tonnage','productivite'].forEach(function(k){
      if(d.annee===2023&&d[k]!=null) { if(!tkTrend[d.site][k]) tkTrend[d.site][k]={}; tkTrend[d.site][k].v23=d[k]; }
      if(d.annee===2025&&d[k]!=null) { if(!tkTrend[d.site][k]) tkTrend[d.site][k]={}; tkTrend[d.site][k].v25=d[k]; }
    });
  });
  function kpiWentUp(site, kpiKey){
    var t=(tkTrend[site]||{})[kpiKey]||{};
    if(t.v23==null||t.v25==null) return null; // inconnu
    return t.v25>t.v23; // true=hausse, false=baisse
  }

  // ── 1. Tableau synthèse ──────────────────────────────────────────────────
  var s='<div class="hm-wrap"><table style="font-size:.8rem;border-collapse:collapse;width:100%">';
  s+='<thead><tr style="background:#f8fafc">';
  s+='<th style="padding:8px 12px;text-align:left">Site</th>';
  s+='<th style="padding:8px 12px;text-align:center;color:#d97706" colspan="2">Personnel \u20ac/t &mdash; KPI dominant</th>';
  s+='<th style="padding:8px 12px;text-align:center;color:#dc2626" colspan="2">Maintenance \u20ac/t &mdash; KPI dominant</th>';
  s+='</tr><tr style="background:#fafafa;font-size:.72rem;color:#64748b">';
  s+='<th></th><th style="padding:4px 12px">KPI</th><th style="padding:4px 12px">r &nbsp;&nbsp; ce qui s\u2019est pass\u00e9</th>';
  s+='<th style="padding:4px 12px">KPI</th><th style="padding:4px 12px">r &nbsp;&nbsp; ce qui s\u2019est pass\u00e9</th></tr></thead><tbody>';
  sites.forEach(function(site,i){
    var c=TK_CORR[site]||{};
    var bp=bestKpi(c.pers||{}), bm=bestKpi(c.maint||{});
    var bg=i%2?'#fafbff':'#fff';
    var note=site==='Sevran'?' <span style="font-size:.65rem;color:#94a3b8">(2 ans)</span>':'';
    function cell(b){
      if(!b.k)return '<td colspan="2" style="text-align:center;color:#94a3b8;padding:7px 12px">\u2014</td>';
      var cl=corrColor(b.r);
      // Sens observé : KPI a-t-il monté ou baissé entre 2023 et 2025 ?
      var up=kpiWentUp(site, b.k);
      var kpiDir=up===null?null:(up?'\u2191':'\u2193');
      var chargeDir; // charge a évolué dans le sens donné par le signe de r × direction KPI
      if(kpiDir!==null){
        var chargeUp=(up&&b.r>0)||(!up&&b.r<0);
        chargeDir=chargeUp?'\u2191':'\u2193';
      }
      var sens;
      if(kpiDir===null){
        sens=b.r>0?'\u2191 KPI \u2192 \u2191 charge':'\u2191 KPI \u2192 \u2193 charge';
      } else {
        // Direction observée en premier (gras), direction inverse en gris
        sens='<strong>'+kpiDir+' KPI \u2192 '+chargeDir+' charge</strong>';
      }
      return '<td style="padding:7px 12px;text-align:center;font-weight:600">'+TK_CORR_KPI_LBL[b.k]+'</td>'
        +'<td style="padding:7px 12px;text-align:center"><span style="background:'+cl.bg+';color:'+cl.fg+';padding:2px 8px;border-radius:10px;font-weight:600;font-size:.75rem">'+b.r.toFixed(2)+'</span>'
        +' <span style="font-size:.68rem;color:#475569">'+sens+'</span></td>';
    }
    s+='<tr style="border-bottom:1px solid #f1f5f9;background:'+bg+'">';
    s+='<td style="padding:7px 12px;font-weight:600">'+site+note+'</td>';
    s+=cell(bp)+cell(bm);
    s+='</tr>';
  });
  s+='</tbody></table></div>';
  var el=document.getElementById('tk-corr-summary');
  if(el) el.innerHTML=s;

}

function renderTkScatter(){
  // dispo_process : pas de données 2023 → on exclut 2023 et on l'indique
  var noData2023 = (tkKpi==='dispo_process');
  var data=tkScFiltered().filter(function(d){
    return !noData2023 || d.annee!==2023;
  });
  var xLbl=TK_KPI_LABELS[tkKpi]||tkKpi;
  var lp=document.getElementById('tk-kpi-lbl-pers');  if(lp) lp.textContent=xLbl;
  var lm=document.getElementById('tk-kpi-lbl-maint'); if(lm) lm.textContent=xLbl;
  var pPts=data.filter(function(d){return d[tkKpi]!=null&&d.personnel!=null;})
               .map(function(d){return {x:d[tkKpi],y:d.personnel,label:d.site,annee:d.annee};});
  mkScatterTk('tk-sc-pers',pPts,xLbl,'Personnel \u20ac/t','tk-verdict-pers');
  var qPts=data.filter(function(d){return d[tkKpi]!=null&&d.maintenance!=null;})
               .map(function(d){return {x:d[tkKpi],y:d.maintenance,label:d.site,annee:d.annee};});
  mkScatterTk('tk-sc-maint',qPts,xLbl,'Maintenance \u20ac/t','tk-verdict-maint');
}

function linReg(pts){
  var n=pts.length; if(n<2) return null;
  var sx=0,sy=0,sxy=0,sxx=0;
  pts.forEach(function(p){sx+=p.x;sy+=p.y;sxy+=p.x*p.y;sxx+=p.x*p.x;});
  var det=n*sxx-sx*sx; if(Math.abs(det)<1e-9) return null;
  var m=(n*sxy-sx*sy)/det, b=(sy-m*sx)/n;
  var ymean=sy/n, ss_tot=0, ss_res=0;
  pts.forEach(function(p){ss_tot+=(p.y-ymean)*(p.y-ymean);ss_res+=(p.y-(m*p.x+b))*(p.y-(m*p.x+b));});
  var r2=ss_tot>0?1-ss_res/ss_tot:0;
  var xs=pts.map(function(p){return p.x;});
  return {m:m,b:b,r2:r2,xmin:Math.min.apply(null,xs),xmax:Math.max.apply(null,xs)};
}

function tkScatterDs(data, xKey, yKey){
  var anc=[],rec=[];
  data.forEach(function(d){
    if(d[xKey]==null||d[yKey]==null) return;
    var pt={x:d[xKey],y:d[yKey],label:d.site,annee:d.annee};
    if(d.gen==='ancien') anc.push(pt); else rec.push(pt);
  });
  return {anc:anc,rec:rec};
}

var tkLabelPlugin={id:'tkLabels',afterDraw:function(chart){
  var ctx=chart.ctx;
  chart.data.datasets.forEach(function(ds,di){
    var meta=chart.getDatasetMeta(di);
    if(meta.type!=='scatter') return;
    meta.data.forEach(function(pt,i){
      var raw=ds.data[i]; if(!raw||!raw.label) return;
      ctx.save();
      ctx.font='bold 10px "Segoe UI",sans-serif';
      ctx.fillStyle='#334155';
      ctx.fillText(raw.label,pt.x+8,pt.y-5);
      ctx.restore();
    });
  });
}};

function tkSetVerdict(elId,r2){
  var el=document.getElementById(elId); if(!el||r2==null) return;
  var v=r2>0.5?{t:'Corr\u00e9lation forte',   c:'#059669',b:'#d1fae5',bd:'#059669'}
         :r2>0.2?{t:'Corr\u00e9lation mod\u00e9r\u00e9e',c:'#d97706',b:'#fef3c7',bd:'#d97706'}
         :        {t:'Corr\u00e9lation faible', c:'#6b7280',b:'#f3f4f6',bd:'#9ca3af'};
  el.textContent=v.t;
  el.style.color=v.c; el.style.background=v.b; el.style.border='1px solid '+v.bd;
}

function mkScatterTk(id, pts, xLbl, yLbl, verdictId){
  var reg=linReg(pts);
  if(reg&&verdictId) tkSetVerdict(verdictId,reg.r2);
  if(!pts.length) return;
  var labelPlugin={
    id:'lbl_'+id,
    afterDraw:function(chart){
      if(chart.tooltip&&chart.tooltip.getActiveElements&&chart.tooltip.getActiveElements().length) return;
      var ctx=chart.ctx;
      chart.data.datasets.forEach(function(ds,di){
        var meta=chart.getDatasetMeta(di);
        if(meta.type!=='scatter') return;
        meta.data.forEach(function(pt,i){
          var raw=ds.data[i];
          if(!raw||!raw.label) return;
          ctx.save();
          ctx.font='600 10px system-ui,sans-serif';
          ctx.textAlign='left';
          ctx.strokeStyle='rgba(255,255,255,.95)';
          ctx.lineWidth=3;
          ctx.lineJoin='round';
          ctx.strokeText(raw.label,pt.x+12,pt.y-4);
          ctx.fillStyle='#1e293b';
          ctx.fillText(raw.label,pt.x+12,pt.y-4);
          ctx.restore();
        });
      });
    }
  };
  var ds=[{label:'Sites',data:pts,
    backgroundColor:'rgba(0,130,179,.8)',
    borderColor:'#fff',
    borderWidth:2,
    pointRadius:11,pointHoverRadius:14,
    type:'scatter'}];
  if(reg) ds.push({label:'Tendance (R\u00b2='+reg.r2.toFixed(2)+')',
    data:[{x:reg.xmin,y:reg.m*reg.xmin+reg.b},{x:reg.xmax,y:reg.m*reg.xmax+reg.b}],
    type:'line',borderColor:'#f59e0b',borderWidth:2,pointRadius:0,fill:false,tension:0});
  return mkChart(id,{type:'scatter',data:{datasets:ds},plugins:[labelPlugin],options:{responsive:true,maintainAspectRatio:false,
    plugins:{
      legend:{display:!!reg,position:'bottom',labels:{font:{size:10},color:'#64748b',boxWidth:24,padding:14}},
      tooltip:{callbacks:{label:function(ctx){var r=ctx.raw;
        var xUnit=(xLbl.match(/\(([^)]+)\)/)||['',''])[1]||'';
        var xFmt=xUnit==='h'?Math.round(r.x).toString():r.x.toFixed(1);
        return (r.label||'')+(r.annee?' ('+r.annee+')':'')
          +' \u2014 '+(xFmt+(xUnit?' '+xUnit:''))
          +' / '+r.y.toFixed(1)+'\u20ac/t';}}}},
    scales:{
      x:{title:{display:true,text:xLbl,font:{size:11},color:'#475569'},
         grid:{color:'rgba(0,0,0,.06)'},ticks:{color:'#64748b'}},
      y:{title:{display:true,text:yLbl,font:{size:11},color:'#475569'},
         grid:{color:'rgba(0,0,0,.06)'},ticks:{color:'#64748b'}}
    }}});
}

function tkSetYr(yr,el){
  tkYr=yr;
  document.querySelectorAll('.tk-yr').forEach(function(b){b.classList.remove('active');});
  el.classList.add('active');
  renderTk();
}

function tkSetSite(s){ tkSite=s; renderTkSiteDetail(); }

function renderTkSiteDetail(){
  var site=tkSite;
  var d=getTkMerged().filter(function(r){return r.site===site;}).sort(function(a,b){return a.annee-b.annee;});
  if(!d.length) return;
  var yrs=d.map(function(r){return r.annee;});

  // KPI cards avec tendance — refYr : année de référence pour le calcul d'évolution
  function setSkCard(valId,subId,trendId,vals,unit,higherIsBetter,refYr){
    var lastYr=yrs[yrs.length-1];
    var refYear=refYr||yrs[0]; // par défaut première année disponible
    var v25=vals[yrs.indexOf(lastYr)];
    var vRef=vals[yrs.indexOf(refYear)];
    var el=document.getElementById(valId); if(el) el.textContent=v25!=null?v25.toFixed(1)+unit:'\u2014';
    var s=document.getElementById(subId);  if(s)  s.textContent='R'+lastYr;
    var t=document.getElementById(trendId); if(!t) return;
    if(vRef!=null&&v25!=null&&vRef!==0){
      var pct=(v25-vRef)/Math.abs(vRef)*100;
      var up=pct>=0;
      var good=(higherIsBetter&&up)||(!higherIsBetter&&!up);
      t.textContent=(up?'\u25b2 ':'\u25bc ')+Math.abs(pct).toFixed(1)+'% vs '+refYear;
      t.style.color=good?'#10b981':'#ef4444';
    } else { t.textContent=''; }
  }
  setSkCard('tk-sk-dispo',      'tk-sk-dispo-s',     'tk-sk-dispo-t',      d.map(function(r){return r.dispo;}),         '%', true, 2023);
  setSkCard('tk-sk-dispo-proc', 'tk-sk-dispo-proc-s','tk-sk-dispo-proc-t', d.map(function(r){return r.dispo_process;}),  '%', true, 2024);
  setSkCard('tk-sk-debit', 'tk-sk-debit-s','tk-sk-debit-t', d.map(function(r){return r.debit;}),      ' t/h',true,  2023);
  setSkCard('tk-sk-refus', 'tk-sk-refus-s','tk-sk-refus-t', d.map(function(r){return r.refus;}),      '%',   false, 2023);
  setSkCard('tk-sk-pers',  'tk-sk-pers-s', 'tk-sk-pers-t',  d.map(function(r){return r.personnel;}),  '\u20ac',false,2023);
  setSkCard('tk-sk-maint', 'tk-sk-maint-s','tk-sk-maint-t', d.map(function(r){return r.maintenance;}),'\u20ac',false,2023);

  // CA + contexte
  renderTkCaChart();

  // Note analytique
  renderTkSiteCharts();
}

var tkKpiLines={debit:false,dispo:false,dispo_process:false,refus:false,heures:false,tonnage:false};
var TK_KLINE_COL={debit:'#0082b3',dispo:'#059669',dispo_process:'#0ea5e9',refus:'#ef4444',heures:'#8b5cf6',tonnage:'#6366f1'};
var TK_KLINE_LBL={debit:'D\u00e9bit (t/h)',dispo:'Dispo globale (%)',dispo_process:'Dispo process (%)',refus:'Refus (%)',heures:'Heures (h)',tonnage:'Tonnage entrant (t)'};
var TK_KLINE_UNIT={debit:'t/h',dispo:'%',dispo_process:'%',refus:'%',heures:'h',tonnage:'t'};

function tkToggleKpiLine(key,el){
  var wasActive=tkKpiLines[key];
  // comportement radio : un seul KPI à la fois
  Object.keys(tkKpiLines).forEach(function(k){tkKpiLines[k]=false;});
  document.querySelectorAll('.tk-kline').forEach(function(b){
    b.style.background=''; b.style.color=b.dataset.col; b.style.borderColor=b.dataset.col;
  });
  if(!wasActive){
    tkKpiLines[key]=true;
    el.style.background=TK_KLINE_COL[key]; el.style.color='#fff'; el.style.borderColor=TK_KLINE_COL[key];
  }
  renderTkSiteCharts();
}

function renderTkSiteCharts(){
  var site=tkSite;
  var d=getTkMerged().filter(function(r){return r.site===site;}).sort(function(a,b){return a.annee-b.annee;});
  if(!d.length) return;
  var yrs=d.map(function(r){return r.annee;});
  var activeKpi=Object.keys(tkKpiLines).find(function(k){return tkKpiLines[k];})||null;
  var hasLines=!!activeKpi;

  function buildCfg(chargeKey,chargeLabel,barColor,barBorder){
    // Barre en arrière-plan (order élevé = dessiné en premier)
    var ds=[{label:chargeLabel,data:d.map(function(r){return r[chargeKey];}),
      type:'bar',backgroundColor:barColor,borderColor:barBorder,borderWidth:2,yAxisID:'y',order:2}];
    // Courbe KPI au premier plan (order faible = dessiné en dernier)
    if(activeKpi){
      var lineData=d.map(function(r){return activeKpi==='tonnage'?Math.round(r[activeKpi]):r[activeKpi];});
      ds.push({label:TK_KLINE_LBL[activeKpi],data:lineData,
        type:'line',borderColor:TK_KLINE_COL[activeKpi],backgroundColor:'transparent',
        borderWidth:2.5,pointRadius:7,pointHoverRadius:10,tension:.35,fill:false,yAxisID:'y2',order:1});
    }
    var scales={y:{position:'left',title:{display:true,text:'\u20ac/t',font:{size:10}},grid:{color:'#f0f0f0'}}};
    if(hasLines) scales.y2={position:'right',
      title:{display:true,text:TK_KLINE_UNIT[activeKpi],font:{size:10}},
      grid:{drawOnChartArea:false},
      ticks:{callback:function(v){return activeKpi==='tonnage'?Math.round(v).toLocaleString('fr-FR'):v;}}};
    return {type:'bar',data:{labels:yrs,datasets:ds},options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{font:{size:10},boxWidth:12}}},scales:scales}};
  }
  mkChart('tk-pers-chart',  buildCfg('personnel',  'Personnel \u20ac/t',  'rgba(245,158,11,.85)','#d97706'));
  mkChart('tk-maint-chart', buildCfg('maintenance','Maintenance \u20ac/t','rgba(239,68,68,.8)',  '#dc2626'));
}

function renderTkCaChart(){
  var site=tkSite;
  var pl=DATA.filter(function(d){return d.Site===site&&[2023,2024,2025].indexOf(+d.Annee)>=0;})
             .sort(function(a,b){return +a.Annee-+b.Annee;});
  if(!pl.length) return;
  var yrs=pl.map(function(d){return +d.Annee;});
  var caData=pl.map(function(d){return d.CA!=null?Math.round(Math.abs(+d.CA)/1e4)/100:null;}); // M€
  var tkd=getTkMerged().filter(function(d){return d.site===site;}).sort(function(a,b){return a.annee-b.annee;});
  var xData,xLbl,xColor,xBg;
  if(tkCaX==='refus'){
    xData=tkd.map(function(r){return r.refus;});
    xLbl='Taux de refus (%)'; xColor='#ef4444'; xBg='rgba(239,68,68,.10)';
  } else {
    xData=pl.map(function(d){return d.Tonnes_entrantes!=null?Math.round(Math.abs(+d.Tonnes_entrantes)):null;});
    xLbl='Tonnage entrant (t)'; xColor='#8b5cf6'; xBg='rgba(139,92,246,.10)';
  }
  mkChart('tk-ca-chart',{type:'bar',data:{labels:yrs,datasets:[
    {label:'CA (M\u20ac)',data:caData,backgroundColor:'rgba(0,58,99,.75)',borderColor:'#003a63',borderWidth:2,yAxisID:'y',order:2},
    {label:xLbl,data:xData,type:'line',borderColor:xColor,backgroundColor:xBg,borderWidth:2.5,pointRadius:7,tension:.3,fill:true,yAxisID:'y2',order:1}
  ]},options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:'bottom',labels:{font:{size:11}}}},
    scales:{
      y: {position:'left', title:{display:true,text:'M\u20ac',font:{size:10}},grid:{color:'#f0f0f0'}},
      y2:{position:'right',title:{display:true,text:tkCaX==='refus'?'%':'t',font:{size:10}},grid:{drawOnChartArea:false}}
    }}});
}

var tkTblSort={col:'site',asc:true};
function tkSortBy(col){
  if(tkTblSort.col===col) tkTblSort.asc=!tkTblSort.asc;
  else{tkTblSort.col=col;tkTblSort.asc=col==='site';}
  renderTkTable();
}

function renderTkTable(){
  var m=getTkMerged();
  var allSites=Array.from(new Set(m.map(function(d){return d.site;}))).sort();
  // Année affichée et année N-1 pour l'évolution
  var yrCur=tkYr==='all'?2025:+tkYr;
  var yrRef=yrCur>2023?yrCur-1:null;
  var yrLbl=yrCur;
  var rows=allSites.map(function(s){
    var dc=m.find(function(r){return r.site===s&&r.annee===yrCur;})||{};
    var dr=yrRef?m.find(function(r){return r.site===s&&r.annee===yrRef;})||{}:{};
    return{site:s,
      tonnage:dc.tonnage??null,
      dispo:dc.dispo??null,          dispoR:dr.dispo??null,
      dispo_process:dc.dispo_process??null, dispo_processR:dr.dispo_process??null,
      debit:dc.debit??null,   debitR:dr.debit??null,
      refus:dc.refus??null,   refusR:dr.refus??null,
      pers:dc.personnel??null, persR:dr.personnel??null,
      maint:dc.maintenance??null,maintR:dr.maintenance??null};
  });
  // Plages heatmap
  var COLS=['dispo','debit','refus','pers','maint'];
  var rng={};
  COLS.forEach(function(k){
    var v=rows.map(function(r){return r[k];}).filter(function(v){return v!=null;});
    rng[k]={mn:Math.min.apply(null,v),mx:Math.max.apply(null,v)};
  });
  // Rangs (pas pour débit ni tonnage)
  var RANK_CFG={dispo:true,refus:false,pers:false,maint:false};
  var rnk={};
  Object.keys(RANK_CFG).forEach(function(k){
    var hib=RANK_CFG[k];
    var sorted=rows.filter(function(r){return r[k]!=null;}).slice()
      .sort(function(a,b){return hib?b[k]-a[k]:a[k]-b[k];});
    sorted.forEach(function(r,i){rnk[r.site]=rnk[r.site]||{};rnk[r.site][k]=i+1;});
  });
  // Tri
  rows.sort(function(a,b){
    var k=tkTblSort.col;
    var va=k==='site'?a.site:a[k], vb=k==='site'?b.site:b[k];
    if(va==null&&vb==null)return 0;
    if(va==null)return 1; if(vb==null)return -1;
    var r=k==='site'?va.localeCompare(vb):va-vb;
    return tkTblSort.asc?r:-r;
  });
  // Couleur texte heatmap
  function heatCol(val,key,hib){
    if(val==null)return '#1e293b';
    var r=rng[key]; if(!r||r.mx===r.mn)return '#1e293b';
    var t=(val-r.mn)/(r.mx-r.mn);
    var good=hib?t:1-t;
    if(good>=0.72)return '#059669';
    if(good>=0.45)return '#1e293b';
    return '#dc2626';
  }
  function heatW(val,key,hib){
    if(val==null)return '400';
    var r=rng[key]; if(!r||r.mx===r.mn)return '400';
    var t=(val-r.mn)/(r.mx-r.mn);
    var good=hib?t:1-t;
    return (good>=0.72||good<=0.28)?'700':'400';
  }
  // Flèche évolution vs N-1
  function evo(vCur,vRef,hib){
    if(!yrRef||vCur==null||vRef==null||vRef===0)return '';
    var pct=(vCur-vRef)/Math.abs(vRef)*100;
    if(Math.abs(pct)<0.1)return '';
    var up=pct>=0;
    var good=(hib&&up)||(!hib&&!up);
    return '<span style="font-size:.7rem;color:'+(good?'#059669':'#dc2626')+';margin-left:4px">'+(up?'\u25b2':'\u25bc')+Math.abs(pct).toFixed(1)+'%</span>';
  }
  function si(col){
    if(tkTblSort.col!==col)return '<span style="opacity:.25;font-size:.65rem"> \u21c5</span>';
    return '<span style="font-size:.65rem"> '+(tkTblSort.asc?'\u2191':'\u2193')+'</span>';
  }
  function th(col,lbl){return '<th onclick="tkSortBy(&#39;'+col+'&#39;)" style="cursor:pointer;white-space:nowrap;user-select:none;padding:8px 12px">'+lbl+si(col)+'</th>';}
  var n=rows.length;
  function rb(site,key){
    if(!rnk[site]||!rnk[site][key])return '';
    var r=rnk[site][key];
    var col=r<=3?'#059669':r>=n-2?'#dc2626':'#94a3b8';
    return '<sup style="font-size:.62rem;font-weight:700;color:'+col+';margin-left:2px">'+r+'</sup>';
  }
  var suffix=' '+yrLbl;
  var evoNote=yrRef?'<div style="font-size:.75rem;color:#64748b;margin-bottom:8px">\u25b2\u25bc \u00c9volution par rapport \u00e0 '+(yrRef)+'</div>':'';
  var h=evoNote+'<div class="hm-wrap"><table class="hm-table" style="font-size:.82rem;border-collapse:collapse;width:100%"><thead><tr style="background:#f8fafc">';
  h+=th('site','Site');
  h+=th('tonnage','Tonnage'+suffix);
  h+=th('dispo','Dispo globale'+suffix);
  h+=th('dispo_process','Dispo process'+suffix);
  h+=th('debit','D\u00e9bit'+suffix);
  h+=th('refus','Refus'+suffix);
  h+=th('pers','Personnel \u20ac/t');
  h+=th('maint','Maintenance \u20ac/t');
  h+='</tr></thead><tbody>';
  function td(val,fmt,key,hib,ref,evoVal){
    var col=heatCol(val,key,hib), fw=heatW(val,key,hib);
    var txt=val!=null?'<span style="color:'+col+';font-weight:'+fw+'">'+fmt(val)+'</span>':'—';
    return '<td style="text-align:center;padding:7px 10px">'+txt+(key?rb('__site__',key):'')+(evoVal||'')+'</td>';
  }
  rows.forEach(function(r,i){
    h+='<tr style="border-bottom:1px solid #f1f5f9;'+(i%2?'background:#fafbff':'')+'\">';
    h+='<td style="font-weight:600;padding:7px 12px;white-space:nowrap">'+r.site+'</td>';
    h+='<td style="text-align:center;padding:7px 10px;color:#475569">'+(r.tonnage!=null?Math.round(r.tonnage).toLocaleString('fr-FR')+' t':'—')+'</td>';
    h+='<td style="text-align:center;padding:7px 10px"><span style="color:'+heatCol(r.dispo,'dispo',true)+';font-weight:'+heatW(r.dispo,'dispo',true)+'">'+(r.dispo!=null?r.dispo.toFixed(1)+'%':'—')+'</span>'+rb(r.site,'dispo')+evo(r.dispo,r.dispoR,true)+'</td>';
    h+='<td style="text-align:center;padding:7px 10px"><span style="color:'+heatCol(r.dispo_process,'dispo',true)+';font-weight:'+heatW(r.dispo_process,'dispo',true)+'">'+(r.dispo_process!=null?r.dispo_process.toFixed(1)+'%':'—')+'</span>'+evo(r.dispo_process,r.dispo_processR,true)+'</td>';
    h+='<td style="text-align:center;padding:7px 10px">'+(r.debit!=null?r.debit.toFixed(1)+' t/h':'—')+evo(r.debit,r.debitR,true)+'</td>';
    h+='<td style="text-align:center;padding:7px 10px"><span style="color:'+heatCol(r.refus,'refus',false)+';font-weight:'+heatW(r.refus,'refus',false)+'">'+(r.refus!=null?r.refus.toFixed(1)+'%':'—')+'</span>'+rb(r.site,'refus')+evo(r.refus,r.refusR,false)+'</td>';
    h+='<td style="text-align:center;padding:7px 10px"><span style="color:'+heatCol(r.pers,'pers',false)+';font-weight:'+heatW(r.pers,'pers',false)+'">'+(r.pers!=null?r.pers.toFixed(1)+'\u20ac':'—')+'</span>'+rb(r.site,'pers')+evo(r.pers,r.persR,false)+'</td>';
    h+='<td style="text-align:center;padding:7px 10px"><span style="color:'+heatCol(r.maint,'maint',false)+';font-weight:'+heatW(r.maint,'maint',false)+'">'+(r.maint!=null?r.maint.toFixed(1)+'\u20ac':'—')+'</span>'+rb(r.site,'maint')+evo(r.maint,r.maintR,false)+'</td>';
    h+='</tr>';
  });
  h+='</tbody></table></div>';
  document.getElementById('tk-table-wrap').innerHTML=h;
}

function renderTk(){
  var m=getTkMerged();
  var sites=Array.from(new Set(m.map(function(d){return d.site;}))).sort();
  var sel=document.getElementById('tk-site-sel');
  if(!sel.options.length){ sites.forEach(function(s){var o=document.createElement('option');o.value=s;o.text=s;sel.appendChild(o);}); }
  if(!tkSite) tkSite=sites[0];
  sel.value=tkSite;
  renderTkSiteDetail();
  renderTkCorr();
  renderTkScatter();
  renderTkTable();
}

// ══════════════════════════════════════════════════════
// ONGLET Q1 2026 — renderQ1() / renderQ1Site()
// Comparaison Réel Q1 2026 vs Budget Q1 2026.
// Vue globale : 5 scorecards parc (CA, PNE, Marge, EBITDA, EBIT) + 2 graphes
//   barres horizontales par site (EBITDA écart, CA écart) colorés vert/rouge.
// Vue par site : 5 scorecards + 2 graphes (synthèse financière + charges).
// Convention couleur : vert = au-dessus du budget, rouge = en dessous.
// ══════════════════════════════════════════════════════
var q1Site = null;

// ── Helpers Q1 ────────────────────────────────────────────────────────────────
function q1Get(site, met, col){
  var r = Q1_DATA.find(function(d){return d.Site===site && d.Metrique===met;});
  return (r && r[col]!=null) ? +r[col] : null;
}
function q1Sum(met, col){
  return Q1_DATA.filter(function(d){return d.Metrique===met;})
    .reduce(function(s,d){return s+(d[col]!=null?+d[col]:0);},0);
}

// ── Scorecards (parc ou site) ─────────────────────────────────────────────────
function q1RenderCards(containerId, getVal){
  var mets = [
    {key:'CA',label:'CA'},{key:'PNE',label:'PNE'},
    {key:'Marge_brute',label:'Marge brute'},
    {key:'EBITDA',label:'EBITDA'},{key:'EBIT',label:'EBIT'},
  ];
  var wrap = document.getElementById(containerId);
  wrap.innerHTML = '';
  mets.forEach(function(m){
    var r26=getVal(m.key,'R2026'), b26=getVal(m.key,'B2026');
    var ecart=(r26!=null&&b26!=null)?r26-b26:null;
    var isGood=ecart!=null&&ecart>=0;
    var cls=ecart==null?'neutral':(isGood?'green':'red');
    var pct=(b26&&b26!==0)?((r26/b26-1)*100):null;
    var fillW=pct!=null?Math.min(Math.max((r26/b26*100),0),140):0;
    var ecartStr=ecart!=null
      ?'<span class="e-amt">'+(ecart>=0?'+':'')+(ecart/1e6).toFixed(2).replace('.',',')+'\u00a0M\u20ac</span>'
       +'<span class="e-pct">'+(pct!=null?(pct>=0?'+':'')+pct.toFixed(1)+'%':'')+'</span>'
      :'\u2014';
    var card=document.createElement('div');
    card.className='q1-sc '+cls;
    card.innerHTML=
      '<div class="q1-sc-label">'+m.label+'</div>'+
      '<div class="q1-sc-val">'+(r26!=null?fmtM(r26):'\u2014')+'</div>'+
      '<div class="q1-sc-bud">Budget\u00a0: '+(b26!=null?fmtM(b26):'\u2014')+'</div>'+
      '<div class="q1-sc-ecart '+(ecart==null?'':isGood?'pos':'neg')+'">'+
        (ecart==null?'\u2014':(isGood?'\u25b2\u00a0':'\u25bc\u00a0')+ecartStr)+'</div>'+
      '<div class="q1-prog"><div class="q1-prog-fill '+(isGood?'green':'red')+
        '" style="width:'+Math.min(fillW,100)+'%"></div></div>';
    wrap.appendChild(card);
  });
}

// ── Accordion : 5 métriques P&L, chacune expandable en vue site par site ──────
function q1RenderAccordion(){
  var mets=[
    {key:'CA',label:'CA'},{key:'PNE',label:'PNE'},
    {key:'Marge_brute',label:'Marge brute'},
    {key:'EBITDA',label:'EBITDA'},{key:'EBIT',label:'EBIT'},
  ];
  var sites=[...new Set(Q1_DATA.map(function(d){return d.Site;}))].sort();
  var wrap=document.getElementById('q1-accordion');
  wrap.innerHTML='';

  mets.forEach(function(m,idx){
    var r26=q1Sum(m.key,'R2026'), b26=q1Sum(m.key,'B2026');
    var ecart=r26-b26;
    var pct=(b26&&b26!==0)?((ecart/Math.abs(b26))*100):null;
    var isGood=ecart>=0;
    var col=isGood?'#10b981':'#ef4444';
    var fillW=b26?Math.min(Math.max(r26/b26*100,0),130):0;
    var ecartStr=(ecart>=0?'+':'')+(ecart/1e3).toFixed(0)+'\u00a0k\u20ac'
      +(pct!=null?' ('+(pct>=0?'+':'')+pct.toFixed(1)+'%)':'');

    var item=document.createElement('div');
    item.className='q1-acc-item';

    var hdr=document.createElement('div');
    hdr.className='q1-acc-hdr';
    hdr.innerHTML=
      '<div class="q1-acc-met">'+m.label+'</div>'+
      '<div class="q1-acc-r26">'+fmtM(r26)+'</div>'+
      '<div class="q1-acc-bud">Budget\u00a0: '+fmtM(b26)+'</div>'+
      '<div class="q1-acc-bar"><div class="q1-acc-bar-fill" style="width:'+Math.min(fillW,100)+'%;background:'+col+'"></div></div>'+
      '<div class="q1-acc-ecart '+(isGood?'pos':'neg')+'">'+(isGood?'\u25b2':'\u25bc')+'\u00a0'+ecartStr+'</div>'+
      '<div class="q1-acc-chev'+(idx===0?' open':'')+'">&#9660;</div>';

    var body=document.createElement('div');
    body.className='q1-acc-body'+(idx===0?' open':'');

    // Barres par site, triées par écart desc
    var sData=sites.map(function(s){
      var r=q1Get(s,m.key,'R2026'),b=q1Get(s,m.key,'B2026');
      return {site:s,r26:r,b26:b,ecart:(r!=null&&b!=null?r-b:null)};
    }).sort(function(a,b){
      if(a.ecart==null)return 1; if(b.ecart==null)return -1;
      return b.ecart-a.ecart;
    });
    var maxA=Math.max.apply(null,sData.map(function(d){return d.ecart!=null?Math.abs(d.ecart):0;}));
    if(!maxA)maxA=1;
    var bHtml='';
    sData.forEach(function(d){
      var iG=d.ecart!=null&&d.ecart>=0;
      var c=d.ecart==null?'#94a3b8':(iG?'#10b981':'#ef4444');
      var bW=d.ecart!=null?Math.round(Math.abs(d.ecart)/maxA*100):0;
      var p=(d.b26&&d.b26!==0)?((d.r26/d.b26-1)*100).toFixed(1):null;
      var sg=d.ecart!=null&&d.ecart>=0?'+':'';
      var vS=d.ecart!=null?sg+(d.ecart/1e3).toFixed(0)+'k\u20ac'+(p?' ('+sg+p+'%)':''):'\u2014';
      bHtml+='<div class="q1-site-bar">'+
        '<div class="q1-site-bar-lbl">'+d.site+'</div>'+
        '<div class="q1-site-bar-track"><div class="q1-site-bar-fill" style="width:'+bW+'%;background:'+c+'">'+
          (bW>22?vS:'')+'</div></div>'+
        (bW<=22?'<div class="q1-site-bar-val" style="color:'+c+'">'+vS+'</div>':'')+
        '</div>';
    });
    body.innerHTML=bHtml;

    hdr.addEventListener('click',function(){
      var open=body.classList.contains('open');
      body.classList.toggle('open',!open);
      hdr.querySelector('.q1-acc-chev').classList.toggle('open',!open);
    });
    item.appendChild(hdr);
    item.appendChild(body);
    wrap.appendChild(item);
  });
}

// ── Bullet charts (vue par site) ──────────────────────────────────────────────
// Chaque ligne : barre grise = budget, barre colorée = réel, trait vertical = jalon budget
// ── Vue par site : même style de barres HTML que l'accordion ─────────────────
function renderQ1Site(){
  var site=q1Site;
  q1RenderCards('q1-site-cards',function(met,col){return q1Get(site,met,col);});

  document.getElementById('q1-site-fin-title').textContent=
    site+' \u2014 Synth\u00e8se financi\u00e8re \u2014 R\u00e9el vs Budget Q1 2026';
  document.getElementById('q1-site-chg-title').textContent=
    site+' \u2014 Charges d\u00e9taill\u00e9es \u2014 R\u00e9el vs Budget Q1 2026';

  var finMet=[
    ['CA','CA'],['PNE','PNE'],['Marge_brute','Marge brute'],['EBITDA','EBITDA'],['EBIT','EBIT']
  ];
  var chgMet=[
    ['Personnel','Personnel'],['Energie','\u00c9nergie'],
    ['Maint_courante','Maint. courante'],['Maint_oblig','Maint. oblig.'],
    ['Traitement_sp','Trait. s.-p.'],['Autres_couts','Autres co\u00fbts']
  ];

  // Réutilise le même rendu que l'accordion mais pour un seul site
  function renderSiteSectionBars(containerId, metrics, isCharges){
    // écart : pour charges, économies = |budget| - |réel| ; pour financier : réel - budget
    var ecarts=metrics.map(function(m){
      var r=q1Get(site,m[0],'R2026'), b=q1Get(site,m[0],'B2026');
      if(r==null||b==null) return null;
      return isCharges ? Math.abs(b)-Math.abs(r) : r-b;
    });
    var maxA=Math.max.apply(null,ecarts.map(function(v){return v!=null?Math.abs(v):0;}));
    if(!maxA) maxA=1;
    var html='';
    metrics.forEach(function(m,i){
      var r=q1Get(site,m[0],'R2026'), b=q1Get(site,m[0],'B2026');
      var ecart=ecarts[i];
      var isGood=ecart!=null&&ecart>=0;
      var col=ecart==null?'#94a3b8':(isGood?'#10b981':'#ef4444');
      var bW=ecart!=null?Math.round(Math.abs(ecart)/maxA*100):0;
      var pct=(b&&b!==0)?(isCharges?(Math.abs(b)-Math.abs(r))/Math.abs(b)*100:(r-b)/Math.abs(b)*100):null;
      var sg=ecart!=null&&ecart>=0?'+':'';
      var vS=ecart!=null
        ?sg+(ecart/1e3).toFixed(0)+'k\u20ac'+(pct!=null?' ('+(pct>=0?'+':'')+pct.toFixed(1)+'%)':'')
        :'\u2014';
      // Ligne : label | réel | budget | barre | écart
      html+='<div class="q1-acc-hdr" style="cursor:default;padding:10px 10px">'+
        '<div class="q1-acc-met">'+m[1]+'</div>'+
        '<div class="q1-acc-r26">'+(r!=null?fmtM(isCharges?Math.abs(r):r):'\u2014')+'</div>'+
        '<div class="q1-acc-bud">Budget\u00a0: '+(b!=null?fmtM(isCharges?Math.abs(b):b):'\u2014')+'</div>'+
        '<div class="q1-acc-bar"><div class="q1-acc-bar-fill" style="width:'+bW+'%;background:'+col+'"></div></div>'+
        '<div class="q1-acc-ecart '+(ecart==null?'':isGood?'pos':'neg')+'">'+(ecart==null?'\u2014':(isGood?'\u25b2\u00a0':'\u25bc\u00a0')+vS)+'</div>'+
        '</div>';
    });
    document.getElementById(containerId).innerHTML=html;
  }

  renderSiteSectionBars('q1-site-fin-rows', finMet, false);
  renderSiteSectionBars('q1-site-chg-rows', chgMet, true);
}

// ── Rendu principal onglet Q1 ─────────────────────────────────────────────────
function renderQ1(){
  var sites=[...new Set(Q1_DATA.map(function(d){return d.Site;}))].sort();
  q1RenderCards('q1-global-cards',function(met,col){return q1Sum(met,col);});
  q1RenderAccordion();
  if(!q1Site)q1Site=sites[0];
  var sel=document.getElementById('q1-site-sel');
  if(!sel.options.length){
    sites.forEach(function(s){var o=document.createElement('option');o.value=s;o.text=s;sel.appendChild(o);});
  }
  sel.value=q1Site;
  renderQ1Site();
}

function q1SetSite(s){q1Site=s;renderQ1Site();}

// ══════════════════════════════════════════════════════
// INITIALISATION — exécutée une seule fois au chargement de la page
// Peuple dynamiquement les listes déroulantes et boutons-sites de chaque onglet
// à partir de la constante SITES (déduite des données).
// Lance renderHome() après deux frames pour laisser le DOM se stabiliser.
// Configure aussi les événements beforeprint/afterprint pour le PDF.
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
      else if(id==='tk') renderTk();
      else if(id==='q1') renderQ1();
    }); });
  });
})();
</script>
</body>
</html>
"""

# ── Injection des placeholders ───────────────────────────────────────────────
# Chaque %%PLACEHOLDER%% dans le template HTML est remplacé par la valeur
# Python correspondante. L'ordre n'a pas d'importance.
html_out = (HTML
    .replace("%%CHARTJS%%", CHARTJS)   # librairie Chart.js (inline ou CDN)
    .replace("%%DATE%%",    GENERATED) # date/heure de génération
    .replace("%%LOGO%%",    LOGO_B64)  # logo base64
    .replace("%%DATA%%",    DATA_JSON) # données P&L (data_synthese.csv)
    .replace("%%EURT%%",    EUR_T_JSON)# charges €/t détaillées (data_synthese_eur_t.csv)
    .replace("%%KPI%%",     KPI_JSON)  # KPIs techniques (data_kpi_techniques.csv)
    .replace("%%Q1_DATA%%", Q1_JSON)   # comptes réels Q1 2026 (data_q1_2026.csv)
)

# ── Écriture du fichier final ─────────────────────────────────────────────────
# UTF-8 sans BOM — compatible avec tous les navigateurs modernes.
out_path = os.path.join(BASE, "dashboard.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"[OK] dashboard.html ({os.path.getsize(out_path)//1024} Ko) - {GENERATED}")
