#!/usr/bin/env python3
"""
CISA KEV Browser — Data Updater
================================
Run this script to fetch the latest CISA KEV data and rebuild
the standalone HTML file with fresh embedded data.

Usage:
    python3 build.py

Requirements:
    Python 3.7+  (no third-party packages needed)

The script produces:  cisa-kev-browser.html
Open that file in any browser — no server or internet needed.
"""

import json
import urllib.request
import urllib.error
import sys
import os
from datetime import datetime

CISA_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
OUT_FILE  = os.path.join(os.path.dirname(__file__), "cisa-kev-browser.html")

# ── HTML template (everything except the data) ─────────────────────────────
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>CISA KEV Browser — Known Exploited Vulnerabilities</title>
<meta name="description" content="Browse and search the CISA Known Exploited Vulnerabilities catalog. Standalone — no server required." />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300..700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
<style>
/* ── TOKENS ─────────────────────────────────────────────────────── */
:root,[data-theme=light]{
  --bg:#f0f2f5;--surface:#fff;--surface2:#f8f9fb;--surface-off:#e8ecf0;
  --border:#d0d5dd;--divider:#e1e5ea;
  --text:#0f172a;--text-m:#64748b;--text-f:#94a3b8;--text-inv:#f8fafc;
  --primary:#1d4ed8;--primary-h:#1e40af;--primary-hi:#dbeafe;
  --danger:#dc2626;--danger-bg:#fef2f2;--danger-b:#fecaca;
  --warn:#d97706;--warn-bg:#fffbeb;--warn-b:#fde68a;
  --success:#16a34a;--code:#0369a1;--code-bg:#f0f9ff;
  --r-sm:.375rem;--r-md:.5rem;--r-lg:.75rem;--r-xl:1rem;--r-full:9999px;
  --sh-sm:0 1px 3px rgba(15,23,42,.06);--sh-md:0 4px 12px rgba(15,23,42,.08);
  --sh-lg:0 12px 32px rgba(15,23,42,.12);
  --tr:160ms cubic-bezier(.16,1,.3,1);
  --xs:clamp(.75rem,.7rem + .2vw,.8125rem);
  --sm:clamp(.8125rem,.775rem + .25vw,.875rem);
  --base:clamp(.875rem,.825rem + .25vw,.9375rem);
  --lg:clamp(1rem,.95rem + .35vw,1.125rem);
  --xl:clamp(1.25rem,1.1rem + .5vw,1.5rem);
  --font:'Geist','Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  --mono:'JetBrains Mono','Fira Code',monospace;
}
[data-theme=dark]{
  --bg:#0b0f18;--surface:#111827;--surface2:#1a2234;--surface-off:#131c2e;
  --border:#1e2d45;--divider:#1a2642;
  --text:#e2e8f0;--text-m:#94a3b8;--text-f:#475569;--text-inv:#0f172a;
  --primary:#60a5fa;--primary-h:#93c5fd;--primary-hi:#1e3a5f;
  --danger:#f87171;--danger-bg:#200a0a;--danger-b:#7f1d1d;
  --warn:#fbbf24;--warn-bg:#1c1300;--warn-b:#78350f;
  --success:#4ade80;--code:#38bdf8;--code-bg:#0c1929;
  --sh-sm:0 1px 3px rgba(0,0,0,.3);--sh-md:0 4px 12px rgba(0,0,0,.4);
  --sh-lg:0 12px 32px rgba(0,0,0,.5);
}
@media(prefers-color-scheme:light){:root:not([data-theme]){
  --bg:#f0f2f5;--surface:#fff;--surface2:#f8f9fb;--surface-off:#e8ecf0;
  --border:#d0d5dd;--divider:#e1e5ea;
  --text:#0f172a;--text-m:#64748b;--text-f:#94a3b8;
  --primary:#1d4ed8;--primary-h:#1e40af;--primary-hi:#dbeafe;
  --danger:#dc2626;--danger-bg:#fef2f2;--danger-b:#fecaca;
  --warn:#d97706;--warn-bg:#fffbeb;--warn-b:#fde68a;
  --code:#0369a1;--code-bg:#f0f9ff;
}}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
body{min-height:100dvh;font-family:var(--font);font-size:var(--base);color:var(--text);
  background:var(--bg);line-height:1.6;transition:background .2s,color .2s}
a{color:var(--primary);text-decoration:none}
a:hover{color:var(--primary-h);text-decoration:underline}
button{cursor:pointer;background:none;border:none;font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--primary);outline-offset:3px;border-radius:var(--r-sm)}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--text-f)}
input,select{font:inherit;color:inherit}
.app{display:flex;flex-direction:column;min-height:100dvh}
/* HEADER */
.hdr{background:var(--surface);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:50;box-shadow:var(--sh-sm)}
.hdr-inner{max-width:1600px;margin:0 auto;padding:0 1.5rem;height:56px;
  display:flex;align-items:center;justify-content:space-between;gap:1rem}
.brand{display:flex;align-items:center;gap:.75rem}
.logo{width:32px;height:32px;flex-shrink:0;color:var(--primary)}
.brand-text{display:flex;flex-direction:column;line-height:1.2}
.brand-title{font-size:var(--lg);font-weight:700;letter-spacing:-.02em}
.brand-sub{font-size:var(--xs);color:var(--text-m);font-family:var(--mono)}
.hdr-right{display:flex;align-items:center;gap:.5rem}
.meta-pill{font-size:var(--xs);font-family:var(--mono);color:var(--text-f);
  background:var(--surface-off);border:1px solid var(--border);
  padding:.2rem .6rem;border-radius:var(--r-full);white-space:nowrap}
.icon-btn{display:flex;align-items:center;justify-content:center;
  width:32px;height:32px;border-radius:var(--r-md);color:var(--text-m);
  transition:color var(--tr),background var(--tr)}
.icon-btn:hover{color:var(--text);background:var(--surface-off)}
/* STATS */
.stats{background:var(--surface2);border-bottom:1px solid var(--border)}
.stats-inner{max-width:1600px;margin:0 auto;padding:.75rem 1.5rem;
  display:flex;gap:1.5rem;flex-wrap:wrap}
.stat{display:flex;flex-direction:column;gap:.1rem;min-width:80px}
.stat-val{font-size:var(--lg);font-weight:700;font-family:var(--mono);
  letter-spacing:-.02em;line-height:1}
