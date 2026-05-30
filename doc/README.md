# GerPrint — Sistema de Gestão de Impressoras

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Desenvolvido com Claude](https://img.shields.io/badge/Desenvolvido%20com-Claude%20AI-orange.svg)](https://www.anthropic.com)

Sistema web desenvolvido em Django para monitoramento e controle de impressoras via protocolo SNMP. Permite acompanhar contadores de páginas, calcular custos por impressora, gerar relatórios mensais e agendar coletas automáticas.

> **Desenvolvido com o auxílio do Claude**, modelo de inteligência artificial da [Anthropic](https://www.anthropic.com).

---

## Sumário

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Modelos de Dados](#modelos-de-dados)
- [Instalação](#instalação)
- [Iniciando o Servidor](#iniciando-o-servidor)
- [Funcionalidades](#funcionalidades)
- [Rotas (URLs)](#rotas-urls)
- [Comandos de Gerenciamento](#comandos-de-gerenciamento)
- [Agendamento Automático (Cron)](#agendamento-automático-cron)
- [Painel Administrativo](#painel-administrativo)

---

## Visão Geral

O GerPrint monitora impressoras conectadas à rede local (faixa `192.168.1.10–20`) usando SNMP para ler contadores de páginas. Os dados coletados são armazenados localmente e exibidos em um dashboard com gráficos, tabelas pivot mensais e exportação para CSV.

**Contexto de uso:** instituição com múltiplas impressoras distribuídas em setores (Loja, Secretaria, Educação Infantil, Coordenação, Contabilidade etc.).

---

## Tecnologias

| Componente | Versão |
|---|---|
| Python | 3.13 |
| Django | 6.0.5 |
| pysnmp | 7.1.27 |
| APScheduler | 3.11.2 |
| Bootstrap | 5.3.3 (CDN) |
| Chart.js | 4.4.3 (CDN) |
| Banco de dados | SQLite (`db.sqlite3`) |
| Fuso horário | America/Sao_Paulo |

---

## Estrutura do Projeto

```
app_server_gerprint/
├── core/                        # Configurações Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── impressoras/                 # App principal
│   ├── models.py                # Modelos de dados
│   ├── views.py                 # Views (lógica de negócio)
│   ├── urls.py                  # Rotas da aplicação
│   ├── forms.py                 # Formulários
│   ├── admin.py                 # Interface administrativa
│   ├── snmp_collector.py        # Coleta SNMP via pysnmp
│   │
│   ├── templates/impressoras/   # Templates HTML
│   │   ├── base.html            # Layout base (sidebar + topbar)
│   │   ├── dashboard.html       # Painel principal
│   │   ├── relatorios.html      # Relatório pivot mensal
│   │   ├── coletar.html         # Coleta imediata + agendamentos
│   │   ├── impressora_list.html
│   │   ├── impressora_detail.html
│   │   ├── impressora_form.html
│   │   ├── impressora_confirm_delete.html
│   │   └── leitura_manual.html
│   │
│   └── management/commands/     # Comandos CLI
│       ├── importar_planilha.py
│       ├── importar_txt_2025.py
│       ├── coletar_snmp.py
│       └── executar_agendamentos.py
│
├── doc/
│   └── README.md                # Esta documentação
│
├── db.sqlite3                   # Banco de dados SQLite
├── requirements.txt
├── manage.py
└── iniciar.sh                   # Script de inicialização rápida
```

---

## Modelos de Dados

### `Impressora`
Cadastro de cada impressora na rede.

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | CharField | Nome identificador |
| `localizacao` | CharField | Setor/local físico |
| `numero_serie` | CharField | Número de série |
| `ip` | GenericIPAddressField | Endereço IP na rede local |
| `comunidade_snmp` | CharField | Community SNMP (padrão: `public`) |
| `versao_snmp` | CharField | Versão SNMP: `1`, `2c` ou `3` |
| `oid_contador` | CharField | OID para leitura do contador de páginas |
| `oid_toner` | CharField | OID para nível de toner (opcional) |
| `custo_por_pagina` | DecimalField | Custo unitário por página impressa |
| `franquia_mensal` | DecimalField | Franquia mensal contratada |
| `ativo` | BooleanField | Se está sendo monitorada |

### `LeituraContador`
Registro histórico de cada leitura SNMP ou manual.

| Campo | Tipo | Descrição |
|---|---|---|
| `impressora` | ForeignKey | Impressora relacionada |
| `lido_em` | DateTimeField | Data/hora da leitura |
| `valor_contador` | BigIntegerField | Valor do contador de páginas |
| `nivel_toner` | IntegerField | Nível de toner em % (opcional) |
| `manual` | BooleanField | Se foi inserida manualmente |
| `erro` | CharField | Mensagem de erro SNMP (vazio = OK) |

### `RelatorioMensal`
Consolidação mensal de páginas e custos por impressora.

| Campo | Tipo | Descrição |
|---|---|---|
| `impressora` | ForeignKey | Impressora relacionada |
| `ano` / `mes` | IntegerField | Período de referência |
| `contador_inicial` | BigIntegerField | Contador no início do mês |
| `contador_final` | BigIntegerField | Contador no fim do mês |
| `paginas_impressas` | BigIntegerField | Calculado: `final - inicial` |
| `custo_total` | DecimalField | Calculado: `paginas × custo_por_pagina` |

> Os campos `paginas_impressas` e `custo_total` são recalculados automaticamente no `save()`.

### `AgendamentoColeta`
Configuração de coletas SNMP automáticas.

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | CharField | Nome descritivo do agendamento |
| `impressora` | ForeignKey | Impressora alvo (nulo = todas) |
| `todas` | BooleanField | Se coleta todas as impressoras |
| `frequencia` | CharField | `diaria` ou `intervalo` |
| `horario` | TimeField | Horário fixo (para frequência diária) |
| `intervalo_minutos` | PositiveIntegerField | Intervalo em minutos |
| `ativo` | BooleanField | Se está habilitado |
| `proxima_execucao` | DateTimeField | Próximo disparo agendado |
| `ultima_execucao` | DateTimeField | Última vez que foi executado |

---

## Instalação

```bash
# 1. Clonar/copiar o projeto
cd app_server_gerprint

# 2. Criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Aplicar as migrações
python manage.py migrate

# 5. Criar superusuário (se necessário)
python manage.py createsuperuser
```

### Importar dados históricos

**Via planilha ODS:**
```bash
python manage.py importar_planilha planilha_modelo_sistema_gestao_impressoras.ods
```

**Via arquivo TXT (contadores 2025):**
```bash
python manage.py importar_txt_2025 contador_impressora_cfcr_2025.txt
```

---

## Iniciando o Servidor

```bash
# Usando o script de inicialização
./iniciar.sh

# Ou manualmente
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Acesse em: `http://127.0.0.1:8000`

---

## Funcionalidades

### Dashboard
- KPIs do mês selecionado: total de páginas, custo, impressoras ativas.
- Gráfico de volume mensal (barras) e custo mensal (linha) para o ano.
- Ranking das top impressoras por volume no mês.
- Tabela de status SNMP em tempo real (Online / Erro / Sem dados).
- Filtro por ano e mês.

### Impressoras
- Listagem completa com status, último contador e ações rápidas.
- Cadastro, edição e exclusão de impressoras.
- Detalhe por impressora: histórico de leituras e gráficos do ano.
- Coleta SNMP individual diretamente da listagem.

### Relatórios
- Tabela pivot: Impressora × Mês com totais por linha e coluna.
- Duas abas: **Volume de Impressão** (páginas) e **Custos Mensais** (R$).
- Gráfico de barras por mês em cada aba.
- **Exportação CSV** com BOM UTF-8 (compatível com Excel) separado por `;`.
  - URL: `/relatorios/exportar/?ano=2025&tipo=volume`
  - URL: `/relatorios/exportar/?ano=2025&tipo=custos`

### Coleta SNMP
- **Coleta imediata**: dispara coleta agora para uma impressora específica ou todas.
- **Agendamentos**: cria, pausa, ativa, executa manualmente ou remove agendamentos.
  - Frequência diária com horário fixo.
  - Frequência por intervalo (a cada X minutos).
  - Alvo: impressora individual ou todas.

### Leitura Manual
- Permite registrar um contador manualmente quando a coleta SNMP não está disponível.

---

## Rotas (URLs)

| URL | Nome | Descrição |
|---|---|---|
| `/` | `dashboard` | Painel principal |
| `/impressoras/` | `impressora_list` | Lista todas as impressoras |
| `/impressoras/nova/` | `impressora_create` | Cadastrar impressora |
| `/impressoras/<id>/` | `impressora_detail` | Detalhe da impressora |
| `/impressoras/<id>/editar/` | `impressora_edit` | Editar impressora |
| `/impressoras/<id>/excluir/` | `impressora_delete` | Excluir impressora |
| `/impressoras/<id>/coletar/` | `coletar_impressora` | Coletar SNMP de uma |
| `/impressoras/<id>/leitura-manual/` | `leitura_manual` | Registrar leitura manual |
| `/coletar/` | `coletar` | Tela de coleta + agendamentos |
| `/coletar/agora/` | `coletar_todas` | Coletar todas (redireciona ao dashboard) |
| `/relatorios/` | `relatorios` | Relatório pivot anual |
| `/relatorios/exportar/` | `relatorios_csv` | Download CSV do relatório |
| `/api/status/` | `api_status` | JSON com status de todas as impressoras |
| `/admin/` | — | Painel administrativo Django |

---

## Comandos de Gerenciamento

```bash
# Coleta SNMP imediata de todas as impressoras ativas
python manage.py coletar_snmp

# Executa agendamentos vencidos (para uso com cron)
python manage.py executar_agendamentos

# Importa dados históricos da planilha ODS
python manage.py importar_planilha [arquivo.ods]

# Importa contadores do arquivo TXT 2025
python manage.py importar_txt_2025 [arquivo.txt]
```

---

## Agendamento Automático (Cron)

Os agendamentos criados pela interface precisam de um processo externo que execute o comando periodicamente. Adicione ao `crontab` do servidor:

```bash
crontab -e
```

```cron
# Verifica e executa agendamentos de coleta a cada minuto
* * * * * cd /caminho/para/app_server_gerprint && source venv/bin/activate && python manage.py executar_agendamentos >> /var/log/gerprint_coleta.log 2>&1
```

O comando verifica todos os agendamentos ativos com `proxima_execucao <= agora`, executa a coleta e recalcula a próxima execução automaticamente.

---

## Painel Administrativo

Acesse `/admin/` com as credenciais do superusuário.

- **Credenciais padrão (desenvolvimento):** `admin` / `admin123`
- Permite gerenciar diretamente `Impressora`, `LeituraContador` e `RelatorioMensal`.

---

## API

### `GET /api/status/`

Retorna o status atual de todas as impressoras ativas em JSON.

```json
{
  "impressoras": [
    {
      "id": 1,
      "nome": "Brother 830",
      "ip": "192.168.1.11",
      "contador": 71736,
      "nivel_toner": null,
      "online": true,
      "ultima_leitura": "2025-05-30T08:00:00-03:00",
      "erro": null
    }
  ]
}
```

---

## Observações de Segurança

> O projeto está configurado para **desenvolvimento**. Antes de usar em produção:

- Alterar `SECRET_KEY` em `settings.py` para um valor seguro e mantê-lo em variável de ambiente.
- Definir `DEBUG = False`.
- Restringir `ALLOWED_HOSTS` ao IP/domínio real do servidor.
- Configurar um banco de dados mais robusto (PostgreSQL).
- Servir arquivos estáticos via Nginx/Apache com `python manage.py collectstatic`.

---

## Desenvolvimento com Inteligência Artificial

Este projeto foi desenvolvido com o auxílio do **[Claude](https://www.anthropic.com)**, modelo de linguagem da Anthropic, utilizado como assistente de programação ao longo de todo o ciclo de desenvolvimento — incluindo modelagem de dados, views, templates, coleta SNMP, exportação CSV, agendamentos e documentação.

O uso de IA como ferramenta de desenvolvimento não altera os termos da licença: o código permanece sob responsabilidade do autor e distribuído integralmente sob GPL v3.

---

## Licença

Copyright (C) 2025  Aderson Silva \<aderson.slv@gmail.com\>

Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo sob os termos da **GNU General Public License** conforme publicada pela Free Software Foundation, na versão 3 da Licença, ou (a seu critério) qualquer versão posterior.

Este programa é distribuído na esperança de que seja útil, mas **SEM NENHUMA GARANTIA**; sem sequer a garantia implícita de COMERCIALIZAÇÃO ou ADEQUAÇÃO A UM FIM ESPECÍFICO.

- Texto completo da licença: [`../LICENSE`](../LICENSE)
- Explicação em português: [`LICENCA.md`](LICENCA.md)
- Texto oficial online: <https://www.gnu.org/licenses/gpl-3.0.html>
