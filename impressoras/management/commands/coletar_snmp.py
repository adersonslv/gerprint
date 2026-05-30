from django.core.management.base import BaseCommand
from impressoras.snmp_collector import coletar_todas


class Command(BaseCommand):
    help = 'Coleta contadores SNMP de todas as impressoras ativas'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando coleta SNMP...')
        resultados = coletar_todas()
        for r in resultados:
            status = self.style.SUCCESS('OK') if r['ok'] else self.style.ERROR(f"ERRO: {r['erro']}")
            self.stdout.write(f"  {r['impressora']}: {status}")
        self.stdout.write(self.style.SUCCESS(f'Coleta concluída. {len(resultados)} impressoras processadas.'))