.stat-lbl{font-size:var(--xs);color:var(--text-m);text-transform:uppercase;
  letter-spacing:.04em;font-weight:500}
.stat-danger .stat-val{color:var(--danger)}
.stat-warn .stat-val{color:var(--warn)}
.stat-new .stat-val{color:var(--success)}
.stat-val-sm{font-size:var(--sm) !important;font-family:var(--mono);letter-spacing:0 !important}
/* FILTERS */
.filters{background:var(--surface);border-bottom:1px solid var(--border);
  padding:.875rem 1.5rem;max-width:1600px;width:100%;margin:0 auto}
.filter-row{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}
.search-wrap{position:relative;flex:1;min-width:240px;max-width:600px}
.search-icon{position:absolute;left:.75rem;top:50%;transform:translateY(-50%);
  color:var(--text-m);pointer-events:none;z-index:1}
.search-icon svg{display:block}
.search-inp{width:100%;padding:.5rem .75rem .5rem 2.25rem;font-size:var(--sm);height:36px;
  background:var(--surface2);border:1px solid var(--border);border-radius:var(--r-md);
  color:var(--text);transition:border-color var(--tr)}
.search-inp:focus{outline:none;border-color:var(--primary)}
.search-inp::placeholder{color:var(--text-f)}
.search-clear{position:absolute;right:.5rem;top:50%;transform:translateY(-50%);
  color:var(--text-m);padding:.2rem;border-radius:var(--r-sm);
  display:none;align-items:center;justify-content:center}
.search-clear:hover{color:var(--text);background:var(--surface-off)}
.search-clear.visible{display:flex}
.filter-toggle{display:flex;align-items:center;gap:.4rem;
  padding:0 .875rem;height:36px;border-radius:var(--r-md);
  border:1px solid var(--border);font-size:var(--sm);font-weight:500;
  color:var(--text-m);background:var(--surface2);
  transition:all var(--tr);white-space:nowrap}
.filter-toggle:hover,.filter-toggle.active{color:var(--primary);
  border-color:var(--primary);background:var(--primary-hi)}
.export-btn,.refresh-data-btn{display:flex;align-items:center;gap:.4rem;
  padding:0 .875rem;height:36px;border-radius:var(--r-md);
  border:1px solid var(--border);font-size:var(--sm);font-weight:500;
  color:var(--text-m);background:var(--surface2);
  transition:all var(--tr);white-space:nowrap}
.export-btn:hover,.refresh-data-btn:hover{color:var(--primary);
  border-color:var(--primary);background:var(--primary-hi)}
.export-btn:disabled{opacity:.4;pointer-events:none}
.refresh-data-btn{color:var(--success);border-color:color-mix(in srgb,var(--success) 40%,transparent)}
.refresh-data-btn:hover{color:var(--success);border-color:var(--success);
  background:color-mix(in srgb,var(--success) 10%,transparent)}
.adv-filters{display:none;flex-wrap:wrap;gap:1rem;
  margin-top:.875rem;padding-top:.875rem;
  border-top:1px solid var(--divider);align-items:flex-end}
.adv-filters.open{display:flex}
.fg{display:flex;flex-direction:column;gap:.3rem;min-width:140px}
.fg-lbl{font-size:var(--xs);font-weight:600;color:var(--text-m);
  text-transform:uppercase;letter-spacing:.05em}
.fg-sel,.fg-date{height:34px;font-size:var(--sm);padding:0 .625rem;
  background:var(--surface2);border:1px solid var(--border);
  border-radius:var(--r-md);color:var(--text);transition:border-color var(--tr)}
.fg-sel:focus,.fg-date:focus{outline:none;border-color:var(--primary)}
.fg-sel{padding-right:1.75rem;appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right .5rem center}
.clear-all-btn{display:flex;align-items:center;gap:.3rem;
  padding:0 .75rem;height:34px;border-radius:var(--r-md);
  border:1px solid var(--border);font-size:var(--sm);
  color:var(--text-m);background:var(--surface2);transition:all var(--tr)}
.clear-all-btn:hover{color:var(--danger);border-color:var(--danger)}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.625rem}
.chip{display:inline-flex;align-items:center;gap:.3rem;font-size:var(--xs);
  font-weight:500;color:var(--primary);background:var(--primary-hi);
  border:1px solid color-mix(in srgb,var(--primary) 30%,transparent);
  border-radius:var(--r-full);padding:.2rem .5rem .2rem .625rem}
.chip button{display:flex;align-items:center;opacity:.7;transition:opacity var(--tr)}
.chip button:hover{opacity:1}
/* TABLE */
.table-area{flex:1;max-width:1600px;width:100%;margin:0 auto;padding:1rem 1.5rem}
.table-scroll{overflow-x:auto;border:1px solid var(--border);
  border-radius:var(--r-lg);box-shadow:var(--sh-sm);background:var(--surface)}
table{width:100%;border-collapse:collapse;font-size:var(--sm)}
thead{background:var(--surface-off);position:sticky;top:0;z-index:10}
th{padding:.625rem .875rem;text-align:left;font-size:var(--xs);
  font-weight:600;color:var(--text-m);text-transform:uppercase;
  letter-spacing:.05em;border-bottom:1px solid var(--border);white-space:nowrap}
.th-sort{cursor:pointer;user-select:none}
.th-sort:hover{color:var(--text);background:var(--surface2)}
.sort-ico{opacity:.35;vertical-align:middle;margin-left:.3rem;font-style:normal;font-size:.75em}
.sort-ico.on{opacity:1;color:var(--primary)}
td{padding:.6rem .875rem;border-bottom:1px solid var(--divider);vertical-align:middle}
tr:hover td{background:var(--surface2)}
tr:last-child td{border-bottom:none}
tr.overdue-row td{background:color-mix(in srgb,var(--danger-bg) 60%,transparent)}
tr.overdue-row:hover td{background:var(--danger-bg)}
.td-cve{width:150px}
.cve-id{font-family:var(--mono);font-size:var(--xs);font-weight:600;
  color:var(--primary);cursor:pointer;transition:color var(--tr)}
