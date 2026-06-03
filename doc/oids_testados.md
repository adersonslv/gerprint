# Banco Comunitário de OIDs — GerPrint

Modelos de impressoras testados pela comunidade com suas configurações SNMP.

> **Como contribuir:** testou um modelo não listado? Abra uma
> [issue de novo modelo](../../issues/new?template=novo_modelo.yml) — não precisa saber programar.

---

## Como usar esta tabela

1. Localize seu fabricante/modelo
2. Copie o(s) OID(s) listado(s)
3. No GerPrint, edite a impressora e cole o OID no campo **"OID Contador"**
4. Para modelos multifuncionais com múltiplos OIDs, coloque **um por linha** — os valores são somados automaticamente

---

## Canon

### Inkjet / Ink Tank (série G, PIXMA, MAXIFY)

| Modelo | OID Contador | Versão SNMP | Observações |
|---|---|---|---|
| Canon G7010 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | Multifuncional. `.4.1.1` = impressão PC. Adicionar `.4.1.2` se quiser somar cópias |
| Canon G4100 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | |

### Laser / Multifuncional (imageRUNNER, MAXIFY GX)

| Modelo | OID Contador | Versão SNMP | Observações |
|---|---|---|---|
| imageRUNNER 5110 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | |
| MAXIFY GX7010 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | Identificado como "Canon 7010" no SNMP |

### OIDs de Toner — Canon (geral)

| Cor | OID |
|---|---|
| Preto | `1.3.6.1.2.1.43.11.1.1.9.1.1` |
| Ciano | `1.3.6.1.2.1.43.11.1.1.9.1.2` |
| Magenta | `1.3.6.1.2.1.43.11.1.1.9.1.3` |
| Amarelo | `1.3.6.1.2.1.43.11.1.1.9.1.4` |

---

## Brother

| Modelo | OID Contador | Versão SNMP | Observações |
|---|---|---|---|
| MFC-830 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | |
| KM-3540 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | |

### OID alternativo Brother (total pages)

```
1.3.6.1.4.1.2435.2.3.9.4.2.1.1.1.1.0
```

---

## Ricoh

| Modelo | OID Contador | Versão SNMP | Observações |
|---|---|---|---|
| MP 3510 | `1.3.6.1.4.1.367.3.2.1.2.1.1.0` | v2c | OID proprietário Ricoh |

### OID padrão como fallback

```
1.3.6.1.2.1.43.10.2.1.4.1.1
```

---

## Lexmark

| Modelo | OID Contador | Versão SNMP | Observações |
|---|---|---|---|
| LEX 711 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | v2c | |

---

## OIDs padrão (funciona na maioria dos modelos)

Estes OIDs seguem o **Printer MIB (RFC 3805)** e funcionam na maioria das impressoras de rede:

| OID | Descrição |
|---|---|
| `1.3.6.1.2.1.43.10.2.1.4.1.1` | `prtMarkerLifeCount` — contador vitalício, motor 1 |
| `1.3.6.1.2.1.43.10.2.1.4.1.2` | `prtMarkerLifeCount` — contador vitalício, motor 2 |

---

## OIDs proprietários por fabricante

| Fabricante | OID | Tipo |
|---|---|---|
| Ricoh / Aficio | `1.3.6.1.4.1.367.3.2.1.2.1.1.0` | Total counter |
| HP | `1.3.6.1.4.1.11.2.3.9.4.2.1.4.1.2.5` | Total pages |
| Konica Minolta | `1.3.6.1.4.1.18334.1.1.1.5.7.2.1.0` | Total counter |
| Brother | `1.3.6.1.4.1.2435.2.3.9.4.2.1.1.1.1.0` | Total pages |
| Kyocera | `1.3.6.1.4.1.1347.43.10.1.1.12.1.1` | Total counter |
| Epson | `1.3.6.1.4.1.1248.1.2.2.1.1.1.5.1` | Total impressions |

---

## Diagnóstico no GerPrint

Se seu modelo não está listado, use a ferramenta integrada:

1. Acesse o detalhe da impressora
2. Clique em **"Diagnosticar OID"**
3. Clique em **"Testar todos os OIDs"**
4. O OID que retornar o valor correto é o que deve ser configurado

Depois, registre o resultado abrindo uma [issue](../../issues/new?template=novo_modelo.yml) para ajudar outros usuários!
