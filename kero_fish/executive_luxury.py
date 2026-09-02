from __future__ import annotations


LUXURY_CSS = r"""
<style>
/* Camada final V12.1: usa seletores fortes para vencer o CSS-base do painel. */
html body .stApp{background:linear-gradient(135deg,#123858 0%,#0c2d4b 52%,#103652 100%)!important;color:#fff!important}
html body [data-testid='stHeader']{background:rgba(10,39,64,.96)!important;border-bottom:1px solid #3c6c91!important}

/* Marca d'água premium fica acima do fundo e abaixo da interação. */
html body [data-testid='stAppViewContainer']::after{content:'KERO  FISH';position:fixed;left:60%;top:55%;transform:translate(-50%,-50%) rotate(-9deg);z-index:9998;pointer-events:none;user-select:none;white-space:nowrap;font-family:Georgia,'Times New Roman',serif;font-size:clamp(92px,11vw,178px);font-weight:800;letter-spacing:.10em;color:rgba(244,207,111,.055);text-shadow:0 1px 0 rgba(255,255,255,.02)}

html body .kero-top h2{font-size:32px!important;line-height:1.3!important}
html body .kero-top .premium{font-size:16px!important;padding:7px 15px!important}
html body .kero-date{font-size:16px!important}
html body .exec-title{font-size:34px!important;line-height:1.25!important}
html body .exec-sub{font-size:17px!important;line-height:1.45!important;color:#edf5fb!important}
html body .metric-card{height:120px!important;padding:15px 14px!important}
html body .metric-label{font-size:14px!important;line-height:1.2!important;min-height:26px!important}
html body .metric-value{font-size:25px!important;line-height:1.2!important;margin-top:6px!important}
html body .metric-note{font-size:13px!important;margin-top:6px!important}
html body [data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(180deg,#123b5d,#0c2d49)!important;border-color:#3a6c92!important}
html body [data-testid='stVerticalBlockBorderWrapper'] h3{font-size:23px!important}
html body .alert-label{font-size:14px!important}.alert-value{font-size:27px!important}.alert-note{font-size:13px!important}.footerbar{font-size:13px!important}

/* Abas e formulários */
html body .kf-page-title{font-size:31px!important}html body .kf-page-sub{font-size:15px!important;color:#d9e8f2!important}
html body label[data-testid='stWidgetLabel'] p{font-size:14px!important}
html body [data-testid='stTextInput'] input,html body [data-testid='stNumberInput'] input,html body [data-testid='stDateInput'] input,html body textarea{font-size:15px!important;background:#24567c!important}
html body [data-testid='stExpander']{background:linear-gradient(180deg,rgba(24,62,91,.94),rgba(16,47,73,.92))!important;border-color:#47789c!important}
html body .stButton>button,html body .stFormSubmitButton>button{font-size:14px!important}

@media(max-width:900px){html body [data-testid='stAppViewContainer']::after{font-size:80px;left:58%}html body .exec-title{font-size:29px!important}html body .metric-value{font-size:21px!important}}
</style>
"""


def install_executive_luxury(ui) -> None:
    """Instala CSS de luxo e garante reaplicação depois do CSS-base do app."""
    ui.st.markdown(LUXURY_CSS, unsafe_allow_html=True)

    # O app.py define PREMIUM_CSS depois da importação do pacote. Por isso,
    # anexamos esta camada também ao atributo sempre que possível no momento
    # da instalação; páginas que usam o CSS-base continuam compatíveis.
    try:
        if isinstance(getattr(ui, 'PREMIUM_CSS', None), str) and LUXURY_CSS not in ui.PREMIUM_CSS:
            ui.PREMIUM_CSS += LUXURY_CSS
    except Exception:
        pass
