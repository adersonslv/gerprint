import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from impressoras.models import Impressora, LeituraContador, RelatorioMensal

NS = {
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
}

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

NOMES_COMPLETOS = {
    1: ('LOJA - Lexmark LEX 711', 'LOJA', '74638D6601D8'),
    2: ('LOJA - Brother KM 3540', 'LOJA', 'LSH5611146'),
    3: ('LOJA - Canon 5110', 'LOJA', 'AEMK07695'),
    4: ('LOJA - Brother 830', 'LOJA', 'U67681G5H364140'),
    5: ('SECRETARIA - Canon 7010', 'SECRETARIA', 'KMLJ33178'),
    6: ('EDUC. INFANTIL - Canon 7010', 'EDUCAÇÃO INFANTIL', 'KMLJ11703'),
    7: ('COORD. ENS. MÉDIO - Canon G4100', 'COORD. ENS. MÉDIO', 'KKVG59057'),
    8: ('CONTABILIDADE - Canon G7010', 'CONTABILIDADE', 'KMLJ36560'),
    9: ('SECRETARIA - Ricoh R 3510', 'SECRETARIA', 'T316Q110165'),
    10: ('COORDENAÇÃO - Canon G7010', 'COORDENAÇÃO', 'KMLJ31609'),
    11: ('DIREÇÃO PEDAGOGIA - Canon 7010', 'DIREÇÃO PEDAGOGIA', 'KMLJ36564'),
    12: ('CONTABILIDADE - Canon 7010 (2)', 'CONTABILIDADE', 'KMNB21380'),
    13: ('DIR. RODRIGO - Canon 7010', 'DIREÇÃO', 'KMLJ29121'),
}


def get_cell_text(cell):
    texts = cell.findall('.//text:p', NS)
    return ' '.join(t.text or '' for t in texts if t.text).strip()


def parse_number(text):
    if not text or text in ('#REF!', ''):
        return None
    cleaned = text.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def get_sheet_rows(root, sheet_name):
    for sheet in root.findall('.//table:table', NS):
        name = sheet.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name')
        if name == sheet_name:
            rows = []
            for row in sheet.findall('table:table-row', NS):
                cells = row.findall('table:table-cell', NS)
                row_data = []
                for cell in cells:
                    repeat = int(cell.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated', 1))
                    text = get_cell_text(cell)
                    for _ in range(min(repeat, 5)):
                        row_data.append(text)
                rows.append(row_data)
            return rows
    return []


class Command(BaseCommand):
    help = 'Importa dados da planilha ODS para o banco de dados'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', nargs='?', default='planilha_modelo_sistema_gestao_impressoras.ods')

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        self.stdout.write(f'Importando {arquivo}...')

        z = zipfile.ZipFile(arquivo)
        content = z.read('content.xml').decode('utf-8')
        root = ET.fromstring(content)

        cadastro = get_sheet_rows(root, 'Cadastro_Impressoras')
        leituras = get_sheet_rows(root, 'Leituras_Contadores')

        impressoras_map = {}

        for row in cadastro[1:]:
            if len(row) < 10 or not row[1].strip().isdigit():
                continue
            id_imp = int(row[1])
            ip = row[6].strip() if len(row) > 6 else ''
            if not ip:
                continue

            custo_raw = parse_number(row[3]) if len(row) > 3 else 0.10
            custo = Decimal(str(custo_raw)) if custo_raw else Decimal('0.10')

            nome, localizacao, serie = NOMES_COMPLETOS.get(id_imp, (row[2], '', ''))
            comunidade = row[7].strip() if len(row) > 7 else 'public'
            oid_contador = row[9].strip() if len(row) > 9 else '1.3.6.1.2.1.43.10.2.1.4.1.1'
            oid_toner = row[10].strip() if len(row) > 10 else ''
            obs = row[11].strip() if len(row) > 11 else ''

            imp, created = Impressora.objects.update_or_create(
                ip=ip,
                defaults={
                    'nome': nome,
                    'localizacao': localizacao,
                    'numero_serie': serie,
                    'comunidade_snmp': comunidade,
                    'versao_snmp': '2c',
                    'oid_contador': oid_contador,
                    'oid_toner': oid_toner,
                    'custo_por_pagina': custo,
                    'ativo': True,
                    'observacoes': obs,
                }
            )
            impressoras_map[id_imp] = imp
            action = 'Criada' if created else 'Atualizada'
            self.stdout.write(f'  {action}: {nome} ({ip})')

        ano_atual = 2025
        for row in leituras:
            if len(row) < 4 or not row[1].strip().isdigit():
                continue
            id_imp = int(row[1])
            imp = impressoras_map.get(id_imp)
            if not imp:
                continue

            for mes_idx, mes_nome in enumerate(MESES):
                col = 4 + mes_idx
                if col >= len(row):
                    break
                valor = parse_number(row[col])
                if valor is None:
                    continue

                data = timezone.make_aware(datetime(ano_atual, mes_idx + 1, 28))
                LeituraContador.objects.get_or_create(
                    impressora=imp,
                    lido_em__year=ano_atual,
                    lido_em__month=mes_idx + 1,
                    manual=True,
                    defaults={
                        'lido_em': data,
                        'valor_contador': int(valor),
                        'manual': True,
                    }
                )

            self._gerar_relatorios(imp, leituras, id_imp, ano_atual)

        self.stdout.write(self.style.SUCCESS('Importação concluída!'))

    def _gerar_relatorios(self, imp, leituras, id_imp, ano):
        leitura_row = None
        for row in leituras:
            if len(row) > 1 and row[1].strip().isdigit() and int(row[1]) == id_imp:
                leitura_row = row
                break
        if not leitura_row:
            return

        contador_inicial = parse_number(leitura_row[3]) if len(leitura_row) > 3 else None
        if contador_inicial is None:
            return

        prev = int(contador_inicial)
        for mes_idx in range(12):
            col = 4 + mes_idx
            if col >= len(leitura_row):
                break
            atual = parse_number(leitura_row[col])
            if atual is None:
                break

            RelatorioMensal.objects.update_or_create(
                impressora=imp,
                ano=ano,
                mes=mes_idx + 1,
                defaults={
                    'contador_inicial': prev,
                    'contador_final': int(atual),
                }
            )
            RelatorioMensal.objects.filter(impressora=imp, ano=ano, mes=mes_idx + 1).update(
                paginas_impressas=max(0, int(atual) - prev),
                custo_total=max(0, int(atual) - prev) * imp.custo_por_pagina,
            )
            prev = int(atual)