.cve-id:hover{color:var(--primary-h);text-decoration:underline}
.td-vendor{width:130px;font-weight:500;max-width:130px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.td-product{width:140px;max-width:140px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.td-name{max-width:300px}
.vuln-name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;line-height:1.4}
.td-date{white-space:nowrap;font-family:var(--mono);font-size:var(--xs);color:var(--text-m)}
.due-wrap{display:flex;flex-direction:column;gap:.1rem}
.due-tag{font-size:var(--xs);font-weight:600}
.due-tag.overdue{color:var(--danger)}
.due-tag.soon{color:var(--warn)}
.td-ransom{white-space:nowrap}
.badge{display:inline-flex;align-items:center;gap:.2rem;font-size:var(--xs);
  font-weight:600;padding:.15rem .5rem;border-radius:var(--r-full);border:1px solid transparent}
.badge-ransom{color:var(--danger);
  background:color-mix(in srgb,var(--danger) 12%,transparent);
  border-color:color-mix(in srgb,var(--danger) 30%,transparent)}
.badge-unknown{color:var(--text-f);background:var(--surface-off);border-color:var(--border)}
.td-cwe{min-width:90px}
.cwe-badges{display:flex;flex-wrap:wrap;gap:.3rem}
.cwe-tag{display:inline-flex;align-items:center;font-family:var(--mono);
  font-size:var(--xs);font-weight:600;color:var(--code);
  background:var(--code-bg);
  border:1px solid color-mix(in srgb,var(--code) 25%,transparent);
  border-radius:var(--r-sm);padding:.1rem .4rem;
  text-decoration:none;transition:all var(--tr)}
.cwe-tag:hover{text-decoration:underline}
.faint{color:var(--text-f)}
.td-action{width:40px;text-align:center}
.detail-btn{display:flex;align-items:center;justify-content:center;
  width:28px;height:28px;border-radius:var(--r-sm);
  color:var(--text-f);transition:all var(--tr)}
.detail-btn:hover{color:var(--primary);background:var(--primary-hi)}
.no-results{text-align:center;padding:4rem 2rem;color:var(--text-m)}
.no-results svg{margin:0 auto 1rem;opacity:.4}
/* PAGINATION */
.pagination{display:flex;align-items:center;justify-content:space-between;
  padding:.875rem 0;flex-wrap:wrap;gap:.5rem}
.page-info{font-size:var(--sm);color:var(--text-m);font-family:var(--mono)}
.page-ctrls{display:flex;align-items:center;gap:.4rem}
.page-btn{padding:0 .625rem;height:30px;border-radius:var(--r-md);
  border:1px solid var(--border);font-size:var(--sm);
  color:var(--text-m);background:var(--surface2);transition:all var(--tr)}
.page-btn:hover:not(:disabled){color:var(--primary);border-color:var(--primary)}
.page-btn:disabled{opacity:.35;pointer-events:none}
.page-num{font-size:var(--sm);color:var(--text-m);padding:0 .5rem;white-space:nowrap}
/* MODAL */
.modal-bg{display:none;position:fixed;inset:0;z-index:100;
  background:rgba(0,0,0,.6);backdrop-filter:blur(4px);
  align-items:flex-start;justify-content:center;padding:2rem 1rem;overflow-y:auto}
.modal-bg.open{display:flex}
.modal{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r-xl);width:100%;max-width:780px;
  box-shadow:var(--sh-lg);position:relative;margin:auto}
.modal-inner{padding:2rem}
.modal-close{position:absolute;top:1rem;right:1rem;
  display:flex;align-items:center;justify-content:center;
  width:32px;height:32px;border-radius:var(--r-md);
  color:var(--text-m);transition:all var(--tr)}
.modal-close:hover{color:var(--text);background:var(--surface-off)}
.modal-cve-row{display:flex;flex-wrap:wrap;align-items:center;gap:.75rem;margin-bottom:.75rem}
.modal-cve-id{font-family:var(--mono);font-size:var(--lg);font-weight:700;
  color:var(--primary);letter-spacing:-.01em}
.modal-title{font-size:var(--xl);font-weight:700;line-height:1.3;
  letter-spacing:-.02em;margin-bottom:1.5rem}
.meta-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
  gap:1.25rem;margin-bottom:1.5rem}
.meta-item{display:flex;flex-direction:column;gap:.25rem}
.meta-lbl{font-size:var(--xs);font-weight:600;color:var(--text-m);
  text-transform:uppercase;letter-spacing:.05em}
.meta-val{font-size:var(--sm);font-weight:500;display:flex;
  align-items:center;gap:.35rem;flex-wrap:wrap}
.meta-overdue{color:var(--danger)}
.meta-danger{color:var(--danger);font-weight:600}
.overdue-pill{font-size:var(--xs);font-weight:600;color:var(--danger);
  background:var(--danger-bg);border:1px solid var(--danger-b);
  padding:.1rem .4rem;border-radius:var(--r-full)}
.modal-hr{border:none;border-top:1px solid var(--divider);margin:1.5rem 0}
.sec-title{font-size:var(--base);font-weight:700;margin-bottom:.625rem;letter-spacing:-.01em}
.sec-body{font-size:var(--sm);color:var(--text-m);line-height:1.75}
.action-box{background:var(--surface2);border:1px solid var(--border);
  border-left:3px solid var(--primary);border-radius:var(--r-md);
  padding:.875rem 1rem;margin-bottom:1.5rem}
.action-box.overdue{border-left-color:var(--danger);
  background:var(--danger-bg);border-color:var(--danger-b)}
.action-box p{font-size:var(--sm);color:var(--text-m);line-height:1.75}
.ref-links{display:flex;flex-wrap:wrap;gap:.5rem}
.ref-link{display:inline-flex;align-items:center;gap:.35rem;font-size:var(--sm);
  font-weight:500;padding:.4rem .75rem;border-radius:var(--r-md);
  border:1px solid var(--border);background:var(--surface2);
  color:var(--text-m);transition:all var(--tr);text-decoration:none}
.ref-link:hover{color:var(--primary);border-color:var(--primary);background:var(--primary-hi)}
.ref-link.nvd{color:var(--code);border-color:color-mix(in srgb,var(--code) 30%,transparent);
  background:var(--code-bg)}
.ref-link.cisa{color:var(--primary);border-color:color-mix(in srgb,var(--primary) 30%,transparent);
  background:var(--primary-hi)}
.notes-box{font-size:var(--xs);font-family:var(--mono);color:var(--text-m);
  background:var(--surface-off);border:1px solid var(--border);
  border-radius:var(--r-md);padding:.75rem 1rem;line-height:1.7;
  word-break:break-word;margin-top:.625rem}
