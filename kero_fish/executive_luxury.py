from __future__ import annotations


def install_executive_luxury(ui) -> None:
    """Requinte executivo, melhor legibilidade e marca d'água, sem alterar regras de negócio."""
    st = ui.st
    st.markdown(r"""
    <style>
    :root{--gold:#d9ae48;--gold2:#f3d47c;--ink:#f7fafc;--muted:#bfd0dc}
    /* Azul executivo levemente mais claro, mantendo contraste e sofisticação. */
    .stApp{background:linear-gradient(135deg,#0b2946 0%,#071f38 55%,#092641 100%)!important;color:#fff}
    [data-testid='stHeader']{background:rgba(7,31,56,.94)!important;border-bottom:1px solid #2b5b82!important}
    .block-container{max-width:1500px;padding-left:2rem!important;padding-right:2rem!important;position:relative!important;isolation:isolate}
    .block-container:before{content:'KERO\A FISH';white-space:pre;position:fixed;z-index:-1;left:calc(50% + 90px);top:55%;transform:translate(-50%,-50%) rotate(-8deg);font-family:Arial,sans-serif;font-size:clamp(90px,12vw,190px);line-height:.72;font-weight:950;letter-spacing:.04em;text-align:center;color:rgba(218,181,91,.07);pointer-events:none;user-select:none}
    .block-container:after{content:'PEIXE  •  CAMARÃO   |   PREMIUM ERP';position:fixed;z-index:-1;left:calc(50% + 90px);top:68%;transform:translateX(-50%) rotate(-8deg);font-size:14px;font-weight:800;letter-spacing:.34em;color:rgba(232,204,133,.09);white-space:nowrap;pointer-events:none}
    .kf-page-head{position:relative;overflow:hidden!important;align-items:center!important;margin:4px 0 20px!important;padding:20px 24px!important;border:1px solid rgba(217,174,72,.42)!important;border-left:3px solid var(--gold)!important;border-radius:17px!important;background:linear-gradient(120deg,rgba(11,40,66,.97),rgba(17,55,84,.94))!important;box-shadow:0 18px 46px rgba(0,0,0,.20),inset 0 1px 0 rgba(255,255,255,.05)!important}
    .kf-page-head:before{content:'KERO FISH';position:absolute;right:130px;top:50%;transform:translateY(-50%);font-size:54px;font-weight:950;letter-spacing:.13em;color:rgba(235,205,127,.07);pointer-events:none;white-space:nowrap}
    .kf-page-head:after{content:'';position:absolute;left:24px;bottom:0;width:110px;height:2px;background:linear-gradient(90deg,var(--gold),transparent)}
    .kf-page-title{font-size:29px!important;font-weight:850!important;color:var(--ink)!important}.kf-page-sub{font-size:14px!important;color:var(--muted)!important;margin-top:6px!important}.kf-page-tag{color:var(--gold2)!important;border:1px solid rgba(217,174,72,.58)!important;padding:7px 12px!important;border-radius:999px!important;font-size:10px!important;font-weight:850!important}
    [data-testid='stExpander']{border:1px solid rgba(99,139,169,.52)!important;border-radius:15px!important;background:linear-gradient(180deg,rgba(14,43,68,.86),rgba(10,34,56,.80))!important;box-shadow:0 12px 32px rgba(0,0,0,.13)!important;margin-bottom:14px!important}
    [data-testid='stForm']{border:1px solid rgba(99,139,169,.44)!important;border-radius:15px!important;background:rgba(10,36,59,.62)!important;padding:18px!important}
    [data-testid='stTextInput'] input,[data-testid='stNumberInput'] input,[data-testid='stDateInput'] input,textarea,[data-baseweb='select']>div{border-radius:9px!important;border-color:rgba(101,143,174,.68)!important;background:linear-gradient(180deg,rgba(27,66,98,.96),rgba(21,57,87,.96))!important;font-size:14px!important}
    label[data-testid='stWidgetLabel'] p{font-size:13px!important;font-weight:700!important;color:#e4edf3!important}
    .stButton>button,.stFormSubmitButton>button{border-radius:9px!important;min-height:40px!important;font-size:13px!important;font-weight:780!important}.stButton>button[kind='primary'],.stFormSubmitButton>button[kind='primary']{color:#102031!important;border:1px solid #e4c365!important;background:linear-gradient(180deg,#f3d47c,#c99a34)!important}
    /* Painel geral: aumento moderado para leitura à distância. */
    .kero-top h2{font-size:29px!important}.kero-date{font-size:14px!important}.exec-title{font-size:30px!important}.exec-sub{font-size:14.5px!important;color:#dce8f1!important}
    .metric-label{font-size:12px!important;line-height:1.18!important}.metric-value{font-size:21px!important}.metric-note{font-size:11px!important}
    [data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(180deg,#0c2d4b,#08233d)!important;border-color:#2c5b80!important}
    [data-testid='stVerticalBlockBorderWrapper'] h3{font-size:20px!important}
    [data-testid='stMetric']{border:1px solid rgba(94,136,168,.46);border-radius:13px;padding:12px 14px;background:linear-gradient(145deg,rgba(20,55,83,.82),rgba(11,38,62,.80))}
    [data-testid='stDataEditor'],[data-testid='stDataFrame']{border:1px solid rgba(94,136,168,.46)!important;border-radius:13px!important;overflow:hidden!important}
    .alert-label{font-size:12.5px!important}.alert-value{font-size:24px!important}.alert-note{font-size:11px!important}.footerbar{font-size:12px!important}
    .stTabs [data-baseweb='tab']{font-size:13px!important}
    @media(max-width:900px){.block-container{padding-left:1rem!important;padding-right:1rem!important}.block-container:before{left:55%;font-size:86px}.block-container:after{display:none}.kf-page-head{padding:16px!important}.kf-page-head:before{display:none}.kf-page-title{font-size:25px!important}.kf-page-tag{display:none}}
    </style>
    """, unsafe_allow_html=True)
