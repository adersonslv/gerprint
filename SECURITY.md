# Política de Segurança

## Versões suportadas

| Branch / Tag | Suporte de segurança |
|---|---|
| `main` | ✅ Ativo |
| Releases anteriores | ❌ Sem suporte |

Recomendamos sempre usar a versão mais recente do repositório.

## Reportando uma vulnerabilidade

**Não abra uma issue pública para relatar vulnerabilidades de segurança.**

Envie um e-mail para **aderson.slv@gmail.com** com:

- Descrição da vulnerabilidade
- Passos para reproduzir
- Impacto potencial
- Sugestão de correção (opcional)

### O que esperar

| Prazo | Ação |
|---|---|
| Até 48h | Confirmação de recebimento |
| Até 7 dias | Avaliação e classificação |
| Até 30 dias | Correção ou plano de correção |

Você será creditado na correção (a menos que prefira anonimato).

## Escopo

### Dentro do escopo

- Injeção de código (SQL, command injection, XSS)
- Autenticação/autorização inadequada
- Exposição de dados sensíveis (SECRET_KEY, senhas, dados de impressoras)
- CSRF ou outras vulnerabilidades de sessão

### Fora do escopo

- Vulnerabilidades dependentes de `DEBUG=True` ou `SECRET_KEY` insegura em produção — a documentação já alerta sobre isso
- Problemas na infraestrutura de rede SNMP do usuário
- Ataques de força bruta sem rate limiting (sem autenticação habilitada no deploy padrão)

## Boas práticas para deploy em produção

Antes de expor o GerPrint na rede, configure:

```bash
SECRET_KEY=<chave-longa-e-aleatória>   # openssl rand -base64 50
DEBUG=False
ALLOWED_HOSTS=192.168.1.100,gerprint.intranet
```

Consulte a seção **Observações de Segurança** em [`doc/README.md`](doc/README.md) para orientações completas.