.badge-overdue{color:var(--danger);
  background:color-mix(in srgb,var(--danger) 12%,transparent);
  border-color:color-mix(in srgb,var(--danger) 30%,transparent)}
.modal-nav{display:flex;justify-content:space-between;gap:1rem;margin-top:1.5rem}
.mnav-btn{display:flex;align-items:center;gap:.5rem;padding:.5rem .875rem;
  border:1px solid var(--border);border-radius:var(--r-lg);
  background:var(--surface);color:var(--text-m);font-size:var(--sm);
  transition:all var(--tr)}
.mnav-btn:hover{color:var(--primary);border-color:var(--primary);background:var(--primary-hi)}
.mnav-text{display:flex;flex-direction:column;line-height:1.2}
.mnav-text.right{text-align:right}
.mnav-lbl{font-size:var(--xs);color:var(--text-f)}
.mnav-cve{font-family:var(--mono);font-size:var(--xs);font-weight:600}
/* DATA-AGE BANNER */
.data-banner{background:color-mix(in srgb,var(--warn) 12%,transparent);
  border-bottom:1px solid color-mix(in srgb,var(--warn) 30%,transparent);
  padding:.5rem 1.5rem;text-align:center;font-size:var(--xs);color:var(--warn);
  display:flex;align-items:center;justify-content:center;gap:.75rem}
.data-banner a{color:var(--warn);font-weight:600;text-decoration:underline}
.data-banner.hidden{display:none}
footer{background:var(--surface);border-top:1px solid var(--border);
  padding:1rem 1.5rem;text-align:center;font-size:var(--xs);color:var(--text-f)}
footer a{color:var(--primary)}
@media(max-width:768px){
  .hdr-inner{padding:0 1rem}
  .brand-sub,.meta-pill{display:none}
  .filters{padding:.75rem 1rem}
  .table-area{padding:.75rem 1rem}
  .modal-inner{padding:1.25rem}
  .modal-title{font-size:var(--lg)}
}
</style>
</head>
<body>
<div class="app">
  <!-- HEADER -->
  <header class="hdr">
    <div class="hdr-inner">
      <div class="brand">
        <svg class="logo" aria-label="KEV Browser" viewBox="0 0 36 36" fill="none">
          <rect width="36" height="36" rx="8" fill="currentColor"/>
          <path d="M18 6L30 12V20C30 26.6 24.8 31.8 18 33C11.2 31.8 6 26.6 6 20V12L18 6Z"
            fill="none" stroke="var(--bg)" stroke-width="2" stroke-linejoin="round"/>
          <path d="M13 18L16.5 21.5L23 15" stroke="var(--bg)" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="brand-text">
          <span class="brand-title">KEV Browser</span>
          <span class="brand-sub">CISA Known Exploited Vulnerabilities</span>
        </div>
      </div>
      <div class="hdr-right">
        <span class="meta-pill" id="catalog-meta">__CATALOG_META__</span>
        <button class="icon-btn" id="btn-theme" aria-label="Toggle theme">
          <svg id="theme-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
        </button>
      </div>
    </div>
  </header>

  <!-- DATA AGE BANNER (shown if data is >30 days old) -->
  <div class="data-banner hidden" id="data-banner">
    ⚠ Embedded data is <span id="data-age-days"></span> days old.
    Run <code>python3 build.py</code> to refresh, or
    <a href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog" target="_blank" rel="noopener">view the live catalog</a>.
  </div>

  <!-- STATS -->
  <div class="stats">
    <div class="stats-inner">
      <div class="stat"><span class="stat-val" id="s-total">—</span><span class="stat-lbl">Total KEVs</span></div>
      <div class="stat"><span class="stat-val" id="s-match">—</span><span class="stat-lbl">Matching</span></div>
      <div class="stat stat-danger"><span class="stat-val" id="s-ransom">—</span><span class="stat-lbl">Ransomware Known</span></div>
      <div class="stat stat-warn"><span class="stat-val" id="s-overdue">—</span><span class="stat-lbl">Past Due Date</span></div>
      <div class="stat stat-new"><span class="stat-val" id="s-newest-date">—</span><span class="stat-lbl">Latest Entry Date</span></div>
      <div class="stat"><span class="stat-val stat-val-sm" id="s-newest-cve">—</span><span class="stat-lbl">Latest CVE</span></div>
    </div>
  </div>

  <!-- FILTERS -->
  <div class="filters">
    <div class="filter-row">
      <div class="search-wrap">
        <span class="search-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </span>
        <input class="search-inp" id="inp-search" type="search"
          placeholder="Search CVE ID, vendor, product, description, CWE…" autocomplete="off" />
        <button class="search-clear" id="btn-clear-search" aria-label="Clear search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6 6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <button class="filter-toggle" id="btn-toggle-adv">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>
        </svg>
        <span id="filter-toggle-label">Filters</span>
      </button>
      <button class="export-btn" id="btn-export">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Export CSV
      </button>
    </div>
    <!-- Advanced filters -->
    <div class="adv-filters" id="adv-filters">
      <div class="fg">
        <label class="fg-lbl">Vendor / Project</label>
        <select class="fg-sel" id="sel-vendor"><option value="">All vendors</option></select>
      </div>
      <div class="fg">
        <label class="fg-lbl">Ransomware Use</label>
        <select class="fg-sel" id="sel-ransom">
          <option value="">All</option>
          <option value="Known">Known ransomware use</option>
          <option value="Unknown">Unknown</option>
        </select>
      </div>
      <div class="fg">
        <label class="fg-lbl">CWE</label>
        <select class="fg-sel" id="sel-cwe"><option value="">All CWEs</option></select>
      </div>
      <div class="fg">
        <label class="fg-lbl">Date Added From</label>
        <input class="fg-date" id="inp-date-from" type="date" />
      </div>
      <div class="fg">
        <label class="fg-lbl">Date Added To</label>
        <input class="fg-date" id="inp-date-to" type="date" />
      </div>
      <div class="fg" id="clear-all-wrap" style="display:none">
        <label class="fg-lbl">&nbsp;</label>
        <button class="clear-all-btn" id="btn-clear-all">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6 6 18M6 6l12 12"/>
          </svg> Clear all
        </button>
      </div>
    </div>
    <div class="chips" id="chips-row"></div>
  </div>

  <!-- TABLE -->
  <main class="table-area">
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th class="th-sort td-cve" data-col="cveID">CVE ID <i class="sort-ico" id="ico-cveID">↕</i></th>
            <th class="th-sort td-vendor" data-col="vendorProject">Vendor <i class="sort-ico" id="ico-vendorProject">↕</i></th>
            <th class="th-sort td-product" data-col="product">Product <i class="sort-ico" id="ico-product">↕</i></th>
            <th class="td-name">Vulnerability</th>
            <th class="th-sort td-date" data-col="dateAdded">Added <i class="sort-ico" id="ico-dateAdded">↕</i></th>
            <th class="th-sort td-date" data-col="dueDate">Due <i class="sort-ico" id="ico-dueDate">↕</i></th>
            <th class="td-ransom">Ransomware</th>
            <th class="td-cwe">CWE(s)</th>
            <th class="td-action"></th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="pagination">
      <span class="page-info" id="page-info">—</span>
      <div class="page-ctrls">
        <button class="page-btn" id="btn-first">««</button>
        <button class="page-btn" id="btn-prev">‹</button>
        <span class="page-num" id="page-num">—</span>
        <button class="page-btn" id="btn-next">›</button>
        <button class="page-btn" id="btn-last">»»</button>
      </div>
    </div>
  </main>

  <footer>
    Embedded data: <strong>__CATALOG_VERSION__</strong> · Released <strong>__RELEASE_DATE__</strong> ·
    <a href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog" target="_blank" rel="noopener">
      CISA KEV Catalog
    </a> · Run <code>python3 build.py</code> to update
  </footer>
