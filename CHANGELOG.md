# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Adicionado
- Diagnóstico SNMP (`/impressoras/<id>/snmp-probe/`) — testa múltiplos OIDs e permite aplicar o correto com um clique
- Suporte a múltiplos OIDs por impressora — valores somados automaticamente na coleta (útil para separar impressão PC + cópia local em multifuncionais)
- Escaneamento de rede (`/impressoras/escanear/`) — detecta impressoras via SNMP em uma sub-rede /24
- `docker-compose.yml` e `Dockerfile` para deploy em um comando
- Variáveis de ambiente para `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS`
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- Templates de issue: bug report, feature request, novo modelo de impressora
- CI via GitHub Actions (lint + Django check)

---

## [0.1.0] — 2025-05-01

### Adicionado
- **Dashboard** com KPIs mensais, gráfico de volume, gráfico de custo e ranking de impressoras
- **Cadastro de impressoras** com suporte a SNMP v1/v2c, múltiplos toners e custo por página
- **Coleta SNMP** individual ou em lote com registro histórico de leituras
- **Agendamentos** de coleta por horário fixo ou intervalo em minutos
- **Relatório mensal** em tabela pivot (Impressora × Mês) com abas de volume e custo
- **Exportação CSV** com BOM UTF-8 compatível com Excel
- **Leitura manual** de contador quando SNMP não está disponível
- **Monitoramento de toner** com barra de progresso por cor e alertas de nível crítico
- **Status de hardware** via `hrPrinterDetectedErrorState` (papel, atolamento, tampa aberta etc.)
- **Multi-entidade** — agrupa impressoras por filial ou setor com filtro no dashboard e relatórios
- **API JSON** em `/api/status/` com status de todas as impressoras ativas
- **Painel administrativo** Django em `/admin/`
- Comandos de gerenciamento: `importar_planilha`, `importar_txt_2025`, `coletar_snmp`, `executar_agendamentos`
- Modelos de dados: `Impressora`, `LeituraContador`, `LeituraToner`, `TonerConfig`, `RelatorioMensal`, `AgendamentoColeta`

### Impressoras validadas no lançamento
- Canon G7010, G4100, imageRUNNER 5110, MAXIFY GX7010
- Brother MFC-830, KM-3540
- Ricoh MP 3510
- Lexmark LEX 711
