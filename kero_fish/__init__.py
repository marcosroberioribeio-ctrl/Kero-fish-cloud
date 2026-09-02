__version__ = "12.1.0"
APP_NAME = "Kero Fish ERP Premium"

# A V12.1 de teste instala a camada opcional de endereço por CEP antes
# de o entrypoint chamar ui.run(). A inicialização do banco garante que
# as migrações leves possam acrescentar as colunas sem afetar dados atuais.
from . import ui as ui  # noqa: E402
from .cep_ui import install_cep_overrides  # noqa: E402

ui.init_db()
install_cep_overrides(ui)