</div>

<!-- MODAL -->
<div class="modal-bg" id="modal-bg" role="dialog" aria-modal="true">
  <div class="modal">
    <button class="modal-close" id="modal-close" aria-label="Close">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6 6 18M6 6l12 12"/>
      </svg>
    </button>
    <div class="modal-inner" id="modal-inner"></div>
  </div>
</div>

<script>
/* ═══════════════════════════════════════════════════════════════
   CISA KEV BROWSER — Standalone Offline Edition
   Data embedded at build time. Run build.py to refresh.
   No server. No internet required. Open in any browser.
═══════════════════════════════════════════════════════════════ */

// ── Embedded data (injected by build.py) ──────────────────────
const CATALOG = __CATALOG_JSON__;

// ── Data-age warning (show if > 30 days old) ──────────────────
(function checkAge() {
  const released = new Date(CATALOG.dateReleased);
  const ageDays = Math.floor((Date.now() - released.getTime()) / 86400000);
  if (ageDays > 30) {
    document.getElementById('data-banner').classList.remove('hidden');
    document.getElementById('data-age-days').textContent = ageDays;
  }
})();

const PAGE_SIZE = 50;
let filtered = [];
let page = 1;
let sortBy = 'dateAdded';
let sortDir = 'desc';
let modalIdx = -1;

const filters = { search:'', vendor:'', ransomware:'', cwe:'', dateFrom:'', dateTo:'' };

const $ = id => document.getElementById(id);
const tbody     = $('tbody');
const chipsRow  = $('chips-row');
const clearWrap = $('clear-all-wrap');
const modalBg   = $('modal-bg');
const modalInner= $('modal-inner');
const advFilter = $('adv-filters');

// ── Theme ──────────────────────────────────────────────────────
(function initTheme() {
  const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  updateThemeIcon(dark);
})();
function updateThemeIcon(isDark) {
  $('theme-icon').innerHTML = isDark
    ? '<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>'
    : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
}
$('btn-theme').addEventListener('click', () => {
  const html = document.documentElement;
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  updateThemeIcon(next === 'dark');
});

