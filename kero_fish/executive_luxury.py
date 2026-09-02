from __future__ import annotations


def install_executive_luxury(ui) -> None:
    """Camada visual de requinte executivo, sem alterar regras de negócio."""
    st = ui.st
    st.markdown(r"""
    <style>
    :root{--kf-navy:#061727;--kf-panel:#0a2136;--kf-panel2:#0d2942;--kf-line:#254762;--kf-gold:#d7ad4a;--kf-gold2:#f0cf78;--kf-text:#f5f8fb;--kf-muted:#9fb5c7}
    .block-container{max-width:1500px;padding-left:2.0rem!important;padding-right:2.0rem!important}
    .kf-page-head{position:relative;overflow:hidden!important;align-items:center!important;margin:4px 0 20px!important;padding:20px 24px!important;border:1px solid rgba(215,173,74,.30)!important;border-radius:18px!important;background:linear-gradient(120deg,rgba(7,28,47,.98),rgba(11,40,64,.94))!important;box-shadow:0 18px 46px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.035)!important}
    .kf-page-head:before{content:'KERO FISH';position:absolute;right:145px;top:50%;transform:translateY(-50%);font-size:52px;font-weight:900;letter-spacing:.14em;color:rgba(255,255,255,.018);pointer-events:none;white-space:nowrap}
    .kf-page-head:after{content:'';position:absolute;left:24px;bottom:0;width:86px;height:2px;background:linear-gradient(90deg,var(--kf-gold),transparent)}
    .kf-page-title{font-size:27px!important;font-weight:800!important;letter-spacing:-.02em!important;color:var(--kf-text)!important;text-shadow:0 1px 10px rgba(0,0,0,.15)}
    .kf-page-sub{font-size:12.5px!important;color:var(--kf-muted)!important;margin-top:6px!important;letter-spacing:.01em}
    .kf-page-tag{position:relative;z-index:2;color:var(--kf-gold2)!important;border:1px solid rgba(215,173,74,.52)!important;background:linear-gradient(180deg,rgba(74,56,20,.55),rgba(35,29,16,.72))!important;padding:7px 12px!important;border-radius:999px!important;font-size:9px!important;font-weight:800!important;letter-spacing:.13em!important;box-shadow:inset 0 1px rgba(255,255,255,.06),0 5px 18px rgba(0,0,0,.18)}
    [data-testid='stExpander']{border:1px solid rgba(83,121,150,.42)!important;border-radius:16px!important;background:linear-gradient(180deg,rgba(9,31,51,.82),rgba(7,25,42,.76))!important;box-shadow:0 12px 34px rgba(0,0,0,.14),inset 0 1px rgba(255,255,255,.025)!important;margin-bottom:14px!important}
    [data-testid='stExpander'] details summary{padding-top:4px!important;padding-bottom:4px!important;font-weight:700!important;letter-spacing:.005em}
    [data-testid='stForm']{border:1px solid rgba(83,121,150,.34)!important;border-radius:16px!important;background:rgba(6,25,42,.55)!important;padding:18px!important}
    [data-testid='stTextInput'] input,[data-testid='stNumberInput'] input,[data-testid='stDateInput'] input,textarea,[data-baseweb='select']>div{border-radius:10px!important;border-color:rgba(76,112,140,.55)!important;background:rgba(17,48,75,.88)!important;box-shadow:inset 0 1px 2px rgba(0,0,0,.14)!important;transition:border-color .16s ease,box-shadow .16s ease!important}
    [data-testid='stTextInput'] input:focus,[data-testid='stNumberInput'] input:focus,[data-testid='stDateInput'] input:focus,textarea:focus{border-color:rgba(215,173,74,.82)!important;box-shadow:0 0 0 2px rgba(215,173,74,.09)!important}
    label[data-testid='stWidgetLabel'] p{font-size:11.5px!important;font-weight:650!important;color:#d8e3eb!important;letter-spacing:.005em}
    .stButton>button,.stFormSubmitButton>button{border-radius:10px!important;min-height:39px!important;font-weight:750!important;letter-spacing:.01em!important;transition:transform .15s ease,box-shadow .15s ease!important}
    .stButton>button[kind='primary'],.stFormSubmitButton>button[kind='primary']{color:#102031!important;border:1px solid #e1bd61!important;background:linear-gradient(180deg,#f0cf78,#c99a35)!important;box-shadow:0 7px 18px rgba(170,124,30,.16)!important}
    .stButton>button[kind='primary']:hover,.stFormSubmitButton>button[kind='primary']:hover{transform:translateY(-1px);box-shadow:0 9px 24px rgba(170,124,30,.24)!important}
    [data-testid='stMetric']{border:1px solid rgba(74,111,140,.35);border-radius:14px;padding:12px 14px;background:linear-gradient(145deg,rgba(13,42,67,.74),rgba(7,27,45,.72));box-shadow:0 9px 24px rgba(0,0,0,.12)}
    [data-testid='stMetricLabel']{color:var(--kf-muted)!important}[data-testid='stMetricValue']{font-weight:800!important;letter-spacing:-.02em!important}
    [data-testid='stDataEditor'],[data-testid='stDataFrame']{border:1px solid rgba(76,111,139,.34)!important;border-radius:14px!important;overflow:hidden!important;box-shadow:0 13px 34px rgba(0,0,0,.15)!important}
    .stTabs [data-baseweb='tab-list']{gap:7px!important;border-bottom:1px solid rgba(84,117,143,.34)!important}
    .stTabs [data-baseweb='tab']{height:42px!important;padding:8px 15px!important;border-radius:10px 10px 0 0!important;color:#aec2d2!important;font-weight:650!important}
    .stTabs [aria-selected='true']{color:var(--kf-gold2)!important;background:linear-gradient(180deg,rgba(30,64,91,.88),rgba(15,43,67,.72))!important;border-bottom:2px solid var(--kf-gold)!important}
    [data-testid='stAlert']{border-radius:12px!important;border-width:1px!important}
    hr{border-color:rgba(82,113,138,.28)!important}
    @media(max-width:900px){.block-container{padding-left:1rem!important;padding-right:1rem!important}.kf-page-head{padding:16px!important}.kf-page-head:before{display:none}.kf-page-title{font-size:23px!important}.kf-page-tag{display:none}}
    </style>
    """, unsafe_allow_html=True)
