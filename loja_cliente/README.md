# Kero Fish Loja Cliente — MVP PWA

A nova loja online do Kero Fish fica separada do ERP administrativo e pode ser instalada no celular como PWA.

## O que esta primeira versão entrega

- catálogo responsivo carregado dos produtos do ERP;
- busca de produtos;
- carrinho persistente no navegador;
- checkout com nome, telefone, CEP, endereço e forma de pagamento;
- criação de pedido online em tabela própria (`pedidos_online`);
- PWA instalável na tela inicial;
- API separada do painel administrativo;
- nenhuma venda é lançada automaticamente no ERP nesta fase: o pedido entra como `NOVO`, preservando estoque e financeiro até a validação interna.

## Arquitetura

Cliente (PWA) → API Loja → `pedidos_online` → validação interna → ERP

Essa separação impede que o cliente tenha qualquer acesso ao ERP e evita alterações indevidas em estoque/financeiro antes de o pedido ser confirmado.

## Execução local

```bash
pip install -r loja_cliente/requirements.txt
uvicorn loja_cliente.server:app --reload --port 8000
```

Abra `http://localhost:8000`.

## Próxima etapa

Criar no ERP a tela **Pedidos Online**, com ações de confirmar/cancelar e, ao confirmar, transformar o pedido em venda, contas a receber, financeiro, estoque e entrega de forma transacional.