// ── Helpers ────────────────────────────────────────────────────
function fmtDate(d) {
  if (!d) return '—';
  const [y,m,day] = d.split('-');
  const M = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${M[+m-1]} ${+day}, ${y}`;
}
function isOverdue(d) { return d && new Date(d) < new Date(); }
function dueDays(d) { return d ? Math.ceil((new Date(d)-Date.now())/86400000) : null; }
function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function nvdHref(cveID) { return `https://nvd.nist.gov/vuln/detail/${cveID}`; }
function refLinks(notes, cveID) {
  if (!notes) return [];
  return [...notes.matchAll(/https?:\/\/[^\s;]+/g)]
    .map(m=>m[0]).filter(u=>u!==nvdHref(cveID));
}

// ── Bootstrap ──────────────────────────────────────────────────
(function init() {
  // Vendors
  const vendors = [...new Set(CATALOG.vulnerabilities.map(v=>v.vendorProject))].sort();
  const vSel = $('sel-vendor');
  vendors.forEach(v => {
    const o = document.createElement('option');
    o.value = v; o.textContent = v; vSel.appendChild(o);
  });
  // CWEs
  const cwes = new Set();
  CATALOG.vulnerabilities.forEach(v=>(v.cwes||[]).forEach(c=>cwes.add(c)));
  const cweSorted = [...cwes].sort((a,b)=>+a.replace('CWE-','')-+b.replace('CWE-',''));
  const cSel = $('sel-cwe');
  cweSorted.forEach(c => {
    const o = document.createElement('option');
    o.value = c; o.textContent = c; cSel.appendChild(o);
  });
  $('s-total').textContent = CATALOG.count.toLocaleString();

  // Show the newest entry prominently in the stats bar
  const newest = CATALOG.vulnerabilities[0]; // already sorted newest-first by build.py
  if (newest) {
    const [y,mo,d] = newest.dateAdded.split('-');
    const M = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    $('s-newest-date').textContent = `${M[+mo-1]} ${+d}, ${y}`;
    $('s-newest-cve').textContent  = newest.cveID;
  }

  applyFilters();
})();

// ── Filter & sort ──────────────────────────────────────────────
function applyFilters() {
  let list = CATALOG.vulnerabilities;
  if (filters.search.trim()) {
    const q = filters.search.toLowerCase();
    list = list.filter(v =>
      v.cveID.toLowerCase().includes(q) ||
      v.vendorProject.toLowerCase().includes(q) ||
      v.product.toLowerCase().includes(q) ||
      v.vulnerabilityName.toLowerCase().includes(q) ||
      v.shortDescription.toLowerCase().includes(q) ||
      (v.cwes||[]).some(c=>c.toLowerCase().includes(q)) ||
      (v.notes||'').toLowerCase().includes(q)
    );
  }
  if (filters.vendor) list = list.filter(v=>v.vendorProject===filters.vendor);
  if (filters.ransomware) list = list.filter(v=>v.knownRansomwareCampaignUse===filters.ransomware);
  if (filters.cwe) list = list.filter(v=>(v.cwes||[]).includes(filters.cwe));
  if (filters.dateFrom) list = list.filter(v=>v.dateAdded>=filters.dateFrom);
  if (filters.dateTo) list = list.filter(v=>v.dateAdded<=filters.dateTo);

  list = [...list].sort((a,b) => {
    const va=a[sortBy]||'', vb=b[sortBy]||'';
    const c = va<vb?-1:va>vb?1:0;
    return sortDir==='asc'?c:-c;
  });
  filtered = list;
  page = 1;

  $('s-match').textContent = filtered.length.toLocaleString();
  $('s-ransom').textContent = filtered.filter(v=>v.knownRansomwareCampaignUse==='Known').length.toLocaleString();
  $('s-overdue').textContent = filtered.filter(v=>isOverdue(v.dueDate)).length.toLocaleString();

  updateSortIcons();
  updateChips();
  renderPage();
}

function updateSortIcons() {
  document.querySelectorAll('.sort-ico').forEach(el=>{el.textContent='↕';el.classList.remove('on')});
  const el = $('ico-'+sortBy);
  if (el) { el.textContent = sortDir==='asc'?'↑':'↓'; el.classList.add('on'); }
}

// ── Render ─────────────────────────────────────────────────────
function renderPage() {
  const total = Math.max(1, Math.ceil(filtered.length/PAGE_SIZE));
  const start = (page-1)*PAGE_SIZE;
  const rows = filtered.slice(start, start+PAGE_SIZE);

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="no-results">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg><p>No vulnerabilities match your filters.</p></td></tr>`;
  } else {
    tbody.innerHTML = rows.map((v,i) => {
      const od = isOverdue(v.dueDate);
      const dd = dueDays(v.dueDate);
      const dueTag = od
        ? `<span class="due-tag overdue">Overdue</span>`
        : (dd!==null&&dd<=14?`<span class="due-tag soon">In ${dd}d</span>`:'');
      const cweBadges = (v.cwes&&v.cwes.length)
        ? v.cwes.map(c=>`<a class="cwe-tag" href="https://cwe.mitre.org/data/definitions/${c.replace('CWE-','')}.html" target="_blank" rel="noopener">${esc(c)}</a>`).join('')
        : `<span class="faint">—</span>`;
      const ransomBadge = v.knownRansomwareCampaignUse==='Known'
        ? `<span class="badge badge-ransom">⚠ Ransomware</span>`
        : `<span class="badge badge-unknown">Unknown</span>`;
      return `<tr class="${od?'overdue-row':''}">
        <td class="td-cve"><span class="cve-id" data-idx="${start+i}">${esc(v.cveID)}</span></td>
        <td class="td-vendor" title="${esc(v.vendorProject)}">${esc(v.vendorProject)}</td>
        <td class="td-product" title="${esc(v.product)}">${esc(v.product)}</td>
        <td class="td-name"><span class="vuln-name" title="${esc(v.vulnerabilityName)}">${esc(v.vulnerabilityName)}</span></td>
        <td class="td-date">${fmtDate(v.dateAdded)}</td>
        <td class="td-date"><div class="due-wrap">${fmtDate(v.dueDate)}${dueTag}</div></td>
        <td class="td-ransom">${ransomBadge}</td>
        <td class="td-cwe"><div class="cwe-badges">${cweBadges}</div></td>
        <td class="td-action"><button class="detail-btn" data-idx="${start+i}" title="View ${esc(v.cveID)}">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
        </button></td>
      </tr>`;
    }).join('');
  }
  const from = filtered.length?start+1:0;
  const to = Math.min(start+PAGE_SIZE,filtered.length);
  $('page-info').textContent = filtered.length
    ? `${from.toLocaleString()}–${to.toLocaleString()} of ${filtered.length.toLocaleString()}`
    : 'No results';
  $('page-num').textContent = `Page ${page} / ${total}`;
  $('btn-first').disabled = page===1;
  $('btn-prev').disabled  = page===1;
  $('btn-next').disabled  = page===total;
  $('btn-last').disabled  = page===total;
}

// ── Chips ──────────────────────────────────────────────────────
function updateChips() {
  const has = filters.search||filters.vendor||filters.ransomware||filters.cwe||filters.dateFrom||filters.dateTo;
  clearWrap.style.display = has?'':'none';
  const toggle = $('btn-toggle-adv');
  toggle.classList.toggle('active', !!has);
  $('filter-toggle-label').textContent = has?'Filters (active)':'Filters';
  const parts = [];
  if (filters.search) parts.push(['search',`Search: "${filters.search}"`]);
  if (filters.vendor) parts.push(['vendor',`Vendor: ${filters.vendor}`]);
  if (filters.ransomware) parts.push(['ransomware',`Ransomware: ${filters.ransomware}`]);
  if (filters.cwe) parts.push(['cwe',`CWE: ${filters.cwe}`]);
  if (filters.dateFrom) parts.push(['dateFrom',`From: ${filters.dateFrom}`]);
  if (filters.dateTo) parts.push(['dateTo',`To: ${filters.dateTo}`]);
  chipsRow.innerHTML = parts.map(([k,l])=>
    `<span class="chip">${esc(l)}<button data-chip="${k}">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 6 6 18M6 6l12 12"/>
      </svg></button></span>`
  ).join('');
}

// ── Modal ──────────────────────────────────────────────────────
function openModal(idx) {
  modalIdx = idx;
  const v = filtered[idx]; if (!v) return;
  const od = isOverdue(v.dueDate);
  const refs = refLinks(v.notes, v.cveID);
  const cwesHtml = (v.cwes&&v.cwes.length)
    ? v.cwes.map(c=>`<a class="cwe-tag" href="https://cwe.mitre.org/data/definitions/${c.replace('CWE-','')}.html" target="_blank" rel="noopener">${esc(c)}</a>`).join('')
    : '<span class="faint">None listed</span>';
  const prevV = filtered[idx-1], nextV = filtered[idx+1];
  const calIcon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;color:var(--text-m)"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
  const extIcon = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;
  modalInner.innerHTML = `
    <div class="modal-cve-row">
      <span class="modal-cve-id">${esc(v.cveID)}</span>
      ${v.knownRansomwareCampaignUse==='Known'?`<span class="badge badge-ransom">⚠ Known Ransomware Use</span>`:''}
      ${od?`<span class="badge badge-overdue">Past Due Date</span>`:''}
    </div>
    <h2 class="modal-title">${esc(v.vulnerabilityName)}</h2>
    <div class="meta-grid">
      <div class="meta-item"><span class="meta-lbl">Vendor / Project</span><span class="meta-val">${esc(v.vendorProject)}</span></div>
      <div class="meta-item"><span class="meta-lbl">Product</span><span class="meta-val">${esc(v.product)}</span></div>
      <div class="meta-item"><span class="meta-lbl">Date Added to KEV</span>
        <span class="meta-val">${calIcon}${fmtDate(v.dateAdded)}</span></div>
      <div class="meta-item"><span class="meta-lbl">Remediation Due Date</span>
        <span class="meta-val ${od?'meta-overdue':''}">${calIcon}${fmtDate(v.dueDate)}
          ${od?`<span class="overdue-pill">Overdue</span>`:''}</span></div>
      <div class="meta-item"><span class="meta-lbl">Ransomware Use</span>
        <span class="meta-val ${v.knownRansomwareCampaignUse==='Known'?'meta-danger':''}">${esc(v.knownRansomwareCampaignUse||'—')}</span></div>
      <div class="meta-item"><span class="meta-lbl">CWE(s)</span>
        <div class="meta-val" style="margin-top:.15rem">${cwesHtml}</div></div>
    </div>
    <hr class="modal-hr"/>
    <div style="margin-bottom:1.5rem">
      <h3 class="sec-title">Description</h3>
      <p class="sec-body">${esc(v.shortDescription)}</p>
    </div>
    <div style="margin-bottom:1.5rem">
      <h3 class="sec-title">Required Action</h3>
      <div class="action-box ${od?'overdue':''}"><p>${esc(v.requiredAction)}</p></div>
    </div>
    <div style="margin-bottom:${v.notes?'1.5rem':'0'}">
      <h3 class="sec-title">References</h3>
      <div class="ref-links">
        <a class="ref-link nvd" href="${esc(nvdHref(v.cveID))}" target="_blank" rel="noopener">${extIcon} NVD — ${esc(v.cveID)}</a>
        <a class="ref-link cisa" href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog" target="_blank" rel="noopener">${extIcon} CISA KEV Catalog</a>
        ${refs.slice(0,5).map(u=>{let l=u;try{l=new URL(u).hostname}catch{}return`<a class="ref-link" href="${esc(u)}" target="_blank" rel="noopener">${extIcon} ${esc(l)}</a>`;}).join('')}
      </div>
    </div>
    ${v.notes?`<div><h3 class="sec-title">Notes</h3><div class="notes-box">${esc(v.notes)}</div></div>`:''}
    <div class="modal-nav">
      ${prevV?`<button class="mnav-btn" id="mnav-prev">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
        <div class="mnav-text"><span class="mnav-lbl">Previous</span><span class="mnav-cve">${esc(prevV.cveID)}</span></div>
      </button>`:'<div></div>'}
      ${nextV?`<button class="mnav-btn" id="mnav-next">
        <div class="mnav-text right"><span class="mnav-lbl">Next</span><span class="mnav-cve">${esc(nextV.cveID)}</span></div>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
      </button>`:'<div></div>'}
    </div>`;
  const pb = $('mnav-prev'), nb = $('mnav-next');
  if (pb) pb.addEventListener('click',()=>openModal(idx-1));
  if (nb) nb.addEventListener('click',()=>openModal(idx+1));
  modalBg.classList.add('open');
  document.body.style.overflow='hidden';
}
function closeModal() {
  modalBg.classList.remove('open');
  document.body.style.overflow='';
  modalIdx=-1;
}

// ── Export CSV ─────────────────────────────────────────────────
function exportCSV() {
  const hdrs = ['CVE ID','Vendor','Product','Vulnerability Name','Date Added','Due Date','Ransomware','CWEs','Short Description','Required Action'];
  const rows = filtered.map(v=>[
    v.cveID,v.vendorProject,v.product,v.vulnerabilityName,
    v.dateAdded,v.dueDate,v.knownRansomwareCampaignUse||'',
    (v.cwes||[]).join('; '),v.shortDescription,v.requiredAction
  ].map(c=>`"${String(c||'').replace(/"/g,'""')}"`).join(','));
  const csv = [hdrs.join(','),...rows].join('\n');
  const a = document.createElement('a');
  const today = new Date().toISOString().split('T')[0];
  a.href = URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download = `cisa-kev-${today}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── Events ─────────────────────────────────────────────────────
$('inp-search').addEventListener('input', e=>{
  filters.search=e.target.value;
  $('btn-clear-search').classList.toggle('visible',!!filters.search);
  applyFilters();
});
$('btn-clear-search').addEventListener('click',()=>{
  $('inp-search').value=''; filters.search='';
  $('btn-clear-search').classList.remove('visible');
  applyFilters();
});
$('btn-toggle-adv').addEventListener('click',()=>advFilter.classList.toggle('open'));
$('sel-vendor').addEventListener('change',e=>{filters.vendor=e.target.value;applyFilters()});
$('sel-ransom').addEventListener('change',e=>{filters.ransomware=e.target.value;applyFilters()});
$('sel-cwe').addEventListener('change',e=>{filters.cwe=e.target.value;applyFilters()});
$('inp-date-from').addEventListener('change',e=>{filters.dateFrom=e.target.value;applyFilters()});
$('inp-date-to').addEventListener('change',e=>{filters.dateTo=e.target.value;applyFilters()});
$('btn-clear-all').addEventListener('click',()=>{
  filters.search=filters.vendor=filters.ransomware=filters.cwe=filters.dateFrom=filters.dateTo='';
  $('inp-search').value=''; $('sel-vendor').value=''; $('sel-ransom').value='';
  $('sel-cwe').value=''; $('inp-date-from').value=''; $('inp-date-to').value='';
  $('btn-clear-search').classList.remove('visible');
  applyFilters();
});
chipsRow.addEventListener('click',e=>{
  const k=e.target.closest('[data-chip]')?.dataset.chip; if(!k) return;
  filters[k]='';
  if(k==='search'){$('inp-search').value='';$('btn-clear-search').classList.remove('visible')}
  if(k==='vendor') $('sel-vendor').value='';
  if(k==='ransomware') $('sel-ransom').value='';
  if(k==='cwe') $('sel-cwe').value='';
  if(k==='dateFrom') $('inp-date-from').value='';
  if(k==='dateTo') $('inp-date-to').value='';
  applyFilters();
});
document.querySelectorAll('.th-sort').forEach(th=>th.addEventListener('click',()=>{
  const col=th.dataset.col;
  if(sortBy===col){sortDir=sortDir==='asc'?'desc':'asc';}
  else{sortBy=col;sortDir=(col==='dateAdded'||col==='dueDate')?'desc':'asc';}
  applyFilters();
}));
tbody.addEventListener('click',e=>{
  const el=e.target.closest('.cve-id')||e.target.closest('.detail-btn');
  if(el){const idx=parseInt(el.dataset.idx);if(!isNaN(idx))openModal(idx);}
});
$('modal-close').addEventListener('click',closeModal);
modalBg.addEventListener('click',e=>{if(e.target===modalBg)closeModal()});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape') closeModal();
  if(modalBg.classList.contains('open')){
    if(e.key==='ArrowLeft'&&modalIdx>0) openModal(modalIdx-1);
    if(e.key==='ArrowRight'&&modalIdx<filtered.length-1) openModal(modalIdx+1);
  }
  if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();$('inp-search').focus();}
});
$('btn-first').addEventListener('click',()=>{page=1;renderPage()});
$('btn-prev').addEventListener('click',()=>{page--;renderPage()});
$('btn-next').addEventListener('click',()=>{page++;renderPage()});
$('btn-last').addEventListener('click',()=>{page=Math.max(1,Math.ceil(filtered.length/PAGE_SIZE));renderPage()});
$('btn-export').addEventListener('click',exportCSV);
</script>
</body>
</html>
"""

def build(kev_data):
    """Inject KEV data into the HTML template and write the output file."""
    released_raw = kev_data.get('dateReleased','')
    released_date = released_raw.split('T')[0] if released_raw else 'Unknown'
    version = kev_data.get('catalogVersion', 'Unknown')
    count = kev_data.get('count', len(kev_data.get('vulnerabilities',[])))

    meta = f"v{version} · {released_date} · {count:,} entries"
    kev_json = json.dumps(kev_data, separators=(',', ':'), ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace('__CATALOG_META__', meta)
    html = html.replace('__CATALOG_VERSION__', f"v{version}")
    html = html.replace('__RELEASE_DATE__', released_date)
    html = html.replace('__CATALOG_JSON__', kev_json)

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_FILE) / 1024
    return size_kb, count, version, released_date


def fetch_kev():
    """
    Always fetches a completely fresh copy from CISA.
    Uses multiple cache-busting strategies to guarantee the CDN
    never returns a stale response:
      1. Unique timestamp query string appended to the URL
      2. Random nonce query param
      3. Full no-cache / no-store request headers
      4. If-None-Match / If-Modified-Since stripped (no conditional GETs)
    """
    import time
    import random
    import ssl

    ts    = int(time.time())
    nonce = random.randint(100000, 999999)
    url   = f"{CISA_URL}?_={ts}&nocache={nonce}"

    print(f"  URL: {url}")

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent':          f'CISA-KEV-Browser/2.0 (build/{ts})',
            'Cache-Control':       'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma':              'no-cache',
            'Expires':             '0',
            'Accept':              'application/json',
            # Prevent any conditional GET that could return 304 + stale body
            'If-None-Match':       '',
            'If-Modified-Since':   '',
        }
    )

    # Create a fresh SSL context (no session resumption that could serve cached)
    ctx = ssl.create_default_context()

    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        raw = resp.read()

    kev_data = json.loads(raw.decode('utf-8'))

    # Verify the payload is complete and genuine
    declared = kev_data.get('count', 0)
    actual   = len(kev_data.get('vulnerabilities', []))
    if actual == 0:
        raise ValueError("Response contained no vulnerabilities — possible truncated/cached response")
    if declared != actual:
        print(f"  ⚠ Count mismatch: header says {declared}, got {actual} entries. Using actual.")
        kev_data['count'] = actual

    # Sort newest-first so the HTML always opens with the most recent entries
    kev_data['vulnerabilities'].sort(
        key=lambda v: v.get('dateAdded', ''), reverse=True
    )

    return kev_data


if __name__ == '__main__':
    print("=" * 60)
    print("  CISA KEV Browser — Data Updater")
    print("=" * 60)
    print(f"\nFetching latest KEV data from CISA...")

    try:
        kev_data = fetch_kev()
        count    = kev_data.get('count', 0)
        version  = kev_data.get('catalogVersion', '?')
        released = kev_data.get('dateReleased', '')[:10]

        # Show the 3 newest entries so you can visually confirm freshness
        newest = kev_data['vulnerabilities'][:3]
        print(f"✓ Downloaded {count:,} vulnerabilities")
        print(f"  Catalog:  v{version}  (released {released})")
        print(f"  Newest entries:")
        for v in newest:
            print(f"    {v['dateAdded']}  {v['cveID']:<22}  {v['vendorProject']}")

    except urllib.error.URLError as e:
        print(f"✗ Network error: {e}")
        print("\nFalling back to local kev.json if present...")
        local = os.path.join(os.path.dirname(__file__), 'kev.json')
        if os.path.exists(local):
            with open(local, encoding='utf-8') as f:
                kev_data = json.load(f)
            kev_data['vulnerabilities'].sort(
                key=lambda v: v.get('dateAdded', ''), reverse=True
            )
            print(f"✓ Loaded local fallback: {kev_data.get('count',0):,} entries")
            print(f"  ⚠ This may be outdated. Fix your network and re-run.")
        else:
            print("✗ No local fallback found. Check your internet connection and retry.")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    print(f"\nBuilding standalone HTML...")
    size_kb, count, version, released = build(kev_data)

    print(f"\n✓ Done!")
    print(f"  Output:  cisa-kev-browser.html")
    print(f"  Size:    {size_kb:.0f} KB")
    print(f"  Built:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nOpen cisa-kev-browser.html in any browser.")
    print("=" * 60)
