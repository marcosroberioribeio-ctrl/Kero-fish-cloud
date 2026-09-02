# -*- coding: utf-8 -*-
"""Kero Fish ERP Premium 12.1 - entrada da versão de teste."""
from kero_fish import ui

# Tema Premium Conforto: mantém a identidade azul/turquesa, com fundo mais
# claro e contraste mais confortável para uso prolongado.
ui.PREMIUM_CSS = """
<style>
:root { --kero-navy:#102b49; --kero-blue:#1b4d78; --kero-cyan:#24d7e7; --kero-gold:#d7a438; }
.stApp { background: radial-gradient(circle at 75% 0%, #285b82 0%, #183e62 38%, #102b49 100%); color:#f8fbff; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#245578 0%,#173b5d 100%); border-right:1px solid rgba(255,255,255,.14); }
[data-testid="stMetric"] { background:rgba(31,75,111,.88); border:1px solid rgba(79,220,232,.24); border-radius:16px; padding:14px 16px; box-shadow:0 10px 24px rgba(0,0,0,.14); }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid rgba(79,220,232,.30); border-radius:14px; overflow:hidden; background:rgba(28,67,101,.52); }
div.stButton > button { border-radius:10px; font-weight:700; border:1px solid rgba(79,220,232,.42); }
div.stButton > button[kind="primary"] { background:linear-gradient(90deg,#19cde1,#48e4d8); color:#08233a; border:0; }
.kero-title { font-size:2rem; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; color:#ffffff; }
.kero-sub { color:#c2dff2; margin-bottom:1rem; }
.kero-card { background:rgba(31,75,111,.82); border:1px solid rgba(255,255,255,.12); border-radius:16px; padding:16px; margin-bottom:14px; }
.kero-badge { display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(36,215,231,.16); color:#baf8ff; border:1px solid rgba(79,220,232,.32); font-size:.82rem; font-weight:700; }
.kero-ok { color:#8dffc0; font-weight:700; }
.kero-warn { color:#ffe09a; font-weight:700; }
</style>
"""

ui.run()
