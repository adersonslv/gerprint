# GerPrint — Printer Management System

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-green?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![CI](https://github.com/adersonslv/gerprint/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

**GerPrint** is an open-source web system for monitoring network printers via SNMP. Track page counters, calculate costs per department, generate monthly reports, and schedule automatic data collection — all without installing any agent on the printers.

![GerPrint Dashboard](doc/screenshot/dashboard_gerprint.png)

> 🇧🇷 [Documentação em Português](README.md)

---

## ✨ Features

- **📊 Dashboard** with monthly KPIs, volume charts and printer ranking
- **🖨️ SNMP Monitoring** — reads page counters automatically (v1, v2c)
- **🔍 Network Scan** — discovers printers on the subnet with one click
- **💰 Monthly Reports** with pages and cost pivot table, CSV export
- **📅 Scheduled Collection** — by fixed time or interval
- **🎨 Multi-OID per printer** — sums PC-print and copy counters for true total
- **🔧 SNMP Diagnostic** — identifies the correct OID for any model
- **🏷️ Multi-entity** — groups printers by branch, department or contract

---

## 🚀 Quick Start

```bash
git clone https://github.com/adersonslv/gerprint.git
cd gerprint
docker compose up -d
```

Open **http://localhost:8000** · Admin: `admin` / `admin123`

> **SNMP note:** printers must be reachable from the container.
> If they don't respond, uncomment `network_mode: host` in `docker-compose.yml` (Linux only).

---

## 🖼️ Screenshots

<table>
  <tr>
    <td align="center">
      <img src="doc/screenshot/impressoras_gerprint.png" alt="Printer list" width="420"/>
      <br/><sub>Printer list</sub>
    </td>
    <td align="center">
      <img src="doc/screenshot/relatorios_gerprint.png" alt="Monthly report" width="420"/>
      <br/><sub>Monthly pivot report</sub>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="doc/screenshot/coletor_gerprint.png" alt="SNMP collection" width="420"/>
      <br/><sub>SNMP collection & scheduling</sub>
    </td>
    <td align="center">
      <img src="doc/screenshot/cadastroImpressora_gerprint.png" alt="Printer form" width="420"/>
      <br/><sub>Printer registration</sub>
    </td>
  </tr>
</table>

---

## 🛠️ Manual Installation

```bash
git clone https://github.com/adersonslv/gerprint.git
cd gerprint

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🖨️ Tested Printers

| Brand | Model | Counter OID | Notes |
|---|---|---|---|
| Canon | G7010 / G4100 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | Inkjet MFP |
| Canon | imageRUNNER 5110 / GX7010 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | Laser MFP |
| Brother | MFC-830 / KM-3540 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | |
| Ricoh | MP 3510 | `1.3.6.1.4.1.367.3.2.1.2.1.1.0` | Proprietary OID |
| Lexmark | LEX 711 | `1.3.6.1.2.1.43.10.2.1.4.1.1` | |

Full OID database: [`doc/oids_testados.md`](doc/oids_testados.md)

> Tested on a model not listed? Open an [issue](../../issues/new?template=novo_modelo.yml)!

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | insecure (dev) | Django secret key — **change in production** |
| `DEBUG` | `True` | Set `False` in production |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `DJANGO_SUPERUSER_USERNAME` | — | Auto-creates admin on first run |
| `DJANGO_SUPERUSER_PASSWORD` | — | Admin initial password |
| `PORT` | `8000` | Server port |

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

- 🐛 **Bugs** → [Bug report](../../issues/new?template=bug_report.yml)
- 💡 **Ideas** → [Feature request](../../issues/new?template=feature_request.yml)
- 🖨️ **New printer model** → [Submit OIDs](../../issues/new?template=novo_modelo.yml)
- 💬 **Questions** → [Discussions](../../discussions)

---

## 📄 License

Copyright © 2025 [Aderson Silva](mailto:aderson.slv@gmail.com) — [GPL v3](LICENSE)

<sub>Developed with the assistance of <a href="https://www.anthropic.com">Claude AI</a> (Anthropic)</sub>
