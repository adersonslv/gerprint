from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from impressoras.models import Impressora, LeituraContador, RelatorioMensal

# Mapeamento posição no txt → IP da impressora no banco
MAPA_IPS = {
    1: '192.168.1.10',  # Lexmark (B1) - TB
    2: '192.168.1.11',  # Brother (B1 - Primeira a esquerda)
    3: '192.168.1.12',  # Brother/Canon (B1 - Lado da Lexmark)
    4: '192.168.1.13',  # Toshiba (B1)
    5: '192.168.1.14',  # Cannon (Secretaria)
    6: '192.168.1.15',  # Lexmark (Secretaria)
    7: '192.168.1.16',  # Ricoh 377 (Secretaria)
    8: '192.168.1.17',  # Ricoh 4510 (Irmã Clarice)
    9: '192.168.1.18',  # Cannon (Elis)
}

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def parse_valor(texto):
    t = texto.strip()
    if not t:
        return None
    # Remove formato brasileiro: "317.341,00" → 317341
    t = t.replace('.', '').replace(',', '.')
    try:
        return int(float(t))
    except ValueError:
        return None


class Command(BaseCommand):
    help = 'Importa dados do arquivo TXT de contadores 2025'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', nargs='?',
                            default='contador_impressora_cfcr_2025.txt')

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        self.stdout.write(f'Lendo {arquivo}...')

        with open(arquivo, encoding='utf-8') as f:
            linhas = f.readlines()

        # Linha 0 é cabeçalho (começa com TAB); dados a partir da linha 1
        # Formato: nome_impressora TAB jan TAB fev ... TAB dez
        dados = []
        pos = 1
        for linha in linhas[1:]:
            cols = linha.rstrip('\n').split('\t')
            nome_txt = cols[0].strip()
            if not nome_txt:
                continue
            valores = [parse_valor(c) for c in cols[1:]]
            while len(valores) < 12:
                valores.append(None)
            dados.append((pos, nome_txt, valores[:12]))
            pos += 1

        self.stdout.write(f'  {len(dados)} impressoras encontradas no arquivo\n')

        for num, nome_txt, valores in dados:
            ip = MAPA_IPS.get(num)
            if not ip:
                self.stdout.write(self.style.WARNING(f'  Sem mapeamento para linha {num} ({nome_txt})'))
                continue

            try:
                imp = Impressora.objects.get(ip=ip)
            except Impressora.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  Impressora não encontrada: IP {ip}'))
                continue

            self.stdout.write(f'  [{num}] {nome_txt} → {imp.nome}')

            # Apaga leituras e relatórios de 2025 desta impressora
            LeituraContador.objects.filter(impressora=imp, lido_em__year=2025).delete()
            RelatorioMensal.objects.filter(impressora=imp, ano=2025).delete()

            prev_valor = None
            for mes_idx, valor in enumerate(valores):
                mes = mes_idx + 1

                if valor is None:
                    continue

                # Leitura de contador (último dia do mês)
                data_leitura = timezone.make_aware(datetime(2025, mes, 28))
                LeituraContador.objects.create(
                    impressora=imp,
                    lido_em=data_leitura,
                    valor_contador=valor,
                    manual=True,
                )

                # Relatório mensal
                if prev_valor is not None:
                    paginas = max(0, valor - prev_valor)
                    custo = paginas * imp.custo_por_pagina
                    RelatorioMensal.objects.update_or_create(
                        impressora=imp, ano=2025, mes=mes,
                        defaults={
                            'contador_inicial': prev_valor,
                            'contador_final': valor,
                            'paginas_impressas': paginas,
                            'custo_total': custo,
                        }
                    )
                    self.stdout.write(
                        f'      {MESES[mes_idx]:10}: {prev_valor:>10} → {valor:>10}  '
                        f'{paginas:>6} págs  R$ {float(custo):.2f}'
                    )

                prev_valor = valor

        self.stdout.write(self.style.SUCCESS('\nImportação 2025 concluída!'))
