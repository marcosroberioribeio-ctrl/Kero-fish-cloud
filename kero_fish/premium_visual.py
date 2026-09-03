from __future__ import annotations


def install_premium_visual(ui) -> None:
    """Aplica refinamento visual às abas operacionais sem alterar o Painel Geral."""
    st = ui.st

    def page_header(title: str, subtitle: str = "") -> None:
        st.markdown(
            """
            <style>
            /* Kero Fish Premium — acabamento das abas operacionais */
            .kf-op-head{
                position:relative;overflow:hidden;display:flex;align-items:center;
                justify-content:space-between;gap:18px;margin:0 0 16px;padding:18px 20px;
                border:1px solid rgba(75,139,191,.55);border-radius:18px;
                background:linear-gradient(135deg,rgba(12,48,80,.98),rgba(5,25,46,.98));
                box-shadow:0 14px 34px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.06);
            }
            .kf-op-head:before{content:"";position:absolute;left:0;top:0;width:5px;height:100%;background:linear-gradient(180deg,#f6c64d,#d99a16)}
            .kf-op-head:after{content:"";position:absolute;width:230px;height:230px;border-radius:50%;right:-110px;top:-155px;background:radial-gradient(circle,rgba(246,198,77,.16),transparent 68%);pointer-events:none}
            .kf-op-title{font-size:27px;font-weight:900;line-height:1.08;letter-spacing:-.03em;color:#f8fbff;text-shadow:0 1px 0 #0004}
            .kf-op-sub{font-size:12.5px;line-height:1.45;color:#bdd2e4;margin-top:6px;max-width:850px}
            .kf-op-seal{display:flex;align-items:center;gap:7px;white-space:nowrap;border:1px solid rgba(241,185,47,.62);background:linear-gradient(135deg,#342b13,#17170f);color:#f4c54d;padding:7px 11px;border-radius:999px;font-size:10px;font-weight:900;letter-spacing:.08em;box-shadow:inset 0 1px 0 #ffffff12,0 5px 15px #0003}
            .kf-op-seal:before{content:"◆";font-size:8px;color:#ffe082}

            /* Expansores e formulários: aspecto de cartão premium */
            [data-testid="stExpander"]{
                border:1px solid rgba(62,119,166,.58)!important;border-radius:15px!important;
                background:linear-gradient(180deg,rgba(8,35,61,.90),rgba(5,24,43,.94))!important;
                box-shadow:0 10px 28px rgba(0,0,0,.20)!important;overflow:hidden!important;
            }
            [data-testid="stExpander"] summary{min-height:46px!important;font-weight:800!important;color:#f2f7fb!important}
            [data-testid="stExpander"] summary:hover{background:rgba(33,83,124,.22)!important}
            [data-testid="stForm"]{
                border:1px solid rgba(62,119,166,.48)!important;border-radius:15px!important;
                background:linear-gradient(180deg,rgba(7,31,55,.78),rgba(4,21,39,.84))!important;
                box-shadow:inset 0 1px 0 rgba(255,255,255,.035)!important;padding:16px!important;
            }

            /* Campos: menos chapados, mais definidos */
            [data-baseweb="input"]>div,[data-baseweb="select"]>div,[data-baseweb="textarea"]>div,
            [data-testid="stNumberInput"] input,[data-testid="stDateInput"] input{
                background:linear-gradient(180deg,#153e66,#103657)!important;
                border:1px solid rgba(87,149,199,.58)!important;border-radius:10px!important;
                box-shadow:inset 0 1px 1px rgba(255,255,255,.035),0 3px 10px rgba(0,0,0,.12)!important;
            }
            [data-baseweb="input"]>div:focus-within,[data-baseweb="select"]>div:focus-within,[data-baseweb="textarea"]>div:focus-within{
                border-color:#6ec8ff!important;box-shadow:0 0 0 1px rgba(110,200,255,.42),0 5px 14px rgba(0,0,0,.18)!important;
            }
            label,[data-testid="stWidgetLabel"]{font-weight:700!important;color:#e9f2fa!important}

            /* Botões */
            div.stButton>button,div[data-testid="stFormSubmitButton"]>button{
                min-height:38px;border-radius:10px!important;font-weight:850!important;
                border:1px solid rgba(93,153,202,.55)!important;background:linear-gradient(180deg,#173f64,#0d3151)!important;
                color:#f6fbff!important;box-shadow:0 5px 14px rgba(0,0,0,.18)!important;
            }
            div.stButton>button:hover,div[data-testid="stFormSubmitButton"]>button:hover{
                border-color:#f0bd3e!important;transform:translateY(-1px);box-shadow:0 7px 17px rgba(0,0,0,.24)!important;
            }
            div.stButton>button[kind="primary"],div[data-testid="stFormSubmitButton"]>button[kind="primary"]{
                background:linear-gradient(135deg,#f3bf3e,#d99512)!important;color:#10243a!important;border-color:#ffd86d!important;
                box-shadow:0 7px 18px rgba(206,143,15,.22)!important;
            }

            /* Mensagens */
            [data-testid="stAlert"]{border-radius:11px!important;border-width:1px!important;box-shadow:0 5px 16px rgba(0,0,0,.14)!important}

            /* Métricas e grades */
            [data-testid="stMetric"]{
                background:linear-gradient(145deg,rgba(12,48,80,.92),rgba(6,27,49,.96))!important;
                border:1px solid rgba(69,128,176,.48)!important;border-radius:14px!important;
                padding:12px 14px!important;box-shadow:0 8px 22px rgba(0,0,0,.18)!important;
            }
            [data-testid="stDataEditor"],[data-testid="stDataFrame"]{
                border:1px solid rgba(65,126,176,.52)!important;border-radius:12px!important;
                overflow:hidden!important;box-shadow:0 10px 26px rgba(0,0,0,.22)!important;
            }

            /* Tabs internas de Relatórios/Auditoria */
            .stTabs [data-baseweb="tab-list"]{gap:7px;background:rgba(5,28,50,.68);padding:6px;border-radius:12px;border:1px solid rgba(56,111,157,.34)}
            .stTabs [data-baseweb="tab"]{border-radius:8px!important;padding:8px 13px!important;color:#bcd0e1!important;font-weight:750!important}
            .stTabs [aria-selected="true"]{background:linear-gradient(135deg,#244f73,#163b5d)!important;color:#ffd269!important;box-shadow:inset 0 0 0 1px rgba(241,185,47,.36)}

            /* Separadores e títulos internos */
            h3{letter-spacing:-.015em}.kf-section{margin-top:14px!important;padding-left:10px;border-left:3px solid #eab335}

            @media(max-width:900px){
                .kf-op-head{padding:15px 14px}.kf-op-title{font-size:22px}.kf-op-seal{display:none}
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='kf-op-head'><div><div class='kf-op-title'>{title}</div>"
            f"<div class='kf-op-sub'>{subtitle}</div></div>"
            "<div class='kf-op-seal'>KERO FISH • PREMIUM</div></div>",
            unsafe_allow_html=True,
        )

    ui.page_header = page_header
