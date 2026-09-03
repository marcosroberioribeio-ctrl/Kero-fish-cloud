__version__ = "12.1.0"
APP_NAME = "Kero Fish ERP Premium"
SECURITY_BUILD = "2026-09-02-login-gate"

# A V12.1 de teste instala camadas aditivas sobre o núcleo estável:
# - migrações profissionais de endereço/exercícios anuais;
# - sequência anual de pedidos;
# - CEP automático;
# - operações financeiras integradas e ponto de equilíbrio;
# - filtros mensais/anuais nas listagens de vendas e compras;
# - auditoria vinculada ao usuário da sessão;
# - camada analítica de reconciliação, custos, estoque e auditoria;
# - guardas de consistência para estoque e importações;
# - proteção integral de exercícios fechados;
# - análise executiva com DRE gerencial, caixa projetado e riscos;
# - autenticação individual dos sócios e administração de acessos;
# - recuperação segura dos indicadores quando o razão financeiro estiver vazio;
# - acabamento visual premium.
from . import ui as ui  # noqa: E402
from .annual import ensure_professional_schema, install_annual_order_patch  # noqa: E402
from .cep_ui import install_cep_overrides  # noqa: E402
from .premium_ops import install_premium_operations  # noqa: E402
from .sales_filter import install_sales_filter  # noqa: E402
from .purchases_filter import install_purchases_filter  # noqa: E402
from .break_even import install_break_even  # noqa: E402
from .audit_context import install_audit_context  # noqa: E402
from .analyst_layer import install_analyst_layer  # noqa: E402
from .consistency import install_consistency_guards  # noqa: E402
from .closing_guards import install_closing_guards  # noqa: E402
from .analytics import install_management_analytics  # noqa: E402
from .premium_visual import install_premium_visual  # noqa: E402
from .security import install_security  # noqa: E402
from .dashboard_recovery import install_dashboard_recovery  # noqa: E402
from .executive_luxury import install_executive_luxury  # noqa: E402

ui.init_db()
ensure_professional_schema()
install_annual_order_patch()
install_cep_overrides(ui)
install_premium_operations(ui)
install_sales_filter(ui)
install_purchases_filter(ui)
install_break_even(ui)
install_audit_context(ui)
install_analyst_layer(ui)
install_consistency_guards(ui)
install_closing_guards(ui)
install_management_analytics(ui)
install_premium_visual(ui)
install_security(ui)
install_dashboard_recovery(ui)
install_executive_luxury(ui)
