from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def formatar_cep(valor: str) -> str:
    digitos = _somente_digitos(valor)
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return valor or ""


def consultar_cep(cep: str) -> dict[str, str]:
    digitos = _somente_digitos(cep)
    if len(digitos) != 8:
        raise ValueError("Informe um CEP com 8 dígitos.")
    req = Request(
        f"https://viacep.com.br/ws/{digitos}/json/",
        headers={"User-Agent": "KeroFishERP/12.1"},
    )
    try:
        with urlopen(req, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Não foi possível consultar o CEP agora. Preencha o endereço manualmente.") from exc
    if payload.get("erro"):
        raise ValueError("CEP não encontrado.")
    return {
        "cep": formatar_cep(payload.get("cep", cep)),
        "logradouro": str(payload.get("logradouro", "") or ""),
        "bairro": str(payload.get("bairro", "") or ""),
        "cidade": str(payload.get("localidade", "") or ""),
        "uf": str(payload.get("uf", "") or ""),
        "complemento": str(payload.get("complemento", "") or ""),
    }


def _ensure_address_columns(ui) -> None:
    additions = {
        "clientes": {
            "cep": "TEXT DEFAULT ''",
            "bairro": "TEXT DEFAULT ''",
            "uf": "TEXT DEFAULT ''",
            "numero": "TEXT DEFAULT ''",
            "complemento": "TEXT DEFAULT ''",
        },
        "fornecedores": {
            "cep": "TEXT DEFAULT ''",
            "bairro": "TEXT DEFAULT ''",
            "cidade": "TEXT DEFAULT ''",
            "uf": "TEXT DEFAULT ''",
            "numero": "TEXT DEFAULT ''",
            "complemento": "TEXT DEFAULT ''",
        },
        "entregas": {
            "cep": "TEXT DEFAULT ''",
            "uf": "TEXT DEFAULT ''",
            "numero": "TEXT DEFAULT ''",
            "complemento": "TEXT DEFAULT ''",
        },
    }
    with ui.connect() as conn:
        for table, columns in additions.items():
            existentes = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            for nome, definition in columns.items():
                if nome not in existentes:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {nome} {definition}")


def _cep_fields(ui, prefix: str) -> dict[str, str]:
    st = ui.st
    result_key = f"{prefix}_cep_resultado"
    version_key = f"{prefix}_cep_version"
    st.session_state.setdefault(version_key, 0)

    c1, c2 = st.columns([3, 1])
    cep = c1.text_input("CEP", key=f"{prefix}_cep", placeholder="00000-000")
    if c2.button("🔎 Buscar CEP", key=f"{prefix}_buscar_cep", use_container_width=True):
        try:
            dados = consultar_cep(cep)
            st.session_state[result_key] = dados
            st.session_state[version_key] = int(st.session_state.get(version_key, 0)) + 1
            st.session_state[f"{prefix}_cep_ok"] = True
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    dados = st.session_state.get(result_key, {})
    version = int(st.session_state.get(version_key, 0))

    if st.session_state.pop(f"{prefix}_cep_ok", False):
        st.success("Endereço localizado pelo CEP. Confira os dados e informe o número.")

    # Cada nova consulta de CEP usa uma nova geração de chaves para os widgets.
    # Assim o Streamlit cria os campos já com os valores retornados pela API,
    # sem tentar alterar o session_state de widgets já instanciados.
    c3, c4 = st.columns([4, 1])
    endereco = c3.text_input(
        "Rua / Logradouro",
        value=dados.get("logradouro", ""),
        key=f"{prefix}_endereco_{version}",
    )
    numero = c4.text_input("Número", key=f"{prefix}_numero")
    c5, c6, c7 = st.columns([2, 2, 1])
    bairro = c5.text_input(
        "Bairro",
        value=dados.get("bairro", ""),
        key=f"{prefix}_bairro_{version}",
    )
    cidade = c6.text_input(
        "Cidade",
        value=dados.get("cidade", ""),
        key=f"{prefix}_cidade_{version}",
    )
    uf = c7.text_input(
        "UF",
        value=dados.get("uf", ""),
        max_chars=2,
        key=f"{prefix}_uf_{version}",
    )
    complemento = st.text_input(
        "Complemento",
        value=dados.get("complemento", ""),
        key=f"{prefix}_complemento_{version}",
    )

    return {
        "cep": formatar_cep(dados.get("cep", cep)),
        "endereco": endereco.strip(),
        "numero": numero.strip(),
        "bairro": bairro.strip(),
        "cidade": cidade.strip(),
        "uf": uf.strip().upper(),
        "complemento": complemento.strip(),
    }


def _clear_prefix(st, prefix: str) -> None:
    for key in list(st.session_state):
        if key.startswith(prefix + "_"):
            del st.session_state[key]


def _clientes(ui) -> None:
    st = ui.st
    ui.page_header("👥 Clientes", "Cadastro de clientes com endereço automático por CEP.")
    with st.expander("➕ Novo cliente", expanded=True):
        c1, c2 = st.columns([2, 1])
        nome = c1.text_input("Nome *", key="cli_nome")
        telefone = c2.text_input("Telefone", key="cli_telefone")
        end = _cep_fields(ui, "cli")
        obs = st.text_area("Observações", key="cli_obs")
        if st.button("Cadastrar cliente", type="primary", key="cli_salvar"):
            if not nome.strip():
                st.error("Informe o nome do cliente.")
            else:
                with ui.connect() as conn:
                    conn.execute(
                        "INSERT INTO clientes(nome,telefone,cep,endereco,numero,complemento,bairro,cidade,uf,observacoes,ativo) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                        (nome.strip(), telefone.strip(), end["cep"], end["endereco"], end["numero"], end["complemento"], end["bairro"], end["cidade"], end["uf"], obs.strip()),
                    )
                _clear_prefix(st, "cli")
                st.success("Cliente cadastrado.")
                st.rerun()

    ui.editable_grid(
        "clientes",
        "SELECT id,nome,telefone,cep,endereco,numero,complemento,bairro,cidade,uf,observacoes,ativo FROM clientes ORDER BY nome",
        ["nome","telefone","cep","endereco","numero","complemento","bairro","cidade","uf","observacoes","ativo"],
        ["id"],
        "clientes_cep",
    )


def _fornecedores(ui) -> None:
    st = ui.st
    ui.page_header("🚚 Fornecedores", "Cadastro de fornecedores com endereço automático por CEP.")
    with st.expander("➕ Novo fornecedor", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        nome = c1.text_input("Fornecedor *", key="forn_nome")
        telefone = c2.text_input("Telefone", key="forn_telefone")
        contato = c3.text_input("Contato", key="forn_contato")
        end = _cep_fields(ui, "forn")
        c4, c5 = st.columns(2)
        produto = c4.text_input("Produto fornecido", key="forn_produto")
        prazo = c5.text_input("Prazo de pagamento", key="forn_prazo")
        obs = st.text_area("Observações", key="forn_obs")
        if st.button("Cadastrar fornecedor", type="primary", key="forn_salvar"):
            if not nome.strip():
                st.error("Informe o fornecedor.")
            else:
                with ui.connect() as conn:
                    conn.execute(
                        "INSERT INTO fornecedores(fornecedor,contato,telefone,cep,endereco,numero,complemento,bairro,cidade,uf,produto_fornecido,prazo_pagamento,observacoes,ativo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
                        (nome.strip(), contato.strip(), telefone.strip(), end["cep"], end["endereco"], end["numero"], end["complemento"], end["bairro"], end["cidade"], end["uf"], produto.strip(), prazo.strip(), obs.strip()),
                    )
                _clear_prefix(st, "forn")
                st.success("Fornecedor cadastrado.")
                st.rerun()

    ui.editable_grid(
        "fornecedores",
        "SELECT id,fornecedor,contato,telefone,cep,endereco,numero,complemento,bairro,cidade,uf,produto_fornecido,prazo_pagamento,observacoes,ativo FROM fornecedores ORDER BY fornecedor",
        ["fornecedor","contato","telefone","cep","endereco","numero","complemento","bairro","cidade","uf","produto_fornecido","prazo_pagamento","observacoes","ativo"],
        ["id"],
        "fornecedores_cep",
    )


def _entregas(ui) -> None:
    st = ui.st
    ui.page_header("🛵 Entregas", "Acompanhamento logístico com endereço automático por CEP.")
    with st.expander("➕ Nova entrega", expanded=True):
        c1, c2, c3 = st.columns(3)
        pedido = c1.text_input("Pedido", key="ent_pedido")
        cliente = c2.text_input("Cliente", key="ent_cliente")
        data_ent = c3.date_input("Data", key="ent_data")
        end = _cep_fields(ui, "ent")
        c4, c5, c6 = st.columns(3)
        entregador = c4.text_input("Entregador", key="ent_entregador")
        taxa = c5.number_input("Taxa de entrega", min_value=0.0, step=0.01, key="ent_taxa")
        status = c6.selectbox("Status", ["Aguardando", "Em preparação", "Saiu para entrega", "Entregue", "Cancelado"], key="ent_status")
        obs = st.text_area("Observações", key="ent_obs")
        if st.button("Cadastrar entrega", type="primary", key="ent_salvar"):
            with ui.connect() as conn:
                conn.execute(
                    "INSERT INTO entregas(pedido,cliente,data_ent,cep,endereco,numero,complemento,bairro,cidade,uf,entregador,taxa_entrega,taxa,status,observacoes,observacao) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pedido.strip(), cliente.strip(), data_ent.isoformat(), end["cep"], end["endereco"], end["numero"], end["complemento"], end["bairro"], end["cidade"], end["uf"], entregador.strip(), taxa, taxa, status, obs.strip(), obs.strip()),
                )
            _clear_prefix(st, "ent")
            st.success("Entrega cadastrada.")
            st.rerun()

    ui.editable_grid(
        "entregas",
        "SELECT id,pedido,cliente,data_ent,cep,endereco,numero,complemento,bairro,cidade,uf,entregador,taxa,status,observacao FROM entregas ORDER BY id DESC",
        ["pedido","cliente","data_ent","cep","endereco","numero","complemento","bairro","cidade","uf","entregador","taxa","status","observacao"],
        ["id"],
        "entregas_cep",
    )


def install_cep_overrides(ui) -> None:
    _ensure_address_columns(ui)
    ui.clientes = lambda: _clientes(ui)
    ui.fornecedores = lambda: _fornecedores(ui)

    def run_com_cep():
        st = ui.st
        st.set_page_config(page_title=ui.APP_NAME, page_icon="🐟", layout="wide", initial_sidebar_state="expanded")
        st.markdown(ui.PREMIUM_CSS, unsafe_allow_html=True)
        _, logo = ui._bootstrap()
        page = ui.sidebar(logo)
        if page == "Painel Geral": ui.painel()
        elif page == "Produtos": ui.produtos()
        elif page == "Fornecedores": ui.fornecedores()
        elif page == "Clientes": ui.clientes()
        elif page == "Compras": ui.compras()
        elif page == "Vendas": ui.vendas()
        elif page == "Estoque": ui.estoque()
        elif page == "Financeiro": ui.simple_page("💰 Financeiro", "Entradas e saídas realizadas.", "financeiro", "SELECT id,data,tipo,categoria,descricao,valor,forma_pagamento,origem,origem_id FROM financeiro ORDER BY data DESC,id DESC", ["data","tipo","categoria","descricao","valor","forma_pagamento","origem","origem_id"])
        elif page == "Despesas": ui.simple_page("🧾 Despesas", "Custos e despesas operacionais.", "despesas", "SELECT id,data,categoria,descricao,valor,forma_pagamento,pago,fornecedor,observacao FROM despesas ORDER BY data DESC,id DESC", ["data","categoria","descricao","valor","forma_pagamento","pago","fornecedor","observacao"])
        elif page == "Contas a Pagar": ui.simple_page("📤 Contas a Pagar", "Obrigações pendentes e pagas.", "contas_pagar", "SELECT id,descricao,fornecedor,valor_total,valor_pago,vencimento,status,forma_pagamento,origem,origem_id FROM contas_pagar ORDER BY status,vencimento", ["descricao","fornecedor","valor_total","valor_pago","vencimento","status","forma_pagamento"])
        elif page == "Contas a Receber": ui.simple_page("📥 Contas a Receber", "Recebíveis de vendas a prazo ou parcialmente pagas.", "contas_receber", "SELECT id,descricao,cliente,valor_total,valor_recebido,vencimento,status,forma_pagamento,origem,origem_id FROM contas_receber ORDER BY status,vencimento", ["descricao","cliente","valor_total","valor_recebido","vencimento","status","forma_pagamento"])
        elif page == "Entregas": _entregas(ui)
        elif page == "Relatórios": ui.relatorios()
        elif page == "Importar Planilha": ui.importar()
        elif page == "Auditoria": ui.auditoria()
        elif page == "Diagnóstico": ui.diagnostico()
        elif page == "Backup": ui.backup()

    ui.run = run_com_cep
