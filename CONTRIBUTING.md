# Guia de Contribuição — GerPrint

Obrigado pelo interesse em contribuir! Este documento explica como participar do projeto, independente do nível de experiência.

---

## Tipos de contribuição

| Tipo | Como fazer |
|---|---|
| 🐛 Reportar bug | Abra uma [issue de bug](../../issues/new?template=bug_report.yml) |
| 💡 Sugerir funcionalidade | Abra uma [issue de feature](../../issues/new?template=feature_request.yml) |
| 🖨️ Registrar modelo testado | Abra uma [issue de modelo](../../issues/new?template=novo_modelo.yml) |
| 📝 Melhorar documentação | Edite e abra um Pull Request |
| 🔧 Enviar código | Siga o fluxo abaixo |

---

## Ambiente de desenvolvimento

### Pré-requisitos

- Python 3.11+
- Git
- Acesso a pelo menos uma impressora com SNMP habilitado (opcional para desenvolver UI)

### Setup

```bash
git clone https://github.com/adersonslv/gerprint.git
cd gerprint

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # usuário, e-mail e senha de sua escolha

python manage.py runserver
```

Acesse **http://127.0.0.1:8000**

---

## Fluxo de Pull Request

```
fork → branch → commits → PR
```

1. **Fork** do repositório no GitHub
2. **Crie uma branch** com nome descritivo:
   ```bash
   git checkout -b fix/coleta-timeout-snmp
   git checkout -b feat/exportar-pdf
   git checkout -b docs/adiciona-ricoh-mp3010
   ```
3. **Faça seus commits** (veja padrão abaixo)
4. **Abra o PR** contra a branch `main` usando o template fornecido
5. Aguarde revisão — responderemos em até 7 dias

### Regras básicas

- Um PR por funcionalidade/correção — PRs grandes demais dificultam a revisão
- Inclua uma descrição clara do problema que resolve e como testar
- Se alterar comportamento existente, mencione o impacto

---

## Padrão de commits

Use o formato `tipo: descrição curta em minúsculas`:

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Apenas documentação |
| `refactor` | Refatoração sem mudança de comportamento |
| `chore` | Dependências, CI, configuração |

**Exemplos:**
```
feat: adiciona exportação em PDF dos relatórios
fix: coleta SNMP falha silenciosamente quando IP inválido
docs: adiciona OIDs testados para Kyocera ECOSYS
chore: atualiza pysnmp para 7.2
```

- Limite a linha de assunto a 72 caracteres
- Use o corpo do commit para explicar o **porquê**, não o **o quê**

---

## Adicionando suporte a um novo modelo de impressora

Esta é a contribuição mais valiosa para o projeto. Segue o fluxo:

### 1. Descubra o OID correto

Use a ferramenta de diagnóstico do próprio GerPrint:

- Abra o detalhe de qualquer impressora → botão **"Diagnosticar OID"**
- Clique em **"Testar todos os OIDs"** com a impressora acessível
- Anote qual OID retornou o valor correto (confira no display/relatório da impressora)

Ou via linha de comando:
```bash
snmpwalk -v2c -c public <IP_DA_IMPRESSORA> 1.3.6.1.2.1.43.10.2.1.4.1
```

### 2. Registre via issue

Abra uma [issue de novo modelo](../../issues/new?template=novo_modelo.yml) com as informações. Isso já é suficiente para a contribuição — não precisa saber programar.

### 3. (Opcional) Atualize a tabela no README

Se quiser enviar um PR, adicione uma linha à tabela de **Impressoras testadas** no `README.md`:

```markdown
| Kyocera | ECOSYS M2135dn | `1.3.6.1.2.1.43.10.2.1.4.1.1` | SNMP v2c |
```

---

## Estilo de código

- Siga [PEP 8](https://peps.python.org/pep-0008/) para Python
- Nomenclatura em **português** para variáveis de domínio (`impressora`, `leitura`, `contador`) — mantém coerência com o restante do código
- Sem comentários óbvios; comente apenas o **porquê** de decisões não triviais
- Templates HTML: indentação com 2 espaços, Bootstrap 5 para componentes visuais

---

## Dúvidas

Abra uma [Discussion](../../discussions) ou mencione na issue relevante. Não use issues para perguntas gerais sobre Django ou SNMP — prefira Stack Overflow ou a documentação oficial.

---

## Código de Conduta

Este projeto adota o [Contributor Covenant](https://www.contributor-covenant.org/pt-br/version/2/1/code_of_conduct/).
Seja respeitoso, construtivo e inclusivo em todas as interações.
