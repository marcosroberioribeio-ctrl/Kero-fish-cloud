# Kero Fish ERP Premium 12.1.0 — Estabilização Profissional

Base: `main` / ERP Premium 12.0.2.

## Segurança
- Backup oficial da 12.0.2 preservado na branch `backup-v12.0.2-premium`.
- Nova evolução isolada na branch `v12.1.0-profissional`.
- Snapshot SQLite consistente usando a API `backup()` do SQLite.
- Verificação `PRAGMA integrity_check` antes de aceitar um backup.
- Restauração protegida por backup de emergência e rollback se a integridade falhar.

## Regras de negócio
- Compra exige fornecedor, produto e quantidade válida.
- Venda exige cliente, produto e quantidade válida.
- Venda bloqueada quando o estoque disponível é insuficiente.
- Valor recebido não pode exceder o total da venda.
- Operações validadas registradas na auditoria.

## Operação e governança
- `app.py` tornou-se um entrypoint mínimo.
- Interface separada em `kero_fish/ui.py`.
- Camada de segurança/diagnóstico em `kero_fish/professional.py`.
- Nova tela Diagnóstico do Sistema.
- Auditoria passa a exibir eventos operacionais e importações.
- Backup e restauração reunidos em uma área segura.

## Qualidade
- GitHub Actions com quality gate.
- Compilação automática dos módulos Python.
- Testes unitários para moeda, datas e normalização brasileira.

## Regra de promoção
A `main` não deve ser alterada até a branch 12.1.0 passar nos testes e ser aprovada visualmente no Streamlit.
