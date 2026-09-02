__version__ = "12.1.0"
APP_NAME = "Kero Fish ERP Premium"

# A V12.1 de teste instala camadas aditivas sobre o núcleo estável:
# - migrações profissionais de endereço/exercícios anuais;
# - sequência anual de pedidos;
# - CEP automático;
# - refinamentos premium e operações financeiras integradas;
# - acabamento visual premium e requinte executivo das abas operacionais.
from . import ui as ui  # noqa: E402
from .annual import ensure_professional_schema, install_annual_order_patch  # noqa: E402
from .cep_ui import install_cep_overrides  # noqa: E402
from .premium_ops import install_premium_operations  # noqa: E402
from .premium_visual import install_premium_visual  # noqa: E402
from .executive_luxury import install_executive_luxury  # noqa: E402

ui.init_db()
ensure_professional_schema()
install_annual_order_patch()
install_cep_overrides(ui)
install_premium_operations(ui)
install_premium_visual(ui)
install_executive_luxury(ui)
