__version__ = "12.1.0"
APP_NAME = "Kero Fish ERP Premium"

# A V12.1 de teste instala camadas aditivas sobre o núcleo estável:
# - migrações profissionais de endereço/exercícios anuais;
# - sequência anual de pedidos;
# - CEP automático;
# - operações financeiras integradas e ponto de equilíbrio;
# - camada analítica de reconciliação, custos, estoque e auditoria;
# - autenticação individual dos sócios e administração de acessos;
# - acabamento visual premium.
from . import ui as ui  # noqa: E402
from .annual import ensure_professional_schema, install_annual_order_patch  # noqa: E402
from .cep_ui import install_cep_overrides  # noqa: E402
from .premium_ops import install_premium_operations  # noqa: E402
from .break_even import install_break_even  # noqa: E402
from .analyst_layer import install_analyst_layer  # noqa: E402
from .premium_visual import install_premium_visual  # noqa: E402
from .executive_luxury import install_executive_luxury  # noqa: E402
from .security import install_security  # noqa: E402

ui.init_db()
ensure_professional_schema()
install_annual_order_patch()
install_cep_overrides(ui)
install_premium_operations(ui)
install_break_even(ui)
install_analyst_layer(ui)
install_premium_visual(ui)
install_executive_luxury(ui)
install_security(ui)
