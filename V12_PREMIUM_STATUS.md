# Kero Fish ERP V12 Premium

Preparação técnica concluída em 28/08/2026.

- Branch de segurança criada antes da V12: `backup-pre-v12-premium`.
- Desenvolvimento isolado na branch: `v12-premium`.
- Migração de bancos antigos revisada, inclusive colunas de fornecedores.
- Importação V9 validada com a base real.
- Resultado do teste: 3 produtos, 1 cliente, 2 fornecedores, 1 compra, 2 vendas, 2 entradas financeiras, 1 conta a pagar e 1 entrega.
- Compra validada: Camarão GG, 100 kg x R$ 35,00 = R$ 3.500,00.
- Vendas validadas: Camarão GG R$ 998,00 e Camarão G R$ 449,00.
- Importação é idempotente para evitar duplicidade.

Este arquivo marca o ponto seguro de preparação da V12 Premium antes da publicação do aplicativo na branch principal.