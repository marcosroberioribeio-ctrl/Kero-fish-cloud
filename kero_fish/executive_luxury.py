from __future__ import annotations


def install_executive_luxury(ui) -> None:
    """Requinte executivo e marca d'água, sem alterar regras de negócio."""
    st = ui.st
    st.markdown(r"""
    <style>
    :root{--gold:#d9ae48;--gold2:#f3d47c;--ink:#f5f8fb;--muted:#a9bdcc}
    .block-container{max-width:1500px;padding-left:2rem!important;padding-right:2rem!important;position:relative!important;isolation:isolate}
    /* Marca d'água central: propositalmente perceptível, mas atrás de todo o conteúdo. */
    .block-container:before{content:'KERO\A FISH';white-space:pre;position:fixed;z-index:-1;left:calc(50% + 90px);top:55%;transform:translate(-50%,-50%) rotate(-8deg);font-family:Arial,sans-serif;font-size:clamp(90px,12vw,190px);line-height:.72;font-weight:950;letter-spacing:.04em;text-align:center;color:rgba(210,174,82,.055);text-shadow:0 0 1px rgba(255,255,255,.025);pointer-events:none;user-select:none}
    .block-container:after{content:'PEIXE  •  CAMARÃO   |   PREMIUM ERP';position:fixed;z-index:-1;left:calc(50% + 90px);top:68%;transform:translateX(-50%) rotate(-8deg);font-size:13px;font-weight:800;letter-spacing:.34em;color:rgba(223,194,119,.07);white-space:nowrap;pointer-events:none}
    .kf-page-head{position:relative;overflow:hidden!important;align-items:center!important;margin:4px 0 20px!important;padding:20px 24px!important;border:1px solid rgba(217,174,72,.42)!important;border-left:3px solid var(--gold)!important;border-radius:17px!important;background:linear-gradient(120deg,rgba(7,27,46,.97),rgba(12,42,67,.94))!important;box-shadow:0 18px 46px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.04)!important}
    .kf-page-head:before{content:'KERO FISH';position:absolute;right:130px;top:50%;transform:translateY(-50%);font-size:54px;font-weight:950;letter-spacing:.13em;color:rgba(235,205,127,.055);pointer-events:none;white-space:nowrap}
    .kf-page-head:after{content:'';position:absolute;left:24px;bottom:0;width:110px;height:2px;background:linear-gradient(90deg,var(--gold),transparent)}
    .kf-page-title{font-size:27px!important;font-weight:850!important;letter-spacing:-.025em!important;color:var(--ink)!important}.kf-page-sub{font-size:12.5px!important;color:var(--muted)!important;margin-top:6px!important}
    .kf-page-tag{position:relative;z-index:2;color:var(--gold2)!important;border:1px solid rgba(217,174,72,.58)!important;background:linear-gradient(180deg,rgba(76,57,19,.6),rgba(37,30,15,.76))!important;padding:7px 12px!important;border-radius:999px!important;font-size:9px!important;font-weight:850!important;letter-spacing:.13em!important}
    [data-testid='stExpander']{border:1px solid rgba(81,119,149,.46)!important;border-radius:15px!important;background:linear-gradient(180deg,rgba(9,31,51,.82),rgba(7,25,42,.74))!important;box-shadow:0 12px 32px rgba(0,0,0,.14),inset 0 1px rgba(255,255,255,.025)!important;margin-bottom:14px!important}
    [data-testid='stForm']{border:1px solid rgba(81,119,149,.38)!important;border-radius:15px!important;background:rgba(6,25,42,.56)!important;padding:18px!important}
    [data-testid='stTextInput'] input,[data-testid='stNumberInput'] input,[data-testid='stDateInput'] input,textarea,[data-baseweb='select']>div{border-radius:9px!important;border-color:rgba(78,116,145,.62)!important;background:linear-gradient(180deg,rgba(20,55,84,.94),rgba(15,45,71,.94))!important;box-shadow:inset 0 1px 2px rgba(0,0,0,.16)!important}
    [data-testid='stTextInput'] input:focus,[data-testid='stNumberInput'] input:focus,[data-testid='stDateInput'] input:focus,textarea:focus{border-color:rgba(217,174,72,.9)!important;box-shadow:0 0 0 2px rgba(217,174,72,.10)!important}
    label[data-testid='stWidgetLabel'] p{font-size:11.5px!important;font-weight:700!important;color:#dce7ee!important}
    .stButton>button,.stFormSubmitButton>button{border-radius:9px!important;min-height:39px!important;font-weight:780!important}.stButton>button[kind='primary'],.stFormSubmitButton>button[kind='primary']{color:#102031!important;border:1px solid #e4c365!important;background:linear-gradient(180deg,#f3d47c,#c99a34)!important;box-shadow:0 7px 20px rgba(170,124,30,.19)!important}
    [data-testid='stMetric']{border:1px solid rgba(77,113,141,.4);border-radius:13px;padding:12px 14px;background:linear-gradient(145deg,rgba(13,42,67,.78),rgba(7,27,45,.74));box-shadow:0 9px 24px rgba(0,0,0,.12)}
    [data-testid='stDataEditor'],[data-testid='stDataFrame']{border:1px solid rgba(77,113,141,.4)!important;border-radius:13px!important;overflow:hidden!important;box-shadow:0 13px 34px rgba(0,0,0,.15)!important}
    .stTabs [data-baseweb='tab-list']{gap:7px!important;border-bottom:1px solid rgba(84,117,143,.34)!important}.stTabs [data-baseweb='tab']{height:42px!important;padding:8px 15px!important;border-radius:9px 9px 0 0!important;color:#aec2d2!important;font-weight:680!important}.stTabs [aria-selected='true']{color:var(--gold2)!important;background:rgba(23,57,85,.86)!important;border-bottom:2px solid var(--gold)!important}
    [data-testid='stAlert']{border-radius:11px!important}
    @media(max-width:900px){.block-container{padding-left:1rem!important;padding-right:1rem!important}.block-container:before{left:55%;font-size:86px}.block-container:after{display:none}.kf-page-head{padding:16px!important}.kf-page-head:before{display:none}.kf-page-title{font-size:23px!important}.kf-page-tag{display:none}}
    </style>
    """, unsafe_allow_html=True)
